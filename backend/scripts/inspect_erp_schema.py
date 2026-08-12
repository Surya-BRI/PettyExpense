"""Read-only inspection of ERP-Dev table/column naming conventions.
Run from backend/: python scripts/inspect_erp_schema.py [table1] [table2] ...
No writes, no DDL — SELECT against INFORMATION_SCHEMA only.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.models import engine
from sqlalchemy import text

with engine.connect() as conn:
    args = sys.argv[1:]
    if not args:
        rows = conn.execute(text(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE='BASE TABLE' AND "
            "(TABLE_NAME LIKE '%expense%' OR TABLE_NAME LIKE '%petty%' OR TABLE_NAME LIKE '%Vendor%' "
            "OR TABLE_NAME LIKE '%Netsuite%' OR TABLE_NAME LIKE '%Notification%' OR TABLE_NAME LIKE '%Auth%') "
            "ORDER BY TABLE_NAME"
        )).fetchall()
        print("Matching tables (expense/petty/vendor/netsuite/notification/auth):")
        for r in rows:
            print(f"  {r[0]}")
    else:
        for table in args:
            print(f"\n=== {table} ===")
            cols = conn.execute(text(
                "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH "
                "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=:t ORDER BY ORDINAL_POSITION"
            ), {"t": table}).fetchall()
            for c in cols:
                print(f"  {c[0]:40s} {c[1]:15s} nullable={c[2]:4s} len={c[3]}")
