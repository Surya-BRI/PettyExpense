"""Payment step (Spec 5.5, payment_records).

After the Finance Manager's final approval a reimbursement is "Approved – Unpaid"
(status='approved'). Finance records how it was paid — method, reference and the actual
payment date — which moves it to 'paid' and notifies the employee. The region's Finance
Manager (the companies they cover, see region_scope) or Admin may record payments.

Department model (Dubai): petty cash is settled from the fund at approval and never comes here.

Employee-advance model (Professional Signs, PCA PDF section 7): approved petty-cash bills come
here too. The Accounts Manager records each payment as Process 1 (cash withdrawal from bank)
or Process 2 (direct payment by the Accounts Department) -- `payment_source` -- with its
reference and date. Paying a petty-cash bill tops the employee's PCA back up: it is logged as a
paid top-up of that bill (ErpExpenseFundTopupRequest kind='topup'), which is what the fund
figures count as replenished.
"""
from datetime import date, datetime
from typing import Any, Optional, Union

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from auth.security import CurrentUser
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseApprovalHistory,
    ErpExpenseCategory,
    ErpExpensePaymentRecord,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
)
from services.currency import region_base_currency
from services.region_scope import user_covers, user_region_ids

PAYMENT_METHODS = ("bank_transfer", "cash", "payroll", "cheque")
PAYMENT_METHOD_LABELS = {
    "bank_transfer": "Bank transfer",
    "cash": "Cash",
    "payroll": "Payroll",
    "cheque": "Cheque",
}


def payment_to_dict(p: ErpExpensePaymentRecord) -> dict[str, Any]:
    from services.region_policy import PAYMENT_SOURCE_LABELS

    source = getattr(p, "payment_source", None)
    return {
        "id": p.payment_id,
        "transaction_id": p.transaction_id,
        "amount": p.amount,
        "currency": p.currency,
        "payment_method": p.payment_method,
        # Professional Signs shows the PDF process (cash withdrawal / direct payment) instead.
        "payment_method_label": PAYMENT_SOURCE_LABELS.get(source)
        or PAYMENT_METHOD_LABELS.get(p.payment_method, p.payment_method),
        "payment_source": source,
        "payment_reference": p.payment_reference,
        "payment_date": p.payment_date.date().isoformat() if p.payment_date else None,
        "paid_by": p.paid_by,
        "paid_by_name": p.payer.display_name if p.payer else None,
        "remarks": p.remarks,
        "recorded_at": p.created_on.isoformat() if p.created_on else None,
    }


def _parse_date(value: Union[str, date, datetime, None]) -> datetime:
    if value is None or (isinstance(value, str) and not value.strip()):
        return datetime.combine(date.today(), datetime.min.time())
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", ""))
    except ValueError as exc:
        raise ValueError("Payment date must be a date like 2026-10-30") from exc
    if parsed.date() > date.today():
        raise ValueError("Payment date can't be in the future")
    return parsed


def _payable_amount(txn: ErpExpenseTransaction) -> tuple[float, str]:
    """What the employee is owed, in the company's base currency."""
    base = txn.base_currency or region_base_currency(txn.region)
    if txn.total_amount_base is not None:
        return round(float(txn.total_amount_base), 2), base
    total = txn.total_amount if txn.total_amount is not None else (txn.amount or 0) + (txn.vat_amount or 0)
    bill = (txn.currency or "").strip().upper()
    rate = 1.0 if bill == base else float(txn.exchange_rate or 1.0)
    return round(float(total or 0) * rate, 2), base


def _payable_sql():
    """(currency, amount) SQL expressions matching _payable_amount, so the page totals add
    up the same figures the rows show -- including bills with no stored base amount yet.
    Needs ErpExpenseRegionConfig joined to the query. Don't GROUP BY the currency
    expression on SQL Server (bound literal); see list_claims."""
    t, r = ErpExpenseTransaction, ErpExpenseRegionConfig
    currency = func.coalesce(t.base_currency, r.base_currency, "AED")
    bill_total = func.coalesce(t.total_amount, func.coalesce(t.amount, 0) + func.coalesce(t.vat_amount, 0))
    converted = case(
        (func.upper(func.coalesce(t.currency, "")) == currency, bill_total),
        else_=bill_total * func.coalesce(func.nullif(t.exchange_rate, 0), 1.0),
    )
    return currency, func.coalesce(t.total_amount_base, converted)


class PaymentService:
    def _require_payer(self, db: Session, user: CurrentUser, txn: ErpExpenseTransaction) -> None:
        from services.region_policy import payer_roles

        if user.is_admin:
            return
        if user.role not in payer_roles(txn.region):
            raise PermissionError("You don't record payments for this company")
        if not user_covers(db, user.id, txn.region_id):
            raise PermissionError("This claim belongs to a company you don't handle")

    def record_payment(
        self,
        db: Session,
        user: CurrentUser,
        transaction_id: int,
        *,
        payment_method: Optional[str] = None,
        payment_reference: str,
        payment_date: Union[str, date, datetime, None],
        remarks: Optional[str] = None,
        payment_source: Optional[str] = None,
        notify: bool = True,
    ) -> dict[str, Any]:
        from services.region_policy import PAYMENT_SOURCE_LABELS, PAYMENT_SOURCES, is_employee_model

        txn = (
            db.query(ErpExpenseTransaction)
            .options(joinedload(ErpExpenseTransaction.region), joinedload(ErpExpenseTransaction.payment))
            .filter(ErpExpenseTransaction.transaction_id == transaction_id)
            .first()
        )
        if not txn:
            raise LookupError("Claim not found")
        self._require_payer(db, user, txn)
        employee_model = is_employee_model(txn.region)
        petty_cash = (txn.type or "").strip().lower() == "petty_cash"
        if petty_cash and not employee_model:
            raise ValueError("Petty cash claims are settled from the fund at final approval; there is no payment step")
        if txn.payment is not None or txn.status == "paid":
            raise ValueError("This claim has already been paid")
        if txn.status != "approved":
            raise ValueError("Only approved claims can be marked paid")
        source = (payment_source or "").strip().lower() or None
        if employee_model:
            # PDF section 7: Process 1 (cash withdrawal from bank) or Process 2 (direct payment).
            if source not in PAYMENT_SOURCES:
                raise ValueError(
                    "Choose how it was paid: Process 1 (cash withdrawal from bank) or "
                    "Process 2 (direct payment by the Accounts Department)"
                )
            method = (payment_method or "").strip().lower() or "cash"
        else:
            source = None
            method = (payment_method or "").strip().lower()
        if method not in PAYMENT_METHODS:
            raise ValueError(f"Payment method must be one of: {', '.join(PAYMENT_METHODS)}")
        reference = (payment_reference or "").strip()
        if not reference:
            raise ValueError("Enter the payment reference (transfer number, cheque number, payroll batch…)")
        paid_on = _parse_date(payment_date)
        amount, currency = _payable_amount(txn)
        from services.accounts_cash_service import ACCOUNTS_PETTY_CASH, after_payout, take_payout

        from_accounts_cash = employee_model and source == ACCOUNTS_PETTY_CASH
        if from_accounts_cash:
            # PDF section 6: Process 2 comes out of the Accounts Department's own petty cash.
            take_payout(
                db, txn.region, amount, user.id,
                currency=currency,
                transaction_id=txn.transaction_id,
                reference=reference,
                paid_on=paid_on,
                remarks=(remarks or "").strip() or None,
            )
        record = ErpExpensePaymentRecord(
            transaction_id=txn.transaction_id,
            amount=amount,
            currency=currency,
            payment_method=method,
            payment_reference=reference[:128],
            payment_date=paid_on,
            paid_by=user.id,
            remarks=(remarks or "").strip() or None,
            payment_source=source,
            created_by=user.id,
            is_active=1,
        )
        db.add(record)
        if petty_cash:
            # Paying the bill tops the employee's PCA back up by what the bill took from it.
            self._top_up_pca(db, user, txn, source, method, reference, paid_on, record.remarks)
        txn.status = "paid"
        txn.paid_on = paid_on
        label = PAYMENT_SOURCE_LABELS[source] if source else PAYMENT_METHOD_LABELS[method]
        db.add(
            ErpExpenseApprovalHistory(
                transaction_id=txn.transaction_id,
                stage="finance_manager",
                actor_id=user.id,
                action="paid",
                comment=f"{label} · ref {reference} · {paid_on.date().isoformat()}"
                + (f" · {record.remarks}" if record.remarks else ""),
            )
        )
        db.commit()
        if from_accounts_cash:
            after_payout(db, txn.region_id)
        if notify:
            from services.transaction_service import transaction_service

            db.refresh(txn)
            transaction_service._notify_employee(db, txn, "paid", record.remarks)
        return payment_to_dict(record)

    def _top_up_pca(
        self,
        db: Session,
        user: CurrentUser,
        txn: ErpExpenseTransaction,
        source: Optional[str],
        method: str,
        reference: str,
        paid_on: datetime,
        remarks: Optional[str],
    ) -> None:
        """Employee-advance company: log the payment of an approved petty-cash bill as a paid
        top-up of that bill, so the employee's PCA counts it as replenished."""
        from database.models import ErpExpenseFundTopupBill, ErpExpenseFundTopupRequest
        from services.fund_service import _topup_history, bill_shares, fund_service

        fund = fund_service.employee_advance(db, txn.employee_id, txn.region_id)
        if fund is None:
            return  # no PCA (e.g. removed since): nothing to refill
        taken = fund_service._linked_transaction_ids(db, fund.fund_id)
        if txn.transaction_id in taken:
            raise ValueError("This bill is already on a top-up request; finish or reject that request first")
        part = round(bill_shares(txn, fund.currency).get(None, 0.0), 2)
        if part <= 0:
            return
        row = ErpExpenseFundTopupRequest(
            fund_id=fund.fund_id,
            kind="topup",
            amount=part,
            requester_id=user.id,
            status="paid",
            remarks=remarks,
            verified_by=user.id,
            verified_on=datetime.utcnow(),
            decided_by=user.id,
            decided_on=datetime.utcnow(),
            paid_by=user.id,
            payment_source=source,
            payment_method=method,
            payment_reference=reference[:128],
            payment_date=paid_on,
            is_active=1,
        )
        db.add(row)
        db.flush()
        db.add(ErpExpenseFundTopupBill(topup_id=row.topup_id, transaction_id=txn.transaction_id, amount=part))
        _topup_history(db, row, user.id, "paid", f"Bill #{txn.transaction_id} paid · ref {reference}")

    def record_batch(
        self,
        db: Session,
        user: CurrentUser,
        transaction_ids: list[int],
        *,
        payment_method: Optional[str] = None,
        payment_reference: str,
        payment_date: Union[str, date, datetime, None],
        remarks: Optional[str] = None,
        payment_source: Optional[str] = None,
    ) -> dict[str, Any]:
        """One transfer covering several claims: same method (or, at Professional Signs, the
        same process), reference and date on each."""
        paid: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for transaction_id in dict.fromkeys(transaction_ids):
            try:
                paid.append(
                    self.record_payment(
                        db, user, transaction_id,
                        payment_method=payment_method,
                        payment_reference=payment_reference,
                        payment_date=payment_date,
                        remarks=remarks,
                        payment_source=payment_source,
                    )
                )
            except (LookupError, PermissionError, ValueError) as exc:
                db.rollback()
                skipped.append({"id": transaction_id, "reason": str(exc)})
        return {"paid": paid, "skipped": skipped}

    def list_claims(
        self,
        db: Session,
        user: CurrentUser,
        *,
        status: str = "unpaid",
        region_code: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Reimbursements waiting for payment (or already paid), for the companies this person
        pays, newest approval first. `totals` sums every matching claim (not just this page)
        per base currency."""
        from services.transaction_service import transaction_to_dict

        from services.region_policy import payer_roles

        if not user.is_admin and user.role not in ("finance_manager", "accountant"):
            raise PermissionError("Only the Finance Manager or Admin can see payments")
        # Companies where this person's role records payments (e.g. an Accountant only sees
        # Professional Signs, where the Accounts Department pays).
        paying_region_ids: Optional[set[int]] = None
        if not user.is_admin:
            paying_region_ids = {
                r.region_id for r in db.query(ErpExpenseRegionConfig).all() if user.role in payer_roles(r)
            }
            if not paying_region_ids:
                raise PermissionError("You don't record payments for any company")
        from services.region_policy import is_employee_model

        wanted = "paid" if status == "paid" else "approved"
        # Petty cash is paid here only in employee-advance companies (Professional Signs:
        # paying an approved bill tops up the employee's PCA). Elsewhere it's settled from the
        # department fund at approval.
        employee_region_ids = {
            r.region_id for r in db.query(ErpExpenseRegionConfig).all() if is_employee_model(r)
        }
        type_filter = ErpExpenseTransaction.type != "petty_cash"
        if employee_region_ids:
            type_filter = or_(type_filter, ErpExpenseTransaction.region_id.in_(employee_region_ids))
        q = (
            db.query(ErpExpenseTransaction)
            .outerjoin(ErpExpenseRegionConfig, ErpExpenseRegionConfig.region_id == ErpExpenseTransaction.region_id)
            .filter(ErpExpenseTransaction.status == wanted, type_filter)
        )
        if not user.is_admin:
            region_ids = user_region_ids(db, user.id)
            if region_ids is not None:
                q = q.filter(ErpExpenseTransaction.region_id.in_(region_ids or {-1}))
            q = q.filter(ErpExpenseTransaction.region_id.in_(paying_region_ids or {-1}))
        if region_code and region_code.strip():
            q = q.filter(ErpExpenseRegionConfig.region_code == region_code.strip().upper())
        # Grouped by the two plain currency columns, then combined here: SQL Server rejects a
        # GROUP BY expression containing a bound literal (the 'AED' fallback), since the
        # SELECT and GROUP BY copies are different parameters to it.
        _, pay_amount = _payable_sql()
        totals: dict[str, float] = {}
        for txn_cur, region_cur, amount in (
            q.with_entities(ErpExpenseTransaction.base_currency, ErpExpenseRegionConfig.base_currency, func.sum(pay_amount))
            .group_by(ErpExpenseTransaction.base_currency, ErpExpenseRegionConfig.base_currency)
            .all()
        ):
            currency = (txn_cur or region_cur or "AED").strip().upper()
            totals[currency] = round(totals.get(currency, 0.0) + float(amount or 0), 2)
        total = q.order_by(None).count()
        order = ErpExpenseTransaction.paid_on.desc() if wanted == "paid" else ErpExpenseTransaction.decided_on.desc()
        rows = (
            q.options(
                joinedload(ErpExpenseTransaction.documents),
                joinedload(ErpExpenseTransaction.region),
                joinedload(ErpExpenseTransaction.category).joinedload(ErpExpenseCategory.owning_department),
                joinedload(ErpExpenseTransaction.vendor),
                joinedload(ErpExpenseTransaction.employee).joinedload(ErpAuthExpenseUsers.department),
                joinedload(ErpExpenseTransaction.payment).joinedload(ErpExpensePaymentRecord.payer),
                selectinload(ErpExpenseTransaction.line_items),
            )
            .order_by(order, ErpExpenseTransaction.transaction_id.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 200)))
            .all()
        )
        items = []
        for txn in rows:
            data = transaction_to_dict(txn)
            amount, currency = _payable_amount(txn)
            data["payable_amount"] = amount
            data["payable_currency"] = currency
            data["payment"] = payment_to_dict(txn.payment) if txn.payment else None
            items.append(data)
        return {"items": items, "total": total, "offset": offset, "limit": limit, "totals": totals}


payment_service = PaymentService()
