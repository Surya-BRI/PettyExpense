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
    # Required on approve at the company's journal stage (Professional Signs: Accounts).
    journal_type: Optional[str] = None  # EJV | EJVB
    journal_reference: Optional[str] = None


class BulkApproveRequest(BaseModel):
    transaction_ids: list[int]


@router.get("/history")
def history(
    limit: int = 100,
    user: CurrentUser = Depends(require_approver),
    db: Session = Depends(get_db),
):
    return approval_service.list_history(db, user, limit=limit)


@router.get("/queue")
def queue(
    stage: str,
    user: CurrentUser = Depends(require_approver),
    db: Session = Depends(get_db),
):
    return approval_service.list_queue(db, user, stage)


# -- My backup (an approver names who covers them while away). Declared before
# /{transaction_id} so "backup" isn't read as a claim id. --
class BackupRequest(BaseModel):
    backup_id: int
    start_date: str  # YYYY-MM-DD
    end_date: str


@router.get("/backup")
def my_backup(user: CurrentUser = Depends(require_approver), db: Session = Depends(get_db)):
    from services import delegation_service

    return {
        "backups": delegation_service.list_for(db, user.id),
        "candidates": delegation_service.candidates(db, user.id),
        "today": delegation_service.today(),
    }


@router.post("/backup")
def set_my_backup(body: BackupRequest, user: CurrentUser = Depends(require_approver), db: Session = Depends(get_db)):
    from services import delegation_service

    try:
        return delegation_service.create(db, user.id, body.backup_id, body.start_date, body.end_date)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/backup/{delegation_id}")
def remove_my_backup(delegation_id: int, user: CurrentUser = Depends(require_approver), db: Session = Depends(get_db)):
    from services import delegation_service

    try:
        delegation_service.remove(db, delegation_id, approver_id=user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


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
        return approval_service.advance(
            db, user, transaction_id, "approve", body.comment,
            journal_type=body.journal_type, journal_reference=body.journal_reference,
        )
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
