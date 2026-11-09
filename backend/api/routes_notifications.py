from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user
from database.models import ErpExpenseTransaction, get_db
from services import approval_service, notification_service
from services.department_split import stage_base

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Types that originally pointed the recipient at an approval action (as opposed to 'approval' /
# 'rejection' / 'dispute' / 'paid', which always just inform the employee about their own claim).
_APPROVER_FACING_TYPES = {"submission", "approval_pending", "resubmit"}


def _type_ids(type_: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """(topup_id, fund_id) carried in a petty-cash notification type, else (None, None):
    'topup_<step>_<topupId>', 'pca_<advance|topup>_<step>_<topupId>' -> topup id;
    'fund_low_<fundId>_<cycle>', 'pca_reminder_<fundId>_<cycle>' -> fund id."""
    parts = (type_ or "").split("_")
    try:
        if type_ and (type_.startswith("fund_low_") or type_.startswith("pca_reminder_")):
            return None, int(parts[-2])
        if type_ and (type_.startswith("topup_") or type_.startswith("pca_")):
            return int(parts[-1]), None
    except (ValueError, IndexError):
        pass
    return None, None


def _regions_for(db: Session, rows, txns: dict) -> dict[int, Optional[str]]:
    """notification id -> company code it is about (the claim's, or the top-up's / fund's),
    so the app can switch to that company before opening it. Two queries for the whole page."""
    from database.models import ErpExpenseFundTopupRequest, ErpExpensePettyCashFund, ErpExpenseRegionConfig

    topup_ids, fund_ids = set(), set()
    for r in rows:
        t, f = _type_ids(r.type)
        if t:
            topup_ids.add(t)
        if f:
            fund_ids.add(f)
    topup_fund = (
        dict(
            db.query(ErpExpenseFundTopupRequest.topup_id, ErpExpenseFundTopupRequest.fund_id)
            .filter(ErpExpenseFundTopupRequest.topup_id.in_(topup_ids))
            .all()
        )
        if topup_ids
        else {}
    )
    all_funds = fund_ids | set(topup_fund.values())
    fund_region = (
        dict(
            db.query(ErpExpensePettyCashFund.fund_id, ErpExpenseRegionConfig.region_code)
            .join(ErpExpenseRegionConfig, ErpExpenseRegionConfig.region_id == ErpExpensePettyCashFund.region_id)
            .filter(ErpExpensePettyCashFund.fund_id.in_(all_funds))
            .all()
        )
        if all_funds
        else {}
    )
    out: dict[int, Optional[str]] = {}
    for r in rows:
        txn = txns.get(r.transaction_id)
        if txn is not None:
            out[r.notification_id] = txn.region.region_code if txn.region else None
            continue
        t, f = _type_ids(r.type)
        out[r.notification_id] = fund_region.get(f if f else topup_fund.get(t))
    return out


def _to_dict(row, txn: Optional[ErpExpenseTransaction], actionable: bool, region_code: Optional[str] = None) -> dict:
    return {
        "id": row.notification_id,
        "transaction_id": row.transaction_id,
        # Company the notification is about; the app switches to it before opening it.
        "region_code": region_code,
        "type": row.type,
        "status": row.status,
        "message": row.message,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "current_stage": stage_base(txn.current_stage) if txn else None,
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

    regions = _regions_for(db, rows, txns)
    result = []
    for r in rows:
        txn = txns.get(r.transaction_id)
        actionable = r.type in _APPROVER_FACING_TYPES and _is_actionable(txn)
        result.append(_to_dict(r, txn, actionable, regions.get(r.notification_id)))
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
