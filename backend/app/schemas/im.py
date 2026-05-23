from datetime import datetime

from pydantic import BaseModel, Field


class MessageSend(BaseModel):
    chat_type: int = Field(..., description="1单聊 2群聊")
    receiver_id: int | None = None
    group_id: int | None = None
    content: str = Field(..., min_length=1, max_length=2000000)
    msg_type: int = 1


class FriendAdd(BaseModel):
    friend_id: int


class MessageOut(BaseModel):
    id: int
    chat_type: int
    sender_id: int
    receiver_id: int | None
    group_id: int | None
    content: str
    msg_type: int
    is_recalled: int
    audit_status: int
    created_at: datetime

    class Config:
        from_attributes = True


class GroupCreate(BaseModel):
    group_name: str
    member_ids: list[int] = []
    invite_bot: bool = False
    agent_ids: list[int] = []


class GroupAdminCreate(BaseModel):
    group_name: str
    owner_id: int
    member_ids: list[int] = []
    is_bot_enabled: int = 1
    status: int = 1
    agent_ids: list[int] = []


class GroupAdminUpdate(BaseModel):
    group_name: str | None = None
    owner_id: int | None = None
    is_bot_enabled: int | None = None
    status: int | None = None


class SystemMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    msg_type: int = 99


class GroupOut(BaseModel):
    id: int
    group_name: str
    owner_id: int
    status: int
    is_bot_enabled: int
    created_at: datetime

    class Config:
        from_attributes = True


class FriendOut(BaseModel):
    friend_id: int
    username: str
    real_name: str | None
    status: int


class FriendRequestOut(BaseModel):
    requester_id: int
    username: str
    real_name: str | None
    created_at: datetime


class UserProfileOut(BaseModel):
    user_id: int
    username: str
    real_name: str | None
    avatar: str | None
    status: int


class GroupMemberOut(BaseModel):
    user_id: int
    username: str | None
    real_name: str | None
    role: int
    member_type: str = "user"
    agent_id: int | None = None
    agent_name: str | None = None


class GroupMemberAdd(BaseModel):
    member_ids: list[int] = []
    agent_ids: list[int] = []


class SensitiveWordCreate(BaseModel):
    word: str
    level: int
    category: str | None = None


class MessageSearch(BaseModel):
    sender_id: int | None = None
    group_id: int | None = None
    keyword: str | None = None
    msg_type: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    page: int = 1
    page_size: int = 20


class RecallRequest(BaseModel):
    message_id: int
    reason: str = "该消息因违规被管理员撤回"
