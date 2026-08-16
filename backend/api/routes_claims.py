from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user
from database.models import ErpExpenseCategory, get_db
from services import approval_service
from services.storage import storage_service
from services.transaction_service import transaction_service

router = APIRouter(prefix="/api/claims", tags=["claims"])

categories_router = APIRouter(prefix="/api", tags=["reference"])


@categories_router.get("/categories")
def list_active_categories(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Read-only category picker for the bill-capture form (any authenticated user)."""
    categories = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.is_active == 1).all()
    return [{"id": c.category_id, "name": c.category_name, "name_ar": c.category_name_ar} for c in categories]


class CreateClaimRequest(BaseModel):
    vendor: str
    amount: float
    vat_amount: float = 0.0
    total_amount: Optional[float] = None
    currency: str = "AED"
    exchange_rate: float = 1.0
    bill_date: Optional[str] = None
    category_id: int
    region_code: str = "IN"
    type: str = "reimbursement"  # petty_cash | reimbursement
    project_id: Optional[int] = None
    op_number: Optional[str] = None
    remarks: Optional[str] = None
    receipt_id: Optional[int] = None
    s3_key: Optional[str] = None
    submit: bool = True


class UpdateClaimRequest(BaseModel):
    vendor: Optional[str] = None
    amount: Optional[float] = None
    vat_amount: Optional[float] = None
    total_amount: Optional[float] = None
    bill_date: Optional[str] = None
    category_id: Optional[int] = None
    project_id: Optional[int] = None
    op_number: Optional[str] = None
    remarks: Optional[str] = None


@router.post("/ocr")
async def ocr_receipt(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store + OCR in one call (scripts / fallback). The app uses upload then analyze."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    content_type = file.content_type or "image/jpeg"
    return transaction_service.run_ocr(db, data, content_type, file.filename or "receipt.jpg")


@router.post("/ocr/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the photo to S3 only — returns immediately so the UI can leave Add receipt."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    content_type = file.content_type or "image/jpeg"
    return transaction_service.store_receipt(db, data, content_type, file.filename or "receipt.jpg")


@router.post("/receipts/{receipt_id}/ocr")
def analyze_receipt(
    receipt_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run PaddleOCR on an already-stored receipt."""
    try:
        return transaction_service.analyze_receipt(db, receipt_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
            remarks=body.remarks,
            receipt_id=body.receipt_id,
            s3_key=body.s3_key,
            submit=body.submit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mine")
def my_claims(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return transaction_service.list_mine(db, user)


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
    """After a dispute: employee corrects the bill and resubmits. Returns to the exact
    stage that disputed it, per Phase 2's dispute-return design (approval_service.resubmit_after_dispute)."""
    try:
        return approval_service.resubmit_after_dispute(db, user, claim_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
