import json
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload, selectinload

from auth.security import CurrentUser
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseApproverDelegation,
    ErpExpenseCategory,
    ErpExpenseHodAssignment,
    ErpExpenseLineItem,
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
    department — unless that department's HOD group is identical to the employee's own HOD
    group (auto-skip, no duplicate approval by the same people). A department can have more
    than one active HOD (see _hods_for_department); the skip only fires when the two groups
    match exactly, since any genuinely different reviewer in the set is still a real approval
    step worth keeping."""
    # Relationship access, not a fresh db.query() -- region/category/employee are already
    # eager-loaded onto `txn` by every caller that matters (list_queue, transaction_to_dict),
    # so re-querying them here was a redundant round-trip per call, on every transaction, to a
    # remote high-latency DB -- the dominant cost behind a queue load that should be instant.
    region = txn.region
    category = txn.category
    employee = txn.employee

    base: list[str] = list(_matrix(region)["stages"])

    if category and category.owning_department_id and employee and category.owning_department_id != employee.department_id:
        own_hod_ids = (
            {u.user_id for u in _hods_for_department(db, employee.department_id)} if employee.department_id else set()
        )
        dept_hod_ids = {u.user_id for u in _hods_for_department(db, category.owning_department_id)}
        if dept_hod_ids and dept_hod_ids != own_hod_ids:
            idx = base.index("hod") + 1 if "hod" in base else 0
            base = base[:idx] + ["department_hod"] + base[idx:]

    return base


def _hods_for_department(db: Session, department_id: int) -> list[ErpAuthExpenseUsers]:
    # A department can genuinely have more than one active HOD (co-HODs, a handover overlap,
    # etc.) -- every one of them is a valid approver for that stage, not just whichever row
    # a plain .first() happened to return. One joined query, not an assignment lookup followed
    # by a separate user lookup -- each round trip to this DB is expensive.
    return (
        db.query(ErpAuthExpenseUsers)
        .join(ErpExpenseHodAssignment, ErpExpenseHodAssignment.user_id == ErpAuthExpenseUsers.user_id)
        .filter(ErpExpenseHodAssignment.department_id == department_id, ErpExpenseHodAssignment.is_active == 1)
        .all()
    )


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


def resolve_current_approvers(db: Session, txn: ErpExpenseTransaction) -> list[ErpAuthExpenseUsers]:
    # Single entry point for "who should be notified about this transaction right now" — used by submit and resubmit.
    _ensure_stage(db, txn)
    if not txn.current_stage:
        return []
    return resolve_stage_approvers(db, txn, txn.current_stage)


def resolve_stage_approvers(db: Session, txn: ErpExpenseTransaction, stage: str) -> list[ErpAuthExpenseUsers]:
    """Everyone who may act on `stage` for this transaction -- a department (hod/department_hod)
    or a plain role (accountant/finance_manager) can genuinely have more than one active person
    in it, and all of them are valid approvers, not just one arbitrarily-picked row. Callers
    check membership (`user.id in {a.user_id for a in approvers}`) rather than equality, and
    notify every entry rather than a single target."""
    # Relationship access, not a fresh query -- see the same note in resolve_stage_sequence.
    employee = txn.employee
    category = txn.category

    approvers: list[ErpAuthExpenseUsers] = []
    if stage == "hod":
        if employee and employee.department_id:
            approvers = _hods_for_department(db, employee.department_id)
    elif stage == "department_hod":
        if category and category.owning_department_id:
            approvers = _hods_for_department(db, category.owning_department_id)
    else:
        approvers = (
            db.query(ErpAuthExpenseUsers)
            .join(ErpAuthExpenseUsers.role)
            .filter(ErpAuthExpenseUsers.role.has(role_code=stage), ErpAuthExpenseUsers.is_active == 1)
            .all()
        )
    # Delegation is per-person -- each active approver might have their own backup covering
    # them for a date range, independent of who else is also active on this stage. Dedup by
    # user_id afterward: two different approvers could delegate to the same backup, or a
    # delegate might already be an active approver on this stage in their own right.
    resolved = [_apply_delegation(db, a) for a in approvers]
    seen: set[int] = set()
    deduped: list[ErpAuthExpenseUsers] = []
    for a in resolved:
        if a is not None and a.user_id not in seen:
            seen.add(a.user_id)
            deduped.append(a)
    return deduped


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

    # current_stage is normally already set at submission time (_notify_finance_on_submit ->
    # resolve_current_approvers -> _ensure_stage), so this should touch zero or very few rows --
    # not the dominant case. Previously every actionable transaction in the whole system, every
    # stage, every department, got fetched (4 eager joins each) and stage-filtered in Python on
    # every single queue load; this bounds that lazy-init pass to just the unstaged leftovers.
    unstaged = (
        db.query(ErpExpenseTransaction)
        .filter(
            ErpExpenseTransaction.status.in_(ACTIONABLE_STATUSES),
            ErpExpenseTransaction.current_stage.is_(None),
        )
        .all()
    )
    for txn in unstaged:
        _ensure_stage(db, txn)

    candidates = (
        db.query(ErpExpenseTransaction)
        .options(
            joinedload(ErpExpenseTransaction.documents),
            joinedload(ErpExpenseTransaction.region),
            joinedload(ErpExpenseTransaction.category),
            joinedload(ErpExpenseTransaction.vendor),
            joinedload(ErpExpenseTransaction.employee),
            # selectinload, not joinedload -- this is a one-to-many, and joining it in would
            # multiply each transaction row per line item instead of fetching them separately.
            selectinload(ErpExpenseTransaction.line_items).joinedload(ErpExpenseLineItem.category),
        )
        .filter(
            ErpExpenseTransaction.status.in_(ACTIONABLE_STATUSES),
            ErpExpenseTransaction.current_stage == stage,
        )
        .order_by(ErpExpenseTransaction.created_on.desc())
        .all()
    )
    results = []
    for txn in candidates:
        approvers = resolve_stage_approvers(db, txn, stage)
        if not user.is_admin and user.id not in {a.user_id for a in approvers}:
            continue
        results.append(transaction_to_dict(txn, db=db))
    return results


def advance(db: Session, user: CurrentUser, transaction_id: int, action: str, comment: Optional[str]) -> dict[str, Any]:
    from services import notification_service
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

    approvers = resolve_stage_approvers(db, txn, stage)
    if not user.is_admin and user.id not in {a.user_id for a in approvers}:
        raise PermissionError("You are not the approver for this stage")

    if action in ("dispute", "reject") and (not comment or not comment.strip()):
        raise ValueError(f"A comment is required to {action}")
    # "Warn, allow-with-justification" per spec -- approving a duplicate-flagged claim is the
    # one place this actually matters, since the flag has no dedicated resolve action of its
    # own (unlike vendor matching) and never blocks approve otherwise. Accountant stage only,
    # same as the vendor-resolve gate -- HOD/Finance Manager aren't required to justify it.
    if action == "approve" and stage == "accountant" and txn.duplicate_flag and (not comment or not comment.strip()):
        raise ValueError("A comment is required to approve a duplicate-flagged claim")

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
        txn.remarks = comment
        _history(db, txn.transaction_id, user.id, stage, "reject", comment)
    else:  # dispute
        txn.status = "disputed"
        txn.dispute_returned = 1
        txn.remarks = comment
        _history(db, txn.transaction_id, user.id, stage, "dispute", comment)

    db.commit()
    txn = _load_txn(db, transaction_id)

    vendor_name = txn.vendor.vendor_name if txn.vendor else (txn.vendor_raw_text or "unknown vendor")
    from services import email_templates

    if action == "approve":
        if txn.status == "approved":
            employee = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == txn.employee_id).first()
            content = email_templates.approval_final_email(email_templates.build_context(txn))
            notification_service.send(
                db, employee, "approval", txn.transaction_id,
                f"Expense claim approved ({vendor_name})", f"تمت الموافقة على مطالبة النفقات ({vendor_name})",
                f"Your claim {txn.transaction_id} for {txn.currency} {txn.amount} was approved.",
                f"تمت الموافقة على مطالبتك رقم {txn.transaction_id} بمبلغ {txn.currency} {txn.amount}.",
                html_body_en=content.html,
            )
        else:
            next_approvers = resolve_stage_approvers(db, txn, txn.current_stage)
            content = email_templates.approval_pending_email(email_templates.build_context(txn))
            for next_approver in next_approvers:
                notification_service.send(
                    db, next_approver, "approval", txn.transaction_id,
                    f"Claim awaiting your approval ({vendor_name})", f"مطالبة نفقات في انتظار موافقتك ({vendor_name})",
                    f"Claim {txn.transaction_id} for {txn.currency} {txn.amount} is now at your stage ({txn.current_stage}).",
                    f"المطالبة رقم {txn.transaction_id} بمبلغ {txn.currency} {txn.amount} وصلت إلى مرحلتك ({txn.current_stage}).",
                    html_body_en=content.html,
                )
    else:
        employee = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == txn.employee_id).first()
        if action == "reject":
            content = email_templates.rejection_email(email_templates.build_context(txn, comment=comment))
            notification_service.send(
                db, employee, "rejection", txn.transaction_id,
                f"Expense claim rejected ({vendor_name})", f"تم رفض مطالبة النفقات ({vendor_name})",
                f"Your claim {txn.transaction_id} was rejected. Reason: {comment}",
                f"تم رفض مطالبتك رقم {txn.transaction_id}. السبب: {comment}",
                html_body_en=content.html,
            )
        else:  # dispute
            content = email_templates.dispute_email(email_templates.build_context(txn, comment=comment))
            notification_service.send(
                db, employee, "dispute", txn.transaction_id,
                f"Expense claim needs correction ({vendor_name})", f"مطالبة النفقات تحتاج إلى تصحيح ({vendor_name})",
                f"Your claim {txn.transaction_id} was sent back for correction. Reason: {comment}",
                f"تم إرجاع مطالبتك رقم {txn.transaction_id} للتصحيح. السبب: {comment}",
                html_body_en=content.html,
            )

    return transaction_to_dict(txn, include_history=True, db=db)


def resolve_vendor(
    db: Session,
    user: CurrentUser,
    transaction_id: int,
    vendor_id: Optional[int] = None,
    create_new: bool = False,
) -> dict[str, Any]:
    # Closes the loop left open by transaction_service._resolve_vendor no longer auto-creating
    # on a miss: whoever's holding this claim at its current approval stage explicitly links it
    # to an existing vendor or confirms it's genuinely new, instead of a flag nobody can act on.
    from database.models import ErpExpenseVendor
    from services.transaction_service import transaction_to_dict

    txn = _load_txn(db, transaction_id)
    if txn.status not in ACTIONABLE_STATUSES:
        raise ValueError("Transaction is not awaiting approval")

    _ensure_stage(db, txn)
    stage = txn.current_stage
    if not stage:
        raise ValueError("No approval stage resolved for this transaction")

    if not user.is_admin:
        # Vendor matching is an Accountant decision per spec, not any current-stage approver's
        # call -- an HOD sitting earlier in the sequence shouldn't be resolving this.
        if stage != "accountant":
            raise PermissionError("Only the Accountant stage (or an Admin) can resolve an unmatched vendor")
        approvers = resolve_stage_approvers(db, txn, stage)
        if user.id not in {a.user_id for a in approvers}:
            raise PermissionError("You are not the approver for this stage")

    if txn.vendor_id:
        raise ValueError("Vendor is already resolved for this transaction")
    if not txn.vendor_raw_text:
        raise ValueError("No unmatched vendor text on this transaction")
    if (vendor_id is None) == (not create_new):
        raise ValueError("Pass exactly one of vendor_id or create_new=true")

    if vendor_id is not None:
        vendor = (
            db.query(ErpExpenseVendor)
            .filter(ErpExpenseVendor.vendor_id == vendor_id, ErpExpenseVendor.is_active == 1)
            .first()
        )
        if not vendor:
            raise LookupError("Vendor not found")
    else:
        vendor = ErpExpenseVendor(vendor_name=txn.vendor_raw_text, source="accountant_confirmed", is_active=1)
        db.add(vendor)
        db.flush()

    txn.vendor_id = vendor.vendor_id
    txn.vendor_raw_text = None
    _history(db, txn.transaction_id, user.id, stage, "vendor_resolved", f"Linked to vendor #{vendor.vendor_id} ({vendor.vendor_name})")
    db.commit()
    txn = _load_txn(db, transaction_id)
    return transaction_to_dict(txn, include_history=True, db=db)


def resubmit_after_dispute(db: Session, user: CurrentUser, transaction_id: int) -> dict[str, Any]:
    from services import notification_service
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

    approvers = resolve_current_approvers(db, txn)
    vendor_name = txn.vendor.vendor_name if txn.vendor else (txn.vendor_raw_text or "unknown vendor")
    # "resubmit" is a distinct type from "submission" -- reusing "submission" collided with the
    # (transactionId, type, userId, channel) idempotency key whenever the resubmit lands on the
    # same approver who received the original submission notification (e.g. a dispute at the
    # first stage), silently swallowing the resubmit notification.
    from services import email_templates

    ctx = email_templates.build_context(txn)
    content = email_templates.resubmit_email(ctx)
    for approver in approvers:
        notification_service.send(
            db, approver, "resubmit", txn.transaction_id,
            f"Corrected claim resubmitted ({vendor_name})", f"تم إعادة تقديم المطالبة المصححة ({vendor_name})",
            f"Claim {txn.transaction_id} was corrected and resubmitted for your review.",
            f"تم تصحيح المطالبة رقم {txn.transaction_id} وإعادة تقديمها لمراجعتك.",
            html_body_en=content.html,
        )
    return transaction_to_dict(txn, include_history=True, db=db)


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
        approvers = resolve_stage_approvers(db, txn, txn.current_stage) if txn.current_stage else []
        if not user.is_admin and user.id not in {a.user_id for a in approvers}:
            skipped.append({"id": transaction_id, "reason": "not_your_stage"})
            continue
        # Duplicate and unmatched-vendor review are Accountant-stage concerns (per spec) --
        # an HOD or Finance Manager's bulk-approve isn't blocked by either; only the
        # Accountant's is, forcing a manual look exactly where that judgment call belongs.
        if txn.current_stage == "accountant":
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
