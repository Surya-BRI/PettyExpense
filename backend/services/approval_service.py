import json
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from auth.security import CurrentUser
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseApproverDelegation,
    ErpExpenseCategory,
    ErpExpenseHodAssignment,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
)

TERMINAL_STATUSES = ("approved", "rejected", "paid")
ACTIONABLE_STATUSES = ("submitted", "disputed")


def _matrix(region: ErpExpenseRegionConfig) -> dict[str, Any]:
    return json.loads(region.approval_matrix_json)


def resolve_stage_sequence(db: Session, txn: ErpExpenseTransaction) -> list[str]:
    """Base stages come from the region's approval matrix. 'department_hod' is spliced in
    right after 'hod' when the category's owning department differs from the employee's own
    department — unless that department's HOD turns out to be the same person as the
    employee's own HOD (auto-skip, no duplicate approval by the same person)."""
    region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == txn.region_id).first()
    category = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.category_id == txn.category_id).first()
    employee = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == txn.employee_id).first()

    base: list[str] = list(_matrix(region)["stages"])

    if category and category.owning_department_id and employee and category.owning_department_id != employee.department_id:
        own_hod = _hod_for_department(db, employee.department_id) if employee.department_id else None
        dept_hod = _hod_for_department(db, category.owning_department_id)
        if dept_hod and (not own_hod or dept_hod.user_id != own_hod.user_id):
            idx = base.index("hod") + 1 if "hod" in base else 0
            base = base[:idx] + ["department_hod"] + base[idx:]

    return base


def _hod_for_department(db: Session, department_id: int) -> Optional[ErpAuthExpenseUsers]:
    assignment = (
        db.query(ErpExpenseHodAssignment)
        .filter(ErpExpenseHodAssignment.department_id == department_id, ErpExpenseHodAssignment.is_active == 1)
        .first()
    )
    if not assignment:
        return None
    return db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == assignment.user_id).first()


def _apply_delegation(db: Session, approver: Optional[ErpAuthExpenseUsers]) -> Optional[ErpAuthExpenseUsers]:
    if not approver:
        return None
    today = datetime.utcnow().strftime("%Y-%m-%d")
    delegation = (
        db.query(ErpExpenseApproverDelegation)
        .filter(
            ErpExpenseApproverDelegation.approver_id == approver.user_id,
            ErpExpenseApproverDelegation.start_date <= today,
            ErpExpenseApproverDelegation.end_date >= today,
        )
        .first()
    )
    if not delegation:
        return approver
    return db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == delegation.backup_id).first() or approver


def resolve_stage_approver(db: Session, txn: ErpExpenseTransaction, stage: str) -> Optional[ErpAuthExpenseUsers]:
    employee = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == txn.employee_id).first()
    category = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.category_id == txn.category_id).first()

    approver: Optional[ErpAuthExpenseUsers] = None
    if stage == "hod":
        if employee and employee.department_id:
            approver = _hod_for_department(db, employee.department_id)
    elif stage == "department_hod":
        if category and category.owning_department_id:
            approver = _hod_for_department(db, category.owning_department_id)
    else:
        approver = (
            db.query(ErpAuthExpenseUsers)
            .join(ErpAuthExpenseUsers.role)
            .filter(ErpAuthExpenseUsers.role.has(role_code=stage), ErpAuthExpenseUsers.is_active == 1)
            .first()
        )
    return _apply_delegation(db, approver)


def _ensure_stage(db: Session, txn: ErpExpenseTransaction) -> None:
    """Lazily set current_stage the first time a submitted transaction is looked at by the
    approval engine, so submitter-side code (transaction_service) doesn't need to know about
    stage sequencing at all."""
    if txn.current_stage or txn.status not in ACTIONABLE_STATUSES:
        return
    seq = resolve_stage_sequence(db, txn)
    txn.current_stage = seq[0] if seq else None
    _update_stage_due(db, txn)
    db.commit()


def _update_stage_due(db: Session, txn: ErpExpenseTransaction) -> None:
    if not txn.current_stage:
        txn.stage_due_at = None
        return
    region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == txn.region_id).first()
    sla_hours = _matrix(region).get("sla_hours", {}).get(txn.current_stage, 48)
    txn.stage_due_at = datetime.utcnow() + timedelta(hours=sla_hours)


def _history(db: Session, transaction_id: int, actor_id: int, stage: str, action: str, comment: Optional[str]) -> None:
    from database.models import ErpExpenseApprovalHistory

    db.add(
        ErpExpenseApprovalHistory(
            transaction_id=transaction_id, stage=stage, actor_id=actor_id, action=action, comment=comment
        )
    )


def _load_txn(db: Session, transaction_id: int) -> ErpExpenseTransaction:
    txn = (
        db.query(ErpExpenseTransaction)
        .options(joinedload(ErpExpenseTransaction.approval_history))
        .filter(ErpExpenseTransaction.transaction_id == transaction_id)
        .first()
    )
    if not txn:
        raise LookupError("Transaction not found")
    return txn


def list_queue(db: Session, user: CurrentUser, stage: str) -> list[dict[str, Any]]:
    from services.transaction_service import transaction_to_dict

    candidates = (
        db.query(ErpExpenseTransaction)
        .options(
            joinedload(ErpExpenseTransaction.documents),
            joinedload(ErpExpenseTransaction.region),
            joinedload(ErpExpenseTransaction.category),
            joinedload(ErpExpenseTransaction.vendor),
        )
        .filter(ErpExpenseTransaction.status.in_(ACTIONABLE_STATUSES))
        .order_by(ErpExpenseTransaction.created_on.asc())
        .all()
    )
    results = []
    for txn in candidates:
        _ensure_stage(db, txn)
        if txn.current_stage != stage:
            continue
        approver = resolve_stage_approver(db, txn, stage)
        if not user.is_admin and (not approver or approver.user_id != user.id):
            continue
        results.append(transaction_to_dict(txn))
    return results


def advance(db: Session, user: CurrentUser, transaction_id: int, action: str, comment: Optional[str]) -> dict[str, Any]:
    from services.transaction_service import transaction_to_dict

    if action not in ("approve", "dispute", "reject"):
        raise ValueError(f"Unknown action: {action}")

    txn = _load_txn(db, transaction_id)
    if txn.status not in ACTIONABLE_STATUSES:
        raise ValueError("Transaction is not awaiting approval")

    _ensure_stage(db, txn)
    stage = txn.current_stage
    if not stage:
        raise ValueError("No approval stage resolved for this transaction")

    approver = resolve_stage_approver(db, txn, stage)
    if not user.is_admin and (not approver or approver.user_id != user.id):
        raise PermissionError("You are not the approver for this stage")

    if action in ("dispute", "reject") and (not comment or not comment.strip()):
        raise ValueError(f"A comment is required to {action}")

    if action == "approve":
        seq = resolve_stage_sequence(db, txn)
        idx = seq.index(stage)
        _history(db, txn.transaction_id, user.id, stage, "approve", comment)
        if idx == len(seq) - 1:
            # TODO(Phase 3): petty-cash hard/soft balance check before finalizing approval.
            txn.status = "approved"
            txn.current_stage = None
            txn.stage_due_at = None
            txn.decided_on = datetime.utcnow()
        else:
            txn.current_stage = seq[idx + 1]
            txn.dispute_returned = 0
            _update_stage_due(db, txn)
    elif action == "reject":
        txn.status = "rejected"
        txn.decided_on = datetime.utcnow()
        _history(db, txn.transaction_id, user.id, stage, "reject", comment)
    else:  # dispute
        txn.status = "disputed"
        txn.dispute_returned = 1
        _history(db, txn.transaction_id, user.id, stage, "dispute", comment)

    db.commit()
    txn = _load_txn(db, transaction_id)
    return transaction_to_dict(txn, include_history=True)


def resubmit_after_dispute(db: Session, user: CurrentUser, transaction_id: int) -> dict[str, Any]:
    from services.transaction_service import transaction_to_dict

    txn = _load_txn(db, transaction_id)
    if txn.employee_id != user.id:
        raise PermissionError("Only the submitter can resubmit")
    if txn.status != "disputed":
        raise ValueError("Only disputed claims can be resubmitted")
    # current_stage is deliberately left untouched — resubmitting returns the claim to the
    # exact stage that disputed it, not to the start of the chain.
    txn.status = "submitted"
    txn.dispute_returned = 0
    db.commit()
    txn = _load_txn(db, transaction_id)
    return transaction_to_dict(txn, include_history=True)


def bulk_approve(db: Session, user: CurrentUser, transaction_ids: list[int]) -> dict[str, Any]:
    approved: list[int] = []
    skipped: list[dict[str, Any]] = []
    for transaction_id in transaction_ids:
        try:
            txn = _load_txn(db, transaction_id)
        except LookupError:
            skipped.append({"id": transaction_id, "reason": "not_found"})
            continue
        if txn.status not in ACTIONABLE_STATUSES:
            skipped.append({"id": transaction_id, "reason": "not_awaiting_approval"})
            continue
        _ensure_stage(db, txn)
        approver = resolve_stage_approver(db, txn, txn.current_stage) if txn.current_stage else None
        if not user.is_admin and (not approver or approver.user_id != user.id):
            skipped.append({"id": transaction_id, "reason": "not_your_stage"})
            continue
        if txn.duplicate_flag:
            skipped.append({"id": transaction_id, "reason": "duplicate_flagged"})
            continue
        if not txn.vendor_id:
            skipped.append({"id": transaction_id, "reason": "vendor_unresolved"})
            continue
        region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == txn.region_id).first()
        threshold = _matrix(region).get("bulk_approve_threshold")
        if threshold is not None and txn.amount > threshold:
            skipped.append({"id": transaction_id, "reason": "over_bulk_threshold"})
            continue
        advance(db, user, transaction_id, "approve", None)
        approved.append(transaction_id)
    return {"approved": approved, "skipped": skipped}
