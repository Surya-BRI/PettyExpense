from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import CurrentUser, require_role
from database.models import get_db
from services.payment_service import PAYMENT_METHOD_LABELS, payment_service

router = APIRouter(prefix="/api/payments", tags=["payments"])

require_payer = require_role("finance_manager")


class PaymentRequest(BaseModel):
    transaction_id: int
    payment_method: str  # bank_transfer | cash | payroll | cheque
    payment_reference: str
    payment_date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    remarks: Optional[str] = None


class BatchPaymentRequest(BaseModel):
    transaction_ids: list[int]
    payment_method: str
    payment_reference: str
    payment_date: Optional[str] = None
    remarks: Optional[str] = None


def _errors(fn):
    try:
        return fn()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/methods")
def payment_methods(user: CurrentUser = Depends(require_payer)):
    return [{"code": code, "label": label} for code, label in PAYMENT_METHOD_LABELS.items()]


@router.get("")
def list_payments(
    status: str = Query("unpaid", pattern="^(unpaid|paid)$"),
    region_code: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_payer),
    db: Session = Depends(get_db),
):
    """Approved reimbursements waiting for payment (status=unpaid) or already paid."""
    return _errors(
        lambda: payment_service.list_claims(
            db, user, status=status, region_code=region_code, limit=limit, offset=offset
        )
    )


@router.post("")
def record_payment(body: PaymentRequest, user: CurrentUser = Depends(require_payer), db: Session = Depends(get_db)):
    return _errors(
        lambda: payment_service.record_payment(
            db, user, body.transaction_id,
            payment_method=body.payment_method,
            payment_reference=body.payment_reference,
            payment_date=body.payment_date,
            remarks=body.remarks,
        )
    )


@router.post("/batch")
def record_batch(body: BatchPaymentRequest, user: CurrentUser = Depends(require_payer), db: Session = Depends(get_db)):
    """One transfer covering several claims: each gets the same method, reference and date."""
    return _errors(
        lambda: payment_service.record_batch(
            db, user, body.transaction_ids,
            payment_method=body.payment_method,
            payment_reference=body.payment_reference,
            payment_date=body.payment_date,
            remarks=body.remarks,
        )
    )
