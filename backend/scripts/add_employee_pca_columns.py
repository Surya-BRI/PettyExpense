# Adds the employee-advance (Professional Signs PCA) columns if missing, and backfills
# kind='topup' on existing top-up rows. create_all() never ALTERs existing tables. Idempotent.
# Run: python scripts/add_employee_pca_columns.py  (also run from the startup seed)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from database.models import engine

COLUMNS = {
    "ErpExpenseFundTopupRequest": [
        ("kind", "NVARCHAR(16) NULL"),
        ("hodApprovedBy", "INT NULL"),
        ("hodApprovedOn", "DATETIME NULL"),
        ("paymentSource", "NVARCHAR(32) NULL"),
        ("paidBy", "INT NULL"),
    ],
    "ErpExpensePettyCashFund": [
        ("opNumber", "NVARCHAR(128) NULL"),
        ("opName", "NVARCHAR(256) NULL"),
    ],
    "ErpExpenseTransaction": [
        ("journalType", "NVARCHAR(8) NULL"),
        ("journalReference", "NVARCHAR(64) NULL"),
    ],
    # Professional Signs: which PDF section 7 process paid the bill (bank | accounts_petty_cash).
    "ErpExpensePaymentRecord": [
        ("paymentSource", "NVARCHAR(32) NULL"),
    ],
}


def _exists(conn, table: str, column: str | None = None) -> bool:
    if column is None:
        sql = (
            "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND TABLE_TYPE = 'BASE TABLE'"
        )
        return conn.execute(text(sql), {"table": table}).fetchone() is not None
    sql = (
        "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND COLUMN_NAME = :column"
    )
    return conn.execute(text(sql), {"table": table, "column": column}).fetchone() is not None


def ensure_employee_pca_columns() -> None:
    with engine.connect() as conn:
        for table, columns in COLUMNS.items():
            if not _exists(conn, table):
                continue
            for name, ddl in columns:
                if not _exists(conn, table, name):
                    conn.execute(text(f"ALTER TABLE dbo.{table} ADD {name} {ddl}"))
        conn.commit()
        if _exists(conn, "ErpExpenseFundTopupRequest", "kind"):
            conn.execute(text("UPDATE dbo.ErpExpenseFundTopupRequest SET kind = 'topup' WHERE kind IS NULL"))
            conn.commit()


if __name__ == "__main__":
    ensure_employee_pca_columns()
    print("Employee PCA columns ensured")
