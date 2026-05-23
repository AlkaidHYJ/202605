from sqlalchemy.orm import Session

from app.models.im import ImGroup, ImGroupMember, ImMessage, ImMessageAuditLog, ImSensitiveWord
from app.services.sensitive_filter import engine


def reload_sensitive_words(db: Session):
    words = db.query(ImSensitiveWord).all()
    engine.build([(w.word, w.level, w.category) for w in words])


def check_message_content(db: Session, content: str) -> tuple[bool, str | None, int]:
    """返回 (是否允许发送, 命中词, audit_status)"""
    hit = engine.max_level(content)
    if not hit:
        return True, None, 0
    if hit.level == 1:
        return False, hit.word, 2
    return True, hit.word, 1


def save_message(
    db: Session,
    *,
    chat_type: int,
    sender_id: int,
    content: str,
    msg_type: int,
    receiver_id: int | None,
    group_id: int | None,
    audit_status: int,
    hit_word: str | None,
    hit_level: int | None,
) -> ImMessage:
    msg = ImMessage(
        chat_type=chat_type,
        sender_id=sender_id,
        receiver_id=receiver_id,
        group_id=group_id,
        content=content,
        msg_type=msg_type,
        audit_status=audit_status,
    )
    db.add(msg)
    db.flush()
    if hit_word:
        db.add(
            ImMessageAuditLog(
                message_id=msg.id,
                hit_word=hit_word,
                hit_level=hit_level,
                action=1 if hit_level == 1 else 2,
            )
        )
    db.commit()
    db.refresh(msg)
    return msg


def recall_message(
    db: Session, message_id: int, operator_id: int, reason: str
) -> ImMessage | None:
    msg = db.query(ImMessage).filter(ImMessage.id == message_id).first()
    if not msg:
        return None
    msg.is_recalled = 1
    msg.recall_reason = reason
    db.add(
        ImMessageAuditLog(
            message_id=msg.id,
            operator_id=operator_id,
            action=3,
        )
    )
    db.commit()
    db.refresh(msg)
    return msg
