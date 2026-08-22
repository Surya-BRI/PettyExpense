import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models import ErpAuthExpenseUsers, ErpExpenseNotification, ErpExpenseNotificationPreference
from services.email_service import email_service

logger = logging.getLogger("expense.notifications")

CHANNELS = ("email", "in_app")


def _is_enabled(db: Session, user_id: int, channel: str, category: str) -> bool:
    pref = (
        db.query(ErpExpenseNotificationPreference)
        .filter(
            ErpExpenseNotificationPreference.user_id == user_id,
            ErpExpenseNotificationPreference.channel == channel,
            ErpExpenseNotificationPreference.category == category,
        )
        .first()
    )
    return pref.is_enabled == 1 if pref else True  # no preference row means enabled by default


def _already_sent(db: Session, transaction_id: Optional[int], type_: str, user_id: int, channel: str) -> bool:
    existing = (
        db.query(ErpExpenseNotification)
        .filter(
            ErpExpenseNotification.transaction_id == transaction_id,
            ErpExpenseNotification.type == type_,
            ErpExpenseNotification.user_id == user_id,
            ErpExpenseNotification.channel == channel,
        )
        .first()
    )
    return existing is not None


def _record(db: Session, user_id: int, transaction_id: Optional[int], type_: str, channel: str, status: str, message: str) -> None:
    db.add(
        ErpExpenseNotification(
            user_id=user_id,
            transaction_id=transaction_id,
            type=type_,
            channel=channel,
            status=status,
            message=message,
            sent_at=datetime.utcnow(),
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # a concurrent call already recorded this exact (transaction, type, user, channel) row


def _pick_language(user: ErpAuthExpenseUsers, en: str, ar: str) -> str:
    return ar if user.language_preference == "ar" else en


def _send_channel(
    db: Session,
    user: ErpAuthExpenseUsers,
    type_: str,
    transaction_id: Optional[int],
    channel: str,
    subject_en: str,
    subject_ar: str,
    body_en: str,
    body_ar: str,
) -> None:
    if not _is_enabled(db, user.user_id, channel, type_):
        return
    if _already_sent(db, transaction_id, type_, user.user_id, channel):
        return
    subject = _pick_language(user, subject_en, subject_ar)
    body = _pick_language(user, body_en, body_ar)
    if channel == "email":
        sent = email_service.notify(user.email, subject, body)
        _record(db, user.user_id, transaction_id, type_, channel, "sent" if sent else "failed", f"{subject}\n\n{body}")
    else:
        _record(db, user.user_id, transaction_id, type_, channel, "sent", f"{subject}\n\n{body}")


def send(
    db: Session,
    user: Optional[ErpAuthExpenseUsers],
    type_: str,
    transaction_id: Optional[int],
    subject_en: str,
    subject_ar: str,
    body_en: str,
    body_ar: str,
) -> None:
    # No approver could be resolved for this stage — nothing to notify, not an error.
    if user is None:
        return
    for channel in CHANNELS:
        try:
            _send_channel(db, user, type_, transaction_id, channel, subject_en, subject_ar, body_en, body_ar)
        except Exception:
            # A notification failure must never surface to the caller or affect the already-committed state change.
            logger.exception(
                "Notification failed: user=%s type=%s channel=%s transaction=%s", user.user_id, type_, channel, transaction_id
            )


def send_test(db: Session, user: ErpAuthExpenseUsers, channel: str, subject: str, body: str) -> bool:
    # Bypasses idempotency/preferences deliberately — this is an explicit admin credential check, not a real lifecycle event.
    if channel == "email":
        sent = email_service.notify(user.email, subject, body)
    else:
        sent = True
    _record(db, user.user_id, None, "test", channel, "sent" if sent else "failed", f"{subject}\n\n{body}")
    return sent


def list_for_user(db: Session, user_id: int, limit: int = 20, offset: int = 0) -> list[ErpExpenseNotification]:
    return (
        db.query(ErpExpenseNotification)
        .filter(ErpExpenseNotification.user_id == user_id, ErpExpenseNotification.channel == "in_app")
        .order_by(ErpExpenseNotification.sent_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(ErpExpenseNotification)
        .filter(
            ErpExpenseNotification.user_id == user_id,
            ErpExpenseNotification.channel == "in_app",
            ErpExpenseNotification.status != "read",
        )
        .count()
    )


def mark_read(db: Session, user_id: int, notification_id: int) -> None:
    row = (
        db.query(ErpExpenseNotification)
        .filter(ErpExpenseNotification.notification_id == notification_id, ErpExpenseNotification.user_id == user_id)
        .first()
    )
    if not row:
        raise LookupError("Notification not found")
    row.status = "read"
    db.commit()


def mark_all_read(db: Session, user_id: int) -> int:
    rows = (
        db.query(ErpExpenseNotification)
        .filter(
            ErpExpenseNotification.user_id == user_id,
            ErpExpenseNotification.channel == "in_app",
            ErpExpenseNotification.status != "read",
        )
        .all()
    )
    for row in rows:
        row.status = "read"
    db.commit()
    return len(rows)
