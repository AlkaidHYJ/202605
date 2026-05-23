from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.im import ImFriend, ImGroup, ImGroupMember, ImMessage
from app.models.system import SysUser
from app.models.business import DigitalAgent
from app.schemas.common import PageResult, ResponseModel
from app.schemas.im import (
    FriendAdd,
    FriendOut,
    GroupCreate,
    GroupMemberAdd,
    GroupMemberOut,
    GroupOut,
    MessageOut,
    MessageSend,
)
from app.services import im_service
from app.services.agent_runtime import find_mentioned_agents, generate_agent_reply
from app.websocket.manager import ws_manager

router = APIRouter()


def _agent_member_id(agent_id: int) -> int:
    return -abs(agent_id)


def _build_group_history_text(db: Session, group_id: int) -> str:
    messages = (
        db.query(ImMessage)
        .filter(ImMessage.group_id == group_id, ImMessage.is_recalled == 0)
        .order_by(ImMessage.created_at.desc())
        .limit(settings.IM_CONTEXT_ROUNDS * 2)
        .all()
    )
    messages = list(reversed(messages))
    members = db.query(ImGroupMember).filter(ImGroupMember.group_id == group_id).all()
    user_ids = [m.user_id for m in members if m.user_id > 0]
    agent_ids = [abs(m.user_id) for m in members if m.user_id < 0]
    users = db.query(SysUser).filter(SysUser.id.in_(user_ids)).all() if user_ids else []
    agents = (
        db.query(DigitalAgent).filter(DigitalAgent.id.in_(agent_ids)).all()
        if agent_ids
        else []
    )
    user_map = {u.id: u for u in users}
    agent_map = {a.id: a for a in agents}
    lines: list[str] = []
    for message in messages:
        if message.sender_id == 0:
            sender_name = "系统消息"
        elif message.sender_id > 0:
            user = user_map.get(message.sender_id)
            sender_name = user.real_name or user.username if user else f"用户{message.sender_id}"
        else:
            agent = agent_map.get(abs(message.sender_id))
            sender_name = agent.agent_name if agent else f"数字员工{abs(message.sender_id)}"
        lines.append(f"{sender_name}: {message.content}")
    return "\n".join(lines).strip()


def _build_group_members(db: Session, group_id: int) -> list[GroupMemberOut]:
    members = db.query(ImGroupMember).filter(ImGroupMember.group_id == group_id).all()
    user_ids = [m.user_id for m in members if m.user_id > 0]
    agent_ids = [abs(m.user_id) for m in members if m.user_id < 0]
    users = (
        db.query(SysUser).filter(SysUser.id.in_(user_ids)).all()
        if user_ids
        else []
    )
    agents = (
        db.query(DigitalAgent).filter(DigitalAgent.id.in_(agent_ids)).all()
        if agent_ids
        else []
    )
    user_map = {u.id: u for u in users}
    agent_map = {a.id: a for a in agents}
    result: list[GroupMemberOut] = []
    for member in members:
        if member.user_id > 0:
            user_row = user_map.get(member.user_id)
            if not user_row:
                continue
            result.append(
                GroupMemberOut(
                    user_id=member.user_id,
                    username=user_row.username,
                    real_name=user_row.real_name,
                    role=member.role,
                    member_type="user",
                )
            )
        else:
            agent_id = abs(member.user_id)
            agent = agent_map.get(agent_id)
            if not agent:
                continue
            result.append(
                GroupMemberOut(
                    user_id=member.user_id,
                    username=None,
                    real_name=None,
                    role=member.role,
                    member_type="agent",
                    agent_id=agent_id,
                    agent_name=agent.agent_name,
                )
            )
    return result


@router.post("/messages", response_model=ResponseModel[MessageOut])
async def send_message(
    body: MessageSend,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    if body.chat_type == 2 and body.group_id:
        group = db.query(ImGroup).filter(ImGroup.id == body.group_id).first()
        if not group or group.status == 3:
            raise HTTPException(400, "群组不存在或已解散")
        if group.status == 2:
            raise HTTPException(403, "群组已全员禁言")

    allowed, hit_word, audit_status = im_service.check_message_content(db, body.content)
    if not allowed:
        raise HTTPException(400, detail=f"含违规内容，命中敏感词：{hit_word}")

    msg = im_service.save_message(
        db,
        chat_type=body.chat_type,
        sender_id=user.id,
        content=body.content,
        msg_type=body.msg_type,
        receiver_id=body.receiver_id,
        group_id=body.group_id,
        audit_status=audit_status,
        hit_word=hit_word,
        hit_level=2 if hit_word else None,
    )
    payload = {
        "type": "message",
        "data": {
            **MessageOut.model_validate(msg).model_dump(),
            "sender_name": user.real_name or user.username,
        },
    }
    if body.chat_type == 1 and body.receiver_id:
        await ws_manager.send_to_users({user.id, body.receiver_id}, payload)
    if body.chat_type == 2 and body.group_id:
        group_members = db.query(ImGroupMember).filter(ImGroupMember.group_id == body.group_id).all()
        member_ids = [
            m.user_id
            for m in group_members
            if m.user_id > 0
        ]
        await ws_manager.send_to_users(set(member_ids), payload)
        if body.msg_type == 1:
            agent_ids = [abs(m.user_id) for m in group_members if m.user_id < 0]
            if agent_ids:
                agent_rows = (
                    db.query(DigitalAgent)
                    .filter(DigitalAgent.id.in_(agent_ids), DigitalAgent.status == 1)
                    .all()
                )
                mentioned_agents = find_mentioned_agents(body.content, agent_rows)
                if mentioned_agents:
                    history_text = _build_group_history_text(db, body.group_id)
                    for agent in mentioned_agents:
                        result = generate_agent_reply(
                            db,
                            agent.id,
                            body.content,
                            history_text=history_text,
                        )
                        agent_msg = im_service.save_message(
                            db,
                            chat_type=2,
                            sender_id=_agent_member_id(agent.id),
                            content=result["reply"],
                            msg_type=1,
                            receiver_id=None,
                            group_id=body.group_id,
                            audit_status=0,
                            hit_word=None,
                            hit_level=None,
                        )
                        agent_payload = {
                            "type": "message",
                            "data": {
                                **MessageOut.model_validate(agent_msg).model_dump(),
                                "sender_name": agent.agent_name,
                            },
                        }
                        await ws_manager.send_to_users(set(member_ids), agent_payload)
                        history_text = f"{history_text}\n{agent.agent_name}: {result['reply']}".strip()
    return ResponseModel(data=MessageOut.model_validate(msg))


@router.get("/messages", response_model=ResponseModel[PageResult[MessageOut]])
def list_messages(
    chat_type: int | None = None,
    group_id: int | None = None,
    receiver_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    q = db.query(ImMessage).filter(ImMessage.is_recalled == 0)
    if group_id:
        q = q.filter(ImMessage.group_id == group_id)
    if receiver_id:
        q = q.filter(
            ((ImMessage.sender_id == user.id) & (ImMessage.receiver_id == receiver_id))
            | ((ImMessage.sender_id == receiver_id) & (ImMessage.receiver_id == user.id))
        )
    if chat_type:
        q = q.filter(ImMessage.chat_type == chat_type)
    total = q.count()
    items = (
        q.order_by(ImMessage.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ResponseModel(
        data=PageResult(
            total=total,
            items=[MessageOut.model_validate(m) for m in reversed(items)],
        )
    )


@router.post("/groups", response_model=ResponseModel[GroupOut])
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    group = ImGroup(
        group_name=body.group_name,
        owner_id=user.id,
        is_bot_enabled=1 if body.invite_bot else 0,
    )
    db.add(group)
    db.flush()
    db.add(ImGroupMember(group_id=group.id, user_id=user.id, role=1))
    for mid in body.member_ids:
        if mid != user.id:
            db.add(ImGroupMember(group_id=group.id, user_id=mid, role=3))
    if body.invite_bot:
        db.add(ImGroupMember(group_id=group.id, user_id=0, role=4))
    for agent_id in body.agent_ids:
        db.add(
            ImGroupMember(
                group_id=group.id,
                user_id=_agent_member_id(agent_id),
                role=4,
            )
        )
    db.commit()
    db.refresh(group)
    return ResponseModel(data=GroupOut.model_validate(group))


@router.get("/groups", response_model=ResponseModel[list[GroupOut]])
def my_groups(db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    group_ids = (
        db.query(ImGroupMember.group_id)
        .filter(ImGroupMember.user_id == user.id)
        .subquery()
    )
    groups = (
        db.query(ImGroup)
        .filter(ImGroup.id.in_(group_ids), ImGroup.is_deleted == 0, ImGroup.status != 3)
        .all()
    )
    return ResponseModel(data=[GroupOut.model_validate(g) for g in groups])


@router.get("/groups/{group_id}/members", response_model=ResponseModel[list[GroupMemberOut]])
def group_members(
    group_id: int,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    in_group = db.query(ImGroupMember).filter(
        ImGroupMember.group_id == group_id, ImGroupMember.user_id == user.id
    ).first()
    if not in_group:
        raise HTTPException(status_code=403, detail="无权查看该群成员")
    return ResponseModel(data=_build_group_members(db, group_id))


@router.post("/groups/{group_id}/members", response_model=ResponseModel[list[GroupMemberOut]])
def add_group_members(
    group_id: int,
    body: GroupMemberAdd,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    in_group = db.query(ImGroupMember).filter(
        ImGroupMember.group_id == group_id, ImGroupMember.user_id == user.id
    ).first()
    if not in_group:
        raise HTTPException(status_code=403, detail="无权修改该群成员")
    for member_id in body.member_ids:
        if member_id == user.id:
            continue
        exists = db.query(ImGroupMember).filter(
            ImGroupMember.group_id == group_id,
            ImGroupMember.user_id == member_id,
        ).first()
        if not exists:
            db.add(ImGroupMember(group_id=group_id, user_id=member_id, role=3))
    for agent_id in body.agent_ids:
        agent_user_id = _agent_member_id(agent_id)
        exists = db.query(ImGroupMember).filter(
            ImGroupMember.group_id == group_id,
            ImGroupMember.user_id == agent_user_id,
        ).first()
        if not exists:
            db.add(ImGroupMember(group_id=group_id, user_id=agent_user_id, role=4))
    db.commit()
    return group_members(group_id, db, user)


@router.get("/friends", response_model=ResponseModel[list[FriendOut]])
def list_friends(db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    friends = (
        db.query(ImFriend, SysUser)
        .join(SysUser, SysUser.id == ImFriend.friend_id)
        .filter(ImFriend.user_id == user.id, ImFriend.status == 1)
        .all()
    )
    return ResponseModel(
        data=[
            FriendOut(
                friend_id=friend.friend_id,
                username=friend_user.username,
                real_name=friend_user.real_name,
                status=friend_user.status,
            )
            for friend, friend_user in friends
        ]
    )


@router.post("/friends", response_model=ResponseModel[FriendOut])
def add_friend(
    body: FriendAdd,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    if body.friend_id == user.id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")
    friend_user = db.query(SysUser).filter(SysUser.id == body.friend_id).first()
    if not friend_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    exist = (
        db.query(ImFriend)
        .filter(ImFriend.user_id == user.id, ImFriend.friend_id == body.friend_id)
        .first()
    )
    if not exist:
        db.add(ImFriend(user_id=user.id, friend_id=body.friend_id, status=1))
        db.add(ImFriend(user_id=body.friend_id, friend_id=user.id, status=1))
        db.commit()
    return ResponseModel(
        data=FriendOut(
            friend_id=friend_user.id,
            username=friend_user.username,
            real_name=friend_user.real_name,
            status=friend_user.status,
        )
    )
