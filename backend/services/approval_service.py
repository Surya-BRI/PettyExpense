import json
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator, Optional, TypeVar

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
from services.currency import bill_and_base_text
from services.department_split import (
    DEPARTMENT_HOD,
    cross_department_ids,
    stage_base,
    stage_department_id,
    stage_key,
)
from services.region_scope import covers_region

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = ("approved", "rejected", "paid")
# Only `submitted` is in an approver's hands. After a dispute the claim sits with
# the employee (`disputed`) until they correct and resubmit — it must not stay
# in the approver queue or accept Approve/Reject, or HOD can "approve" a bill
# that never cleanly reaches Accountant.
ACTIONABLE_STATUSES = ("submitted",)
# Draft/internal bookkeeping stays in the table but is not shown as workflow history.
INTERNAL_HISTORY_ACTIONS = frozenset({"created", "edited", "vendor_resolved"})

_CACHE_KEY = "approver_lookup_cache"
_T = TypeVar("_T")


@contextmanager
def approver_lookup_cache(db: Session) -> Iterator[None]:
    """Remembers approver lookups (HODs per department+company, role holders per company,
    today's delegations) for the length of a list request. A queue or claims list asks the
    same few questions for every row -- once in resolve_stage_approvers and again in
    transaction_to_dict's stage sequence -- and each answer is a round trip to a slow remote
    DB. Inside this block each distinct question hits the DB once. Only wrap read-only
    loops: the cached answers don't see writes made inside the block. Nested use is a no-op."""
    owner = _CACHE_KEY not in db.info
    if owner:
        db.info[_CACHE_KEY] = {}
    try:
        yield
    finally:
        if owner:
            db.info.pop(_CACHE_KEY, None)


def _cached(db: Session, key: tuple, load: Callable[[], _T]) -> _T:
    cache = db.info.get(_CACHE_KEY)
    if cache is None:
        return load()
    if key not in cache:
        cache[key] = load()
    return cache[key]


def _matrix(region: ErpExpenseRegionConfig) -> dict[str, Any]:
    return json.loads(region.approval_matrix_json)


def resolve_stage_sequence(db: Session, txn: ErpExpenseTransaction) -> list[str]:
    """Base stages come from the region's approval matrix. One 'department_hod:<id>' stage is
    spliced in right after 'hod' for every other department that owns part of the bill — the
    claim category on a single-item bill, or any line's category on a multi-item bill (a Sales
    bill with one IT line goes to the IT HOD too). A department is skipped when its HOD group
    is identical to the employee's own HOD group (no duplicate approval by the same people).
    A department can have more than one active HOD (see _hods_for_department); the skip only
    fires when the two groups match exactly."""
    # Relationship access, not a fresh db.query() -- region/category/employee are already
    # eager-loaded onto `txn` by every caller that matters (list_queue, transaction_to_dict),
    # so re-querying them here was a redundant round-trip per call, on every transaction, to a
    # remote high-latency DB -- the dominant cost behind a queue load that should be instant.
    region = txn.region
    employee = txn.employee

    base: list[str] = list(_matrix(region)["stages"])

    other_departments = cross_department_ids(txn) if employee else []
    if other_departments:
        own_hod_ids = (
            {u.user_id for u in _hods_for_department(db, employee.department_id, txn.region_id)}
            if employee.department_id
            else set()
        )
        extra = []
        for dept_id in other_departments:
            dept_hod_ids = {u.user_id for u in _hods_for_department(db, dept_id, txn.region_id)}
            if dept_hod_ids:
                if dept_hod_ids != own_hod_ids:
                    extra.append(stage_key(dept_id))
            elif _hods_for_department(db, dept_id):
                # The department has HODs, just none covering this company: keep the step
                # (it goes to Admin) rather than letting the bill skip that department's approval.
                extra.append(stage_key(dept_id))
        idx = base.index("hod") + 1 if "hod" in base else 0
        base = base[:idx] + extra + base[idx:]

    return base


def _department_names(txn: ErpExpenseTransaction) -> dict[int, str]:
    categories = [li.category for li in txn.line_items if li.category] + ([txn.category] if txn.category else [])
    return {
        c.owning_department_id: c.owning_department.department_name
        for c in categories
        if c.owning_department_id and c.owning_department is not None
    }


def resolve_stage_labels(txn: ErpExpenseTransaction) -> dict[str, str]:
    """Human names for the tracker: 'hod' is the employee's department HOD, each
    'department_hod:<id>' is that owning department's HOD (e.g. Sales HOD → IT HOD).
    Plain 'department_hod' (claims staged before per-department keys) uses the claim category."""
    emp_dept = (
        txn.employee.department.department_name
        if txn.employee is not None and txn.employee.department is not None
        else None
    )
    cat_dept = (
        txn.category.owning_department.department_name
        if txn.category is not None and txn.category.owning_department is not None
        else None
    )
    labels = {
        "hod": f"{emp_dept} HOD" if emp_dept else "HOD",
        DEPARTMENT_HOD: f"{cat_dept} HOD" if cat_dept else "Department HOD",
        "accountant": "Accountant",
        "finance_manager": "Finance Manager",
        "employee": "Employee",
    }
    for dept_id, name in _department_names(txn).items():
        labels[stage_key(dept_id)] = f"{name} HOD"
    # A company can rename its steps (Professional Signs: "Accounts (EJV)", "Accounts Manager").
    from services.region_policy import stage_label_overrides

    labels.update(stage_label_overrides(txn.region))
    return labels


def _legacy_department_stage(txn: ErpExpenseTransaction, seq: list[str]) -> Optional[str]:
    """Maps a plain 'department_hod' (staged before per-department keys) onto this sequence."""
    dept_id = txn.category.owning_department_id if txn.category else None
    if dept_id and stage_key(dept_id) in seq:
        return stage_key(dept_id)
    return next((s for s in seq if stage_base(s) == DEPARTMENT_HOD), None)


def realign_open_bills(db: Session, region_id: int) -> int:
    """After a company's stage list changes (e.g. Professional Signs dropping the Accountant
    step), move its bills waiting at a stage that no longer exists to the next one that hasn't
    approved them, so they show in the right queue. Returns how many moved."""
    moved = 0
    rows = (
        db.query(ErpExpenseTransaction)
        .filter(
            ErpExpenseTransaction.region_id == region_id,
            ErpExpenseTransaction.status.in_(ACTIONABLE_STATUSES),
            ErpExpenseTransaction.current_stage.isnot(None),
        )
        .all()
    )
    for txn in rows:
        before = txn.current_stage
        _realign_stage(db, txn)
        if txn.current_stage != before:
            _update_stage_due(db, txn)
            moved += 1
    return moved


def _approved_stages(txn: ErpExpenseTransaction, seq: list[str]) -> set[str]:
    approved = set()
    for h in txn.approval_history:
        if h.action != "approve":
            continue
        stage = _legacy_department_stage(txn, seq) if h.stage == DEPARTMENT_HOD else h.stage
        if stage:
            approved.add(stage)
    return approved


def _realign_stage(db: Session, txn: ErpExpenseTransaction) -> list[str]:
    """Keeps current_stage inside the (possibly changed) sequence. A dispute-edit can add or
    drop a cross-department line, so after resubmit the claim goes to the first stage that
    hasn't approved yet — normally the same stage that disputed it."""
    seq = resolve_stage_sequence(db, txn)
    if txn.current_stage in seq:
        return seq
    if txn.current_stage == DEPARTMENT_HOD:
        mapped = _legacy_department_stage(txn, seq)
        if mapped:
            txn.current_stage = mapped
            return seq
    approved = _approved_stages(txn, seq)
    txn.current_stage = next((s for s in seq if s not in approved), seq[-1] if seq else None)
    return seq


def _hods_for_department(
    db: Session, department_id: int, region_id: Optional[int] = None
) -> list[ErpAuthExpenseUsers]:
    # A department can genuinely have more than one active HOD (co-HODs, a handover overlap,
    # etc.) -- every one of them is a valid approver for that stage, not just whichever row
    # a plain .first() happened to return. One joined query, not an assignment lookup followed
    # by a separate user lookup -- each round trip to this DB is expensive.
    # The same HOD heads the department in every company, but handles a company's bills only
    # if it's their home company or Admin assigned it to them (region_scope.covers_region).
    return _cached(
        db,
        ("hods", department_id, region_id),
        lambda: db.query(ErpAuthExpenseUsers)
        .join(ErpExpenseHodAssignment, ErpExpenseHodAssignment.user_id == ErpAuthExpenseUsers.user_id)
        .filter(
            ErpExpenseHodAssignment.department_id == department_id,
            ErpExpenseHodAssignment.is_active == 1,
            covers_region(region_id),
        )
        .all(),
    )


def _active_with_role(db: Session, role_code: str, region_id: Optional[int] = None) -> list[ErpAuthExpenseUsers]:
    return _cached(
        db,
        ("role", role_code, region_id),
        lambda: db.query(ErpAuthExpenseUsers)
        .join(ErpAuthExpenseUsers.role)
        .filter(
            ErpAuthExpenseUsers.role.has(role_code=role_code),
            ErpAuthExpenseUsers.is_active == 1,
            ErpAuthExpenseUsers.is_deleted == 0,
            covers_region(region_id),
        )
        .all(),
    )


def _todays_backups(db: Session) -> dict[int, ErpAuthExpenseUsers]:
    """approver_id -> backup user for every delegation active today, in two queries total.
    Earliest delegation wins when one approver has overlapping ones."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    delegations = (
        db.query(ErpExpenseApproverDelegation)
        .filter(
            ErpExpenseApproverDelegation.start_date <= today,
            ErpExpenseApproverDelegation.end_date >= today,
        )
        .order_by(ErpExpenseApproverDelegation.delegation_id)
        .all()
    )
    backup_ids = {d.backup_id for d in delegations}
    backups = (
        {u.user_id: u for u in db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id.in_(backup_ids))}
        if backup_ids
        else {}
    )
    out: dict[int, ErpAuthExpenseUsers] = {}
    for d in delegations:
        if d.approver_id not in out and d.backup_id in backups:
            out[d.approver_id] = backups[d.backup_id]
    return out


def _apply_delegation(db: Session, approver: Optional[ErpAuthExpenseUsers]) -> Optional[ErpAuthExpenseUsers]:
    if not approver:
        return None
    if _CACHE_KEY in db.info:
        return _cached(db, ("backups",), lambda: _todays_backups(db)).get(approver.user_id, approver)
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

    region_id = txn.region_id
    approvers: list[ErpAuthExpenseUsers] = []
    if stage == "hod":
        if employee and employee.department_id:
            approvers = _hods_for_department(db, employee.department_id, region_id)
        else:
            # Employee has no department assigned — broadcast to all active HODs of this
            # company so the claim is visible and actionable rather than stuck in limbo forever.
            approvers = _active_with_role(db, "hod", region_id)
    elif stage_base(stage) == DEPARTMENT_HOD:
        dept_id = stage_department_id(stage) or (category.owning_department_id if category else None)
        if dept_id:
            approvers = _hods_for_department(db, dept_id, region_id)
    else:
        # Accountant and Finance Manager are per company: only those covering the bill's company.
        approvers = _active_with_role(db, stage, region_id)
    if not approvers:
        # Nobody configured for this step in this company — Admin gets it instead of the claim
        # sitting unseen (and is notified through the normal submission/stage emails).
        # Inside a list request, warn once per missing (stage, company), not once per claim.
        cache = db.info.get(_CACHE_KEY)
        warn_key = ("warned", stage, region_id)
        if cache is None or warn_key not in cache:
            logger.warning(
                "No %s approver for claim %s (region %s); routing to Admin", stage, txn.transaction_id, region_id
            )
            if cache is not None:
                cache[warn_key] = True
        approvers = _active_with_role(db, "admin")
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
    sla_hours = _matrix(region).get("sla_hours", {}).get(stage_base(txn.current_stage), 48)
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

    _eager_opts = [
        joinedload(ErpExpenseTransaction.documents),
        joinedload(ErpExpenseTransaction.region),
        joinedload(ErpExpenseTransaction.category).joinedload(ErpExpenseCategory.owning_department),
        joinedload(ErpExpenseTransaction.vendor),
        joinedload(ErpExpenseTransaction.employee).joinedload(ErpAuthExpenseUsers.department),
        # selectinload, not joinedload -- one-to-many would multiply rows per line item.
        selectinload(ErpExpenseTransaction.line_items)
        .joinedload(ErpExpenseLineItem.category)
        .joinedload(ErpExpenseCategory.owning_department),
    ]

    # The department_hod queue covers every 'department_hod:<id>' stage; approver
    # membership below narrows it to the departments this user is HOD of.
    stage_filter = (
        ErpExpenseTransaction.current_stage.like(f"{DEPARTMENT_HOD}%")
        if stage == DEPARTMENT_HOD
        else ErpExpenseTransaction.current_stage == stage
    )
    candidates = (
        db.query(ErpExpenseTransaction)
        .options(*_eager_opts)
        .filter(
            ErpExpenseTransaction.status.in_(ACTIONABLE_STATUSES),
            stage_filter,
        )
        .order_by(ErpExpenseTransaction.created_on.desc())
        .all()
    )
    results = []
    # One DB lookup per distinct (department, company) / (role, company) for the whole list,
    # shared by the membership check here and the stage sequence in transaction_to_dict.
    with approver_lookup_cache(db):
        for txn in candidates:
            if not user.is_admin:
                approvers = resolve_stage_approvers(db, txn, txn.current_stage)
                if user.id not in {a.user_id for a in approvers}:
                    continue
            results.append(transaction_to_dict(txn, db=db))
    # Approved-but-unpaid reimbursements are no longer mixed in here: they're listed (paged,
    # per company) by GET /api/payments — see payment_service.
    return results


def _review_stage(txn: ErpExpenseTransaction) -> str:
    """The stage that reviews duplicates: the Accountant, or -- in a company without one
    (Professional Signs: Employee -> HOD -> Accounts Manager) -- the stage booking the journal."""
    from services.region_policy import journal_stage

    return journal_stage(txn.region) or "accountant"


def _record_journal(
    txn: ErpExpenseTransaction, stage: str, journal_type: Optional[str], journal_reference: Optional[str]
) -> Optional[str]:
    """At the company's journal stage (Professional Signs: Accounts books the EJV/EJVB), the
    approver must give the journal type and its ERP number. Returns a history note, or None
    when this stage doesn't record a journal."""
    from services.region_policy import JOURNAL_TYPES, journal_stage

    if stage_base(stage) != journal_stage(txn.region):
        return None
    kind = (journal_type or "").strip().upper()
    if kind not in JOURNAL_TYPES:
        raise ValueError("Choose the journal booked for this bill: EJV, or EJVB for a multi-branch transaction")
    reference = (journal_reference or "").strip()
    if not reference:
        raise ValueError(f"Enter the {kind} number from ERP")
    txn.journal_type = kind
    txn.journal_reference = reference[:64]
    return f"{kind} {txn.journal_reference}"


def advance(
    db: Session,
    user: CurrentUser,
    transaction_id: int,
    action: str,
    comment: Optional[str],
    *,
    journal_type: Optional[str] = None,
    journal_reference: Optional[str] = None,
) -> dict[str, Any]:
    from services import notification_service
    from services.transaction_service import transaction_to_dict

    if action not in ("approve", "dispute", "reject"):
        raise ValueError(f"Unknown action: {action}")

    txn = _load_txn(db, transaction_id)
    if txn.status not in ACTIONABLE_STATUSES:
        raise ValueError("Transaction is not awaiting approval")

    _ensure_stage(db, txn)
    seq = _realign_stage(db, txn)
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
    if action == "approve" and stage == _review_stage(txn) and txn.duplicate_flag and (not comment or not comment.strip()):
        raise ValueError("A comment is required to approve a duplicate-flagged claim")

    if action == "approve":
        idx = seq.index(stage)
        journal_note = _record_journal(txn, stage, journal_type, journal_reference)
        history_comment = " · ".join(p for p in [journal_note, (comment or "").strip()] if p) or comment
        _history(db, txn.transaction_id, user.id, stage, "approve", history_comment)
        if idx == len(seq) - 1:
            # Final approval is the point a petty-cash bill comes off the fund (fund_service
            # _SPEND_STATUSES); it was already reserved against the fund at submit.
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

    from services.transaction_service import vendor_display_name
    vendor_name = vendor_display_name(txn, "unknown vendor")
    from services import email_templates

    if action == "approve":
        if txn.status == "approved":
            employee = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == txn.employee_id).first()
            content = email_templates.approval_final_email(email_templates.build_context(txn))
            notification_service.send(
                db, employee, "approval", txn.transaction_id,
                f"Expense claim approved ({vendor_name})", f"تمت الموافقة على مطالبة النفقات ({vendor_name})",
                f"Your claim {txn.transaction_id} for {bill_and_base_text(txn)} was approved."
                + (" It is now waiting for payment." if (txn.type or "") != "petty_cash" else ""),
                f"تمت الموافقة على مطالبتك رقم {txn.transaction_id} بمبلغ {bill_and_base_text(txn)}.",
                html_body_en=content.html,
            )
            if (txn.type or "").strip().lower() == "petty_cash":
                # The bill just came off the fund(s): warn the HOD if one is now running low.
                from services.fund_service import check_low_funds_for_bill

                check_low_funds_for_bill(db, txn)
        else:
            next_approvers = resolve_stage_approvers(db, txn, txn.current_stage)
            content = email_templates.approval_pending_email(email_templates.build_context(txn))
            stage_label = resolve_stage_labels(txn).get(txn.current_stage, txn.current_stage)
            for next_approver in next_approvers:
                notification_service.send(
                    db, next_approver, "approval_pending", txn.transaction_id,
                    f"Claim awaiting your approval ({vendor_name})", f"مطالبة نفقات في انتظار موافقتك ({vendor_name})",
                    f"Claim {txn.transaction_id} for {bill_and_base_text(txn)} is now at your stage ({stage_label}).",
                    f"المطالبة رقم {txn.transaction_id} بمبلغ {bill_and_base_text(txn)} وصلت إلى مرحلتك ({stage_label}).",
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


def resubmit_after_dispute(db: Session, user: CurrentUser, transaction_id: int) -> dict[str, Any]:
    from services import notification_service
    from services.transaction_service import transaction_to_dict

    txn = _load_txn(db, transaction_id)
    if txn.employee_id != user.id:
        raise PermissionError("Only the submitter can resubmit")
    if txn.status != "disputed":
        raise ValueError("Only disputed claims can be resubmitted")
    from services.transaction_service import transaction_service
    transaction_service._require_unique_submitted_bill_number(
        db, txn.bill_number, txn.transaction_id,
    )
    from services.transaction_service import _stamp_exchange_rate
    # Keeps the rate locked at first submit, so the converted figure (and the petty-cash
    # reservation) doesn't drift while the bill goes back and forth.
    _stamp_exchange_rate(txn, required=True, keep_locked=True)
    if (txn.type or "").strip().lower() == "petty_cash":
        transaction_service._require_petty_cash_limit(db, user, txn)
    # Resubmitting returns the claim to the exact stage that disputed it, not to the start of
    # the chain — unless the edit added a cross-department line whose HOD hasn't approved yet.
    txn.status = "submitted"
    txn.dispute_returned = 0
    _realign_stage(db, txn)
    db.commit()
    txn = _load_txn(db, transaction_id)

    approvers = resolve_current_approvers(db, txn)
    from services.transaction_service import vendor_display_name
    vendor_name = vendor_display_name(txn, "unknown vendor")
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


def list_history(db: Session, user: CurrentUser, limit: int = 100) -> list[dict[str, Any]]:
    """Every action this approver has taken, newest first -- one entry per action, not per
    claim. A bill disputed and later approved by the same HOD shows both entries; history
    is a log and an earlier action must never disappear behind a later one."""
    from database.models import ErpExpenseApprovalHistory
    from services.transaction_service import transaction_to_dict

    rows = (
        db.query(ErpExpenseApprovalHistory, ErpExpenseTransaction)
        .join(ErpExpenseTransaction, ErpExpenseTransaction.transaction_id == ErpExpenseApprovalHistory.transaction_id)
        .options(
            joinedload(ErpExpenseTransaction.documents),
            joinedload(ErpExpenseTransaction.region),
            joinedload(ErpExpenseTransaction.category),
            joinedload(ErpExpenseTransaction.vendor),
            joinedload(ErpExpenseTransaction.employee),
            selectinload(ErpExpenseTransaction.line_items).joinedload(ErpExpenseLineItem.category),
        )
        .filter(
            ErpExpenseApprovalHistory.actor_id == user.id,
            ~ErpExpenseApprovalHistory.action.in_(INTERNAL_HISTORY_ACTIONS),
        )
        .order_by(
            ErpExpenseApprovalHistory.acted_on.desc(),
            ErpExpenseApprovalHistory.approval_history_id.desc(),
        )
        .limit(limit)
        .all()
    )

    results = []
    claim_dicts: dict[int, dict[str, Any]] = {}  # one claim can appear several times
    for hist, txn in rows:
        if txn.transaction_id not in claim_dicts:
            claim_dicts[txn.transaction_id] = transaction_to_dict(txn)
        d = dict(claim_dicts[txn.transaction_id])
        d["history_id"] = hist.approval_history_id
        d["my_action"] = hist.action
        d["my_action_stage"] = stage_base(hist.stage)
        d["my_action_stage_key"] = hist.stage
        d["my_actioned_at"] = hist.acted_on.isoformat() if hist.acted_on else None
        d["my_comment"] = hist.comment
        results.append(d)
    return results


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
        # Duplicate review is an Accountant-stage concern (per spec) -- an HOD or Finance
        # Manager's bulk-approve isn't blocked by it; only the Accountant's is.
        if txn.current_stage == _review_stage(txn) and txn.duplicate_flag:
            skipped.append({"id": transaction_id, "reason": "duplicate_flagged"})
            continue
        # The journal (EJV/EJVB + number) is entered per bill, so it can't be bulk-approved.
        from services.region_policy import journal_stage

        if stage_base(txn.current_stage) == journal_stage(txn.region):
            skipped.append({"id": transaction_id, "reason": "journal_required"})
            continue
        region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == txn.region_id).first()
        threshold = _matrix(region).get("bulk_approve_threshold")
        if threshold is not None and txn.amount > threshold:
            skipped.append({"id": transaction_id, "reason": "over_bulk_threshold"})
            continue
        advance(db, user, transaction_id, "approve", None)
        approved.append(transaction_id)
    return {"approved": approved, "skipped": skipped}
