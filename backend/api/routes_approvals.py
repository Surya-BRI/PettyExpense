from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import CurrentUser, require_approver
from database.models import get_db
from services import approval_service

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class DecisionRequest(BaseModel):
    comment: Optional[str] = None


class BulkApproveRequest(BaseModel):
    transaction_ids: list[int]


@router.get("/queue")
def queue(
    stage: str,
    user: CurrentUser = Depends(require_approver),
    db: Session = Depends(get_db),
):
    return approval_service.list_queue(db, user, stage)


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int,
    user: CurrentUser = Depends(require_approver),
    db: Session = Depends(get_db),
):
    from services.transaction_service import transaction_service

    try:
        return transaction_service.get_claim(db, user, transaction_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/{transaction_id}/approve")
def approve(
    transaction_id: int,
    body: DecisionRequest,
    user: CurrentUser = Depends(require_approver),
    db: Session = Depends(get_db),
):
    try:
        return approval_service.advance(db, user, transaction_id, "approve", body.comment)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{transaction_id}/dispute")
def dispute(
    transaction_id: int,
    body: DecisionRequest,
    user: CurrentUser = Depends(require_approver),
    db: Session = Depends(get_db),
):
    try:
        return approval_service.advance(db, user, transaction_id, "dispute", body.comment)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{transaction_id}/reject")
def reject(
    transaction_id: int,
    body: DecisionRequest,
    user: CurrentUser = Depends(require_approver),
    db: Session = Depends(get_db),
):
    try:
        return approval_service.advance(db, user, transaction_id, "reject", body.comment)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bulk-approve")
def bulk_approve(
    body: BulkApproveRequest,
    user: CurrentUser = Depends(require_approver),
    db: Session = Depends(get_db),
):
    return approval_service.bulk_approve(db, user, body.transaction_ids)
