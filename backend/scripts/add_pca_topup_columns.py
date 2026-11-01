# Adds PCA replenishment columns on ErpExpenseFundTopupRequest if missing.
# create_all() never ALTERs existing tables. Idempotent.
# Run: python scripts/add_pca_topup_columns.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from database.models import engine

TABLE = "ErpExpenseFundTopupRequest"
COLUMNS = [
    ("verifiedBy", "INT NULL"),
    ("verifiedOn", "DATETIME NULL"),
    ("paymentMethod", "NVARCHAR(32) NULL"),
    ("paymentReference", "NVARCHAR(128) NULL"),
    ("paymentDate", "DATETIME NULL"),
]


def column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND COLUMN_NAME = :column"
        ),
        {"table": table, "column": column},
    ).fetchone()
    return row is not None


def ensure_pca_topup_columns() -> None:
    with engine.connect() as conn:
        table_row = conn.execute(
            text(
                "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND TABLE_TYPE = 'BASE TABLE'"
            ),
            {"table": TABLE},
        ).fetchone()
        if not table_row:
            return
        for name, ddl in COLUMNS:
            if column_exists(conn, TABLE, name):
                continue
            conn.execute(text(f"ALTER TABLE dbo.{TABLE} ADD {name} {ddl}"))
        conn.commit()


if __name__ == "__main__":
    ensure_pca_topup_columns()
    print(f"dbo.{TABLE} PCA columns ensured")
