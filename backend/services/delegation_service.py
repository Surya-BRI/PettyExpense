"""Backup approvers (delegation, Spec 5.2).

An approver who will be away names a backup for a date range -- themselves from the app, or
Admin for them. While the range is on, every bill waiting on the approver goes to the backup
instead: queue, approve/dispute/reject rights, submission emails and SLA alerts
(approval_service.resolve_stage_approvers applies it). Nothing is copied or moved, so bills
go back to the approver by themselves when the range ends or the backup is removed.

Dates are calendar days in Gulf time (UTC+4) -- the dates people pick in the app.
"""
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, exists, or_
from sqlalchemy.orm import Session

from auth.security import APPROVER_ROLES
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseApproverDelegation,
    ErpExpenseHodAssignment,
    ErpMasterExpenseRole,
)
from services.region_scope import belongs_to_region, user_region_ids

GULF_OFFSET = timedelta(hours=4)

ROLE_LABELS = {
    "hod": "Head of Department",
    "accountant": "Accountant",
    "head_accountant": "Head of Accountant",
    "finance_manager": "Finance Manager",
    "admin": "Admin",
}


def today() -> str:
    """Today's date (YYYY-MM-DD) in Gulf time."""
    return (datetime.utcnow() + GULF_OFFSET).date().isoformat()


def _user(db: Session, user_id: int) -> Optional[ErpAuthExpenseUsers]:
    return db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == user_id).first()


def _role_code(user: Optional[ErpAuthExpenseUsers]) -> Optional[str]:
    return user.role.role_code if user is not None and user.role is not None else None


def _person(user: Optional[ErpAuthExpenseUsers]) -> Optional[dict[str, Any]]:
    if user is None:
        return None
    role = _role_code(user)
    return {
        "id": user.user_id,
        "display_name": user.display_name,
        "role": role,
        "role_label": ROLE_LABELS.get(role or "", role or ""),
        "department_name": user.department.department_name if user.department else None,
    }


def to_dict(db: Session, d: ErpExpenseApproverDelegation) -> dict[str, Any]:
    now = today()
    return {
        "id": d.delegation_id,
        "approver_id": d.approver_id,
        "backup_id": d.backup_id,
        "approver": _person(_user(db, d.approver_id)),
        "backup": _person(_user(db, d.backup_id)),
        "start_date": d.start_date,
        "end_date": d.end_date,
        "is_active": d.start_date <= now <= d.end_date,
    }


def list_for(db: Session, approver_id: Optional[int] = None, include_past: bool = False) -> list[dict[str, Any]]:
    """Current and upcoming backups (oldest first), for one approver or everyone."""
    q = db.query(ErpExpenseApproverDelegation)
    if approver_id is not None:
        q = q.filter(ErpExpenseApproverDelegation.approver_id == approver_id)
    if not include_past:
        q = q.filter(ErpExpenseApproverDelegation.end_date >= today())
    rows = q.order_by(ErpExpenseApproverDelegation.start_date, ErpExpenseApproverDelegation.delegation_id).all()
    return [to_dict(db, d) for d in rows]


# Approval levels, lowest first. A backup must be at the approver's level or above.
ROLE_LEVELS = ("hod", "accountant", "head_accountant", "finance_manager")


def _hod_department_ids(db: Session, user: ErpAuthExpenseUsers) -> set[int]:
    """Departments an HOD heads (active HOD assignments; their own department as fallback)."""
    ids = {
        d
        for (d,) in db.query(ErpExpenseHodAssignment.department_id).filter(
            ErpExpenseHodAssignment.user_id == user.user_id, ErpExpenseHodAssignment.is_active == 1
        )
    }
    if not ids and user.department_id:
        ids = {user.department_id}
    return ids


def candidates(db: Session, approver_id: int) -> list[dict[str, Any]]:
    """Who can be this approver's backup:
    - same role or higher (HOD < Accountant < Head of Accountant < Finance Manager);
    - an HOD only from the same department -- never another department's HOD;
    - in the approver's own company (home company; Admin-ticked ones if no home is recorded)."""
    approver = _user(db, approver_id)
    role = _role_code(approver)
    if approver is None or role not in ROLE_LEVELS:
        return []
    allowed_roles = ROLE_LEVELS[ROLE_LEVELS.index(role):]

    q = (
        db.query(ErpAuthExpenseUsers)
        .join(ErpAuthExpenseUsers.role)
        .filter(
            ErpMasterExpenseRole.role_code.in_(allowed_roles),
            ErpAuthExpenseUsers.is_active == 1,
            ErpAuthExpenseUsers.is_deleted == 0,
            ErpAuthExpenseUsers.user_id != approver_id,
        )
    )

    companies = {approver.home_region_id} if approver.home_region_id else user_region_ids(db, approver_id)
    if companies:
        # belongs_to_region, not covers_region: people with no company recorded don't count.
        q = q.filter(and_(*[belongs_to_region(r) for r in companies]))

    if role == "hod":
        departments = _hod_department_ids(db, approver)
        heads_same_department = exists().where(
            ErpExpenseHodAssignment.user_id == ErpAuthExpenseUsers.user_id,
            ErpExpenseHodAssignment.is_active == 1,
            ErpExpenseHodAssignment.department_id.in_(departments or {-1}),
        )
        q = q.filter(
            or_(
                ErpMasterExpenseRole.role_code != "hod",
                heads_same_department,
                ErpAuthExpenseUsers.department_id.in_(departments or {-1}),
            )
        )
    return [_person(u) for u in q.order_by(ErpAuthExpenseUsers.display_name).all()]


def _parse(value: str, what: str) -> str:
    try:
        return date.fromisoformat((value or "").strip()[:10]).isoformat()
    except ValueError as exc:
        raise ValueError(f"Choose the {what} date") from exc


def create(db: Session, approver_id: int, backup_id: int, start_date: str, end_date: str) -> dict[str, Any]:
    """Raises LookupError (unknown person) or ValueError (anything the person must fix)."""
    from services import notification_service

    approver = _user(db, approver_id)
    if approver is None:
        raise LookupError("Approver not found")
    if _role_code(approver) not in APPROVER_ROLES:
        raise ValueError("Only an HOD, Accountant, Head of Accountant or Finance Manager can have a backup")
    if backup_id == approver_id:
        raise ValueError("Choose someone else as the backup")
    if backup_id not in {c["id"] for c in candidates(db, approver_id)}:
        raise ValueError(
            "The backup must be in the same company, at the same level or higher, "
            "and an HOD only from the same department"
        )

    start = _parse(start_date, "start")
    end = _parse(end_date, "end")
    if end < start:
        raise ValueError("The end date must be on or after the start date")
    if end < today():
        raise ValueError("The end date has already passed")

    overlap = (
        db.query(ErpExpenseApproverDelegation)
        .filter(
            ErpExpenseApproverDelegation.approver_id == approver_id,
            ErpExpenseApproverDelegation.start_date <= end,
            ErpExpenseApproverDelegation.end_date >= start,
        )
        .first()
    )
    if overlap is not None:
        other = _user(db, overlap.backup_id)
        raise ValueError(
            f"{approver.display_name} already has a backup ({other.display_name if other else 'someone'}) "
            f"from {overlap.start_date} to {overlap.end_date}. Remove it first."
        )

    d = ErpExpenseApproverDelegation(approver_id=approver_id, backup_id=backup_id, start_date=start, end_date=end)
    db.add(d)
    db.commit()
    db.refresh(d)

    backup = _user(db, backup_id)
    who = approver.display_name or "an approver"
    notification_service.send(
        db,
        backup,
        f"delegation_{d.delegation_id}"[:32],
        None,
        f"You are the backup approver for {who}",
        f"أنت المعتمد البديل عن {who}",
        f"From {start} to {end}, bills waiting for {who} come to you. "
        f"You can approve, dispute or reject them from your Claims queue.",
        f"من {start} إلى {end}، ستصلك المطالبات التي تنتظر موافقة {who}. "
        f"يمكنك اعتمادها أو الاعتراض عليها أو رفضها من قائمة المطالبات.",
    )
    return to_dict(db, d)


def remove(db: Session, delegation_id: int, approver_id: Optional[int] = None) -> None:
    """approver_id: when given (an approver removing their own backup), it must be theirs."""
    d = (
        db.query(ErpExpenseApproverDelegation)
        .filter(ErpExpenseApproverDelegation.delegation_id == delegation_id)
        .first()
    )
    if d is None or (approver_id is not None and d.approver_id != approver_id):
        raise LookupError("Backup not found")
    db.delete(d)
    db.commit()
