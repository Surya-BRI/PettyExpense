"""SLA breach detection — Phase 2 data model only. No scheduler wiring here;
that lands in Phase 5 (notifications) / Phase 9 (hardening) once there's a real
job runner and a notifications backend to push breaches to."""
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from database.models import ErpExpenseTransaction


def check_overdue_stages(db: Session) -> list[dict[str, Any]]:
    now = datetime.utcnow()
    overdue = (
        db.query(ErpExpenseTransaction)
        .filter(
            ErpExpenseTransaction.stage_due_at.isnot(None),
            ErpExpenseTransaction.stage_due_at < now,
            ErpExpenseTransaction.status.in_(("submitted", "disputed")),
        )
        .all()
    )
    return [
        {
            "transaction_id": t.transaction_id,
            "stage": t.current_stage,
            "stage_due_at": t.stage_due_at.isoformat() if t.stage_due_at else None,
            "hours_overdue": round((now - t.stage_due_at).total_seconds() / 3600, 1) if t.stage_due_at else None,
        }
        for t in overdue
    ]
