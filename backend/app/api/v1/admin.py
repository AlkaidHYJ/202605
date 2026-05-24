import json
from hashlib import sha256

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin, hash_password
from app.models.im import ImGroup, ImGroupMember, ImMessage, ImSensitiveWord
from app.models.business import AiModel, AiSkill, DigitalAgent
from app.models.system import SysDept, SysUser
from app.schemas.ai import (
    AiModelCreate,
    AiModelOut,
    AiModelTestRequest,
    AiModelUpdate,
    AiSkillAutoGenerateOut,
    AiSkillAutoGenerateRequest,
    AiSkillCreate,
    AiSkillOut,
    AiSkillUpdate,
    DigitalAgentCreate,
    DigitalAgentOut,
    DigitalAgentPromptGenerateRequest,
    DigitalAgentUpdate,
)
from app.schemas.auth import UserCreate, UserOut, UserUpdate
from app.schemas.common import PageResult, ResponseModel
from app.schemas.im import (
    GroupAdminCreate,
    GroupAdminUpdate,
    GroupOut,
    MessageOut,
    RecallRequest,
    SensitiveWordCreate,
    SystemMessageRequest,
)
from app.services import im_service
from app.services.skill_executor import execute_skill
from app.websocket.manager import ws_manager

router = APIRouter()


class SkillRunRequest(BaseModel):
    args: dict = Field(default_factory=dict)


def _json_list(value: list[int] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _agent_member_id(agent_id: int) -> int:
    return -abs(agent_id)


def _parse_file_message(message: ImMessage) -> dict | None:
    if message.msg_type != 2:
        return None
    try:
        payload = json.loads(message.content)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    file_url = payload.get("url") or payload.get("fileUrl")
    if not file_url:
        return None
    file_type = payload.get("type") or "file"
    if file_type not in {"image", "file"}:
        return None
    fingerprint = sha256(file_url.encode("utf-8")).hexdigest()
    return {
        "file_id": fingerprint,
        "file_name": payload.get("fileName") or payload.get("name") or f"文件-{message.id}",
        "file_size": payload.get("fileSize") or "-",
        "file_type": file_type,
        "file_url": file_url,
        "source_message_id": message.id,
        "group_id": message.group_id,
        "sender_id": message.sender_id,
        "created_at": message.created_at,
    }


def _openai_chat(base_url: str, api_key: str, model_id: str, message: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        url = normalized + "/chat/completions"
    else:
        url = normalized + "/v1/chat/completions"
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"模型请求失败: {resp.text}")
        data = resp.json()
        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices:
            return _openai_chat_stream(client, url, payload, headers)
        return (
            choices[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )


def _openai_chat_stream(
    client: httpx.Client,
    url: str,
    payload: dict,
    headers: dict,
) -> str:
    stream_payload = {**payload, "stream": True}
    content_chunks: list[str] = []
    with client.stream("POST", url, json=stream_payload, headers=headers) as resp:
        if resp.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"模型请求失败: {resp.text}")
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("data: "):
                data = line[len("data: ") :].strip()
            else:
                continue
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            delta = (
                (chunk.get("choices") or [{}])[0].get("delta", {}) if isinstance(chunk, dict) else {}
            )
            piece = delta.get("content") or delta.get("reasoning_content") or ""
            if piece:
                content_chunks.append(piece)
    return "".join(content_chunks).strip()


@router.get("/users", response_model=ResponseModel[PageResult[UserOut]])
def list_users(
    keyword: str | None = None,
    user_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(SysUser)
    if user_id:
        q = q.filter(SysUser.id == user_id)
    if keyword:
        q = q.filter(
            (SysUser.username.contains(keyword)) | (SysUser.real_name.contains(keyword))
        )
    total = q.count()
    users = q.offset((page - 1) * page_size).limit(page_size).all()
    return ResponseModel(
        data=PageResult(total=total, items=[UserOut.model_validate(u) for u in users])
    )


@router.post("/users", response_model=ResponseModel[UserOut])
def create_user(body: UserCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    if db.query(SysUser).filter(SysUser.username == body.username).first():
        raise HTTPException(400, "用户名已存在")
    user = SysUser(
        username=body.username,
        password_hash=hash_password(body.password),
        real_name=body.real_name,
        dept_id=body.dept_id,
        is_admin=body.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ResponseModel(data=UserOut.model_validate(user))


@router.put("/users/{user_id}", response_model=ResponseModel[UserOut])
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if body.username and body.username != user.username:
        if db.query(SysUser).filter(SysUser.username == body.username).first():
            raise HTTPException(400, "用户名已存在")
        user.username = body.username
    if body.password:
        user.password_hash = hash_password(body.password)
    if body.real_name is not None:
        user.real_name = body.real_name
    if body.dept_id is not None:
        user.dept_id = body.dept_id
    if body.status is not None:
        user.status = body.status
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    db.commit()
    db.refresh(user)
    return ResponseModel(data=UserOut.model_validate(user))


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: SysUser = Depends(get_current_admin),
):
    if admin.id == user_id:
        raise HTTPException(400, "不能删除当前登录管理员")
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.is_admin == 1:
        raise HTTPException(400, "不能删除管理员账号")
    db.delete(user)
    db.commit()
    return ResponseModel(message="用户已删除")


@router.get("/depts")
def list_depts(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    depts = db.query(SysDept).filter(SysDept.status == 1).order_by(SysDept.sort_order).all()
    return ResponseModel(
        data=[
            {"id": d.id, "parent_id": d.parent_id, "dept_name": d.dept_name}
            for d in depts
        ]
    )


@router.get("/groups", response_model=ResponseModel[PageResult[GroupOut]])
def admin_groups(
    keyword: str | None = None,
    group_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(ImGroup).filter(ImGroup.is_deleted == 0)
    if group_id:
        q = q.filter(ImGroup.id == group_id)
    if keyword:
        q = q.filter(ImGroup.group_name.contains(keyword))
    total = q.count()
    groups = q.order_by(ImGroup.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ResponseModel(
        data=PageResult(total=total, items=[GroupOut.model_validate(g) for g in groups])
    )


@router.post("/groups", response_model=ResponseModel[GroupOut])
def admin_create_group(
    body: GroupAdminCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    owner = db.query(SysUser).filter(SysUser.id == body.owner_id).first()
    if not owner:
        raise HTTPException(404, "群主不存在")
    group = ImGroup(
        group_name=body.group_name,
        owner_id=body.owner_id,
        is_bot_enabled=body.is_bot_enabled,
        status=body.status,
    )
    db.add(group)
    db.flush()
    db.add(ImGroupMember(group_id=group.id, user_id=body.owner_id, role=1))
    for member_id in body.member_ids:
        if member_id != body.owner_id:
            db.add(ImGroupMember(group_id=group.id, user_id=member_id, role=3))
    if body.is_bot_enabled == 1:
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


@router.put("/groups/{group_id}", response_model=ResponseModel[GroupOut])
def admin_update_group(
    group_id: int,
    body: GroupAdminUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    group = db.query(ImGroup).filter(ImGroup.id == group_id).first()
    if not group:
        raise HTTPException(404, "群组不存在")
    if body.group_name is not None:
        group.group_name = body.group_name
    if body.owner_id is not None:
        group.owner_id = body.owner_id
    if body.is_bot_enabled is not None:
        group.is_bot_enabled = body.is_bot_enabled
    if body.status is not None:
        group.status = body.status
    db.commit()
    db.refresh(group)
    return ResponseModel(data=GroupOut.model_validate(group))


@router.delete("/groups/{group_id}")
def admin_delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    group = db.query(ImGroup).filter(ImGroup.id == group_id).first()
    if not group:
        raise HTTPException(404, "群组不存在")
    group.is_deleted = 1
    group.status = 3
    db.commit()
    return ResponseModel(message="群组已删除")


@router.post("/groups/{group_id}/mute")
def mute_group(group_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    group = db.query(ImGroup).filter(ImGroup.id == group_id).first()
    if not group:
        raise HTTPException(404, "群组不存在")
    group.status = 2
    db.commit()
    return ResponseModel(message="已全员禁言")


@router.post("/groups/{group_id}/dissolve")
def dissolve_group(group_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    group = db.query(ImGroup).filter(ImGroup.id == group_id).first()
    if not group:
        raise HTTPException(404, "群组不存在")
    group.status = 3
    group.is_deleted = 1
    db.commit()
    return ResponseModel(message="群组已解散（软删除）")


@router.get("/messages", response_model=ResponseModel[PageResult[MessageOut]])
def search_messages(
    sender_id: int | None = None,
    group_id: int | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(ImMessage)
    if sender_id:
        q = q.filter(ImMessage.sender_id == sender_id)
    if group_id:
        q = q.filter(ImMessage.group_id == group_id)
    if keyword:
        q = q.filter(ImMessage.content.contains(keyword))
    total = q.count()
    items = q.order_by(ImMessage.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ResponseModel(
        data=PageResult(total=total, items=[MessageOut.model_validate(m) for m in items])
    )


@router.post("/messages/recall")
async def recall_message_api(
    body: RecallRequest,
    db: Session = Depends(get_db),
    admin: SysUser = Depends(get_current_admin),
):
    msg = im_service.recall_message(db, body.message_id, admin.id, body.reason)
    if not msg:
        raise HTTPException(404, "消息不存在")
    await ws_manager.broadcast_recall(msg.id, body.reason)
    return ResponseModel(message="撤回指令已下发")


@router.post("/groups/{group_id}/system-message", response_model=ResponseModel[MessageOut])
async def admin_send_system_message(
    group_id: int,
    body: SystemMessageRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    group = db.query(ImGroup).filter(ImGroup.id == group_id).first()
    if not group or group.is_deleted == 1 or group.status == 3:
        raise HTTPException(404, "群组不存在或已解散")
    msg = im_service.save_message(
        db,
        chat_type=2,
        sender_id=0,
        content=body.content,
        msg_type=body.msg_type,
        receiver_id=None,
        group_id=group_id,
        audit_status=0,
        hit_word=None,
        hit_level=None,
    )
    payload = {
        "type": "message",
        "data": {
            **MessageOut.model_validate(msg).model_dump(),
            "sender_name": "系统消息",
            "system": True,
        },
    }
    member_ids = [
        m.user_id
        for m in db.query(ImGroupMember).filter(ImGroupMember.group_id == group_id).all()
    ]
    await ws_manager.send_to_users(set(member_ids), payload)
    return ResponseModel(data=MessageOut.model_validate(msg))


@router.get("/sensitive-words")
def list_sensitive_words(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    words = db.query(ImSensitiveWord).all()
    return ResponseModel(
        data=[{"id": w.id, "word": w.word, "level": w.level, "category": w.category} for w in words]
    )


@router.post("/sensitive-words")
def add_sensitive_word(
    body: SensitiveWordCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    w = ImSensitiveWord(word=body.word, level=body.level, category=body.category)
    db.add(w)
    db.commit()
    im_service.reload_sensitive_words(db)
    return ResponseModel(message="已添加并刷新词库")


@router.get("/group-members/{group_id}")
def group_members(group_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    members = (
        db.query(ImGroupMember)
        .filter(ImGroupMember.group_id == group_id)
        .order_by(ImGroupMember.role.asc(), ImGroupMember.join_time.asc())
        .all()
    )
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
    data: list[dict] = []
    for member in members:
        if member.user_id > 0:
            user = user_map.get(member.user_id)
            if not user:
                continue
            data.append(
                {
                    "id": member.id,
                    "user_id": member.user_id,
                    "username": user.username,
                    "real_name": user.real_name,
                    "avatar": user.avatar,
                    "role": member.role,
                    "member_type": "user",
                    "join_time": member.join_time.isoformat(),
                }
            )
            continue
        agent_id = abs(member.user_id)
        agent = agent_map.get(agent_id)
        if not agent:
            continue
        data.append(
            {
                "id": member.id,
                "user_id": member.user_id,
                "username": None,
                "real_name": None,
                "avatar": None,
                "role": member.role,
                "member_type": "agent",
                "agent_id": agent_id,
                "agent_name": agent.agent_name,
                "join_time": member.join_time.isoformat(),
            }
        )
    return ResponseModel(data=data)


@router.get("/groups/{group_id}/members")
def group_members_alias(group_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return group_members(group_id, db, _)


@router.get("/files")
def list_files(
    group_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(ImMessage).filter(ImMessage.msg_type == 2)
    if group_id:
        q = q.filter(ImMessage.group_id == group_id)
    messages = q.order_by(ImMessage.created_at.desc()).all()
    files: dict[str, dict] = {}
    for message in messages:
        file_item = _parse_file_message(message)
        if not file_item:
            continue
        asset = files.get(file_item["file_id"])
        if not asset:
            files[file_item["file_id"]] = {
                **file_item,
                "reference_count": 1,
                "latest_message_id": message.id,
                "latest_created_at": message.created_at,
            }
            continue
        asset["reference_count"] += 1
        if message.created_at > asset["latest_created_at"]:
            asset["latest_message_id"] = message.id
            asset["latest_created_at"] = message.created_at
            asset["group_id"] = message.group_id
            asset["sender_id"] = message.sender_id
            asset["source_message_id"] = message.id
    items = sorted(files.values(), key=lambda item: item["latest_created_at"], reverse=True)
    for item in items:
        item["latest_created_at"] = item["latest_created_at"].isoformat()
    return ResponseModel(data={"items": items})


@router.get("/groups/{group_id}/files")
def list_files_alias(
    group_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    return list_files(group_id=group_id, db=db, _=_)


@router.get("/models", response_model=ResponseModel[PageResult[AiModelOut]])
def list_models(
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(AiModel)
    if keyword:
        q = q.filter((AiModel.model_name.contains(keyword)) | (AiModel.model_id.contains(keyword)))
    total = q.count()
    items = q.order_by(AiModel.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ResponseModel(
        data=PageResult(total=total, items=[AiModelOut.model_validate(m) for m in items])
    )


@router.post("/models", response_model=ResponseModel[AiModelOut])
def create_model(
    body: AiModelCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    model = AiModel(
        model_name=body.model_name,
        model_type=body.model_type,
        base_url=body.base_url,
        api_key=body.api_key,
        model_id=body.model_id,
        is_default=body.is_default,
        status=body.status,
    )
    if body.is_default == 1:
        db.query(AiModel).update({AiModel.is_default: 0})
    db.add(model)
    db.commit()
    db.refresh(model)
    return ResponseModel(data=AiModelOut.model_validate(model))


@router.put("/models/{model_id}", response_model=ResponseModel[AiModelOut])
def update_model(
    model_id: int,
    body: AiModelUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    model = db.query(AiModel).filter(AiModel.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(model, field, value)
    if body.is_default == 1:
        db.query(AiModel).filter(AiModel.id != model_id).update({AiModel.is_default: 0})
    db.commit()
    db.refresh(model)
    return ResponseModel(data=AiModelOut.model_validate(model))


@router.post("/models/{model_id}/set-default")
def set_default_model(
    model_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    model = db.query(AiModel).filter(AiModel.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")
    db.query(AiModel).update({AiModel.is_default: 0})
    model.is_default = 1
    db.commit()
    return ResponseModel(message="默认模型已更新")


@router.delete("/models/{model_id}")
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    model = db.query(AiModel).filter(AiModel.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")
    db.delete(model)
    db.commit()
    return ResponseModel(message="模型已删除")


@router.post("/models/{model_id}/test")
def test_model(
    model_id: int,
    body: AiModelTestRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    model = db.query(AiModel).filter(AiModel.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")
    reply = _openai_chat(model.base_url, model.api_key, model.model_id, body.message)
    return ResponseModel(data={"reply": reply})


@router.get("/skills", response_model=ResponseModel[PageResult[AiSkillOut]])
def list_skills(
    keyword: str | None = None,
    skill_type: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(AiSkill)
    if keyword:
        q = q.filter(AiSkill.skill_name.contains(keyword))
    if skill_type:
        q = q.filter(AiSkill.skill_type == skill_type)
    total = q.count()
    items = q.order_by(AiSkill.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ResponseModel(
        data=PageResult(total=total, items=[AiSkillOut.model_validate(s) for s in items])
    )


@router.post("/skills", response_model=ResponseModel[AiSkillOut])
def create_skill(
    body: AiSkillCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    skill = AiSkill(**body.model_dump(by_alias=True))
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return ResponseModel(data=AiSkillOut.model_validate(skill))


@router.put("/skills/{skill_id}", response_model=ResponseModel[AiSkillOut])
def update_skill(
    skill_id: int,
    body: AiSkillUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    skill = db.query(AiSkill).filter(AiSkill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, "技能不存在")
    for field, value in body.model_dump(exclude_unset=True, by_alias=True).items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return ResponseModel(data=AiSkillOut.model_validate(skill))


@router.post("/skills/{skill_id}/run")
def run_skill(
    skill_id: int,
    body: SkillRunRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    skill = db.query(AiSkill).filter(AiSkill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, "技能不存在")
    try:
        result = execute_skill(skill, body.args)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"技能执行失败: {exc}") from exc
    return ResponseModel(data=result)


@router.delete("/skills/{skill_id}")
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    skill = db.query(AiSkill).filter(AiSkill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, "技能不存在")
    db.delete(skill)
    db.commit()
    return ResponseModel(message="技能已删除")


@router.post("/skills/auto-generate", response_model=ResponseModel[AiSkillAutoGenerateOut])
def auto_generate_skill(
    body: AiSkillAutoGenerateRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    model = db.query(AiModel).filter(AiModel.id == body.model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")
    hint = body.description_hint or ""
    prompt = (
        "你是技能设计助手。请输出 JSON，仅包含 description 和 schema_json 两个字段。"
        "description 是技能介绍，schema_json 是函数调用参数 JSON Schema。"
        f"技能名称: {body.skill_name}\n"
        f"技能类型: {body.skill_type}\n"
        f"补充说明: {hint}"
    )
    content = _openai_chat(model.base_url, model.api_key, model.model_id, prompt)
    description = ""
    schema_json = ""
    try:
        data = json.loads(content)
        description = str(data.get("description", ""))
        schema_json = json.dumps(data.get("schema_json", {}), ensure_ascii=False)
    except Exception:
        description = content
        schema_json = "{}"
    return ResponseModel(data=AiSkillAutoGenerateOut(description=description, schema_json=schema_json))


@router.get("/agents", response_model=ResponseModel[PageResult[DigitalAgentOut]])
def list_admin_agents(
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(DigitalAgent)
    if keyword:
        q = q.filter(DigitalAgent.agent_name.contains(keyword))
    total = q.count()
    items = q.order_by(DigitalAgent.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ResponseModel(
        data=PageResult(total=total, items=[DigitalAgentOut.model_validate(a) for a in items])
    )


@router.post("/agents", response_model=ResponseModel[DigitalAgentOut])
def create_admin_agent(
    body: DigitalAgentCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    agent = DigitalAgent(
        agent_name=body.agent_name,
        persona=body.persona,
        model_id=body.model_id,
        skill_ids=_json_list(body.skill_ids),
        status=body.status,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return ResponseModel(data=DigitalAgentOut.model_validate(agent))


@router.put("/agents/{agent_id}", response_model=ResponseModel[DigitalAgentOut])
def update_admin_agent(
    agent_id: int,
    body: DigitalAgentUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    agent = db.query(DigitalAgent).filter(DigitalAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "数字员工不存在")
    data = body.model_dump(exclude_unset=True)
    if "skill_ids" in data:
        data["skill_ids"] = _json_list(data["skill_ids"])
    for field, value in data.items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return ResponseModel(data=DigitalAgentOut.model_validate(agent))


@router.delete("/agents/{agent_id}")
def delete_admin_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    agent = db.query(DigitalAgent).filter(DigitalAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "数字员工不存在")
    db.delete(agent)
    db.commit()
    return ResponseModel(message="数字员工已删除")


@router.post("/agents/generate-prompt")
def generate_agent_prompt(
    body: DigitalAgentPromptGenerateRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    skills = (
        db.query(AiSkill)
        .filter(AiSkill.id.in_(body.skill_ids))
        .all()
        if body.skill_ids
        else []
    )
    skill_names = [s.skill_name for s in skills]
    base_prompt = body.base_prompt or "你是企业数字员工，负责结合技能完成任务。"
    if skill_names:
        prompt = base_prompt + " 可调用技能: " + ", ".join(skill_names)
    else:
        prompt = base_prompt
    return ResponseModel(data={"prompt": prompt})
