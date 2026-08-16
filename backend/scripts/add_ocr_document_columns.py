"""Add OCR VAT/total/currency columns to ErpExpenseDocument if they are missing.

SQLAlchemy create_all() does not ALTER existing tables, so ERP-Dev can lag the
model after ocrVatAmount / ocrTotalAmount / ocrCurrency were added.

Run from backend/: python scripts/add_ocr_document_columns.py
Idempotent — safe to re-run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from database.models import engine

TABLE = "ErpExpenseDocument"
COLUMNS = [
    ("ocrVatAmount", "FLOAT NULL"),
    ("ocrTotalAmount", "FLOAT NULL"),
    ("ocrCurrency", "NVARCHAR(8) NULL"),
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


with engine.connect() as conn:
    table_row = conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND TABLE_TYPE = 'BASE TABLE'"
        ),
        {"table": TABLE},
    ).fetchone()
    if not table_row:
        raise SystemExit(f"Table dbo.{TABLE} does not exist — start the backend once so create_all() can create it.")

    added: list[str] = []
    skipped: list[str] = []
    for name, ddl in COLUMNS:
        if column_exists(conn, TABLE, name):
            skipped.append(name)
            continue
        conn.execute(text(f"ALTER TABLE dbo.{TABLE} ADD {name} {ddl}"))
        added.append(name)
    conn.commit()

print(f"dbo.{TABLE}")
print("  added:  ", added or "(none)")
print("  already:", skipped or "(none)")
