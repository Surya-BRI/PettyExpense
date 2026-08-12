from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import CurrentUser, require_admin
from database.models import get_db
from services.config_service import config_service

router = APIRouter(prefix="/api/admin/config", tags=["config"])


class DepartmentRequest(BaseModel):
    name: str


class RegionRequest(BaseModel):
    region_code: str
    region_name: str
    allocation_model: str = "petty_cash"
    approval_matrix: dict[str, Any]
    petty_cash_hard_limit_enabled: bool = False
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None


class RegionUpdateRequest(BaseModel):
    region_name: Optional[str] = None
    allocation_model: Optional[str] = None
    approval_matrix: Optional[dict[str, Any]] = None
    petty_cash_hard_limit_enabled: Optional[bool] = None
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None


class CategoryRequest(BaseModel):
    name: str
    name_ar: Optional[str] = None
    owning_department_id: Optional[int] = None


class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    owning_department_id: Optional[int] = None
    is_active: Optional[bool] = None


class VendorRequest(BaseModel):
    name: str
    trn_number: Optional[str] = None
    source: str = "manual"


class HodAssignmentRequest(BaseModel):
    user_id: int
    department_id: int


class DelegationRequest(BaseModel):
    approver_id: int
    backup_id: int
    start_date: str
    end_date: str


# -- Departments --
@router.get("/departments")
def list_departments(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.list_departments(db)


@router.post("/departments")
def create_department(body: DepartmentRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.create_department(db, body.name)


# -- Regions --
@router.get("/regions")
def list_regions(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.list_regions(db)


@router.post("/regions")
def create_region(body: RegionRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.create_region(db, body.model_dump())


@router.put("/regions/{region_id}")
def update_region(
    region_id: int, body: RegionUpdateRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    try:
        return config_service.update_region(db, region_id, body.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# -- Categories --
@router.get("/categories")
def list_categories(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.list_categories(db)


@router.post("/categories")
def create_category(body: CategoryRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        return config_service.create_category(db, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/categories/{category_id}")
def update_category(
    category_id: int, body: CategoryUpdateRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    try:
        return config_service.update_category(db, category_id, body.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        config_service.delete_category(db, category_id)
        return {"ok": True}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# -- Vendors --
@router.get("/vendors")
def list_vendors(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.list_vendors(db)


@router.post("/vendors")
def create_vendor(body: VendorRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.create_vendor(db, body.model_dump())


@router.delete("/vendors/{vendor_id}")
def delete_vendor(vendor_id: int, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        config_service.delete_vendor(db, vendor_id)
        return {"ok": True}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# -- HOD assignments (Phase 2) --
@router.get("/hod-assignments")
def list_hod_assignments(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.list_hod_assignments(db)


@router.post("/hod-assignments")
def create_hod_assignment(
    body: HodAssignmentRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    return config_service.create_hod_assignment(db, body.user_id, body.department_id)


# -- Approver delegations (Phase 2) --
@router.get("/delegations")
def list_delegations(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.list_delegations(db)


@router.post("/delegations")
def create_delegation(body: DelegationRequest, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return config_service.create_delegation(db, body.approver_id, body.backup_id, body.start_date, body.end_date)
