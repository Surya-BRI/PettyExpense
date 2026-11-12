"""Employee petty cash for companies on the "site" model -- Blue Rhine Contracting / UAE
("Petty Cash Advance (PCA) – Replenishment Process", assets/docs/BRC_DEPARTMENT_PETTY_CASH.md).

There are no HODs. Each employee holds one petty cash in the company, for all their sites: an
ErpExpensePettyCashFund row with ownerType='employee', whose openingBalance is the approved
limit. Every bill names its site's project OP code (for site-wise reporting), and petty-cash
bills go Employee -> Accountant -> Head of Accountant -> Finance Manager; on final approval the
whole bill comes off the employee's petty cash (fund_service._fund_portion).

* Set: the Accountant (or Admin) gives an employee petty cash, or changes its amount. Live at
  once; logged as an ErpExpenseFundTopupRequest with kind 'advance', status 'set'.
* Top-up (PDF steps 3-7): the Accountant prepares it from the employee's approved bills
  (submitted) -> the Head of Accountant approves (verified) -> the Finance Manager approves and
  records the cash withdrawal from the bank (paid). Paying brings it back to its limit.
  Whoever acts at an open step may reject it with a reason.

Admin may act at any step. Every step is logged in ErpExpenseTopupHistory and notifies the
next person.
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseFundTopupBill,
    ErpExpenseFundTopupRequest,
    ErpExpensePettyCashFund,
    ErpExpenseRegionConfig,
)
from services.currency import region_base_currency
from services.fund_service import (
    _TOPUP_LOAD,
    _load_fund,
    _notify_people,
    _role_or_admin,
    _topup_dict,
    _topup_history,
    fund_service,
    fund_to_dict,
)
from services.payment_service import PAYMENT_METHODS
from services.region_policy import company_label, is_site_model
from services.region_scope import covers_region, user_covers, user_region_ids

ADVANCE = "advance"
TOPUP = "topup"
SET = "set"
# Roles that see every employee's petty cash in a company they cover.
_ACCOUNTS_ROLES = ("accountant", "head_accountant", "finance_manager")


def _role(user: ErpAuthExpenseUsers) -> str:
    return user.role.role_code if user.role else ""


def _is_admin(user: ErpAuthExpenseUsers) -> bool:
    return _role(user) == "admin"


def _region(db: Session, region_id: int) -> ErpExpenseRegionConfig:
    region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
    if region is None:
        raise LookupError("Company not found")
    if not is_site_model(region):
        raise ValueError(f"{region.company_name or region.region_name} doesn't use this petty cash flow")
    return region


def _require_role(db: Session, user: ErpAuthExpenseUsers, roles: tuple[str, ...], region_id: int, what: str) -> None:
    """Admin always; otherwise one of `roles`, for a company the user covers."""
    if _is_admin(user):
        return
    if _role(user) not in roles:
        raise PermissionError(what)
    if not user_covers(db, user.user_id, region_id):
        raise PermissionError("This belongs to a company you don't handle")


def _load_pot(db: Session, fund_id: int) -> ErpExpensePettyCashFund:
    fund = _load_fund(db, fund_id)
    if fund.owner_type != "employee" or not is_site_model(fund.region):
        raise ValueError("This isn't an employee's petty cash in this company")
    return fund


def _load_request(db: Session, request_id: int) -> ErpExpenseFundTopupRequest:
    row = (
        db.query(ErpExpenseFundTopupRequest)
        .options(*_TOPUP_LOAD)
        .filter(ErpExpenseFundTopupRequest.topup_id == request_id)
        .first()
    )
    if row is None:
        raise LookupError("Request not found")
    if row.fund is None or row.fund.owner_type != "employee" or not is_site_model(row.fund.region):
        raise ValueError("This isn't a petty cash request of this company")
    return row


def _summary(row: ErpExpenseFundTopupRequest) -> str:
    fund = row.fund
    who = fund.employee.display_name if fund and fund.employee else "an employee"
    company = company_label(fund.region) if fund and fund.region else ""
    return f"{fund.currency} {row.amount:,.2f} top-up of {who}'s petty cash ({company})"


def _notify(db: Session, row: ErpExpenseFundTopupRequest, step: str, actor_id: int, comment: Optional[str]) -> None:
    fund = row.fund
    region_id = fund.region_id
    what = _summary(row)
    note = f" Comment: {comment.strip()}" if comment and comment.strip() else ""
    key = f"pca_site_{step}_{row.topup_id}"
    if step == "requested":
        people = _role_or_admin(db, "head_accountant", region_id)
        subject, body = "Petty cash top-up to approve", f"The {what} is waiting for the Head of Accountant.{note}"
    elif step == "verified":
        people = _role_or_admin(db, "finance_manager", region_id)
        subject, body = (
            "Petty cash top-up to approve and pay",
            f"The Head of Accountant approved the {what}. Please approve it and record the cash "
            f"withdrawal from the bank.{note}",
        )
    else:  # paid | rejected
        people = [fund.employee, row.requester, *_role_or_admin(db, "accountant", region_id)]
        subject, body = f"Petty cash top-up {step}", f"The {what} was {step}.{note}"
    _notify_people(db, people, key, subject, body, skip_user_id=actor_id)


def _visible_query(db: Session, user: ErpAuthExpenseUsers):
    """Employee petty cash this user may see: their own; Accounts, Head of Accountant and
    Finance Manager everyone's in the companies they cover; Admin all."""
    q = (
        db.query(ErpExpensePettyCashFund)
        .options(
            joinedload(ErpExpensePettyCashFund.region),
            joinedload(ErpExpensePettyCashFund.employee),
            joinedload(ErpExpensePettyCashFund.topups),
        )
        .filter(ErpExpensePettyCashFund.owner_type == "employee", ErpExpensePettyCashFund.is_active == 1)
    )
    role = _role(user)
    if role == "admin":
        return q
    if role not in _ACCOUNTS_ROLES:
        return q.filter(ErpExpensePettyCashFund.employee_id == user.user_id)
    region_ids = user_region_ids(db, user.user_id)
    if region_ids is not None:
        q = q.filter(ErpExpensePettyCashFund.region_id.in_(region_ids or {-1}))
    return q


def _parse_date(value: Optional[str]) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except ValueError as exc:
        raise ValueError("Payment date must be YYYY-MM-DD") from exc


class SitePcaService:
    # ---- reading ---------------------------------------------------------------------

    def pots(
        self, db: Session, user: ErpAuthExpenseUsers, region_id: Optional[int] = None, employee_id: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Employee petty cash this user may see, by employee name."""
        q = _visible_query(db, user)
        if region_id:
            q = q.filter(ErpExpensePettyCashFund.region_id == region_id)
        if employee_id:
            q = q.filter(ErpExpensePettyCashFund.employee_id == employee_id)
        rows = [f for f in q.all() if is_site_model(f.region)]
        rows.sort(key=lambda f: (f.employee.display_name if f.employee else "").lower())
        return [fund_to_dict(db, f) for f in rows]

    def people(self, db: Session, user: ErpAuthExpenseUsers, region_id: int) -> list[dict[str, Any]]:
        """Everyone in the company with their current petty cash (0 = not set), for the
        Accountant's "Set petty cash" picker."""
        region = _region(db, region_id)
        _require_role(db, user, ("accountant",), region.region_id, "Only the Accountant or Admin can set petty cash")
        rows = (
            db.query(ErpAuthExpenseUsers)
            .options(joinedload(ErpAuthExpenseUsers.department))
            .filter(
                ErpAuthExpenseUsers.is_active == 1,
                ErpAuthExpenseUsers.is_deleted == 0,
                covers_region(region.region_id),
            )
            .all()
        )
        rows.sort(key=lambda u: (u.display_name or "").lower())
        limits = {
            employee_id: float(balance or 0)
            for employee_id, balance in db.query(
                ErpExpensePettyCashFund.employee_id, ErpExpensePettyCashFund.opening_balance
            )
            .filter(
                ErpExpensePettyCashFund.region_id == region.region_id,
                ErpExpensePettyCashFund.owner_type == "employee",
                ErpExpensePettyCashFund.is_active == 1,
            )
            .order_by(ErpExpensePettyCashFund.fund_id.desc())  # oldest wins, as employee_advance
        }
        return [
            {
                "id": u.user_id,
                "display_name": u.display_name,
                "department_name": u.department.department_name if u.department else None,
                "advance": round(limits.get(u.user_id, 0.0), 2),
            }
            for u in rows
        ]

    def list_requests(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        region_id: Optional[int] = None,
        status: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        q = _visible_query(db, user)
        if region_id:
            q = q.filter(ErpExpensePettyCashFund.region_id == region_id)
        fund_ids = [f.fund_id for f in q.all() if is_site_model(f.region)]
        if not fund_ids:
            return []
        rq = (
            db.query(ErpExpenseFundTopupRequest)
            .options(*_TOPUP_LOAD)
            .filter(ErpExpenseFundTopupRequest.fund_id.in_(fund_ids), ErpExpenseFundTopupRequest.is_active == 1)
        )
        if status:
            rq = rq.filter(ErpExpenseFundTopupRequest.status == status)
        if kind:
            rq = rq.filter(ErpExpenseFundTopupRequest.kind == kind)
        rows = rq.order_by(ErpExpenseFundTopupRequest.created_on.desc()).all()
        return [_topup_dict(db, r, full_fund=False) for r in rows]

    def request_to_dict(self, db: Session, request_id: int) -> dict[str, Any]:
        return _topup_dict(db, _load_request(db, request_id), full_fund=True)

    def replenishable_bills(self, db: Session, user: ErpAuthExpenseUsers, fund_id: int) -> list[dict[str, Any]]:
        """Approved bills on this petty cash not yet on a top-up (for the Accountant)."""
        fund = _load_pot(db, fund_id)
        _require_role(
            db, user, _ACCOUNTS_ROLES, fund.region_id, "Only Accounts or Admin can see the bills to top up"
        )
        return fund_service.list_replenishable_bills_unchecked(db, fund)

    # ---- set petty cash --------------------------------------------------------------

    def set_pot(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        *,
        region_id: int,
        employee_id: int,
        amount: float,
        remarks: Optional[str] = None,
    ) -> dict[str, Any]:
        """Give an employee petty cash, or change its amount (the new total, not an increase).
        Live at once. It can't go below the bills not yet topped up."""
        region = _region(db, region_id)
        _require_role(db, user, ("accountant",), region.region_id, "Only the Accountant or Admin can set petty cash")
        amount = round(float(amount or 0), 2)
        if amount < 0:
            raise ValueError("The amount can't be negative")
        employee = (
            db.query(ErpAuthExpenseUsers)
            .filter(
                ErpAuthExpenseUsers.user_id == employee_id,
                ErpAuthExpenseUsers.is_active == 1,
                ErpAuthExpenseUsers.is_deleted == 0,
                covers_region(region.region_id),
            )
            .first()
        )
        if employee is None:
            raise ValueError("That person isn't in this company")
        fund = fund_service.employee_advance(db, employee_id, region.region_id)
        before = float(fund.opening_balance or 0) if fund else 0.0
        if fund is None:
            if amount <= 0:
                raise ValueError("Enter the petty cash amount")
            fund = ErpExpensePettyCashFund(
                region_id=region.region_id,
                owner_type="employee",
                employee_id=employee_id,
                currency=region_base_currency(region),
                opening_balance=0.0,
                is_active=1,
            )
            db.add(fund)
            db.flush()
        else:
            figures = fund_to_dict(db, fund)
            outstanding = round(max(0.0, figures["spent"] - figures["replenished"]) + figures["pending_bills"], 2)
            if amount < outstanding:
                raise ValueError(
                    f"{employee.display_name} has {fund.currency} {outstanding:,.2f} of bills not yet topped up. "
                    "The amount can't be less than that."
                )
        if round(amount - before, 2) == 0:
            raise ValueError(f"{employee.display_name}'s petty cash is already {fund.currency} {amount:,.2f}")
        fund.opening_balance = amount
        row = ErpExpenseFundTopupRequest(
            fund_id=fund.fund_id,
            kind=ADVANCE,
            amount=round(amount - before, 2),
            requester_id=user.user_id,
            status=SET,
            remarks=remarks,
            is_active=1,
        )
        db.add(row)
        db.flush()
        comment = f"Set to {fund.currency} {amount:,.2f} (was {before:,.2f})"
        if remarks and remarks.strip():
            comment = f"{comment} · {remarks.strip()}"
        _topup_history(db, row, user.user_id, SET, comment)
        db.commit()
        _notify_people(
            db, [employee], f"pca_site_set_{row.topup_id}", "Your petty cash",
            f"Your petty cash ({company_label(region)}) is now {fund.currency} {amount:,.2f}.",
            skip_user_id=user.user_id,
        )
        return self.request_to_dict(db, row.topup_id)

    # ---- top-up ----------------------------------------------------------------------

    def request_topup(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        fund_id: int,
        transaction_ids: list[int],
        remarks: Optional[str] = None,
    ) -> dict[str, Any]:
        """PDF step 3: the Accountant prepares the top-up from the employee's approved bills."""
        fund = _load_pot(db, fund_id)
        _require_role(db, user, ("accountant",), fund.region_id, "Only the Accountant or Admin can prepare a top-up")
        ids = {int(i) for i in (transaction_ids or []) if i}
        if not ids:
            raise ValueError("Pick the approved bills to top up")
        open_bills = {b["id"]: b["amount"] for b in fund_service.list_replenishable_bills_unchecked(db, fund)}
        if ids - set(open_bills):
            raise ValueError("Only approved bills on this petty cash that aren't on another top-up can be added")
        amount = round(sum(open_bills[i] for i in ids), 2)
        row = ErpExpenseFundTopupRequest(
            fund_id=fund.fund_id, kind=TOPUP, amount=amount, requester_id=user.user_id,
            status="submitted", remarks=remarks, is_active=1,
        )
        db.add(row)
        db.flush()
        for transaction_id in sorted(ids):
            db.add(ErpExpenseFundTopupBill(topup_id=row.topup_id, transaction_id=transaction_id, amount=open_bills[transaction_id]))
        _topup_history(db, row, user.user_id, "requested", remarks)
        db.commit()
        row = _load_request(db, row.topup_id)
        _notify(db, row, "requested", user.user_id, remarks)
        return self.request_to_dict(db, row.topup_id)

    def approve(self, db: Session, user: ErpAuthExpenseUsers, request_id: int, remarks: Optional[str] = None) -> dict[str, Any]:
        """PDF step 4: the Head of Accountant checks the bills and approves."""
        row = _load_request(db, request_id)
        _require_role(
            db, user, ("head_accountant",), row.fund.region_id, "Only the Head of Accountant or Admin can approve this"
        )
        if (row.kind or TOPUP) != TOPUP or row.status != "submitted":
            raise ValueError("Only a top-up waiting for the Head of Accountant can be approved")
        row.status = "verified"
        row.verified_by = user.user_id
        row.verified_on = datetime.utcnow()
        _topup_history(db, row, user.user_id, "verified", remarks)
        db.commit()
        _notify(db, row, "verified", user.user_id, remarks)
        return self.request_to_dict(db, row.topup_id)

    def pay(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        request_id: int,
        *,
        payment_method: str,
        payment_reference: str,
        payment_date: Optional[str] = None,
        remarks: Optional[str] = None,
    ) -> dict[str, Any]:
        """PDF steps 5-7: the Finance Manager approves and records the cash withdrawal from the
        bank. The petty cash is back to its limit."""
        row = _load_request(db, request_id)
        _require_role(
            db, user, ("finance_manager",), row.fund.region_id, "Only the Finance Manager or Admin can approve and pay this"
        )
        if (row.kind or TOPUP) != TOPUP or row.status != "verified":
            raise ValueError("The Head of Accountant must approve this top-up first")
        method = (payment_method or "").strip().lower()
        if method not in PAYMENT_METHODS:
            raise ValueError(f"Payment method must be one of: {', '.join(PAYMENT_METHODS)}")
        reference = (payment_reference or "").strip()
        if not reference:
            raise ValueError("Enter the bank withdrawal reference")
        now = datetime.utcnow()
        row.status = "paid"
        row.decided_by = user.user_id
        row.decided_on = now
        row.paid_by = user.user_id
        row.payment_source = "bank"
        row.payment_method = method
        row.payment_reference = reference[:128]
        row.payment_date = _parse_date(payment_date)
        note = " · ".join(p for p in [f"Paid ({method}, ref {row.payment_reference})", (remarks or "").strip()] if p)
        _topup_history(db, row, user.user_id, "paid", note)
        db.commit()
        _notify(db, row, "paid", user.user_id, remarks)
        return self.request_to_dict(db, row.topup_id)

    def reject(self, db: Session, user: ErpAuthExpenseUsers, request_id: int, comment: Optional[str]) -> dict[str, Any]:
        """The person at the open step (Head of Accountant, or Finance Manager) turns it down;
        the bills are free for a corrected top-up."""
        if not comment or not comment.strip():
            raise ValueError("Say why the top-up is rejected")
        row = _load_request(db, request_id)
        roles = {"submitted": ("head_accountant",), "verified": ("finance_manager",)}.get(row.status)
        if (row.kind or TOPUP) != TOPUP or roles is None:
            raise ValueError("Only a top-up still in progress can be rejected")
        _require_role(db, user, roles, row.fund.region_id, "You can't reject this top-up at its current step")
        row.status = "rejected"
        row.decided_by = user.user_id
        row.decided_on = datetime.utcnow()
        _topup_history(db, row, user.user_id, "rejected", comment)
        db.commit()
        _notify(db, row, "rejected", user.user_id, comment)
        return self.request_to_dict(db, row.topup_id)


site_pca_service = SitePcaService()
