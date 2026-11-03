"""Organisation APIs used from the mobile Admin / HOD / employee / Finance screens."""
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user, get_user_by_id, require_admin, require_role
from database.models import ErpExpenseRegionConfig, get_db
from services.config_service import config_service, region_to_dict
from services.fund_service import fund_service
from services.region_scope import user_covers
from services.storage import storage_service

router = APIRouter(tags=["org"])


class UserRegionsRequest(BaseModel):
    region_codes: list[str]


class FundCreateRequest(BaseModel):
    region_id: int
    owner_type: str
    opening_balance: float
    currency: str = "AED"
    department_id: Optional[int] = None
    employee_id: Optional[int] = None


class FundOpeningRequest(BaseModel):
    opening_balance: float


class FundCreditRequest(BaseModel):
    amount: float
    remarks: Optional[str] = None


class TopupCreateRequest(BaseModel):
    amount: Optional[float] = None
    remarks: Optional[str] = None
    transaction_ids: Optional[list[int]] = None


class TopupDecideRequest(BaseModel):
    remarks: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_date: Optional[str] = None


def _orm_user(db: Session, user: CurrentUser):
    row = get_user_by_id(db, user.id)
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return row


def _logo_public_url(region_code: str) -> str:
    return f"/api/branding/{region_code}/logo"


def _region_with_logo(r) -> dict:
    data = region_to_dict(r)
    if data.get("logo_url") and not str(data["logo_url"]).startswith("http"):
        data["logo_url"] = _logo_public_url(r.region_code)
    return data


@router.get("/api/regions")
def list_regions_for_app(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_region_with_logo(r) for r in db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.is_active == 1).all()]


@router.get("/api/branding/{region_code}")
def get_branding(region_code: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_code == region_code.upper()).first()
    if not r:
        raise HTTPException(status_code=404, detail="Region not found")
    return _region_with_logo(r)


@router.get("/api/branding/{region_code}/logo")
def get_region_logo(region_code: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_code == region_code.upper()).first()
    if not r or not r.logo_url:
        raise HTTPException(status_code=404, detail="Logo not found")
    if r.logo_url.startswith("http"):
        raise HTTPException(status_code=404, detail="Logo is an external URL")
    data = storage_service.read_bytes(r.logo_url)
    if not data:
        raise HTTPException(status_code=404, detail="Logo file missing")
    return Response(content=data, media_type="image/png")


@router.post("/api/admin/config/regions/{region_id}/logo")
def upload_region_logo(
    region_id: int,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    raw = file.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    ext = (file.filename or "logo.png").rsplit(".", 1)[-1].lower()
    if ext not in ("png", "jpg", "jpeg", "webp"):
        ext = "png"
    key = storage_service.save_bytes(raw, content_type=file.content_type or "image/png", ext=ext)
    try:
        updated = config_service.set_region_logo_key(db, region_id, key)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    code = updated["region_code"]
    updated["logo_url"] = _logo_public_url(code)
    return updated


@router.get("/api/admin/users")
def list_users(
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
    region_code: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return config_service.list_users(db, region_code=region_code, q=q, limit=limit, offset=offset)


@router.get("/api/admin/users/{user_id}")
def get_user(
    user_id: int,
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return config_service.get_user(db, user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/api/admin/users/{user_id}/regions")
def set_user_regions(
    user_id: int,
    body: UserRegionsRequest,
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return config_service.set_user_regions(db, user_id, body.region_codes, assigned_by=user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/api/admin/funds")
def admin_list_funds(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return fund_service.list_all(db)


@router.get("/api/admin/department-funds")
def admin_department_funds(
    region_id: int = Query(...),
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return fund_service.list_department_funds(db, region_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/admin/funds")
def admin_create_fund(
    body: FundCreateRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    try:
        return fund_service.create(db, **body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/api/admin/funds/{fund_id}")
def admin_update_fund(
    fund_id: int,
    body: FundOpeningRequest,
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return fund_service.update_opening(db, fund_id, body.opening_balance)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/admin/funds/{fund_id}/credit")
def admin_credit_fund(
    fund_id: int,
    body: FundCreditRequest,
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return fund_service.credit(db, _orm_user(db, user), fund_id, body.amount, body.remarks)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/api/funds/mine")
def my_funds(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return fund_service.list_mine(db, _orm_user(db, user))


@router.get("/api/funds/department-funds")
def covered_department_funds(
    region_id: int = Query(...),
    user: CurrentUser = Depends(require_role("finance_manager")),
    db: Session = Depends(get_db),
):
    """Read-only view of every department's pot in one company, for the Finance Manager
    (Admin's /api/admin/department-funds without the editing). Only companies they cover --
    the same rule that routes bills to their queue. Limits stay Admin's; top-ups stay
    HOD request -> Accounts verify -> FM approve (BRI_DEPARTMENT_PETTY_CASH.md section 7.5)."""
    if not user.is_admin and not user_covers(db, user.id, region_id):
        raise HTTPException(status_code=403, detail="You don't cover this company")
    try:
        return fund_service.list_department_funds(db, region_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/approvals/{transaction_id}/funds")
def bill_funds(
    transaction_id: int,
    user: CurrentUser = Depends(require_role("hod", "finance_manager")),
    db: Session = Depends(get_db),
):
    """The petty-cash pots a bill is paid from (one per paying department) with this bill's
    part in each. The Finance Manager sees every pot, to check the bill fits before final
    approval (PETTY_CASH_PHASED_PLAN.md: limit check at the FM stage); an HOD sees only
    their own department's pot. Empty for a reimbursement. Only for the bill's company."""
    try:
        region_id, rows = fund_service.bill_funds(db, transaction_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not user.is_admin and not user_covers(db, user.id, region_id):
        raise HTTPException(status_code=403, detail="You don't cover this company")
    if user.role == "hod":
        mine = fund_service.my_fund_ids(db, _orm_user(db, user))
        rows = [r for r in rows if r["fund"]["id"] in mine]
    return rows


@router.get("/api/funds/{fund_id}/replenishable-bills")
def replenishable_bills(
    fund_id: int,
    user: CurrentUser = Depends(require_role("hod", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return fund_service.list_replenishable_bills(db, _orm_user(db, user), fund_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/api/funds/{fund_id}/topups")
def create_topup(
    fund_id: int,
    body: TopupCreateRequest,
    user: CurrentUser = Depends(require_role("hod", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return fund_service.request_topup(
            db,
            _orm_user(db, user),
            fund_id,
            body.amount,
            body.remarks,
            body.transaction_ids,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/api/topups")
def list_topups(
    status: Optional[str] = Query(None),
    user: CurrentUser = Depends(require_role("hod", "accountant", "finance_manager", "admin")),
    db: Session = Depends(get_db),
):
    return fund_service.list_topups(db, status=status, user=_orm_user(db, user))


@router.post("/api/topups/{topup_id}/verify")
def verify_topup(
    topup_id: int,
    body: TopupDecideRequest,
    user: CurrentUser = Depends(require_role("accountant", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return fund_service.verify_topup(db, _orm_user(db, user), topup_id, body.remarks)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/topups/{topup_id}/return")
def return_topup(
    topup_id: int,
    body: TopupDecideRequest,
    user: CurrentUser = Depends(require_role("accountant", "admin")),
    db: Session = Depends(get_db),
):
    """Accounts sends a top-up back to the HOD with a reason; its bills are freed."""
    try:
        return fund_service.return_topup(db, _orm_user(db, user), topup_id, body.remarks)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/topups/{topup_id}/approve")
def approve_topup(
    topup_id: int,
    body: TopupDecideRequest,
    user: CurrentUser = Depends(require_role("finance_manager", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return fund_service.decide_topup(
            db,
            _orm_user(db, user),
            topup_id,
            True,
            body.remarks,
            payment_method=body.payment_method,
            payment_reference=body.payment_reference,
            payment_date=body.payment_date,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/topups/{topup_id}/reject")
def reject_topup(
    topup_id: int,
    body: TopupDecideRequest,
    user: CurrentUser = Depends(require_role("finance_manager", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return fund_service.decide_topup(db, _orm_user(db, user), topup_id, False, body.remarks)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
