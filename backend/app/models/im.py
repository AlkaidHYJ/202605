from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImGroup(Base):
    __tablename__ = "im_group"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(String(128), nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[int] = mapped_column(
        Integer, default=1, comment="1正常 2禁言 3解散"
    )
    is_bot_enabled: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ImGroupMember(Base):
    __tablename__ = "im_group_member"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    role: Mapped[int] = mapped_column(
        Integer, default=3, comment="1群主 2管理员 3普通 4数字员工"
    )
    join_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ImMessage(Base):
    __tablename__ = "im_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_type: Mapped[int] = mapped_column(Integer, comment="1单聊 2群聊")
    sender_id: Mapped[int] = mapped_column(BigInteger, index=True)
    receiver_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    group_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    msg_type: Mapped[int] = mapped_column(
        Integer, default=1, comment="1文本 2文件 3数据卡片"
    )
    is_recalled: Mapped[int] = mapped_column(Integer, default=0)
    audit_status: Mapped[int] = mapped_column(
        Integer, default=0, comment="0正常 1已审计 2已阻断"
    )
    recall_reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ImFriend(Base):
    __tablename__ = "im_friend"
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_im_friend"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    friend_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1正常 0删除")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ImSensitiveWord(Base):
    __tablename__ = "im_sensitive_word"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, comment="1阻断 2审计")
    category: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ImMessageAuditLog(Base):
    __tablename__ = "im_message_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    hit_word: Mapped[str | None] = mapped_column(String(128))
    hit_level: Mapped[int | None] = mapped_column(Integer)
    operator_id: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[int] = mapped_column(
        Integer, comment="1阻断 2打标 3撤回"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
