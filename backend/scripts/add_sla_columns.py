# Adds the approval SLA clock columns on ErpExpenseTransaction if missing (stageEnteredAt,
# slaState). create_all() never ALTERs existing tables. Idempotent; also run at startup by
# seed_reference_data.
#
# When the columns are first added, bills already waiting on an approver get a start time
# (from their due time) and bills ALREADY past their time limit are marked escalated, so the
# first SLA run doesn't email a backlog of old bills at once. They still show on the Aging
# report. Run with --alert-backlog to let the SLA job alert them instead.
#
# Run: python scripts/add_sla_columns.py [--alert-backlog]
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from database.models import engine

TABLE = "ErpExpenseTransaction"
COLUMNS = [
    ("stageEnteredAt", "DATETIME NULL"),
    ("slaState", "INT NOT NULL CONSTRAINT DF_ErpExpenseTransaction_slaState DEFAULT 0"),
]


def _column_exists(conn, column: str) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND COLUMN_NAME = :column"
        ),
        {"table": TABLE, "column": column},
    ).fetchone()
    return row is not None


def ensure_sla_columns(alert_backlog: bool = False) -> bool:
    """Returns True when the columns were added now (and open bills backfilled)."""
    if engine.dialect.name != "mssql":
        return False  # local SQLite dev DBs are rebuilt by create_all
    added = False
    with engine.connect() as conn:
        for name, ddl in COLUMNS:
            if _column_exists(conn, name):
                continue
            conn.execute(text(f"ALTER TABLE dbo.{TABLE} ADD {name} {ddl}"))
            added = True
        conn.commit()
    if added:
        _backfill(alert_backlog)
    return added


def _backfill(alert_backlog: bool) -> None:
    from database.models import ErpExpenseRegionConfig, SessionLocal
    from services.sla_service import SLA_ESCALATED, recalculate_due_times

    db = SessionLocal()
    try:
        region_ids = [r.region_id for r in db.query(ErpExpenseRegionConfig.region_id).all()]
        for region_id in region_ids:
            recalculate_due_times(db, region_id)
        if not alert_backlog:
            from database.models import ErpExpenseTransaction

            quiet = (
                db.query(ErpExpenseTransaction)
                .filter(
                    ErpExpenseTransaction.status == "submitted",
                    ErpExpenseTransaction.stage_due_at.isnot(None),
                    ErpExpenseTransaction.stage_due_at <= datetime.utcnow(),
                )
                .update({ErpExpenseTransaction.sla_state: SLA_ESCALATED}, synchronize_session=False)
            )
            db.commit()
            print(f"{quiet} already-overdue bill(s) marked escalated without alerts")
    finally:
        db.close()


if __name__ == "__main__":
    print("added" if ensure_sla_columns("--alert-backlog" in sys.argv) else "already present")
