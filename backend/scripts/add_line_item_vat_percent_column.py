"""One-time migration: add vatPercent column to ErpExpenseLineItem.

Run once against the target DB:
    cd backend
    python -m scripts.add_line_item_vat_percent_column
"""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from sqlalchemy import text
from database.models import SessionLocal

def main():
    db = SessionLocal()
    try:
        db.execute(text("""
            IF NOT EXISTS (
                SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME='ErpExpenseLineItem' AND COLUMN_NAME='vatPercent'
            )
            ALTER TABLE ErpExpenseLineItem ADD vatPercent FLOAT NULL
        """))
        db.commit()
        print("Done — vatPercent column added (or already existed).")
    finally:
        db.close()

if __name__ == "__main__":
    main()
