"""Site petty cash (Blue Rhine Contracting): see services/site_pca_service.py.

Pot:     the Accountant (or Admin) sets an employee's petty cash (one per employee, all sites); live at once.
Top-up:  the Accountant prepares it from approved bills -> Head of Accountant approves ->
         Finance Manager approves and records the cash withdrawal from the bank.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user, get_user_by_id
from database.models import get_db
from services.site_pca_service import site_pca_service

router = APIRouter(prefix="/api/site-pca", tags=["site-pca"])


class SetPotRequest(BaseModel):
    region_id: int
    employee_id: int
    amount: float  # the pot's amount from now on (not an increase)
    remarks: Optional[str] = None


class TopupRequest(BaseModel):
    transaction_ids: list[int]
    remarks: Optional[str] = None


class StepRequest(BaseModel):
    remarks: Optional[str] = None


class RejectRequest(BaseModel):
    comment: str


class PayRequest(BaseModel):
    payment_method: str = "bank_transfer"  # bank_transfer | cash | payroll | cheque
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


@router.get("/pots")
def pots(
    region_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _run(lambda: site_pca_service.pots(db, _orm_user(db, user), region_id, employee_id))


@router.get("/people")
def people(region_id: int = Query(...), user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(lambda: site_pca_service.people(db, _orm_user(db, user), region_id))


@router.post("/pots")
def set_pot(body: SetPotRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(
        lambda: site_pca_service.set_pot(
            db, _orm_user(db, user), region_id=body.region_id, employee_id=body.employee_id,
            amount=body.amount, remarks=body.remarks,
        )
    )


@router.get("/pots/{fund_id}/replenishable-bills")
def replenishable_bills(fund_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(lambda: site_pca_service.replenishable_bills(db, _orm_user(db, user), fund_id))


@router.post("/pots/{fund_id}/topups")
def request_topup(
    fund_id: int, body: TopupRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _run(
        lambda: site_pca_service.request_topup(db, _orm_user(db, user), fund_id, body.transaction_ids, body.remarks)
    )


@router.get("/requests")
def list_requests(
    region_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _run(lambda: site_pca_service.list_requests(db, _orm_user(db, user), region_id, status, kind))


@router.get("/requests/{request_id}")
def get_request(request_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    def load():
        orm = _orm_user(db, user)
        out = site_pca_service.request_to_dict(db, request_id)
        visible = {p["id"] for p in site_pca_service.pots(db, orm)}
        if out["fund_id"] not in visible:
            raise PermissionError("You can't see this request")
        return out

    return _run(load)


@router.post("/requests/{request_id}/approve")
def approve(request_id: int, body: StepRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(lambda: site_pca_service.approve(db, _orm_user(db, user), request_id, body.remarks))


@router.post("/requests/{request_id}/pay")
def pay(request_id: int, body: PayRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(
        lambda: site_pca_service.pay(
            db, _orm_user(db, user), request_id, payment_method=body.payment_method,
            payment_reference=body.payment_reference, payment_date=body.payment_date, remarks=body.remarks,
        )
    )


@router.post("/requests/{request_id}/reject")
def reject(request_id: int, body: RejectRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(lambda: site_pca_service.reject(db, _orm_user(db, user), request_id, body.comment))
