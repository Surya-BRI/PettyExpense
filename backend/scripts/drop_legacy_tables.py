"""One-time manual cleanup: drop the pre-Phase-1 legacy tables on ERP-Dev.
Run from backend/: python scripts/drop_legacy_tables.py
Only run this AFTER confirming the new ErpExpense*/ErpAuthExpenseUsers schema works end-to-end.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.models import engine
from sqlalchemy import text

LEGACY_TABLES = ["expense_claim_history", "expense_receipts", "expense_claims", "expense_app_users"]

with engine.connect() as conn:
    for table in LEGACY_TABLES:
        conn.execute(text(f"IF OBJECT_ID('dbo.{table}', 'U') IS NOT NULL DROP TABLE dbo.{table}"))
    conn.commit()
    print("Dropped (if present):", LEGACY_TABLES)
