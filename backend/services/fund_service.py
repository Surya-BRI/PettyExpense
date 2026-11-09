"""Petty-cash funds: approved limit, available cash, and PCA replenishment.

ERP is the people/department directory. This service owns limits, bills, and top-ups.
Department available = approved limit − unreplenished petty-cash spend. An approved
top-up restores spend; it never raises the limit. Reimbursement does not debit the pot.
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import bindparam, or_, select, text
from sqlalchemy.orm import Session, joinedload, selectinload

from auth.security import ERP_SUBSIDIARY_TO_REGION_CODE
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseFundTopupBill,
    ErpExpenseFundTopupRequest,
    ErpExpenseHodAssignment,
    ErpExpenseLineItem,
    ErpExpensePettyCashFund,
    ErpExpenseRegionConfig,
    ErpExpenseTopupHistory,
    ErpExpenseTransaction,
)
from services.currency import default_base_currency, region_base_currency
from services.department_split import department_shares
from services.notification_service import send
from services.opportunity_lookup import normalize_op
from services.region_policy import is_employee_model, pca_reminder_ratio, pca_spend_limit_ratio
from services.region_scope import user_covers, user_region_ids

# A petty-cash bill comes off the fund at final Finance Manager approval (spec 5.3).
# Bills still moving through approval are reserved (pending), not spent: they block
# over-committing the fund at submit time but don't reduce what's shown as available.
_SPEND_STATUSES = ("approved", "paid")
_PENDING_STATUSES = ("submitted", "disputed")


def base_currency_for_region(region_code: Optional[str]) -> str:
    """Default for a region code alone (scripts). With a region row, use region_base_currency."""
    return default_base_currency(region_code)


def _fund_label(fund: ErpExpensePettyCashFund) -> str:
    if fund.owner_type == "employee":
        name = fund.employee.display_name if fund.employee else f"employee #{fund.employee_id}"
        if is_employee_model(fund.region):
            return f"{name} · advance"
        return f"{name} · individual"
    name = fund.department.department_name if fund.department else f"department #{fund.department_id}"
    return f"{name} · department"


def _tx_amount(row: ErpExpenseTransaction, fund_currency: Optional[str] = None) -> float:
    """Bill total in the fund's currency. A fund is held in its company's base currency, so
    this is the converted total stamped on the bill (totalAmountBase). Bills saved before
    that column existed fall back to total x exchange_rate ("1 bill unit = N base units")."""
    target = (fund_currency or "").strip().upper()
    base = (row.base_currency or "").strip().upper()
    if row.total_amount_base is not None and (not target or base == target):
        return round(float(row.total_amount_base), 2)
    total = float(row.total_amount or ((row.amount or 0) + (row.vat_amount or 0)))
    bill = (row.currency or "").strip().upper()
    rate = float(row.exchange_rate or 0)
    if target and bill and bill != target and rate > 0:
        total *= rate
    return round(total, 2)


def bill_shares(row: ErpExpenseTransaction, fund_currency: Optional[str] = None) -> dict[Optional[int], float]:
    """Bill total in the fund's currency, split by paying department (see department_split).
    Key None = the employee's own pot; other keys are the departments owning cross-department
    lines. Rounded per share, with the rounding remainder on the largest share so the shares
    add up exactly to _tx_amount."""
    total = _tx_amount(row, fund_currency)
    raw = department_shares(row)
    raw_total = sum(raw.values())
    if len(raw) <= 1 or raw_total <= 0:
        return {next(iter(raw), None): total}
    shares = {key: round(total * part / raw_total, 2) for key, part in raw.items()}
    largest = max(shares, key=lambda k: shares[k])
    shares[largest] = round(shares[largest] + total - sum(shares.values()), 2)
    return shares


def _individual_employee_ids(db: Session, region_id: int) -> set[int]:
    return {
        f.employee_id
        for f in db.query(ErpExpensePettyCashFund).filter(
            ErpExpensePettyCashFund.region_id == region_id,
            ErpExpensePettyCashFund.owner_type == "employee",
            ErpExpensePettyCashFund.is_active == 1,
        ).all()
        if f.employee_id
    }


def project_shares(row: ErpExpenseTransaction, fund_currency: Optional[str] = None) -> dict[Optional[str], float]:
    """Bill total in the fund's currency split by project (OP code): each line goes to its own
    OP code, else the claim's. Key None = no OP code. Rounded per share, with the remainder on
    the largest so the shares add up to _tx_amount. Used for the project-wise report: in an
    employee-advance company the advance covers all the employee's projects."""
    total = _tx_amount(row, fund_currency)
    claim_op = normalize_op(row.op_number)
    if not row.line_items:
        return {claim_op: total}
    raw: dict[Optional[str], float] = {}
    for li in row.line_items:
        key = normalize_op(li.op_number) or claim_op
        raw[key] = raw.get(key, 0.0) + float(li.amount or 0)
    raw_total = sum(raw.values())
    if len(raw) <= 1 or raw_total <= 0:
        return {next(iter(raw), claim_op): total}
    shares = {key: round(total * part / raw_total, 2) for key, part in raw.items()}
    largest = max(shares, key=lambda k: shares[k])
    shares[largest] = round(shares[largest] + total - sum(shares.values()), 2)
    return shares


def require_bill_projects(row: ErpExpenseTransaction) -> None:
    """Employee-advance company: every bill names its project -- the claim's OP code, or an
    OP code on each line that has none of the claim's."""
    if None in project_shares(row):
        raise ValueError("Enter the project OP code for this bill (or for each item)")


def _department_pot_unused(fund: ErpExpensePettyCashFund) -> bool:
    """In an employee-advance company (Professional Signs) bills only ever come off the
    employee's own advance, so a department pot there (e.g. left from before the switch)
    pays for nothing."""
    return fund.owner_type == "department" and is_employee_model(fund.region)


def _fund_portion(
    fund: ErpExpensePettyCashFund, row: ErpExpenseTransaction, individual_ids: set[int]
) -> float:
    """How much of this bill comes out of this fund."""
    shares = bill_shares(row, fund.currency)
    if fund.owner_type == "employee":
        if row.employee_id != fund.employee_id:
            return 0.0
        return shares.get(None, 0.0)
    if _department_pot_unused(fund):
        return 0.0
    portion = shares.get(fund.department_id, 0.0)
    employee = row.employee
    if (
        employee is not None
        and employee.department_id == fund.department_id
        and row.employee_id not in individual_ids
    ):
        portion += shares.get(None, 0.0)
    return round(portion, 2)


# Top-up statuses. Department model: submitted -> verified -> approved (paid on approval).
# Employee-advance model: submitted -> hod_approved -> verified -> paid.
# 'returned' and 'rejected' end a request without money moving.
TOPUP_DONE_STATUSES = ("approved", "paid")
TOPUP_OPEN_STATUSES = ("submitted", "hod_approved", "verified")


def _is_replenishment(t: ErpExpenseFundTopupRequest) -> bool:
    """A top-up of spent bills -- not an advance (which raises the employee's limit instead)."""
    return (t.kind or "topup") != "advance" and t.is_active == 1


def _approved_topups(fund: ErpExpensePettyCashFund) -> float:
    return round(
        sum(t.amount for t in fund.topups if _is_replenishment(t) and t.status in TOPUP_DONE_STATUSES),
        2,
    )


def _pending_topups(fund: ErpExpensePettyCashFund) -> float:
    return round(
        sum(t.amount for t in fund.topups if _is_replenishment(t) and t.status in TOPUP_OPEN_STATUSES),
        2,
    )


def _fund_bills(
    db: Session,
    fund: ErpExpensePettyCashFund,
    statuses: tuple[str, ...],
    exclude_transaction_id: Optional[int] = None,
) -> list[tuple[ErpExpenseTransaction, float]]:
    """Petty-cash bills that draw on this fund in the given statuses, with the part of each
    bill this fund pays. A department fund pays its own employees' bills (unless they have
    an individual pot) plus any other employee's lines whose category this department owns."""
    q = (
        db.query(ErpExpenseTransaction)
        .options(
            joinedload(ErpExpenseTransaction.employee),
            joinedload(ErpExpenseTransaction.category),
            selectinload(ErpExpenseTransaction.line_items).joinedload(ErpExpenseLineItem.category),
        )
        .filter(
            ErpExpenseTransaction.region_id == fund.region_id,
            ErpExpenseTransaction.type == "petty_cash",
            ErpExpenseTransaction.status.in_(statuses),
        )
    )
    if exclude_transaction_id:
        q = q.filter(ErpExpenseTransaction.transaction_id != exclude_transaction_id)
    if _department_pot_unused(fund):
        return []
    individual_ids = _individual_employee_ids(db, fund.region_id)
    if fund.owner_type == "employee":
        q = q.filter(ErpExpenseTransaction.employee_id == fund.employee_id)
    else:
        employee_ids = [
            u.user_id
            for u in db.query(ErpAuthExpenseUsers)
            .filter(ErpAuthExpenseUsers.department_id == fund.department_id, ErpAuthExpenseUsers.is_deleted == 0)
            .all()
        ]
        # Claims from people with their own pot don't also hit the department pot.
        debit_ids = [i for i in employee_ids if i not in individual_ids]
        owned_category_ids = [
            c for (c,) in db.query(ErpExpenseCategory.category_id).filter(
                ErpExpenseCategory.owning_department_id == fund.department_id
            )
        ]
        conditions = []
        if debit_ids:
            conditions.append(ErpExpenseTransaction.employee_id.in_(debit_ids))
        if owned_category_ids:
            conditions.append(ErpExpenseTransaction.category_id.in_(owned_category_ids))
            conditions.append(
                ErpExpenseTransaction.transaction_id.in_(
                    select(ErpExpenseLineItem.transaction_id).where(
                        ErpExpenseLineItem.category_id.in_(owned_category_ids)
                    )
                )
            )
        if not conditions:
            return []
        q = q.filter(or_(*conditions))
    out = []
    for row in q.all():
        portion = _fund_portion(fund, row, individual_ids)
        if portion > 0:
            out.append((row, portion))
    return out


def _sum_bills(
    db: Session,
    fund: ErpExpensePettyCashFund,
    statuses: tuple[str, ...],
    exclude_transaction_id: Optional[int] = None,
) -> float:
    return round(sum(p for _, p in _fund_bills(db, fund, statuses, exclude_transaction_id)), 2)


def fund_to_dict(
    db: Session,
    fund: ErpExpensePettyCashFund,
    exclude_transaction_id: Optional[int] = None,
    *,
    spent: Optional[float] = None,
    pending_bills: Optional[float] = None,
) -> dict[str, Any]:
    """exclude_transaction_id leaves one bill out of every figure, so a bill being
    (re)submitted can be checked against what's left without counting itself."""
    if spent is None or pending_bills is None:
        # One pass over the fund's bills for both figures (each pass is several queries).
        rows = _fund_bills(db, fund, _SPEND_STATUSES + _PENDING_STATUSES, exclude_transaction_id)
        if spent is None:
            spent = round(sum(p for tx, p in rows if tx.status in _SPEND_STATUSES), 2)
        if pending_bills is None:
            pending_bills = round(sum(p for tx, p in rows if tx.status in _PENDING_STATUSES), 2)
    replenished = _approved_topups(fund)
    pending = _pending_topups(fund)
    limit = float(fund.opening_balance or 0)
    if fund.owner_type == "department":
        unreplenished = max(0.0, round(spent - replenished, 2))
        remaining = round(limit - unreplenished, 2)
    else:
        unreplenished = max(0.0, round(spent - replenished, 2))
        remaining = round(limit + replenished - spent, 2)
    region = fund.region
    uncommitted = round(remaining - pending_bills, 2)
    # Employee-advance company with a hard limit (Professional Signs: 50%): bills not yet
    # topped up -- approved or still in approval -- may use only that share of the PCA.
    spend_limit = None
    if fund.owner_type == "employee" and is_employee_model(region):
        ratio = pca_spend_limit_ratio(region)
        if ratio is not None:
            spend_limit = round(limit * ratio, 2)
            outstanding = max(0.0, spent - replenished) + pending_bills
            uncommitted = min(uncommitted, round(spend_limit - outstanding, 2))
    return {
        "id": fund.fund_id,
        "region_id": fund.region_id,
        "region_code": region.region_code if region else None,
        "region_name": region.region_name if region else None,
        "company_name": (region.company_name or region.region_name) if region else None,
        "owner_type": fund.owner_type,
        "department_id": fund.department_id,
        "department_name": fund.department.department_name if fund.department else None,
        "employee_id": fund.employee_id,
        "employee_name": fund.employee.display_name if fund.employee else None,
        "op_number": fund.op_number,
        "op_name": fund.op_name,
        "currency": fund.currency,
        "opening_balance": limit,
        "approved_limit": limit,
        "credited": replenished,
        "replenished": replenished,
        "spent": spent,
        "unreplenished_spend": unreplenished if fund.owner_type == "department" else max(0.0, spent - replenished),
        "pending_topup": pending,
        "pending_bills": pending_bills,
        "remaining": remaining,
        "available": remaining,
        # What a new bill can still use: available minus bills already awaiting approval, and
        # (employee advances with a hard limit) never past spend_limit before a top-up.
        "uncommitted": uncommitted,
        "spend_limit": spend_limit,
        "label": _fund_label(fund),
        "is_active": bool(fund.is_active),
    }


def _subsidiary_codes_for_region(region_code: str) -> list[str]:
    wanted = (region_code or "").upper()
    return [code for code, mapped in ERP_SUBSIDIARY_TO_REGION_CODE.items() if mapped == wanted]


def _erp_department_names_for_region(db: Session, region_code: str) -> Optional[list[str]]:
    """Department names used by active ERP employees in this app region. None if ERP is unreachable."""
    codes = _subsidiary_codes_for_region(region_code)
    if not codes:
        return None
    try:
        stmt = text(
            """
            SELECT DISTINCT d.departmentName
            FROM ErpMasterEmployee e
            JOIN ErpMasterRegion r ON r.regionId = e.regionId
            JOIN ErpMasterSubsidiary s ON s.subsidiaryId = r.subsidiaryId
            JOIN ErpMasterDepartment d ON d.departmentId = e.departmentId
            WHERE e.isDeleted = 0 AND e.isActive = 1
              AND s.subsidiaryCode IN :codes
              AND d.departmentName IS NOT NULL
            """
        ).bindparams(bindparam("codes", expanding=True))
        rows = db.execute(stmt, {"codes": codes}).all()
    except Exception:
        db.rollback()
        return None
    names = {(row[0] or "").strip() for row in rows if (row[0] or "").strip()}
    return sorted(names, key=str.lower)


def _ensure_departments(db: Session, names: list[str]) -> list[ErpExpenseDepartment]:
    existing = {
        (d.department_name or "").strip().lower(): d for d in db.query(ErpExpenseDepartment).all()
    }
    created = False
    for name in names:
        key = name.strip().lower()
        if not key or key in existing:
            continue
        row = ErpExpenseDepartment(department_name=name.strip(), is_active=1)
        db.add(row)
        existing[key] = row
        created = True
    if created:
        db.commit()
        existing = {
            (d.department_name or "").strip().lower(): d for d in db.query(ErpExpenseDepartment).all()
        }
    out = []
    seen: set[int] = set()
    for name in names:
        row = existing.get(name.strip().lower())
        if row and row.department_id not in seen:
            seen.add(row.department_id)
            out.append(row)
    return out


def _require_department_model(fund: ErpExpensePettyCashFund) -> None:
    """The department top-up chain doesn't run in an employee-advance company; those
    requests go through services/employee_pca_service.py (/api/pca/...)."""
    if is_employee_model(fund.region):
        raise ValueError("This company uses employee petty cash advances: use the advance top-up steps")


def _load_fund(db: Session, fund_id: int) -> ErpExpensePettyCashFund:
    fund = (
        db.query(ErpExpensePettyCashFund)
        .options(
            joinedload(ErpExpensePettyCashFund.region),
            joinedload(ErpExpensePettyCashFund.department),
            joinedload(ErpExpensePettyCashFund.employee),
            joinedload(ErpExpensePettyCashFund.topups),
        )
        .filter(ErpExpensePettyCashFund.fund_id == fund_id)
        .first()
    )
    if not fund:
        raise LookupError("Fund not found")
    return fund


# A department fund below this share of its approved limit alerts its HODs (and Admin) to raise
# a top-up -- once per replenishment cycle.
LOW_FUND_RATIO = 0.20


def _topup_history(db: Session, row: ErpExpenseFundTopupRequest, actor_id: int, action: str, comment: Optional[str]) -> None:
    """One audit row per top-up step; the step's comment lives here, not appended to remarks."""
    db.add(
        ErpExpenseTopupHistory(
            topup_id=row.topup_id,
            actor_id=actor_id,
            action=action,
            comment=(comment or "").strip() or None,
        )
    )


def _people_with_role(db: Session, role: str, region_id: Optional[int] = None) -> list[ErpAuthExpenseUsers]:
    # Same region-scoped lookup the claim approval chain uses (lazy import: approval_service
    # imports this module).
    from services.approval_service import _active_with_role

    return _active_with_role(db, role, region_id)


def _role_or_admin(db: Session, role: str, region_id: Optional[int]) -> list[ErpAuthExpenseUsers]:
    """Who does this step for a company; Admin when nobody covers it (so nothing gets stuck)."""
    return _people_with_role(db, role, region_id) or _people_with_role(db, "admin")


def _department_hods(db: Session, fund: ErpExpensePettyCashFund) -> list[ErpAuthExpenseUsers]:
    if not fund.department_id:
        return []
    from services.approval_service import _hods_for_department

    return _hods_for_department(db, fund.department_id, fund.region_id)


def _notify_people(
    db: Session,
    people: list[Optional[ErpAuthExpenseUsers]],
    type_: str,
    subject: str,
    body: str,
    skip_user_id: Optional[int] = None,
) -> None:
    """Notifications aren't tied to a claim (transaction_id None), so `type_` carries the
    top-up / fund id to keep the per-user dedup from swallowing later events."""
    seen: set[int] = set()
    for person in people:
        if person is None or person.user_id in seen or person.user_id == skip_user_id:
            continue
        seen.add(person.user_id)
        send(db, person, type_, None, subject_en=subject, subject_ar=subject, body_en=body, body_ar=body)


def _topup_summary(row: ErpExpenseFundTopupRequest, fund: ErpExpensePettyCashFund) -> str:
    dept = fund.department.department_name if fund.department else "Department"
    region = fund.region.region_code if fund.region else ""
    return f"{fund.currency} {row.amount:,.2f} for {dept} petty cash ({region})"


def _notify_topup(db: Session, row: ErpExpenseFundTopupRequest, step: str, actor_id: int, comment: Optional[str]) -> None:
    fund = _load_fund(db, row.fund_id)
    requester = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == row.requester_id).first()
    what = _topup_summary(row, fund)
    note = f" Comment: {comment.strip()}" if comment and comment.strip() else ""
    admins = _people_with_role(db, "admin")
    if step == "requested":
        who = requester.display_name if requester else "Someone"
        _notify_people(
            db, [*_role_or_admin(db, "accountant", fund.region_id), *admins],
            f"topup_requested_{row.topup_id}", "Petty cash top-up to verify",
            f"{who} requested a top-up of {what}. Accounts: please verify the bills.{note}",
            skip_user_id=actor_id,
        )
    elif step == "verified":
        _notify_people(
            db, _role_or_admin(db, "finance_manager", fund.region_id),
            f"topup_verified_{row.topup_id}", "Petty cash top-up to approve",
            f"Accounts verified the top-up of {what}. Please approve and record the payment.{note}",
            skip_user_id=actor_id,
        )
    elif step == "returned":
        _notify_people(
            db, [requester, *_department_hods(db, fund)],
            f"topup_returned_{row.topup_id}", "Petty cash top-up returned",
            f"Your top-up of {what} was returned by Accounts.{note} Fix it and raise a new request.",
            skip_user_id=actor_id,
        )
    else:  # approved | rejected
        _notify_people(
            db, [requester, *_department_hods(db, fund), *admins],
            f"topup_{step}_{row.topup_id}", f"Petty cash top-up {step}",
            f"The top-up of {what} was {step}.{note}",
            skip_user_id=actor_id,
        )


def check_low_fund(db: Session, fund_id: int) -> bool:
    """Alerts the department's HODs (and Admin) once the fund's available cash drops below
    LOW_FUND_RATIO of its limit. Fires once per cycle: the type carries the number of approved
    top-ups, so the next alert only comes after a replenishment. Returns True if it alerted."""
    fund = _load_fund(db, fund_id)
    if fund.owner_type != "department" or not fund.is_active:
        return False
    limit = float(fund.opening_balance or 0)
    if limit <= 0:
        return False
    available = fund_to_dict(db, fund)["available"]
    if available >= limit * LOW_FUND_RATIO:
        return False
    cycle = sum(1 for t in fund.topups if _is_replenishment(t) and t.status in TOPUP_DONE_STATUSES)
    dept = fund.department.department_name if fund.department else "Department"
    region = fund.region.region_code if fund.region else ""
    _notify_people(
        db, [*_department_hods(db, fund), *_people_with_role(db, "admin")],
        f"fund_low_{fund.fund_id}_{cycle}", f"{dept} petty cash is running low",
        f"{dept} petty cash ({region}) has {fund.currency} {available:,.2f} left of its "
        f"{fund.currency} {limit:,.2f} limit. Raise a top-up with the approved bills.",
    )
    return True


def check_advance_reminder(db: Session, fund_id: int) -> bool:
    """Employee advance (Professional Signs): once the approved bills not yet paid reach the
    company's reminder share of the PCA (PDF: about 50%), tell the employee, their HOD and the
    Accounts Manager (who pays them from Payments, which refills the PCA). Once per cycle, like
    the low-fund alert. Returns True if sent."""
    fund = _load_fund(db, fund_id)
    if fund.owner_type != "employee" or not fund.is_active or not is_employee_model(fund.region):
        return False
    limit = float(fund.opening_balance or 0)
    if limit <= 0:
        return False
    figures = fund_to_dict(db, fund)
    if figures["unreplenished_spend"] < limit * pca_reminder_ratio(fund.region):
        return False
    cycle = sum(1 for t in fund.topups if _is_replenishment(t) and t.status in TOPUP_DONE_STATUSES)
    employee = fund.employee
    hods = []
    if employee is not None and employee.department_id:
        from services.approval_service import _hods_for_department

        hods = _hods_for_department(db, employee.department_id, fund.region_id)
    spent = figures["unreplenished_spend"]
    payers = _role_or_admin(db, "finance_manager", fund.region_id)
    _notify_people(
        db, [employee, *hods, *payers],
        f"pca_reminder_{fund.fund_id}_{cycle}", "Petty cash: approved bills to pay",
        f"{fund.employee.display_name if employee else 'An employee'} has {fund.currency} {spent:,.2f} of approved "
        f"petty-cash bills not yet paid, against {fund.currency} {limit:,.2f} of petty cash "
        f"({fund.region.region_code if fund.region else ''}). The Accounts Manager pays them from "
        "Payments, which refills the petty cash.",
    )
    return True


def check_low_funds_for_bill(db: Session, txn: ErpExpenseTransaction) -> None:
    """After a petty-cash bill's final approval: check every department fund it drew on
    (the employee's own department plus any cross-department lines). Never raises."""
    try:
        if is_employee_model(txn.region):
            pot = fund_service.employee_advance(db, txn.employee_id, txn.region_id)
            if pot:
                check_advance_reminder(db, pot.fund_id)
            return
        own = txn.employee.department_id if txn.employee else None
        dept_ids = {own} | {d for d in department_shares(txn) if d}
        dept_ids.discard(None)
        if not dept_ids:
            return
        funds = (
            db.query(ErpExpensePettyCashFund.fund_id)
            .filter(
                ErpExpensePettyCashFund.region_id == txn.region_id,
                ErpExpensePettyCashFund.owner_type == "department",
                ErpExpensePettyCashFund.is_active == 1,
                ErpExpensePettyCashFund.department_id.in_(dept_ids),
            )
            .all()
        )
        for (fund_id,) in funds:
            check_low_fund(db, fund_id)
    except Exception:  # an alert must never break an approval
        import logging

        logging.getLogger(__name__).exception("Low-fund check failed for claim %s", txn.transaction_id)


class FundService:
    def list_all(self, db: Session) -> list[dict[str, Any]]:
        funds = (
            db.query(ErpExpensePettyCashFund)
            .options(
                joinedload(ErpExpensePettyCashFund.region),
                joinedload(ErpExpensePettyCashFund.department),
                joinedload(ErpExpensePettyCashFund.employee),
                joinedload(ErpExpensePettyCashFund.topups),
            )
            .filter(ErpExpensePettyCashFund.is_active == 1)
            .all()
        )
        return [fund_to_dict(db, f) for f in funds]

    def _department_ids_for(self, db: Session, user: ErpAuthExpenseUsers) -> set[int]:
        ids: set[int] = set()
        if user.department_id:
            ids.add(user.department_id)
        assigned = (
            db.query(ErpExpenseHodAssignment)
            .filter(
                ErpExpenseHodAssignment.user_id == user.user_id,
                ErpExpenseHodAssignment.is_active == 1,
            )
            .all()
        )
        ids.update(row.department_id for row in assigned)
        return ids

    def _my_funds_query(self, db: Session, user: ErpAuthExpenseUsers):
        """The user's own pot plus their departments' pots, in the companies they cover (home
        company plus Admin-assigned). Filtered in SQL -- not by loading every fund."""
        dept_ids = self._department_ids_for(db, user)
        owned = [
            (ErpExpensePettyCashFund.owner_type == "employee") & (ErpExpensePettyCashFund.employee_id == user.user_id)
        ]
        if dept_ids:
            owned.append(
                (ErpExpensePettyCashFund.owner_type == "department")
                & (ErpExpensePettyCashFund.department_id.in_(dept_ids))
            )
        q = db.query(ErpExpensePettyCashFund).filter(ErpExpensePettyCashFund.is_active == 1, or_(*owned))
        region_ids = user_region_ids(db, user.user_id)
        if region_ids is not None:
            q = q.filter(ErpExpensePettyCashFund.region_id.in_(region_ids or {-1}))
        return q

    def _my_fund_ids(self, db: Session, user: ErpAuthExpenseUsers) -> set[int]:
        """Permission check only: which funds are this user's (no balances worked out)."""
        return {fid for (fid,) in self._my_funds_query(db, user).with_entities(ErpExpensePettyCashFund.fund_id)}

    def my_fund_ids(self, db: Session, user: ErpAuthExpenseUsers) -> set[int]:
        """The ids of the pots this user owns or whose department they belong to / are HOD of."""
        return self._my_fund_ids(db, user)

    def list_mine(self, db: Session, user: ErpAuthExpenseUsers) -> list[dict[str, Any]]:
        funds = (
            self._my_funds_query(db, user)
            .options(
                joinedload(ErpExpensePettyCashFund.region),
                joinedload(ErpExpensePettyCashFund.department),
                joinedload(ErpExpensePettyCashFund.employee),
                selectinload(ErpExpensePettyCashFund.topups),
            )
            .all()
        )
        return [fund_to_dict(db, f) for f in funds]

    def require_petty_cash_within_limit(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        region_id: int,
        amount: float,
        exclude_transaction_id: Optional[int] = None,
    ) -> None:
        """Block a petty-cash submit that would take the employee's own pot (individual, else
        their department's) below zero. In an employee-advance company the pot is the
        employee's one advance, used for any of their projects."""
        amount = round(float(amount or 0), 2)
        if amount <= 0:
            return
        region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
        if is_employee_model(region):
            fund = self.employee_advance(db, user.user_id, region_id)
            if fund is None or float(fund.opening_balance or 0) <= 0:
                raise ValueError(
                    "You don't have a petty cash advance in this company. File this bill as a reimbursement."
                )
        else:
            fund = self._own_fund(db, user, region_id)
        if fund is None:
            raise ValueError("No petty cash limit is set for this department in this company")
        # Bills already awaiting approval are reserved against the fund too, so two bills
        # can't each pass the check and together overdraw it at final approval.
        figures = fund_to_dict(db, fund, exclude_transaction_id)
        available = float(figures["uncommitted"] or 0)
        if amount > available + 0.004:
            if fund.owner_type == "employee" and is_employee_model(fund.region) and figures["spend_limit"] is not None:
                raise ValueError(
                    f"You can use only {fund.currency} {figures['spend_limit']:,.2f} of your petty cash "
                    f"until your approved bills are paid ({max(available, 0):,.2f} left now). "
                    "Wait for the Accounts Manager to pay them, or submit this as a reimbursement."
                )
            if fund.owner_type == "employee" and is_employee_model(fund.region):
                raise ValueError(
                    f"This bill is more than what's left of your petty cash advance "
                    f"({available:.2f} left). Submit the extra as a reimbursement, or wait for a top-up."
                )
            raise ValueError(
                f"This bill exceeds available petty cash ({available:.2f} left). "
                "Submit a smaller amount or wait for a top-up."
            )

    def require_bill_within_limits(
        self, db: Session, user: ErpAuthExpenseUsers, txn: ErpExpenseTransaction, fund_currency: str
    ) -> None:
        """Checks every fund a petty-cash bill draws on: the employee's own pot for their part,
        and each owning department's fund for its cross-department lines (e.g. IT items)."""
        shares = bill_shares(txn, fund_currency)
        self.require_petty_cash_within_limit(
            db, user, txn.region_id, shares.pop(None, 0.0), exclude_transaction_id=txn.transaction_id,
        )
        for department_id, part in shares.items():
            if part <= 0:
                continue
            fund = (
                db.query(ErpExpensePettyCashFund)
                .options(joinedload(ErpExpensePettyCashFund.department), joinedload(ErpExpensePettyCashFund.topups))
                .filter(
                    ErpExpensePettyCashFund.region_id == txn.region_id,
                    ErpExpensePettyCashFund.owner_type == "department",
                    ErpExpensePettyCashFund.department_id == department_id,
                    ErpExpensePettyCashFund.is_active == 1,
                )
                .first()
            )
            dept = fund.department if fund else db.query(ErpExpenseDepartment).filter(
                ErpExpenseDepartment.department_id == department_id
            ).first()
            name = dept.department_name if dept else f"department #{department_id}"
            if fund is None:
                raise ValueError(
                    f"This bill has {name} items, but no petty cash limit is set for {name} in this company"
                )
            available = float(fund_to_dict(db, fund, txn.transaction_id)["uncommitted"] or 0)
            if part > available + 0.004:
                raise ValueError(
                    f"The {name} items on this bill ({part:.2f}) exceed {name}'s available petty cash "
                    f"({available:.2f} left). Submit a smaller amount or wait for a top-up."
                )

    def employee_advance(
        self, db: Session, employee_id: int, region_id: int
    ) -> Optional[ErpExpensePettyCashFund]:
        """Employee-advance company: the employee's one advance in this company, used for all
        their projects (the oldest active one, should an older setup have left more)."""
        return (
            db.query(ErpExpensePettyCashFund)
            .options(joinedload(ErpExpensePettyCashFund.topups), joinedload(ErpExpensePettyCashFund.region))
            .filter(
                ErpExpensePettyCashFund.region_id == region_id,
                ErpExpensePettyCashFund.owner_type == "employee",
                ErpExpensePettyCashFund.employee_id == employee_id,
                ErpExpensePettyCashFund.is_active == 1,
            )
            .order_by(ErpExpensePettyCashFund.fund_id)
            .first()
        )

    def _own_fund(self, db: Session, user: ErpAuthExpenseUsers, region_id: int) -> Optional[ErpExpensePettyCashFund]:
        """Department model: the employee's individual pot, else their department's."""
        funds = (
            db.query(ErpExpensePettyCashFund)
            .options(joinedload(ErpExpensePettyCashFund.topups))
            .filter(ErpExpensePettyCashFund.region_id == region_id, ErpExpensePettyCashFund.is_active == 1)
            .all()
        )
        individual = next((f for f in funds if f.owner_type == "employee" and f.employee_id == user.user_id), None)
        if individual:
            return individual
        if not user.department_id:
            return None
        return next(
            (f for f in funds if f.owner_type == "department" and f.department_id == user.department_id),
            None,
        )

    def bill_funds(self, db: Session, transaction_id: int) -> tuple[Optional[int], list[dict[str, Any]]]:
        """The petty-cash pots one bill is paid from, with this bill's part in each -- e.g. a
        Sales employee's bill with IT items draws on the Sales pot and the IT pot. Same split
        as the balances (_fund_portion), so the parts add up to what the pots are debited.
        Returns (the bill's region_id, rows); rows are empty for a reimbursement.
        Raises LookupError if the bill doesn't exist."""
        txn = (
            db.query(ErpExpenseTransaction)
            .options(
                joinedload(ErpExpenseTransaction.employee),
                joinedload(ErpExpenseTransaction.category),
                selectinload(ErpExpenseTransaction.line_items).joinedload(ErpExpenseLineItem.category),
            )
            .filter(ErpExpenseTransaction.transaction_id == transaction_id)
            .first()
        )
        if txn is None:
            raise LookupError("Claim not found")
        if (txn.type or "").strip().lower() != "petty_cash" or not txn.region_id:
            return txn.region_id, []
        funds = (
            db.query(ErpExpensePettyCashFund)
            .options(
                joinedload(ErpExpensePettyCashFund.region),
                joinedload(ErpExpensePettyCashFund.department),
                joinedload(ErpExpensePettyCashFund.employee),
                joinedload(ErpExpensePettyCashFund.topups),
            )
            .filter(ErpExpensePettyCashFund.region_id == txn.region_id, ErpExpensePettyCashFund.is_active == 1)
            .all()
        )
        individuals = _individual_employee_ids(db, txn.region_id)
        rows = []
        for fund in funds:
            part = _fund_portion(fund, txn, individuals)
            if part <= 0:
                continue
            # Figures include this bill: while it awaits approval it is already reserved
            # against the pot (pending_bills), once approved it is in `spent`.
            rows.append({"bill_part": round(part, 2), "fund": fund_to_dict(db, fund)})
        # Biggest share first (usually the employee's own department).
        rows.sort(key=lambda r: -r["bill_part"])
        return txn.region_id, rows

    def list_department_funds(self, db: Session, region_id: int) -> list[dict[str, Any]]:
        """Departments + this company's pot. Two reads: department rows, then funds for
        this region. Bill totals are computed once for the company, not once per department."""
        region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
        if not region:
            raise LookupError("Region not found")
        departments = (
            db.query(ErpExpenseDepartment)
            .filter(ErpExpenseDepartment.is_active == 1)
            .order_by(ErpExpenseDepartment.department_name)
            .all()
        )
        funds = (
            db.query(ErpExpensePettyCashFund)
            .options(
                joinedload(ErpExpensePettyCashFund.region),
                joinedload(ErpExpensePettyCashFund.department),
                joinedload(ErpExpensePettyCashFund.employee),
                joinedload(ErpExpensePettyCashFund.topups),
            )
            .filter(
                ErpExpensePettyCashFund.region_id == region_id,
                ErpExpensePettyCashFund.owner_type == "department",
                ErpExpensePettyCashFund.is_active == 1,
            )
            .all()
        )
        by_dept = {f.department_id: f for f in funds if f.department_id}
        extra_ids = set(by_dept) - {d.department_id for d in departments}
        if extra_ids:
            departments = list(departments) + (
                db.query(ErpExpenseDepartment).filter(ErpExpenseDepartment.department_id.in_(extra_ids)).all()
            )
        departments = sorted(departments, key=lambda d: (d.department_name or "").lower())
        bills = (
            db.query(ErpExpenseTransaction)
            .options(
                joinedload(ErpExpenseTransaction.employee),
                joinedload(ErpExpenseTransaction.category),
                selectinload(ErpExpenseTransaction.line_items).joinedload(ErpExpenseLineItem.category),
            )
            .filter(
                ErpExpenseTransaction.region_id == region_id,
                ErpExpenseTransaction.type == "petty_cash",
                ErpExpenseTransaction.status.in_(_SPEND_STATUSES + _PENDING_STATUSES),
            )
            .all()
        )
        individuals = _individual_employee_ids(db, region_id)
        spent: dict[int, float] = {f.fund_id: 0.0 for f in funds}
        pending: dict[int, float] = {f.fund_id: 0.0 for f in funds}
        for row in bills:
            for fund in funds:
                portion = _fund_portion(fund, row, individuals)
                if portion <= 0:
                    continue
                if row.status in _SPEND_STATUSES:
                    spent[fund.fund_id] += portion
                else:
                    pending[fund.fund_id] += portion
        return [
            {
                "department_id": dept.department_id,
                "department_name": dept.department_name,
                "fund": (
                    fund_to_dict(
                        db,
                        by_dept[dept.department_id],
                        spent=round(spent[by_dept[dept.department_id].fund_id], 2),
                        pending_bills=round(pending[by_dept[dept.department_id].fund_id], 2),
                    )
                    if dept.department_id in by_dept
                    else None
                ),
            }
            for dept in departments
        ]

    def update_opening(self, db: Session, fund_id: int, opening_balance: float) -> dict[str, Any]:
        if opening_balance < 0:
            raise ValueError("opening_balance cannot be negative")
        fund = _load_fund(db, fund_id)
        fund.opening_balance = round(float(opening_balance), 2)
        db.commit()
        return fund_to_dict(db, _load_fund(db, fund_id))

    def credit(
        self, db: Session, user: ErpAuthExpenseUsers, fund_id: int, amount: float, remarks: Optional[str]
    ) -> dict[str, Any]:
        if not user.role or user.role.role_code != "admin":
            raise PermissionError("Only Admin can top up a fund directly")
        if amount <= 0:
            raise ValueError("Top-up amount must be greater than 0")
        _load_fund(db, fund_id)
        db.add(
            ErpExpenseFundTopupRequest(
                fund_id=fund_id,
                amount=round(float(amount), 2),
                requester_id=user.user_id,
                status="approved",
                remarks=remarks or "Admin top-up",
                decided_by=user.user_id,
                decided_on=datetime.utcnow(),
                is_active=1,
            )
        )
        db.commit()
        return fund_to_dict(db, _load_fund(db, fund_id))

    def create(
        self,
        db: Session,
        *,
        region_id: int,
        owner_type: str,
        opening_balance: float,
        currency: str = "AED",
        department_id: Optional[int] = None,
        employee_id: Optional[int] = None,
    ) -> dict[str, Any]:
        owner_type = (owner_type or "").strip().lower()
        if owner_type not in ("department", "employee"):
            raise ValueError("owner_type must be department or employee")
        if owner_type == "department" and not department_id:
            raise ValueError("department_id is required for a department fund")
        if owner_type == "employee" and not employee_id:
            raise ValueError("employee_id is required for an individual fund")
        if opening_balance < 0:
            raise ValueError("opening_balance cannot be negative")
        region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
        if not region:
            raise ValueError("Unknown region")
        if owner_type == "employee" and (region.region_code or "").upper() == "DUBAI":
            raise ValueError("Blue Rhine Industries uses department petty cash only")
        if owner_type == "department" and is_employee_model(region):
            raise ValueError(f"{region.company_name or region.region_name} gives petty cash advances to employees, not departments")
        wanted = region_base_currency(region)
        currency = (currency or "").strip().upper() or wanted
        if currency == "AED" and wanted != "AED":
            currency = wanted
        existing = (
            db.query(ErpExpensePettyCashFund)
            .filter(
                ErpExpensePettyCashFund.region_id == region_id,
                ErpExpensePettyCashFund.owner_type == owner_type,
                ErpExpensePettyCashFund.department_id == (department_id if owner_type == "department" else None),
                ErpExpensePettyCashFund.employee_id == (employee_id if owner_type == "employee" else None),
                ErpExpensePettyCashFund.is_active == 1,
            )
            .first()
        )
        if existing:
            raise ValueError("A fund already exists for this owner and region")
        fund = ErpExpensePettyCashFund(
            region_id=region_id,
            owner_type=owner_type,
            department_id=department_id if owner_type == "department" else None,
            employee_id=employee_id if owner_type == "employee" else None,
            currency=currency,
            opening_balance=round(float(opening_balance), 2),
            is_active=1,
        )
        db.add(fund)
        db.commit()
        return fund_to_dict(db, _load_fund(db, fund.fund_id))

    def _linked_transaction_ids(self, db: Session, fund_id: int) -> set[int]:
        """Bills already on a live top-up of this fund. Per fund: a bill split between Sales
        and IT is replenished separately by each department's top-up."""
        q = (
            db.query(ErpExpenseFundTopupBill.transaction_id)
            .join(ErpExpenseFundTopupRequest)
            .filter(
                ErpExpenseFundTopupRequest.fund_id == fund_id,
                ErpExpenseFundTopupRequest.is_active == 1,
                ErpExpenseFundTopupRequest.status.in_(TOPUP_OPEN_STATUSES + TOPUP_DONE_STATUSES),
            )
        )
        return {row[0] for row in q.all()}

    def list_replenishable_bills(self, db: Session, user: ErpAuthExpenseUsers, fund_id: int) -> list[dict[str, Any]]:
        fund = _load_fund(db, fund_id)
        role = user.role.role_code if user.role else ""
        if role == "hod":
            mine_ids = self._my_fund_ids(db, user)
            if fund_id not in mine_ids:
                raise PermissionError("HOD can only see bills for their own department")
        return self.list_replenishable_bills_unchecked(db, fund)

    def list_replenishable_bills_unchecked(self, db: Session, fund: ErpExpensePettyCashFund) -> list[dict[str, Any]]:
        """Approved bills on this fund not yet on a live top-up (caller checks permission)."""
        fund_id = fund.fund_id
        taken = self._linked_transaction_ids(db, fund_id)
        # Only bills that actually came off the fund (final approval) can be replenished.
        bills = sorted(
            _fund_bills(db, fund, _SPEND_STATUSES),
            key=lambda pair: pair[0].transaction_id,
            reverse=True,
        )
        return [
            {
                "id": tx.transaction_id,
                # This fund's part of the bill (e.g. only the IT lines on a Sales bill).
                "amount": portion,
                "bill_total": _tx_amount(tx, fund.currency),
                "bill_date": tx.bill_date,
                "currency": fund.currency,
                "employee_id": tx.employee_id,
            }
            for tx, portion in bills
            if tx.transaction_id not in taken
        ]

    def request_topup(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        fund_id: int,
        amount: Optional[float],
        remarks: Optional[str],
        transaction_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        fund = _load_fund(db, fund_id)
        _require_department_model(fund)
        role = user.role.role_code if user.role else ""
        if role == "admin":
            # Admin raises on a department's behalf (HOD away, or no HOD), for any department pot.
            if fund.owner_type != "department":
                raise ValueError("Top-ups are raised for department petty cash")
        elif role == "hod":
            mine_ids = self._my_fund_ids(db, user)
            if fund_id not in mine_ids:
                raise PermissionError("HOD can only request a top-up for their own department")
        else:
            raise PermissionError("Only the department HOD or Admin can request a top-up")
        ids = [int(i) for i in (transaction_ids or []) if i]
        bill_amount = 0.0
        portions: dict[int, float] = {}
        if ids:
            taken = self._linked_transaction_ids(db, fund_id)
            overlap = set(ids) & taken
            if overlap:
                raise ValueError("One of the bills is already on another top-up")
            txs = (
                db.query(ErpExpenseTransaction)
                .filter(ErpExpenseTransaction.transaction_id.in_(ids))
                .all()
            )
            if len(txs) != len(set(ids)):
                raise ValueError("Unknown bill on this top-up")
            for tx in txs:
                if tx.type != "petty_cash" or tx.region_id != fund.region_id:
                    raise ValueError("Bills must be petty-cash claims for this department")
                if tx.status not in _SPEND_STATUSES:
                    raise ValueError("Only fully approved petty-cash bills can be replenished")
            fund_parts = {tx.transaction_id: p for tx, p in _fund_bills(db, fund, _SPEND_STATUSES)}
            for tx in txs:
                if tx.transaction_id not in fund_parts:
                    raise ValueError("Bills must be petty-cash claims for this department")
                portions[tx.transaction_id] = fund_parts[tx.transaction_id]
            bill_amount = sum(portions.values())
        if bill_amount > 0:
            amount = bill_amount
        if amount is None or amount <= 0:
            raise ValueError("Top-up amount must be greater than 0")
        row = ErpExpenseFundTopupRequest(
            fund_id=fund_id,
            amount=round(float(amount), 2),
            requester_id=user.user_id,
            status="submitted",
            remarks=remarks,
            is_active=1,
        )
        db.add(row)
        db.flush()
        for transaction_id, portion in portions.items():
            db.add(
                ErpExpenseFundTopupBill(
                    topup_id=row.topup_id,
                    transaction_id=transaction_id,
                    amount=portion,
                )
            )
        _topup_history(db, row, user.user_id, "requested", remarks)
        db.commit()
        _notify_topup(db, row, "requested", user.user_id, remarks)
        return self.topup_to_dict(db, row.topup_id)

    def list_topups(
        self, db: Session, status: Optional[str] = None, user: Optional[ErpAuthExpenseUsers] = None
    ) -> list[dict[str, Any]]:
        """One query for every visible top-up, filtered in SQL. Each row carries its fund's
        name / company / currency only -- working out every fund's balance per row was
        several queries per top-up and made this list take ages on a remote DB."""
        # Department pots only: employee advances (Professional Signs) are listed by
        # employee_pca_service, with their own steps.
        q = (
            db.query(ErpExpenseFundTopupRequest)
            .options(*_TOPUP_LOAD)
            .join(ErpExpensePettyCashFund, ErpExpensePettyCashFund.fund_id == ErpExpenseFundTopupRequest.fund_id)
            .filter(ErpExpensePettyCashFund.owner_type == "department")
        )
        if status:
            q = q.filter(ErpExpenseFundTopupRequest.status == status)
        role = user.role.role_code if user and user.role else ""
        if role == "hod":
            q = q.filter(ErpExpenseFundTopupRequest.fund_id.in_(self._my_fund_ids(db, user) or {-1}))
        elif role in ("accountant", "finance_manager"):
            region_ids = user_region_ids(db, user.user_id)
            if region_ids is not None:
                q = q.filter(ErpExpensePettyCashFund.region_id.in_(region_ids or {-1}))
        rows = q.order_by(ErpExpenseFundTopupRequest.created_on.desc()).all()
        return [_topup_dict(db, r, full_fund=False) for r in rows]

    def _require_region_role(self, db: Session, user: ErpAuthExpenseUsers, row: ErpExpenseFundTopupRequest) -> None:
        """Accounts and Finance act only on top-ups of companies they cover; Admin on any.
        Department-model steps only: employee advances have their own chain."""
        if row.fund is not None:
            _require_department_model(row.fund)
        if user.role and user.role.role_code == "admin":
            return
        region_id = row.fund.region_id if row.fund else None
        if not user_covers(db, user.user_id, region_id):
            raise PermissionError("This top-up belongs to a company you don't handle")

    def verify_topup(self, db: Session, user: ErpAuthExpenseUsers, topup_id: int, remarks: Optional[str]) -> dict[str, Any]:
        if not user.role or user.role.role_code not in ("accountant", "admin"):
            raise PermissionError("Only Accounts or Admin can verify a top-up")
        row = db.query(ErpExpenseFundTopupRequest).filter(ErpExpenseFundTopupRequest.topup_id == topup_id).first()
        if not row:
            raise LookupError("Top-up not found")
        self._require_region_role(db, user, row)
        if row.status != "submitted":
            raise ValueError("Only a submitted top-up can be verified")
        row.status = "verified"
        row.verified_by = user.user_id
        row.verified_on = datetime.utcnow()
        _topup_history(db, row, user.user_id, "verified", remarks)
        db.commit()
        _notify_topup(db, row, "verified", user.user_id, remarks)
        return self.topup_to_dict(db, row.topup_id)

    def return_topup(self, db: Session, user: ErpAuthExpenseUsers, topup_id: int, comment: Optional[str]) -> dict[str, Any]:
        """Accounts sends a top-up back to the HOD (wrong bills, missing receipt...). The bills
        are freed (a returned top-up no longer holds them), so the HOD raises a corrected one."""
        if not user.role or user.role.role_code not in ("accountant", "admin"):
            raise PermissionError("Only Accounts or Admin can return a top-up")
        if not comment or not comment.strip():
            raise ValueError("Say why the top-up is being returned")
        row = db.query(ErpExpenseFundTopupRequest).filter(ErpExpenseFundTopupRequest.topup_id == topup_id).first()
        if not row:
            raise LookupError("Top-up not found")
        self._require_region_role(db, user, row)
        if row.status != "submitted":
            raise ValueError("Only a top-up waiting for Accounts can be returned")
        row.status = "returned"
        _topup_history(db, row, user.user_id, "returned", comment)
        db.commit()
        _notify_topup(db, row, "returned", user.user_id, comment)
        return self.topup_to_dict(db, row.topup_id)

    def decide_topup(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        topup_id: int,
        approve: bool,
        remarks: Optional[str],
        payment_method: Optional[str] = None,
        payment_reference: Optional[str] = None,
        payment_date: Optional[str] = None,
    ) -> dict[str, Any]:
        if user.role.role_code not in ("finance_manager", "admin"):
            raise PermissionError("Only Finance Manager or Admin can decide a top-up")
        row = db.query(ErpExpenseFundTopupRequest).filter(ErpExpenseFundTopupRequest.topup_id == topup_id).first()
        if not row:
            raise LookupError("Top-up not found")
        self._require_region_role(db, user, row)
        role = user.role.role_code
        if row.status == "submitted" and role == "admin":
            row.verified_by = user.user_id
            row.verified_on = datetime.utcnow()
        elif row.status != "verified":
            raise ValueError("Accounts must verify this top-up before Finance can decide")
        row.status = "approved" if approve else "rejected"
        row.decided_by = user.user_id
        row.decided_on = datetime.utcnow()
        if approve:
            row.payment_method = payment_method or "bank_transfer"
            row.payment_reference = payment_reference
            if payment_date:
                try:
                    row.payment_date = datetime.fromisoformat(payment_date.replace("Z", ""))
                except ValueError:
                    row.payment_date = datetime.utcnow()
            else:
                row.payment_date = datetime.utcnow()
        action = "approved" if approve else "rejected"
        if row.verified_by == user.user_id and role == "admin" and row.verified_on and not any(
            h.action == "verified" for h in row.history
        ):
            # Admin decided straight from "submitted": record the implied verification too.
            _topup_history(db, row, user.user_id, "verified", None)
        comment = remarks
        if approve and payment_reference:
            comment = " · ".join(p for p in [f"Paid ({row.payment_method}, ref {payment_reference})", remarks] if p)
        _topup_history(db, row, user.user_id, action, comment)
        db.commit()
        _notify_topup(db, row, action, user.user_id, remarks)
        return self.topup_to_dict(db, row.topup_id)

    def topup_to_dict(self, db: Session, topup_id: int) -> dict[str, Any]:
        """One top-up with its fund's full figures (after an action, the screen refreshes
        the fund's balance from this)."""
        row = (
            db.query(ErpExpenseFundTopupRequest)
            .options(*_TOPUP_LOAD)
            .filter(ErpExpenseFundTopupRequest.topup_id == topup_id)
            .first()
        )
        if not row:
            raise LookupError("Top-up not found")
        return _topup_dict(db, row, full_fund=True)


# Everything a top-up row shows, loaded with it (selectin for the one-to-many lists so rows
# aren't multiplied).
_TOPUP_LOAD = (
    joinedload(ErpExpenseFundTopupRequest.requester),
    joinedload(ErpExpenseFundTopupRequest.verifier),
    joinedload(ErpExpenseFundTopupRequest.decider),
    joinedload(ErpExpenseFundTopupRequest.hod_approver),
    joinedload(ErpExpenseFundTopupRequest.payer),
    selectinload(ErpExpenseFundTopupRequest.bills),
    selectinload(ErpExpenseFundTopupRequest.history).joinedload(ErpExpenseTopupHistory.actor),
    joinedload(ErpExpenseFundTopupRequest.fund).joinedload(ErpExpensePettyCashFund.region),
    joinedload(ErpExpenseFundTopupRequest.fund).joinedload(ErpExpensePettyCashFund.department),
    joinedload(ErpExpenseFundTopupRequest.fund).joinedload(ErpExpensePettyCashFund.employee),
)


def _fund_identity(fund: ErpExpensePettyCashFund) -> dict[str, Any]:
    """Which fund this is (no balances): enough for a list row's name, company and currency."""
    region = fund.region
    return {
        "id": fund.fund_id,
        "region_id": fund.region_id,
        "region_code": region.region_code if region else None,
        "region_name": region.region_name if region else None,
        "company_name": (region.company_name or region.region_name) if region else None,
        "owner_type": fund.owner_type,
        "department_id": fund.department_id,
        "department_name": fund.department.department_name if fund.department else None,
        "employee_id": fund.employee_id,
        "employee_name": fund.employee.display_name if fund.employee else None,
        "op_number": fund.op_number,
        "op_name": fund.op_name,
        "currency": fund.currency,
        "approved_limit": float(fund.opening_balance or 0),
        "label": _fund_label(fund),
        "is_active": bool(fund.is_active),
    }


def _topup_dict(db: Session, row: ErpExpenseFundTopupRequest, *, full_fund: bool) -> dict[str, Any]:
    fund = row.fund
    if fund is None:
        fund_payload = None
    elif full_fund:
        fund_payload = fund_to_dict(db, _load_fund(db, fund.fund_id))
    else:
        fund_payload = _fund_identity(fund)
    return {
        "id": row.topup_id,
        "fund_id": row.fund_id,
        "kind": row.kind or "topup",
        "amount": row.amount,
        "status": row.status,
        "hod_approved_by_name": row.hod_approver.display_name if row.hod_approver else None,
        "hod_approved_on": row.hod_approved_on.isoformat() if row.hod_approved_on else None,
        "payment_source": row.payment_source,
        "paid_by_name": row.payer.display_name if row.payer else None,
        "employee_id": fund.employee_id if fund else None,
        "employee_name": fund.employee.display_name if fund and fund.employee else None,
        "remarks": row.remarks,
        "requester_id": row.requester_id,
        "requester_name": row.requester.display_name if row.requester else None,
        "verified_by": row.verified_by,
        "verified_by_name": row.verifier.display_name if row.verifier else None,
        "verified_on": row.verified_on.isoformat() if row.verified_on else None,
        "decided_by": row.decided_by,
        "decided_by_name": row.decider.display_name if row.decider else None,
        "decided_on": row.decided_on.isoformat() if row.decided_on else None,
        "payment_method": row.payment_method,
        "payment_reference": row.payment_reference,
        "payment_date": row.payment_date.isoformat() if row.payment_date else None,
        "transaction_ids": [b.transaction_id for b in (row.bills or [])],
        "created_on": row.created_on.isoformat() if row.created_on else None,
        "department_name": fund.department.department_name if fund and fund.department else None,
        "region_code": fund.region.region_code if fund and fund.region else None,
        "history": _history_entries(row),
        "fund": fund_payload,
    }


def _history_entries(row: ErpExpenseFundTopupRequest) -> list[dict[str, Any]]:
    """Audit trail, oldest first. Top-ups created before ErpExpenseTopupHistory existed get
    their steps rebuilt from the request's own who/when columns."""
    def entry(action, actor, at, comment=None):
        return {
            "action": action,
            "actor_name": actor.display_name if actor else None,
            "comment": comment,
            "at": at.isoformat() if at else None,
        }

    if row.history:
        return [entry(h.action, h.actor, h.acted_on, h.comment) for h in row.history]
    legacy = [entry("requested", row.requester, row.created_on, row.remarks)]
    if row.verified_on:
        legacy.append(entry("verified", row.verifier, row.verified_on))
    if row.decided_on and row.status in ("approved", "rejected"):
        legacy.append(entry(row.status, row.decider, row.decided_on))
    return legacy


fund_service = FundService()
