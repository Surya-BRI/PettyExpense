"""The Accounts Department's own petty cash account (Professional Signs, PCA PDF section 6).

"A separate petty cash account is maintained for the Accounts Department. This is required
because certain employees' PCA requirements are directly paid by the Accounts Department."

One account per employee-model company (ErpExpenseAccountsCash), run as a float:

* Admin or the company's Accounts Manager sets its amount (cashLimit). Each change is logged
  as a 'set' entry.
* Every Process 2 payment ("Direct payment by Accounts Department", payment_source
  'accounts_petty_cash') of a bill or an advance request takes from it ('payout' entry). A
  payment larger than what's left is refused: refill first, or pay by Process 1.
* The Accounts Manager (the company's payer roles) or Admin records a refill from the bank
  ('refill' entry), up to what has been paid out and not refilled yet.
* Available = cashLimit - (paid out - refilled). Below LOW_FUND_RATIO of the amount the payers
  and Admin are alerted once per refill cycle.

Until Admin sets an amount there is no account and Process 2 payments are refused.
"""
from datetime import date, datetime
from typing import Any, Optional, Union

from sqlalchemy.orm import Session, joinedload

from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseAccountsCash,
    ErpExpenseAccountsCashEntry,
    ErpExpenseRegionConfig,
)
from services.currency import region_base_currency
from services.region_policy import company_label, is_employee_model, payer_roles
from services.region_scope import user_covers

ACCOUNTS_PETTY_CASH = "accounts_petty_cash"
PAYOUT, REFILL, SET = "payout", "refill", "set"
# Same threshold as a department pot's low-fund alert.
LOW_RATIO = 0.20
RECENT_ENTRIES = 30


def _role(user: ErpAuthExpenseUsers) -> str:
    return user.role.role_code if user.role else ""


def _region(db: Session, region_id: int) -> ErpExpenseRegionConfig:
    region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
    if region is None:
        raise LookupError("Company not found")
    if not is_employee_model(region):
        raise ValueError(
            f"{region.company_name or region.region_name} has no Accounts Department petty cash account"
        )
    return region


def get_account(db: Session, region_id: int) -> Optional[ErpExpenseAccountsCash]:
    return (
        db.query(ErpExpenseAccountsCash)
        .filter(ErpExpenseAccountsCash.region_id == region_id, ErpExpenseAccountsCash.is_active == 1)
        .first()
    )


def _active_entries(db: Session, account: ErpExpenseAccountsCash) -> list[ErpExpenseAccountsCashEntry]:
    return (
        db.query(ErpExpenseAccountsCashEntry)
        .filter(
            ErpExpenseAccountsCashEntry.accounts_cash_id == account.accounts_cash_id,
            ErpExpenseAccountsCashEntry.is_active == 1,
        )
        .all()
    )


def figures(db: Session, account: ErpExpenseAccountsCash) -> dict[str, float]:
    entries = _active_entries(db, account)
    paid_out = round(sum(e.amount for e in entries if e.kind == PAYOUT), 2)
    refilled = round(sum(e.amount for e in entries if e.kind == REFILL), 2)
    limit = round(float(account.cash_limit or 0), 2)
    to_refill = round(max(0.0, paid_out - refilled), 2)
    return {
        "limit": limit,
        "paid_out": paid_out,
        "refilled": refilled,
        "to_refill": to_refill,
        "available": round(limit - to_refill, 2),
        "refill_count": sum(1 for e in entries if e.kind == REFILL),
    }


def _entry_dict(e: ErpExpenseAccountsCashEntry) -> dict[str, Any]:
    txn = e.transaction
    return {
        "id": e.entry_id,
        "kind": e.kind,
        "amount": round(float(e.amount or 0), 2),
        "transaction_id": e.transaction_id,
        "topup_id": e.topup_id,
        # Who the money went to, for a payout of a bill.
        "employee_name": txn.employee.display_name if txn is not None and txn.employee else None,
        "reference": e.reference,
        "date": e.entry_date.date().isoformat() if e.entry_date else None,
        "remarks": e.remarks,
        "actor_name": e.actor.display_name if e.actor else None,
        "recorded_at": e.created_on.isoformat() if e.created_on else None,
    }


def _parse_date(value: Union[str, date, datetime, None]) -> datetime:
    from services.payment_service import _parse_date as parse

    return parse(value)


def _can_view(db: Session, user: ErpAuthExpenseUsers, region_id: int) -> bool:
    role = _role(user)
    if role == "admin":
        return True
    return role in ("finance_manager", "accountant") and user_covers(db, user.user_id, region_id)


def _require_payer(db: Session, user: ErpAuthExpenseUsers, region: ErpExpenseRegionConfig) -> None:
    if _role(user) == "admin":
        return
    if _role(user) not in payer_roles(region):
        raise PermissionError("Only the Accounts Manager or Admin can refill the Accounts Department petty cash")
    if not user_covers(db, user.user_id, region.region_id):
        raise PermissionError("This company isn't one you handle")


def _can_set(db: Session, user: ErpAuthExpenseUsers, region_id: int) -> bool:
    """Admin, or the company's Accounts Manager (finance_manager covering it)."""
    role = _role(user)
    if role == "admin":
        return True
    return role == "finance_manager" and user_covers(db, user.user_id, region_id)


def _notify_low(db: Session, account: ErpExpenseAccountsCash, figs: dict[str, float]) -> None:
    """Payers and Admin, once per refill cycle, when the account drops below LOW_RATIO."""
    if figs["limit"] <= 0 or figs["available"] >= figs["limit"] * LOW_RATIO:
        return
    from services.employee_pca_service import _payers
    from services.fund_service import _notify_people, _people_with_role

    region = account.region
    _notify_people(
        db,
        [*_payers(db, region), *_people_with_role(db, "admin")],
        f"pca_accounts_cash_low_{account.accounts_cash_id}_{figs['refill_count']}",
        "Accounts Department petty cash is low",
        f"The Accounts Department petty cash ({company_label(region)}) has {account.currency} "
        f"{figs['available']:,.2f} left of {figs['limit']:,.2f}. Refill it from the bank: "
        f"{account.currency} {figs['to_refill']:,.2f} has been paid out.",
    )


def take_payout(
    db: Session,
    region: ErpExpenseRegionConfig,
    amount: float,
    actor_id: int,
    *,
    currency: Optional[str] = None,
    transaction_id: Optional[int] = None,
    topup_id: Optional[int] = None,
    reference: Optional[str] = None,
    paid_on: Optional[datetime] = None,
    remarks: Optional[str] = None,
) -> ErpExpenseAccountsCashEntry:
    """A Process 2 payment: takes `amount` from the account (no commit). Refused when Admin
    hasn't set the account up or it has less left than the payment."""
    account = get_account(db, region.region_id)
    if account is None or float(account.cash_limit or 0) <= 0:
        raise ValueError(
            "The Accounts Department petty cash isn't set up yet: set its amount on Advances → "
            "Accounts cash, or pay by Process 1 (cash withdrawal from bank)"
        )
    if currency and currency.strip().upper() != (account.currency or "").strip().upper():
        raise ValueError(
            f"The Accounts Department petty cash is in {account.currency}; this payment is in {currency}"
        )
    amount = round(float(amount or 0), 2)
    figs = figures(db, account)
    if amount > figs["available"] + 0.005:
        raise ValueError(
            f"The Accounts Department petty cash has only {account.currency} {figs['available']:,.2f} left "
            f"(this payment is {amount:,.2f}). Refill it from the bank first, or pay by Process 1 "
            "(cash withdrawal from bank)"
        )
    entry = ErpExpenseAccountsCashEntry(
        accounts_cash_id=account.accounts_cash_id,
        kind=PAYOUT,
        amount=amount,
        transaction_id=transaction_id,
        topup_id=topup_id,
        reference=(reference or "")[:128] or None,
        entry_date=paid_on or datetime.utcnow(),
        remarks=remarks,
        actor_id=actor_id,
        created_by=actor_id,
        is_active=1,
    )
    db.add(entry)
    return entry


def after_payout(db: Session, region_id: int) -> None:
    """Call after the payout is committed: alerts when the account runs low."""
    account = (
        db.query(ErpExpenseAccountsCash)
        .options(joinedload(ErpExpenseAccountsCash.region))
        .filter(ErpExpenseAccountsCash.region_id == region_id, ErpExpenseAccountsCash.is_active == 1)
        .first()
    )
    if account is not None:
        _notify_low(db, account, figures(db, account))


class AccountsCashService:
    def view(self, db: Session, user: ErpAuthExpenseUsers, region_id: int) -> dict[str, Any]:
        region = _region(db, region_id)
        if not _can_view(db, user, region.region_id):
            raise PermissionError("Only the Accounts Manager, Accounts or Admin can see this account")
        account = get_account(db, region.region_id)
        currency = account.currency if account else region_base_currency(region)
        base = {
            "region_id": region.region_id,
            "region_code": region.region_code,
            "company_name": region.company_name or region.region_name,
            "currency": currency,
            "can_set": _can_set(db, user, region.region_id),
            "can_refill": _role(user) == "admin" or _role(user) in payer_roles(region),
        }
        if account is None:
            return {
                **base, "configured": False,
                "limit": 0.0, "paid_out": 0.0, "refilled": 0.0, "to_refill": 0.0, "available": 0.0,
                "low": False, "entries": [],
            }
        figs = figures(db, account)
        entries = (
            db.query(ErpExpenseAccountsCashEntry)
            .options(
                joinedload(ErpExpenseAccountsCashEntry.actor),
                joinedload(ErpExpenseAccountsCashEntry.transaction),
            )
            .filter(
                ErpExpenseAccountsCashEntry.accounts_cash_id == account.accounts_cash_id,
                ErpExpenseAccountsCashEntry.is_active == 1,
            )
            .order_by(ErpExpenseAccountsCashEntry.entry_id.desc())
            .limit(RECENT_ENTRIES)
            .all()
        )
        figs.pop("refill_count")
        return {
            **base,
            "configured": figs["limit"] > 0,
            **figs,
            "low": figs["limit"] > 0 and figs["available"] < figs["limit"] * LOW_RATIO,
            "entries": [_entry_dict(e) for e in entries],
        }

    def set_limit(
        self, db: Session, user: ErpAuthExpenseUsers, region_id: int, amount: float, remarks: Optional[str] = None
    ) -> dict[str, Any]:
        """Admin or the Accounts Manager sets the account's amount. Not below what's paid out
        and not refilled yet."""
        region = _region(db, region_id)
        if not _can_set(db, user, region.region_id):
            raise PermissionError("Only the Accounts Manager or Admin can set the Accounts Department petty cash amount")
        new = round(float(amount or 0), 2)
        if new < 0:
            raise ValueError("The amount can't be negative")
        account = get_account(db, region.region_id)
        if account is None:
            account = ErpExpenseAccountsCash(
                region_id=region.region_id,
                currency=region_base_currency(region),
                cash_limit=0.0,
                created_by=user.user_id,
                is_active=1,
            )
            db.add(account)
            db.flush()
        old = round(float(account.cash_limit or 0), 2)
        if new == old:
            raise ValueError(f"The Accounts Department petty cash is already {account.currency} {new:,.2f}")
        to_refill = figures(db, account)["to_refill"]
        if new < to_refill:
            raise ValueError(
                f"{account.currency} {to_refill:,.2f} has been paid out and not refilled yet; "
                "the amount can't be lower than that"
            )
        account.cash_limit = new
        account.modified_by = user.user_id
        db.add(
            ErpExpenseAccountsCashEntry(
                accounts_cash_id=account.accounts_cash_id,
                kind=SET,
                amount=round(new - old, 2),
                remarks=" · ".join(
                    p for p in [f"Set to {account.currency} {new:,.2f} (was {old:,.2f})", (remarks or "").strip()] if p
                ),
                actor_id=user.user_id,
                created_by=user.user_id,
                is_active=1,
            )
        )
        db.commit()
        if _role(user) != "admin":
            # Light-touch check: the Accounts Manager can set, pay from and refill this account
            # alone, so Admin hears about every change they make.
            from services.fund_service import _notify_people, _people_with_role

            entry_id = (
                db.query(ErpExpenseAccountsCashEntry.entry_id)
                .filter(ErpExpenseAccountsCashEntry.accounts_cash_id == account.accounts_cash_id)
                .order_by(ErpExpenseAccountsCashEntry.entry_id.desc())
                .limit(1)
                .scalar()
            )
            reason = f" Reason: {remarks.strip()}" if remarks and remarks.strip() else ""
            _notify_people(
                db,
                _people_with_role(db, "admin"),
                f"pca_accounts_cash_set_{account.accounts_cash_id}_{entry_id}",
                "Accounts Department petty cash amount changed",
                f"{user.display_name} changed the Accounts Department petty cash ({company_label(region)}) "
                f"from {account.currency} {old:,.2f} to {new:,.2f}.{reason}",
                skip_user_id=user.user_id,
            )
        return self.view(db, user, region.region_id)

    def refill(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        region_id: int,
        *,
        amount: Optional[float],
        reference: str,
        refill_date: Union[str, date, datetime, None] = None,
        remarks: Optional[str] = None,
    ) -> dict[str, Any]:
        """Money put back from the bank. Defaults to everything paid out and not refilled yet."""
        region = _region(db, region_id)
        _require_payer(db, user, region)
        account = get_account(db, region.region_id)
        if account is None or float(account.cash_limit or 0) <= 0:
            raise ValueError("The Accounts Department petty cash isn't set up yet: set its amount first")
        to_refill = figures(db, account)["to_refill"]
        if to_refill <= 0:
            raise ValueError("Nothing to refill: the Accounts Department petty cash is full")
        value = to_refill if amount is None else round(float(amount), 2)
        if value <= 0:
            raise ValueError("Enter the amount put back")
        if value > to_refill + 0.005:
            raise ValueError(
                f"Only {account.currency} {to_refill:,.2f} has been paid out and not refilled; "
                "a refill can't be more than that"
            )
        ref = (reference or "").strip()
        if not ref:
            raise ValueError("Enter the bank reference (withdrawal or transfer number)")
        db.add(
            ErpExpenseAccountsCashEntry(
                accounts_cash_id=account.accounts_cash_id,
                kind=REFILL,
                amount=value,
                reference=ref[:128],
                entry_date=_parse_date(refill_date),
                remarks=(remarks or "").strip() or None,
                actor_id=user.user_id,
                created_by=user.user_id,
                is_active=1,
            )
        )
        db.commit()
        return self.view(db, user, region.region_id)


accounts_cash_service = AccountsCashService()
