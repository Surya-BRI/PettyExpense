from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user
from database.models import ErpExpenseTransaction, get_db
from services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _to_dict(row, txn: Optional[ErpExpenseTransaction]) -> dict:
    return {
        "id": row.notification_id,
        "transaction_id": row.transaction_id,
        "type": row.type,
        "status": row.status,
        "message": row.message,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        # current_stage lets the client route approver-facing notifications straight to the right approval queue.
        "current_stage": txn.current_stage if txn else None,
        "claim_status": txn.status if txn else None,
    }


@router.get("")
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = notification_service.list_for_user(db, user.id, limit=limit, offset=offset)
    txn_ids = [r.transaction_id for r in rows if r.transaction_id is not None]
    txns = {}
    if txn_ids:
        for t in db.query(ErpExpenseTransaction).filter(ErpExpenseTransaction.transaction_id.in_(txn_ids)).all():
            txns[t.transaction_id] = t
    return [_to_dict(r, txns.get(r.transaction_id)) for r in rows]


@router.get("/unread-count")
def unread_count(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"unread": notification_service.unread_count(db, user.id)}


@router.post("/{notification_id}/read")
def mark_read(
    notification_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        notification_service.mark_read(db, user.id, notification_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = notification_service.mark_all_read(db, user.id)
    return {"marked": count}
