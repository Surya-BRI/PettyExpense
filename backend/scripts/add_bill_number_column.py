"""One-time migration: add billNumber column to ErpExpenseTransaction.

Run once against the target DB:
    cd backend
    python -m scripts.add_bill_number_column
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
                WHERE TABLE_NAME='ErpExpenseTransaction' AND COLUMN_NAME='billNumber'
            )
            ALTER TABLE ErpExpenseTransaction ADD billNumber NVARCHAR(128) NULL
        """))
        db.commit()
        print("Done — billNumber column added (or already existed).")
    finally:
        db.close()

if __name__ == "__main__":
    main()
