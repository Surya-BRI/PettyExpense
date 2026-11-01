from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from auth.security import CurrentUser, get_current_user
from database.models import ErpExpenseCategory, ErpExpenseRegionConfig, ErpExpenseVendor, get_db
from services import approval_service
from services.currency import region_base_currency
from services.exchange_rate_service import ExchangeRateError, lookup_rate
from services.llm_vision_service import LlmVisionError
from services.storage import storage_service
from services.transaction_service import transaction_service

router = APIRouter(prefix="/api/claims", tags=["claims"])

categories_router = APIRouter(prefix="/api", tags=["reference"])


@categories_router.get("/categories")
def list_active_categories(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Read-only category picker for the bill-capture form (any authenticated user)."""
    categories = (
        db.query(ErpExpenseCategory)
        .options(joinedload(ErpExpenseCategory.owning_department))
        .filter(ErpExpenseCategory.is_active == 1)
        .all()
    )
    return [
        {
            "id": c.category_id,
            "name": c.category_name,
            "name_ar": c.category_name_ar,
            # Lines in a category owned by another department go to that department's HOD
            # and, for petty cash, come out of that department's fund.
            "owning_department_id": c.owning_department_id,
            "owning_department_name": c.owning_department.department_name if c.owning_department else None,
        }
        for c in categories
    ]


@categories_router.get("/vendors")
def list_active_vendors(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Read-only vendor list (any authenticated user) — used by the Accountant's unmatched-vendor
    resolve action to pick an existing vendor to link to. Admin-only vendor CRUD stays in
    routes_config.py; this is deliberately just a lookup, no create/edit/delete."""
    vendors = db.query(ErpExpenseVendor).filter(ErpExpenseVendor.is_active == 1).order_by(ErpExpenseVendor.vendor_name).all()
    return [{"id": v.vendor_id, "name": v.vendor_name} for v in vendors]


class LineItemIn(BaseModel):
    description: str
    quantity: Optional[float] = None
    amount: float  # line total as printed on the bill
    category_id: Optional[int] = None
    op_number: Optional[str] = None  # overrides the claim-level op_number for this line
    vat_percent: Optional[float] = None  # VAT % as printed on the bill for this line


class CreateClaimRequest(BaseModel):
    vendor: str
    amount: float
    vat_amount: float = 0.0
    total_amount: Optional[float] = None
    currency: str = "AED"
    exchange_rate: float = 1.0
    bill_date: Optional[str] = None
    category_id: int
    # Company the bill is charged to. Required to submit; a draft without one is saved under
    # the company the user is signed in under (never a hard-coded default).
    region_code: Optional[str] = None
    type: str = "reimbursement"  # petty_cash | reimbursement
    project_id: Optional[int] = None
    op_number: Optional[str] = None
    bill_number: str
    remarks: Optional[str] = None
    receipt_id: Optional[int] = None
    s3_key: Optional[str] = None
    submit: bool = True
    # "Multiple items" bills: when present, total = sum of line amounts and amount = total - vat_amount.
    line_items: list[LineItemIn] = []


class UpdateClaimRequest(BaseModel):
    vendor: Optional[str] = None
    amount: Optional[float] = None
    vat_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    bill_date: Optional[str] = None
    category_id: Optional[int] = None
    region_code: Optional[str] = None  # billed company; omitted here used to make PATCH drop it
    project_id: Optional[int] = None
    type: Optional[str] = None
    op_number: Optional[str] = None
    bill_number: Optional[str] = None
    remarks: Optional[str] = None
    line_items: Optional[list[LineItemIn]] = None


@router.post("/ocr")
async def ocr_receipt(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store + GPT read in one call (scripts / fallback). The app uses upload then analyze."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    content_type = file.content_type or "image/jpeg"
    try:
        return transaction_service.run_ocr(
            db, data, content_type, file.filename or "receipt.jpg", employee_id=user.id, region_code=user.region_code,
        )
    except LlmVisionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


MAX_RECEIPT_PAGES = 5


@router.post("/ocr/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    pages: list[UploadFile] = File(default=[]),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the photo to S3 only — returns immediately so the UI can leave Add receipt.
    `file` is page 1; `pages` are pages 2..N of the same bill (multi-page bills)."""
    if 1 + len(pages) > MAX_RECEIPT_PAGES:
        raise HTTPException(status_code=400, detail=f"A bill can have at most {MAX_RECEIPT_PAGES} pages")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    extra_pages = []
    for page in pages:
        page_data = await page.read()
        if not page_data:
            raise HTTPException(status_code=400, detail="Empty page")
        extra_pages.append((page_data, page.content_type or "image/jpeg", page.filename or "receipt.jpg"))
    content_type = file.content_type or "image/jpeg"
    return transaction_service.store_receipt(
        db, data, content_type, file.filename or "receipt.jpg", extra_pages=extra_pages,
    )


@router.post("/receipts/{receipt_id}/ocr")
def analyze_receipt(
    receipt_id: int,
    mode: str = "auto",  # auto | en | ar — language hint for the scan
    engine: str = "ai",  # ignored; every scan uses GPT
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Read an already-stored receipt with GPT."""
    try:
        return transaction_service.analyze_receipt(
            db, receipt_id, mode=mode, employee_id=user.id, region_code=user.region_code,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LlmVisionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("")
def create_claim(
    body: CreateClaimRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return transaction_service.create_claim(
            db,
            user,
            vendor=body.vendor,
            amount=body.amount,
            vat_amount=body.vat_amount,
            total_amount=body.total_amount,
            currency=body.currency,
            exchange_rate=body.exchange_rate,
            bill_date=body.bill_date,
            category_id=body.category_id,
            region_code=body.region_code,
            type=body.type,
            project_id=body.project_id,
            op_number=body.op_number,
            bill_number=body.bill_number,
            remarks=body.remarks,
            receipt_id=body.receipt_id,
            s3_key=body.s3_key,
            submit=body.submit,
            line_items=[li.model_dump() for li in body.line_items],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/exchange-rate")
def get_exchange_rate(
    from_currency: str = Query(..., alias="from"),
    to_currency: Optional[str] = Query(None, alias="to"),
    region_code: Optional[str] = None,
    date: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Published rate for 1 `from` in `to` (or in `region_code`'s base currency) on the scan
    date (today). Preview only — the rate is stamped on the claim at submit."""
    target = to_currency
    if not target and region_code:
        region = (
            db.query(ErpExpenseRegionConfig)
            .filter(ErpExpenseRegionConfig.region_code == region_code.strip().upper())
            .first()
        )
        if not region:
            raise HTTPException(status_code=404, detail="Unknown region_code")
        target = region_base_currency(region)
    if not target:
        raise HTTPException(status_code=400, detail="Pass `to` or `region_code`")
    try:
        return lookup_rate(from_currency, target, date)
    except ExchangeRateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mine")
def my_claims(
    limit: int = 6,
    offset: int = 0,
    status: str | None = None,
    region_code: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transaction_service.list_mine(
        db, user, limit=limit, offset=offset, status=status, region_code=region_code,
    )


@router.get("/receipts/{receipt_id}/image")
def receipt_image(
    receipt_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        receipt = transaction_service.get_receipt(db, receipt_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    data = storage_service.read_bytes(receipt.s3_key)
    if data is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=data, media_type=receipt.content_type or "image/jpeg")


@router.get("/receipts/{receipt_id}/pages/{page_no}/image")
def receipt_page_image(
    receipt_id: int,
    page_no: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        page = transaction_service.get_receipt_page(db, receipt_id, page_no)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    data = storage_service.read_bytes(page.s3_key)
    if data is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=data, media_type=page.content_type or "image/jpeg")


@router.get("/{claim_id}")
def get_claim(
    claim_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return transaction_service.get_claim(db, user, claim_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/{claim_id}")
def patch_claim(
    claim_id: int,
    body: UpdateClaimRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return transaction_service.update_draft(db, user, claim_id, body.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{claim_id}/submit")
def submit_claim(
    claim_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return transaction_service.submit_claim(db, user, claim_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{claim_id}/resubmit")
def resubmit_claim(
    claim_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """After a dispute: employee corrects the bill and resubmits, returning to the exact stage that disputed it (approval_service.resubmit_after_dispute)."""
    try:
        return approval_service.resubmit_after_dispute(db, user, claim_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
