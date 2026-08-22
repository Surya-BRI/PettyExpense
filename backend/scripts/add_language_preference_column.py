# Adds languagePreference to ErpAuthExpenseUsers if missing (create_all() never ALTERs existing tables). Run: python scripts/add_language_preference_column.py — idempotent, safe to re-run.
# Equivalent raw SQL if you'd rather run it yourself: ALTER TABLE dbo.ErpAuthExpenseUsers ADD languagePreference NVARCHAR(8) NOT NULL DEFAULT 'en';
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from database.models import engine

TABLE = "ErpAuthExpenseUsers"
COLUMNS = [
    ("languagePreference", "NVARCHAR(8) NOT NULL DEFAULT 'en'"),
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
