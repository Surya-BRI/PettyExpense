from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user
from database.models import ErpExpenseTransaction, get_db
from services import approval_service, notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Types that originally pointed the recipient at an approval action (as opposed to 'approval' /
# 'rejection' / 'dispute' / 'paid', which always just inform the employee about their own claim).
_APPROVER_FACING_TYPES = {"submission", "approval_pending", "resubmit"}


def _to_dict(row, txn: Optional[ErpExpenseTransaction], actionable: bool) -> dict:
    return {
        "id": row.notification_id,
        "transaction_id": row.transaction_id,
        "type": row.type,
        "status": row.status,
        "message": row.message,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "current_stage": txn.current_stage if txn else None,
        "claim_status": txn.status if txn else None,
        # Whether the recipient is STILL a genuine current approver for this claim right now --
        # current_stage/claim_status above reflect the transaction's live state, not the state at
        # send time, so an approver's own already-actioned notification (e.g. an HOD who approved
        # and moved the claim on to Accountant) would otherwise be mistaken for one still awaiting
        # their action. The client only deep-links into the approval-action screen when this is true.
        "actionable": actionable,
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

    actionable_by_txn: dict[int, bool] = {}

    def _is_actionable(txn: Optional[ErpExpenseTransaction]) -> bool:
        if txn is None:
            return False
        if txn.transaction_id not in actionable_by_txn:
            approvers = approval_service.resolve_current_approvers(db, txn)
            actionable_by_txn[txn.transaction_id] = user.id in {a.user_id for a in approvers}
        return actionable_by_txn[txn.transaction_id]

    result = []
    for r in rows:
        txn = txns.get(r.transaction_id)
        actionable = r.type in _APPROVER_FACING_TYPES and _is_actionable(txn)
        result.append(_to_dict(r, txn, actionable))
    return result


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
