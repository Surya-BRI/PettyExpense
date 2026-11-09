"""Employee petty cash advances (Professional Signs): see services/employee_pca_service.py.

PCA amount: the employee's HOD (or Admin) sets it; live at once (a limit, not a payment).
Top-up:  employee (or HOD) raises with approved bills -> HOD approves -> Accounts Manager
         verifies -> Accounts Manager pays (cash withdrawal from bank, or direct payment).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user, get_user_by_id
from database.models import get_db
from services.employee_pca_service import employee_pca_service
from services.region_policy import PAYMENT_SOURCE_LABELS

router = APIRouter(prefix="/api/pca", tags=["pca"])


class SetAdvanceRequest(BaseModel):
    region_id: int
    employee_id: int
    op_number: Optional[str] = None  # ignored: one PCA per employee, for all their projects
    amount: float  # the employee's PCA from now on (not an increase)
    remarks: Optional[str] = None  # why this amount


class PcaTopupRequest(BaseModel):
    transaction_ids: list[int]
    remarks: Optional[str] = None


class StepRequest(BaseModel):
    remarks: Optional[str] = None


class PayRequest(BaseModel):
    payment_source: str  # bank | accounts_petty_cash
    payment_method: str  # bank_transfer | cash | payroll | cheque
    payment_reference: str
    payment_date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    remarks: Optional[str] = None


def _orm_user(db: Session, user: CurrentUser):
    row = get_user_by_id(db, user.id)
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return row


def _run(fn):
    try:
        return fn()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/payment-sources")
def payment_sources(user: CurrentUser = Depends(get_current_user)):
    return [{"code": code, "label": label} for code, label in PAYMENT_SOURCE_LABELS.items()]


@router.get("/advances")
def list_advances(
    region_id: Optional[int] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Employee advances with balances: an employee sees their own, an HOD their staff's,
    Accounts / Accounts Manager the companies they cover, Admin all."""
    return employee_pca_service.list_advances(db, _orm_user(db, user), region_id)


@router.get("/staff")
def staff(region_id: int = Query(...), user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Who this HOD (their department staff) or Admin (anyone in the company) can propose an
    advance for."""
    return _run(lambda: employee_pca_service.staff(db, _orm_user(db, user), region_id))


@router.get("/departments")
def departments(region_id: int = Query(...), user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Employees tab: departments with employee counts, how many have petty cash and the total
    limit (fast: no bill figures)."""
    return _run(lambda: employee_pca_service.departments(db, _orm_user(db, user), region_id))


@router.get("/departments/{department_id}/employees")
def department_employees(
    department_id: int,
    region_id: int = Query(...),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """One department's employees with their petty cash figures (department_id 0 = none)."""
    return _run(
        lambda: employee_pca_service.department_employees(db, _orm_user(db, user), region_id, department_id)
    )


@router.get("/summary")
def summary(
    region_id: int = Query(...),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report: one company's employee advances by department, and petty-cash spend by
    project with the employees whose bills named it. An HOD sees their own staff only."""
    return _run(lambda: employee_pca_service.summary(db, _orm_user(db, user), region_id))


@router.get("/requests")
def list_requests(
    status: Optional[str] = Query(None),
    kind: Optional[str] = Query(None, pattern="^(advance|topup)$"),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return employee_pca_service.list_requests(db, _orm_user(db, user), status=status, kind=kind)


@router.get("/requests/{request_id}")
def get_request(request_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    orm = _orm_user(db, user)

    def load():
        visible = {r["id"] for r in employee_pca_service.list_requests(db, orm)}
        if request_id not in visible:
            raise LookupError("Request not found")
        return employee_pca_service.request_to_dict(db, request_id)

    return _run(load)


@router.post("/advances")
def set_advance(body: SetAdvanceRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """The employee's HOD (or Admin) sets their PCA amount (the new total, not an increase).
    Live at once: a PCA is a limit, so there is no approval or payment step."""
    return _run(
        lambda: employee_pca_service.set_advance(
            db, _orm_user(db, user),
            region_id=body.region_id, employee_id=body.employee_id,
            amount=body.amount, remarks=body.remarks,
        )
    )


@router.get("/advances/{fund_id}/replenishable-bills")
def replenishable_bills(fund_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(lambda: employee_pca_service.replenishable_bills(db, _orm_user(db, user), fund_id))


@router.post("/advances/{fund_id}/topups")
def request_topup(
    fund_id: int, body: PcaTopupRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _run(
        lambda: employee_pca_service.request_topup(db, _orm_user(db, user), fund_id, body.transaction_ids, body.remarks)
    )


@router.post("/requests/{request_id}/hod-approve")
def hod_approve(request_id: int, body: StepRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(lambda: employee_pca_service.hod_approve(db, _orm_user(db, user), request_id, body.remarks))


@router.post("/requests/{request_id}/manager-approve")
def manager_approve(
    request_id: int, body: StepRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Accounts Manager: approves an advance, or verifies a top-up the HOD approved."""
    return _run(lambda: employee_pca_service.manager_approve(db, _orm_user(db, user), request_id, body.remarks))


@router.post("/requests/{request_id}/pay")
def pay(request_id: int, body: PayRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(
        lambda: employee_pca_service.pay(
            db, _orm_user(db, user), request_id,
            payment_source=body.payment_source,
            payment_method=body.payment_method,
            payment_reference=body.payment_reference,
            payment_date=body.payment_date,
            remarks=body.remarks,
        )
    )


@router.post("/requests/{request_id}/reject")
def reject(request_id: int, body: StepRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(lambda: employee_pca_service.reject(db, _orm_user(db, user), request_id, body.remarks))
