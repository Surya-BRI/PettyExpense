import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload

from auth.security import CurrentUser
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseApprovalHistory,
    ErpExpenseCategory,
    ErpExpenseDocument,
    ErpExpenseDocumentPage,
    ErpExpenseLineItem,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpExpenseVendor,
)
from services.currency import bill_and_base_text, region_base_currency
from services.department_split import stage_base
from services.exchange_rate_service import ExchangeRateError, lookup_rate
from services.ocr_service import ocr_service, refresh_reference_data
from services.region_scope import require_bill_region_allowed
from services.storage import storage_service


def _field_confidence_json(document: Optional[ErpExpenseDocument]) -> Optional[str]:
    if not document or not document.ocr_raw_json:
        return None
    try:
        data = json.loads(document.ocr_raw_json) if isinstance(document.ocr_raw_json, str) else document.ocr_raw_json
        if isinstance(data, str):
            data = json.loads(data)
        confidence = data.get("field_confidence") if isinstance(data, dict) else None
        return json.dumps(confidence) if confidence else None
    except (TypeError, ValueError):
        return None


def _history(db: Session, transaction_id: int, actor_id: int, stage: str, action: str, comment: Optional[str] = None) -> None:
    db.add(
        ErpExpenseApprovalHistory(
            transaction_id=transaction_id,
            stage=stage,
            actor_id=actor_id,
            action=action,
            comment=comment,
        )
    )


def _resolve_vendor(db: Session, vendor_name: Optional[str]) -> Optional[ErpExpenseVendor]:
    # Exact-match lookup only -- no auto-create on a miss. A miss (new vendor, or OCR/typo
    # variance on a known one) is left unmatched and surfaced to the Accountant via
    # vendor_raw_text / vendor_unmatched instead of silently fragmenting the vendor table
    # with near-duplicate rows ("Uber" / "uber" / "Ubar").
    if not vendor_name or not vendor_name.strip():
        return None
    vendor_name = vendor_name.strip()
    return db.query(ErpExpenseVendor).filter(ErpExpenseVendor.vendor_name == vendor_name).first()


def _replace_line_items(db: Session, txn: ErpExpenseTransaction, lines: list[dict[str, Any]]) -> None:
    """Replaces the transaction's item lines and makes its money fields consistent with them:
    total = sum of line amounts (as printed, VAT-inclusive); amount excl. VAT = total - VAT."""
    category_ids = {ln.get("category_id") for ln in lines if ln.get("category_id") is not None}
    if category_ids:
        known = {c for (c,) in db.query(ErpExpenseCategory.category_id).filter(ErpExpenseCategory.category_id.in_(category_ids)).all()}
        missing = category_ids - known
        if missing:
            raise ValueError(f"Unknown category_id on line items: {sorted(missing)}")
    cleaned = []
    for ln in lines:
        description = (ln.get("description") or "").strip()
        amount = ln.get("amount")
        if not description:
            raise ValueError("Every line item needs a description")
        if amount is None or amount < 0:
            raise ValueError(f"Line item '{description}' needs an amount of 0 or more")
        op_number = (ln.get("op_number") or "").strip() or None
        vat_percent = ln.get("vat_percent")
        vat_percent = float(vat_percent) if vat_percent is not None else None
        cleaned.append((description[:512], ln.get("quantity"), round(float(amount), 2), ln.get("category_id"), op_number, vat_percent))

    txn.line_items.clear()
    for i, (description, quantity, amount, category_id, op_number, vat_percent) in enumerate(cleaned, start=1):
        txn.line_items.append(
            ErpExpenseLineItem(
                line_no=i, description=description, quantity=quantity, amount=amount,
                category_id=category_id, op_number=op_number, vat_percent=vat_percent,
            )
        )
    if cleaned:
        total = round(sum(a for _, _, a, _, _, _ in cleaned), 2)
        vat = round(txn.vat_amount or 0.0, 2)
        if vat > total:
            raise ValueError("VAT can't be more than the total of the line items")
        txn.total_amount = total
        txn.amount = round(total - vat, 2)


def _image_url(s3_key: str, proxy: str) -> str:
    return storage_service.presigned_url(s3_key) or proxy


def _page_urls(document: ErpExpenseDocument, page1_url: str) -> list[dict[str, Any]]:
    """Every page of the bill in order: page 1 is the document itself, then its extra pages."""
    return [{"page_no": 1, "image_url": page1_url}] + [
        {
            "page_no": p.page_no,
            "image_url": _image_url(
                p.s3_key, f"/api/claims/receipts/{document.document_id}/pages/{p.page_no}/image"
            ),
        }
        for p in document.pages
    ]


def _ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1] if "." in filename else "jpg"


def _norm_bill_number(value: Optional[str]) -> Optional[str]:
    """Trim + casefold so 'INV-1' and 'inv-1' count as the same invoice."""
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned.casefold() if cleaned else None


def _quote(bill: str, base: str, *, required: bool) -> Optional[dict[str, Any]]:
    """Today's published rate for 1 bill unit in the base currency, or None when it can't be
    fetched and isn't required (a draft — submit asks again and fails cleanly)."""
    if not bill or bill == base:
        return {"rate": 1.0, "as_of": datetime.utcnow().date().isoformat(), "source": "same_currency"}
    try:
        return lookup_rate(bill, base)
    except ExchangeRateError as exc:
        if required:
            raise ValueError(str(exc)) from exc
        return None


def _base_rate(txn: ErpExpenseTransaction) -> Optional[float]:
    """Rate used for the base-currency figures; None while a foreign bill has no rate yet."""
    bill = (txn.currency or "").strip().upper()
    if not bill or bill == (txn.base_currency or "").strip().upper():
        return 1.0
    if txn.exchange_rate_date and txn.exchange_rate:
        return float(txn.exchange_rate)
    return None


def _fill_base_amounts(txn: ErpExpenseTransaction) -> None:
    rate = _base_rate(txn)
    if rate is None:
        txn.amount_base = txn.vat_amount_base = txn.total_amount_base = None
        return
    total = txn.total_amount if txn.total_amount is not None else (txn.amount or 0) + (txn.vat_amount or 0)
    txn.amount_base = round(float(txn.amount or 0) * rate, 2)
    txn.vat_amount_base = round(float(txn.vat_amount or 0) * rate, 2)
    txn.total_amount_base = round(float(total or 0) * rate, 2)


def _stamp_exchange_rate(txn: ErpExpenseTransaction, *, required: bool, keep_locked: bool = False) -> None:
    """Converts the bill into its company's base currency and stores the rate, its date and
    the converted amounts. keep_locked (dispute → resubmit) reuses the rate already on the
    bill as long as the company's base currency is the same; update_draft clears that rate
    when the bill currency or company changes. A client-sent rate is never used."""
    base = region_base_currency(txn.region)
    locked = (
        keep_locked
        and txn.exchange_rate_date
        and txn.exchange_rate
        and (txn.base_currency or "").strip().upper() == base
    )
    if not locked:
        quote = _quote((txn.currency or "").strip().upper(), base, required=required)
        txn.base_currency = base
        txn.exchange_rate = float(quote["rate"]) if quote else 1.0
        txn.exchange_rate_date = quote.get("as_of") if quote else None
        txn.exchange_rate_source = quote.get("source") if quote else None
    _fill_base_amounts(txn)


def _ocr_bill_number(ocr: Optional[dict[str, Any]]) -> Optional[str]:
    if not ocr:
        return None
    fields = ocr.get("fields") or {}
    return (
        (fields.get("invoice_number") or {}).get("value")
        or (fields.get("transaction_number") or {}).get("value")
        or ocr.get("bill_number")
    )


def _resolve_region_by_id(db: Session, region_id: int) -> Optional[ErpExpenseRegionConfig]:
    return db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()


def _resolve_region(db: Session, region_code: str) -> ErpExpenseRegionConfig:
    region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_code == region_code).first()
    if not region:
        raise ValueError(f"Unknown region_code: {region_code}")
    return region


def _line_cross_department(txn: ErpExpenseTransaction, line: ErpExpenseLineItem) -> tuple[Optional[int], Optional[str]]:
    category = line.category or txn.category
    own = txn.employee.department_id if txn.employee else None
    if not category or not category.owning_department_id or category.owning_department_id == own:
        return None, None
    dept = category.owning_department
    return category.owning_department_id, dept.department_name if dept else None


def payment_status(txn: ErpExpenseTransaction) -> Optional[str]:
    """not_applicable (petty cash, settled from the fund) | unpaid (approved reimbursement
    waiting for Finance) | paid. None while the claim is still in approval."""
    if (txn.type or "").strip().lower() == "petty_cash":
        return "not_applicable"
    if txn.status == "paid":
        return "paid"
    if txn.status == "approved":
        return "unpaid"
    return None


def transaction_to_dict(
    txn: ErpExpenseTransaction,
    include_history: bool = False,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    document = txn.documents[0] if txn.documents else None
    line_rate = _base_rate(txn) if txn.total_amount_base is not None else None
    data: dict[str, Any] = {
        "id": txn.transaction_id,
        "type": txn.type,
        "employee_id": txn.employee_id,
        "employee_name": txn.employee.display_name if txn.employee else None,
        "region_id": txn.region_id,
        "region_code": txn.region.region_code if txn.region else None,
        "project_id": txn.project_cache_id,
        "category_id": txn.category_id,
        "category_name": txn.category.category_name if txn.category else None,
        "vendor_id": txn.vendor_id,
        "vendor_name": txn.vendor.vendor_name if txn.vendor else txn.vendor_raw_text,
        "vendor_unmatched": bool(txn.vendor_raw_text) and not txn.vendor_id,
        "bill_date": txn.bill_date,
        "currency": txn.currency,
        "exchange_rate": txn.exchange_rate,
        "amount": txn.amount,
        "vat_amount": txn.vat_amount,
        "total_amount": txn.total_amount,
        # The same bill in its company's base currency (what petty cash is debited and
        # reimbursements are paid in). Null while a foreign-currency draft has no rate yet.
        "base_currency": txn.base_currency or region_base_currency(txn.region),
        "exchange_rate_date": txn.exchange_rate_date,
        "exchange_rate_source": txn.exchange_rate_source,
        "amount_base": txn.amount_base,
        "vat_amount_base": txn.vat_amount_base,
        "total_amount_base": txn.total_amount_base,
        "op_number": txn.op_number,
        "bill_number": txn.bill_number,
        "status": txn.status,
        "payment_status": payment_status(txn),
        # Base stage name (hod | department_hod | accountant | finance_manager) for role/queue
        # checks; the key says which department for a 'department_hod:<id>' stage and matches
        # the entries of stage_sequence / stage_labels.
        "current_stage": stage_base(txn.current_stage),
        "current_stage_key": txn.current_stage,
        "dispute_returned": bool(txn.dispute_returned),
        "remarks": txn.remarks,
        "duplicate_flag": bool(txn.duplicate_flag),
        "ocr_confidence_json": txn.ocr_confidence_json,
        "created_at": txn.created_on.isoformat() if txn.created_on else None,
        "updated_at": txn.modified_on.isoformat() if txn.modified_on else None,
        "submitted_at": txn.submitted_on.isoformat() if txn.submitted_on else None,
        "decided_at": txn.decided_on.isoformat() if txn.decided_on else None,
        "paid_at": txn.paid_on.isoformat() if txn.paid_on else None,
        "receipt": None,
        "duplicate_warning": None,
        "stage_sequence": [],
        # "multiple" when the bill was itemised: total == sum of these lines.
        "line_mode": "multiple" if txn.line_items else "single",
        "line_items": [
            {
                "id": li.line_item_id,
                "line_no": li.line_no,
                "description": li.description,
                "quantity": li.quantity,
                "amount": li.amount,
                "amount_base": round(li.amount * line_rate, 2) if line_rate is not None else None,
                "category_id": li.category_id,
                "category_name": li.category.category_name if li.category else None,
                # Set when this line belongs to another department than the employee's
                # (its HOD approves it and, for petty cash, its fund pays for it).
                "owning_department_id": _line_cross_department(txn, li)[0],
                "owning_department_name": _line_cross_department(txn, li)[1],
                "op_number": li.op_number,
                "vat_percent": li.vat_percent,
            }
            for li in txn.line_items
        ],
    }
    if db is not None:
        # Lazy import avoids a circular import with approval_service.py.
        from services.approval_service import resolve_stage_labels, resolve_stage_sequence

        try:
            data["stage_sequence"] = resolve_stage_sequence(db, txn)
            data["stage_labels"] = resolve_stage_labels(txn)
        except Exception:
            data["stage_sequence"] = []
            data["stage_labels"] = {}
    if document:
        proxy = f"/api/claims/receipts/{document.document_id}/image"
        image_url = _image_url(document.s3_key, proxy)
        data["receipt"] = {
            "id": document.document_id,
            "s3_key": document.s3_key,
            "content_type": document.content_type,
            "ocr_vendor": document.ocr_vendor,
            "ocr_amount": document.ocr_amount,
            "ocr_vat_amount": document.ocr_vat_amount,
            "ocr_total_amount": document.ocr_total_amount,
            "ocr_currency": document.ocr_currency,
            "ocr_date": document.ocr_date,
            "ocr_confidence": document.ocr_confidence,
            "image_hash": document.hash,
            "image_url": image_url,
            "image_proxy_url": proxy,
        }
        # Detail views only -- list endpoints would lazy-load every claim's pages.
        if include_history:
            data["receipt"]["pages"] = _page_urls(document, image_url)
    if include_history:
        from services.payment_service import payment_to_dict

        data["payment"] = payment_to_dict(txn.payment) if txn.payment else None
        data["history"] = [
            {
                "id": h.approval_history_id,
                "stage": h.stage,
                "actor_id": h.actor_id,
                "actor_name": h.actor.display_name if h.actor else None,
                "action": h.action,
                "remarks": h.comment,
                "created_at": h.acted_on.isoformat() if h.acted_on else None,
            }
            for h in sorted(txn.approval_history, key=lambda x: x.acted_on or datetime.min)
        ]
    return data


class TransactionService:
    def store_receipt(
        self, db: Session, image_bytes: bytes, content_type: str, filename: str,
        extra_pages: list[tuple[bytes, str, str]] = (),
    ) -> dict[str, Any]:
        """Upload to S3 and insert the document row. Does not run OCR.
        extra_pages are pages 2..N of the same bill as (bytes, content_type, filename)."""
        key = storage_service.save_bytes(image_bytes, content_type=content_type, ext=_ext(filename))
        img_hash = storage_service.image_hash(image_bytes)
        document = ErpExpenseDocument(
            transaction_id=None,
            s3_key=key,
            content_type=content_type,
            hash=img_hash,
        )
        for page_no, (page_bytes, page_type, page_name) in enumerate(extra_pages, start=2):
            document.pages.append(
                ErpExpenseDocumentPage(
                    page_no=page_no,
                    s3_key=storage_service.save_bytes(page_bytes, content_type=page_type, ext=_ext(page_name)),
                    content_type=page_type,
                    hash=storage_service.image_hash(page_bytes),
                )
            )
        db.add(document)
        db.commit()
        db.refresh(document)
        return self._receipt_payload(document, ocr=None, duplicate=None, ocr_status="pending")

    def analyze_receipt(
        self, db: Session, receipt_id: int, mode: str = "auto", employee_id: Optional[int] = None,
        region_code: Optional[str] = None,
    ) -> dict[str, Any]:
        document = self.get_receipt(db, receipt_id)
        images = [storage_service.read_bytes(k) for k in [document.s3_key, *(p.s3_key for p in document.pages)]]
        if not all(images):
            raise LookupError("Receipt image not found in storage")
        refresh_reference_data(db)
        # All pages go to GPT in one request so it reads the bill as a whole.
        ocr = ocr_service.run(images, "receipt.jpg", mode=mode, region_code=region_code)
        document.ocr_raw_json = (
            ocr.get("raw_json") if isinstance(ocr.get("raw_json"), str) else json.dumps(ocr.get("raw_json"))
        )
        document.ocr_vendor = ocr.get("vendor") or None
        document.ocr_amount = ocr.get("amount")
        document.ocr_vat_amount = ocr.get("vat_amount")
        document.ocr_total_amount = ocr.get("total_amount")
        document.ocr_currency = ocr.get("currency")
        document.ocr_date = ocr.get("date") or None
        document.ocr_confidence = ocr.get("confidence")
        db.commit()
        db.refresh(document)
        duplicate = self._find_duplicate(
            db, ocr.get("vendor"), ocr.get("amount"), ocr.get("date"), employee_id=employee_id,
            bill_number=_ocr_bill_number(ocr),
        )
        return self._receipt_payload(document, ocr=ocr, duplicate=duplicate, ocr_status="done")

    def run_ocr(
        self, db: Session, image_bytes: bytes, content_type: str, filename: str, employee_id: Optional[int] = None,
        region_code: Optional[str] = None,
    ) -> dict[str, Any]:
        stored = self.store_receipt(db, image_bytes, content_type, filename)
        return self.analyze_receipt(db, stored["receipt_id"], employee_id=employee_id, region_code=region_code)

    def _receipt_payload(
        self,
        document: ErpExpenseDocument,
        *,
        ocr: Optional[dict[str, Any]],
        duplicate: Optional[dict[str, Any]],
        ocr_status: str,
    ) -> dict[str, Any]:
        proxy = f"/api/claims/receipts/{document.document_id}/image"
        image_url = _image_url(document.s3_key, proxy)
        pages = _page_urls(document, image_url)
        ocr = ocr or {}
        return {
            "receipt_id": document.document_id,
            "s3_key": document.s3_key,
            "ocr_status": ocr_status,
            "vendor": ocr.get("vendor") or document.ocr_vendor or "",
            "expense_type": ocr.get("expense_type"),
            "amount": ocr.get("amount", document.ocr_amount),
            "vat_amount": ocr.get("vat_amount", document.ocr_vat_amount),
            "total_amount": ocr.get("total_amount", document.ocr_total_amount),
            "currency": ocr.get("currency") or document.ocr_currency,
            "date": ocr.get("date") or document.ocr_date or "",
            "confidence": ocr.get("confidence", document.ocr_confidence),
            "field_confidence": ocr.get("field_confidence") or {},
            "low_confidence_fields": ocr.get("low_confidence_fields") or [],
            "reconciliation_mismatch": ocr.get("reconciliation_mismatch") or False,
            "bill_number": (
                (ocr.get("fields", {}).get("invoice_number") or {}).get("value")
                or (ocr.get("fields", {}).get("transaction_number") or {}).get("value")
                or None
            ),
            "line_items": ocr.get("line_items") or [],
            "raw_text": ocr.get("raw_text"),
            "image_hash": document.hash,
            "image_url": image_url,
            "image_proxy_url": proxy,
            "page_count": len(pages),
            "pages": pages,
            "duplicate_warning": duplicate,
        }

    def _find_submitted_bill_number(
        self,
        db: Session,
        bill_number: Optional[str],
        exclude_transaction_id: Optional[int] = None,
    ) -> Optional[ErpExpenseTransaction]:
        """Another claim that already used this invoice number and was submitted (not draft/rejected)."""
        needle = _norm_bill_number(bill_number)
        if not needle:
            return None
        q = db.query(ErpExpenseTransaction).filter(
            ErpExpenseTransaction.bill_number.isnot(None),
            ErpExpenseTransaction.status.notin_(("draft", "rejected")),
            func.lower(func.ltrim(func.rtrim(ErpExpenseTransaction.bill_number))) == needle,
        )
        if exclude_transaction_id:
            q = q.filter(ErpExpenseTransaction.transaction_id != exclude_transaction_id)
        return q.first()

    def _require_unique_submitted_bill_number(
        self,
        db: Session,
        bill_number: Optional[str],
        exclude_transaction_id: Optional[int] = None,
    ) -> None:
        hit = self._find_submitted_bill_number(db, bill_number, exclude_transaction_id)
        if hit:
            shown = str(bill_number).strip()
            raise ValueError(
                f"Invoice number {shown} has already been submitted. "
                "You cannot submit the same invoice again."
            )

    def _require_petty_cash_limit(self, db: Session, user: CurrentUser, txn: ErpExpenseTransaction) -> None:
        """Checks the bill (converted to the fund's currency) fits what's left in every pot it
        draws on — the employee's own, plus each owning department's for cross-department
        lines. The exchange rate must already be stamped on `txn`."""
        if txn.region_id is None:
            raise ValueError("Pick a company before submitting a petty-cash bill")
        from auth.security import get_user_by_id
        from services.fund_service import fund_service

        orm = get_user_by_id(db, user.id)
        if orm is None:
            raise ValueError("No petty cash limit is set for this department in this company")
        # New line items / a new transaction must be persistent so their category and
        # employee relationships load for the department split.
        db.flush()
        region = txn.region or _resolve_region_by_id(db, txn.region_id)
        fund_service.require_bill_within_limits(db, orm, txn, region_base_currency(region))

    def _find_duplicate(
        self,
        db: Session,
        vendor_name: Optional[str],
        amount: Optional[float],
        bill_date: Optional[str],
        exclude_transaction_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        bill_number: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        hit = self._find_submitted_bill_number(db, bill_number, exclude_transaction_id)
        if hit:
            shown = str(bill_number).strip()
            return {
                "reason": "same_bill_number",
                "existing_claim_id": hit.transaction_id,
                "message": (
                    f"Invoice number {shown} has already been submitted. "
                    "You cannot submit the same invoice again."
                ),
            }
        # Same-image-hash matching was dropped — re-uploading an identical photo isn't evidence of duplication on its own; same vendor+amount+date is.
        # Scoped to the same employee: two different employees legitimately spending the same
        # amount at the same vendor on the same day (e.g. a common fixed-fare taxi route) is a
        # coincidence, not a duplicate -- only the same person resubmitting/reusing a bill is.
        if vendor_name and amount is not None and bill_date and employee_id is not None:
            vendor = db.query(ErpExpenseVendor).filter(ErpExpenseVendor.vendor_name == vendor_name).first()
            if vendor:
                q = db.query(ErpExpenseTransaction).filter(
                    ErpExpenseTransaction.vendor_id == vendor.vendor_id,
                    ErpExpenseTransaction.amount == amount,
                    ErpExpenseTransaction.bill_date == bill_date,
                    ErpExpenseTransaction.employee_id == employee_id,
                    ErpExpenseTransaction.status != "rejected",
                )
                if exclude_transaction_id:
                    q = q.filter(ErpExpenseTransaction.transaction_id != exclude_transaction_id)
                hit_txn = q.first()
                if hit_txn:
                    return {
                        "reason": "same_vendor_amount_date",
                        "existing_claim_id": hit_txn.transaction_id,
                        "message": "This employee already has another claim with the same vendor, amount, and date.",
                    }
        return None

    def create_claim(
        self,
        db: Session,
        user: CurrentUser,
        *,
        vendor: str,
        amount: float,
        vat_amount: float = 0.0,
        total_amount: Optional[float] = None,
        currency: str = "AED",
        exchange_rate: float = 1.0,
        bill_date: Optional[str],
        category_id: int,
        region_code: str,
        type: str = "reimbursement",
        project_id: Optional[int],
        op_number: Optional[str],
        bill_number: Optional[str],
        remarks: Optional[str],
        receipt_id: Optional[int],
        s3_key: Optional[str],
        submit: bool = True,
        line_items: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        region = _resolve_region(db, region_code)
        require_bill_region_allowed(db, user.id, user.region_code, region.region_code)
        category = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.category_id == category_id).first()
        if not category:
            raise ValueError("Unknown category_id")
        if submit:
            self._require_unique_submitted_bill_number(db, bill_number)
        vendor_obj = _resolve_vendor(db, vendor)

        txn = ErpExpenseTransaction(
            type=type,
            employee_id=user.id,
            region_id=region.region_id,
            project_cache_id=project_id,
            category_id=category.category_id,
            vendor_id=vendor_obj.vendor_id if vendor_obj else None,
            vendor_raw_text=None if vendor_obj else (vendor.strip() if vendor and vendor.strip() else None),
            bill_date=bill_date,
            currency=currency,
            amount=amount,
            vat_amount=vat_amount,
            total_amount=total_amount if total_amount is not None else amount + vat_amount,
            op_number=op_number,
            bill_number=bill_number,
            remarks=remarks,
            status="submitted" if submit else "draft",
            submitted_on=datetime.utcnow() if submit else None,
        )
        txn.region = region
        db.add(txn)
        db.flush()
        if line_items:
            _replace_line_items(db, txn, line_items)
            amount = txn.amount  # duplicate check below compares the line-derived amount
        # The client-sent exchange_rate is ignored; the rate is stamped (and locked on submit) here.
        _stamp_exchange_rate(txn, required=submit)
        if submit and (txn.type or "").strip().lower() == "petty_cash":
            self._require_petty_cash_limit(db, user, txn)

        document = None
        if receipt_id:
            document = db.query(ErpExpenseDocument).filter(ErpExpenseDocument.document_id == receipt_id).first()
        elif s3_key:
            document = db.query(ErpExpenseDocument).filter(ErpExpenseDocument.s3_key == s3_key).first()
        if document:
            document.transaction_id = txn.transaction_id
            txn.ocr_confidence_json = _field_confidence_json(document)

        _history(db, txn.transaction_id, user.id, "employee", "created" if not submit else "submitted")

        duplicate = self._find_duplicate(
            db, vendor, amount, bill_date, txn.transaction_id, employee_id=txn.employee_id,
            bill_number=bill_number,
        )
        txn.duplicate_flag = 1 if duplicate else 0

        db.commit()
        txn = (
            db.query(ErpExpenseTransaction)
            .options(
                joinedload(ErpExpenseTransaction.documents).selectinload(ErpExpenseDocument.pages),
                joinedload(ErpExpenseTransaction.approval_history).joinedload(ErpExpenseApprovalHistory.actor),
                joinedload(ErpExpenseTransaction.region),
                joinedload(ErpExpenseTransaction.category).joinedload(ErpExpenseCategory.owning_department),
                joinedload(ErpExpenseTransaction.employee).joinedload(ErpAuthExpenseUsers.department),
                joinedload(ErpExpenseTransaction.vendor),
                selectinload(ErpExpenseTransaction.line_items),
            )
            .filter(ErpExpenseTransaction.transaction_id == txn.transaction_id)
            .one()
        )
        result = transaction_to_dict(txn, include_history=True, db=db)
        result["duplicate_warning"] = duplicate

        if submit:
            self._notify_finance_on_submit(db, txn)
        return result

    def update_draft(self, db: Session, user: CurrentUser, transaction_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        txn = self._owned_transaction(db, user, transaction_id)
        if txn.status not in ("draft", "disputed"):
            raise ValueError("Only draft or disputed claims can be edited")
        old_currency = (txn.currency or "").strip().upper()
        old_region_id = txn.region_id

        if "vendor" in updates and updates["vendor"]:
            vendor_obj = _resolve_vendor(db, updates["vendor"])
            txn.vendor_id = vendor_obj.vendor_id if vendor_obj else None
            txn.vendor_raw_text = None if vendor_obj else updates["vendor"].strip()
        for field, attr in (
            ("amount", "amount"),
            ("vat_amount", "vat_amount"),
            ("total_amount", "total_amount"),
            ("currency", "currency"),
            ("bill_date", "bill_date"),
            ("category_id", "category_id"),
            ("project_id", "project_cache_id"),
            ("type", "type"),
            ("op_number", "op_number"),
            ("bill_number", "bill_number"),
            ("remarks", "remarks"),
        ):
            if field in updates and updates[field] is not None:
                setattr(txn, attr, updates[field])
        if updates.get("region_code"):
            region = _resolve_region(db, updates["region_code"])
            if region.region_id != txn.region_id:
                require_bill_region_allowed(db, user.id, user.region_code, region.region_code)
            txn.region_id = region.region_id
            txn.region = region
        if updates.get("line_items") is not None:
            # An empty list turns the claim back into a single-amount bill (amount/total as sent).
            _replace_line_items(db, txn, updates["line_items"])
        rate_basis_changed = (
            (txn.currency or "").strip().upper() != old_currency or txn.region_id != old_region_id
        )
        if txn.status == "disputed" and not rate_basis_changed:
            # A disputed bill keeps the rate locked at its first submit; only amounts are re-converted.
            _fill_base_amounts(txn)
        else:
            _stamp_exchange_rate(txn, required=False)
        _history(db, txn.transaction_id, user.id, "employee", "edited")
        db.commit()
        return self.get_claim(db, user, transaction_id)

    def submit_claim(self, db: Session, user: CurrentUser, transaction_id: int) -> dict[str, Any]:
        txn = self._owned_transaction(db, user, transaction_id)
        if txn.status not in ("draft",):
            raise ValueError("Only draft claims can be submitted")
        # A draft is deliberately allowed to be incomplete while saved (see update_draft) -- but
        # actually submitting for approval needs these filled in. Checked here, not just client
        # side, so an incomplete draft can never reach Finance regardless of which UI path (or a
        # future API consumer) triggers the submit.
        vendor_present = bool(txn.vendor_id or (txn.vendor_raw_text and txn.vendor_raw_text.strip()))
        missing = []
        if not vendor_present:
            missing.append("vendor")
        if not txn.currency:
            missing.append("currency")
        if not txn.bill_date:
            missing.append("bill date")
        if not txn.bill_number:
            missing.append("bill number")
        if not txn.total_amount:
            missing.append("total amount")
        if not txn.amount:
            missing.append("amount")
        if missing:
            raise ValueError(f"Finish these fields before submitting: {', '.join(missing)}")
        _stamp_exchange_rate(txn, required=True)
        if (txn.type or "").strip().lower() == "petty_cash":
            self._require_petty_cash_limit(db, user, txn)
        self._require_unique_submitted_bill_number(db, txn.bill_number, txn.transaction_id)
        txn.status = "submitted"
        txn.submitted_on = datetime.utcnow()
        # Re-check for duplicates at submission time — draft edits can change vendor/amount/date after the initial check, making it stale.
        duplicate = self._find_duplicate(
            db, txn.vendor.vendor_name if txn.vendor else None, txn.amount, txn.bill_date, txn.transaction_id,
            employee_id=txn.employee_id, bill_number=txn.bill_number,
        )
        txn.duplicate_flag = 1 if duplicate else 0
        _history(db, txn.transaction_id, user.id, "employee", "submitted")
        db.commit()
        self._notify_finance_on_submit(db, txn)
        return self.get_claim(db, user, transaction_id)

    def list_mine(
        self,
        db: Session,
        user: CurrentUser,
        *,
        limit: int = 6,
        offset: int = 0,
        status: Optional[str] = None,
        region_code: Optional[str] = None,
    ) -> dict[str, Any]:
        q = (
            db.query(ErpExpenseTransaction)
            .filter(ErpExpenseTransaction.employee_id == user.id)
        )
        if status:
            q = q.filter(ErpExpenseTransaction.status == status)
        if region_code and region_code.strip():
            region_ids = [
                r.region_id
                for r in db.query(ErpExpenseRegionConfig.region_id).filter(
                    ErpExpenseRegionConfig.region_code == region_code.strip().upper()
                )
            ]
            q = q.filter(ErpExpenseTransaction.region_id.in_(region_ids or [-1]))
        total = q.count()
        txns = (
            q.options(
                joinedload(ErpExpenseTransaction.documents),
                joinedload(ErpExpenseTransaction.region),
                joinedload(ErpExpenseTransaction.category).joinedload(ErpExpenseCategory.owning_department),
                joinedload(ErpExpenseTransaction.employee).joinedload(ErpAuthExpenseUsers.department),
                joinedload(ErpExpenseTransaction.vendor),
                # Line categories feed the cross-department stage sequence; without this each
                # line lazy-loads its category per row.
                selectinload(ErpExpenseTransaction.line_items)
                .joinedload(ErpExpenseLineItem.category)
                .joinedload(ErpExpenseCategory.owning_department),
            )
            .order_by(ErpExpenseTransaction.created_on.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        from services.approval_service import approver_lookup_cache

        with approver_lookup_cache(db):
            items = [transaction_to_dict(t, db=db) for t in txns]
        return {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def get_claim(self, db: Session, user: CurrentUser, transaction_id: int) -> dict[str, Any]:
        txn = (
            db.query(ErpExpenseTransaction)
            .options(
                joinedload(ErpExpenseTransaction.documents).selectinload(ErpExpenseDocument.pages),
                joinedload(ErpExpenseTransaction.approval_history).joinedload(ErpExpenseApprovalHistory.actor),
                joinedload(ErpExpenseTransaction.region),
                joinedload(ErpExpenseTransaction.category).joinedload(ErpExpenseCategory.owning_department),
                joinedload(ErpExpenseTransaction.employee).joinedload(ErpAuthExpenseUsers.department),
                joinedload(ErpExpenseTransaction.vendor),
                selectinload(ErpExpenseTransaction.line_items),
            )
            .filter(ErpExpenseTransaction.transaction_id == transaction_id)
            .first()
        )
        if not txn:
            raise LookupError("Claim not found")
        if txn.employee_id != user.id and not user.is_approver:
            raise PermissionError("Not allowed")
        data = transaction_to_dict(txn, include_history=True, db=db)
        data["duplicate_warning"] = self._find_duplicate(
            db, txn.vendor.vendor_name if txn.vendor else None, txn.amount, txn.bill_date, txn.transaction_id,
            employee_id=txn.employee_id, bill_number=txn.bill_number,
        )
        return data

    def list_admin(
        self,
        db: Session,
        *,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        q = db.query(ErpExpenseTransaction).options(
            joinedload(ErpExpenseTransaction.documents),
            joinedload(ErpExpenseTransaction.region),
            joinedload(ErpExpenseTransaction.category).joinedload(ErpExpenseCategory.owning_department),
            joinedload(ErpExpenseTransaction.employee).joinedload(ErpAuthExpenseUsers.department),
            joinedload(ErpExpenseTransaction.vendor),
            selectinload(ErpExpenseTransaction.line_items)
            .joinedload(ErpExpenseLineItem.category)
            .joinedload(ErpExpenseCategory.owning_department),
        )
        if status:
            q = q.filter(ErpExpenseTransaction.status == status)
        if category_id:
            q = q.filter(ErpExpenseTransaction.category_id == category_id)
        if employee_id:
            q = q.filter(ErpExpenseTransaction.employee_id == employee_id)
        if project_id:
            q = q.filter(ErpExpenseTransaction.project_cache_id == project_id)
        txns = q.order_by(ErpExpenseTransaction.created_on.desc()).all()
        from services.approval_service import approver_lookup_cache

        with approver_lookup_cache(db):
            return [transaction_to_dict(t, db=db) for t in txns]

    def mark_paid(self, db: Session, user: CurrentUser, transaction_id: int, remarks: Optional[str]) -> dict[str, Any]:
        """Old one-click "mark paid" (web-admin). Records a bank transfer dated today; the
        remarks double as the reference. New clients use payment_service.record_payment."""
        from services.payment_service import payment_service

        payment_service.record_payment(
            db, user, transaction_id,
            payment_method="bank_transfer",
            payment_reference=(remarks or "").strip() or f"CLAIM-{transaction_id}",
            payment_date=None,
            remarks=remarks,
        )
        return self.get_claim(db, user, transaction_id)

    def recent_activity(self, db: Session, limit: int = 50) -> list[dict[str, Any]]:
        """Newest-first feed of workflow events (submit, approve, dispute, reject, paid, ...)
        across all claims -- backs the web dashboard's activity panel. Draft/internal
        bookkeeping (created, edited, vendor_resolved) is omitted."""
        from services.approval_service import INTERNAL_HISTORY_ACTIONS

        rows = (
            db.query(ErpExpenseApprovalHistory)
            .options(
                joinedload(ErpExpenseApprovalHistory.transaction).joinedload(ErpExpenseTransaction.vendor),
                joinedload(ErpExpenseApprovalHistory.transaction).joinedload(ErpExpenseTransaction.employee),
            )
            .filter(~ErpExpenseApprovalHistory.action.in_(INTERNAL_HISTORY_ACTIONS))
            .order_by(ErpExpenseApprovalHistory.acted_on.desc())
            .limit(limit)
            .all()
        )
        actor_ids = {r.actor_id for r in rows}
        actors = {
            u.user_id: u.display_name
            for u in db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id.in_(actor_ids)).all()
        } if actor_ids else {}
        result = []
        for r in rows:
            txn = r.transaction
            result.append({
                "id": r.approval_history_id,
                "transaction_id": r.transaction_id,
                "stage": r.stage,
                "action": r.action,
                "comment": r.comment,
                "actor_id": r.actor_id,
                "actor_name": actors.get(r.actor_id),
                "employee_name": txn.employee.display_name if txn and txn.employee else None,
                "vendor_name": (txn.vendor.vendor_name if txn.vendor else txn.vendor_raw_text) if txn else None,
                "currency": txn.currency if txn else None,
                "total_amount": txn.total_amount if txn else None,
                "region_code": txn.region.region_code if txn and txn.region else None,
                "created_at": r.acted_on.isoformat() if r.acted_on else None,
            })
        return result

    def get_receipt(self, db: Session, receipt_id: int) -> ErpExpenseDocument:
        document = db.query(ErpExpenseDocument).filter(ErpExpenseDocument.document_id == receipt_id).first()
        if not document:
            raise LookupError("Receipt not found")
        return document

    def get_receipt_page(self, db: Session, receipt_id: int, page_no: int) -> ErpExpenseDocumentPage:
        page = (
            db.query(ErpExpenseDocumentPage)
            .filter(ErpExpenseDocumentPage.document_id == receipt_id, ErpExpenseDocumentPage.page_no == page_no)
            .first()
        )
        if not page:
            raise LookupError("Receipt page not found")
        return page

    def _get(self, db: Session, transaction_id: int) -> ErpExpenseTransaction:
        txn = db.query(ErpExpenseTransaction).filter(ErpExpenseTransaction.transaction_id == transaction_id).first()
        if not txn:
            raise LookupError("Claim not found")
        return txn

    def _owned_transaction(self, db: Session, user: CurrentUser, transaction_id: int) -> ErpExpenseTransaction:
        txn = self._get(db, transaction_id)
        if txn.employee_id != user.id and not user.is_approver:
            raise PermissionError("Not allowed")
        return txn

    def _notify_finance_on_submit(self, db: Session, txn: ErpExpenseTransaction) -> None:
        # Notify only the CURRENT stage's approver(s), not every approver-capable user — the chain is sequential.
        from services import approval_service, email_templates, notification_service

        approvers = approval_service.resolve_current_approvers(db, txn)
        vendor_name = txn.vendor.vendor_name if txn.vendor else (txn.vendor_raw_text or "unknown vendor")
        content = email_templates.submission_email(email_templates.build_context(txn))
        for approver in approvers:
            notification_service.send(
                db, approver, "submission", txn.transaction_id,
                f"New expense claim submitted ({vendor_name})", f"تم تقديم مطالبة نفقات جديدة ({vendor_name})",
                f"Claim {txn.transaction_id} for {bill_and_base_text(txn)} is awaiting your review.",
                f"المطالبة رقم {txn.transaction_id} بمبلغ {bill_and_base_text(txn)} في انتظار مراجعتك.",
                html_body_en=content.html,
            )

    def _notify_employee(self, db: Session, txn: ErpExpenseTransaction, action: str, remarks: Optional[str]) -> None:
        from services import email_templates, notification_service

        employee = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == txn.employee_id).first()
        vendor_name = txn.vendor.vendor_name if txn.vendor else (txn.vendor_raw_text or "unknown vendor")
        action_ar = {"paid": "دفع"}.get(action, action)  # only "paid" is used via this path today
        html = None
        body_en = f"Your claim {txn.transaction_id} was {action}. Remarks: {remarks or '-'}"
        body_ar = f"تم {action_ar} مطالبتك رقم {txn.transaction_id}. ملاحظات: {remarks or '-'}"
        if action == "paid":
            html = email_templates.paid_email(email_templates.build_context(txn, comment=remarks)).html
            payment = txn.payment
            if payment is not None:
                paid = f"{payment.currency} {payment.amount:,.2f}"
                day = payment.payment_date.strftime("%d %b %Y")
                body_en = (
                    f"Your claim {txn.transaction_id} was paid: {paid} on {day}, "
                    f"reference {payment.payment_reference}."
                )
                body_ar = (
                    f"تم دفع مطالبتك رقم {txn.transaction_id}: {paid} بتاريخ {day}، "
                    f"المرجع {payment.payment_reference}."
                )
        notification_service.send(
            db, employee, action, txn.transaction_id,
            f"Expense claim {action}: {vendor_name}", f"مطالبة النفقات: {action_ar} ({vendor_name})",
            body_en, body_ar,
            html_body_en=html,
        )


transaction_service = TransactionService()
