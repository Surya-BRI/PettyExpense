# Adds the currency / region-approver / payment columns to existing ERP-Dev tables and
# backfills them. create_all() creates the new ErpExpensePaymentRecord table but never ALTERs
# existing ones. Idempotent; also runs on backend startup (seed_reference_data).
# Run: python scripts/add_currency_region_payment_schema.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from database.models import ErpExpenseRegionConfig, ErpExpenseTransaction, SessionLocal, engine
from services.currency import default_base_currency

COLUMNS = {
    "ErpExpenseRegionConfig": [("baseCurrency", "NVARCHAR(8) NULL")],
    "ErpAuthExpenseUsers": [("homeRegionId", "INT NULL")],
    "ErpExpenseTransaction": [
        ("baseCurrency", "NVARCHAR(8) NULL"),
        ("exchangeRateDate", "NVARCHAR(32) NULL"),
        ("exchangeRateSource", "NVARCHAR(32) NULL"),
        ("amountBase", "FLOAT NULL"),
        ("vatAmountBase", "FLOAT NULL"),
        ("totalAmountBase", "FLOAT NULL"),
    ],
}


def _column_exists(conn, table: str, column: str) -> bool:
    return conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND COLUMN_NAME = :column"
        ),
        {"table": table, "column": column},
    ).fetchone() is not None


def _table_exists(conn, table: str) -> bool:
    return conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :table AND TABLE_TYPE = 'BASE TABLE'"
        ),
        {"table": table},
    ).fetchone() is not None


def ensure_columns() -> None:
    if engine.dialect.name != "mssql":
        return
    with engine.connect() as conn:
        for table, columns in COLUMNS.items():
            if not _table_exists(conn, table):
                continue
            for name, ddl in columns:
                if not _column_exists(conn, table, name):
                    conn.execute(text(f"ALTER TABLE dbo.{table} ADD {name} {ddl}"))
        conn.commit()


def backfill(db) -> None:
    """Region base currency from the default map; base-currency amounts for bills saved
    before they were stored, from each bill's own stamped exchange rate."""
    regions = {}
    for region in db.query(ErpExpenseRegionConfig).all():
        if not region.base_currency:
            region.base_currency = default_base_currency(region.region_code)
        regions[region.region_id] = region.base_currency
    rows = db.query(ErpExpenseTransaction).filter(ErpExpenseTransaction.total_amount_base.is_(None)).all()
    for txn in rows:
        base = regions.get(txn.region_id) or "AED"
        bill = (txn.currency or "").strip().upper()
        if txn.status == "draft" and bill and bill != base and not txn.exchange_rate_date:
            # A foreign draft with no server rate yet is meant to have no converted figure
            # (update_draft leaves it empty); don't invent a 1:1 one on every restart.
            # Saving or submitting the draft fetches the real rate.
            continue
        rate = 1.0 if not bill or bill == base else float(txn.exchange_rate or 0) or 1.0
        total = txn.total_amount if txn.total_amount is not None else (txn.amount or 0) + (txn.vat_amount or 0)
        txn.base_currency = base
        txn.amount_base = round(float(txn.amount or 0) * rate, 2)
        txn.vat_amount_base = round(float(txn.vat_amount or 0) * rate, 2)
        txn.total_amount_base = round(float(total or 0) * rate, 2)
    db.commit()


def ensure_currency_region_payment_schema() -> None:
    ensure_columns()
    db = SessionLocal()
    try:
        backfill(db)
    finally:
        db.close()


if __name__ == "__main__":
    ensure_currency_region_payment_schema()
    print("Currency, home-region and payment columns ensured and backfilled")
