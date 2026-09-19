from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import CurrentUser, require_admin, require_role
from database.models import ErpAuthExpenseUsers, get_db
from services import notification_service
from services.transaction_service import transaction_service

router = APIRouter(prefix="/api/admin", tags=["admin"])

# mark-paid is the final post-approval step (only reachable once status == 'approved',
# i.e. finance_manager has already approved via /api/approvals). Phase 3 formalizes this
# into payment_records; for now it stays a single finance_manager/admin action here.
require_finance_manager = require_role("finance_manager")


class DecisionRequest(BaseModel):
    remarks: Optional[str] = None


class NotifyTestRequest(BaseModel):
    user_id: int
    channel: str  # email | in_app


@router.get("/claims")
def list_claims(
    status: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    user: CurrentUser = Depends(require_role("hod", "accountant", "finance_manager")),
    db: Session = Depends(get_db),
):
    return transaction_service.list_admin(
        db,
        status=status,
        category_id=category_id,
        employee_id=employee_id,
        project_id=project_id,
    )


@router.get("/claims/{claim_id}")
def get_claim(
    claim_id: int,
    user: CurrentUser = Depends(require_role("hod", "accountant", "finance_manager")),
    db: Session = Depends(get_db),
):
    try:
        return transaction_service.get_claim(db, user, claim_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/claims/{claim_id}/mark-paid")
def mark_paid(
    claim_id: int,
    body: DecisionRequest,
    user: CurrentUser = Depends(require_finance_manager),
    db: Session = Depends(get_db),
):
    try:
        return transaction_service.mark_paid(db, user, claim_id, body.remarks)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/notify/test")
def notify_test(
    body: NotifyTestRequest,
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if body.channel not in ("email", "in_app"):
        raise HTTPException(status_code=400, detail="channel must be 'email' or 'in_app'")
    target = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == body.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    sent = notification_service.send_test(
        db, target, body.channel,
        "Petty Expense — test notification",
        f"This is a test {body.channel} notification triggered by {user.display_name}.",
    )
    return {"sent": sent, "channel": body.channel, "to": target.email if body.channel == "email" else target.user_id}
