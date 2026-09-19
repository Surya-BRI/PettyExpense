# Converts VARCHAR/TEXT columns that carry non-Latin text (vendor names, employee names,
# categories, comments, remarks, branding) to NVARCHAR/NTEXT so Arabic content round-trips
# instead of collapsing to "?" under the connection's ANSI codepage. Idempotent, safe to re-run.
# This only prevents FUTURE corruption -- rows already stored as "?" cannot be recovered by an ALTER.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from database.models import engine

TARGETS = [
    ("ErpAuthExpenseUsers", "displayName", "NVARCHAR(256) NOT NULL"),
    ("ErpExpenseCategory", "categoryName", "NVARCHAR(128) NOT NULL"),
    ("ErpExpenseCategory", "categoryNameAr", "NVARCHAR(128) NULL"),
    ("ErpExpenseVendor", "vendorName", "NVARCHAR(256) NOT NULL"),
    ("ErpExpenseTransaction", "remarks", "NVARCHAR(MAX) NULL"),
    ("ErpExpenseApprovalHistory", "comment", "NVARCHAR(MAX) NULL"),
    ("ErpExpenseRegionConfig", "companyName", "NVARCHAR(256) NULL"),
    ("ErpExpenseDocument", "ocrVendor", "NVARCHAR(256) NULL"),
    ("ErpExpenseDocument", "ocrRawJson", "NVARCHAR(MAX) NULL"),
]

# SQL Server refuses ALTER COLUMN while a non-clustered index depends on the column,
# so these need their index dropped first and recreated after with the same definition.
INDEXED_COLUMNS = {
    ("ErpExpenseVendor", "vendorName"): "ix_ErpExpenseVendor_vendorName",
}


def current_type(conn, table: str, column: str):
    row = conn.execute(
        text(
            "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND COLUMN_NAME = :column"
        ),
        {"table": table, "column": column},
    ).fetchone()
    return row[0] if row else None


altered: list[str] = []
skipped: list[str] = []
failed: list[str] = []

for table, column, ddl in TARGETS:
    with engine.connect() as conn:
        dtype = current_type(conn, table, column)
        if dtype is None:
            skipped.append(f"{table}.{column} (column not found)")
            continue
        if dtype.lower() in ("nvarchar", "ntext", "nchar"):
            skipped.append(f"{table}.{column} (already unicode)")
            continue
        index_name = INDEXED_COLUMNS.get((table, column))
        try:
            if index_name:
                conn.execute(text(f"DROP INDEX {index_name} ON dbo.{table}"))
            conn.execute(text(f"ALTER TABLE dbo.{table} ALTER COLUMN {column} {ddl}"))
            if index_name:
                conn.execute(text(f"CREATE INDEX {index_name} ON dbo.{table} ({column})"))
            conn.commit()
            altered.append(f"{table}.{column}")
        except Exception as exc:
            conn.rollback()
            failed.append(f"{table}.{column}: {exc}")

print("altered:", altered or "(none)")
print("skipped:", skipped or "(none)")
print("failed:", failed or "(none)")
print("Note: this only prevents future corruption. Rows already stored as '?' cannot be recovered.")
