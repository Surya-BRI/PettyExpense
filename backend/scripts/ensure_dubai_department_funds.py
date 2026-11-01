"""Create missing Blue Rhine Industries (DUBAI) department pots.

Other companies already have Sales/IT/... limits. DUBAI was added later, so the
one-shot seeder skipped it. This fills any (region, department) pot that exists
in another company but not in DUBAI.

    cd backend
    python -m scripts.ensure_dubai_department_funds
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from database.models import ErpExpenseDepartment, ErpExpensePettyCashFund, ErpExpenseRegionConfig, SessionLocal
from services.fund_service import base_currency_for_region


def main() -> int:
    db = SessionLocal()
    try:
        dubai = (
            db.query(ErpExpenseRegionConfig)
            .filter(ErpExpenseRegionConfig.region_code == "DUBAI")
            .first()
        )
        if not dubai:
            print("DUBAI region row missing")
            return 1
        dubai.company_name = dubai.company_name or "Blue Rhine Industries"
        dubai.is_active = 1

        existing = {
            f.department_id
            for f in db.query(ErpExpensePettyCashFund).filter(
                ErpExpensePettyCashFund.region_id == dubai.region_id,
                ErpExpensePettyCashFund.owner_type == "department",
                ErpExpensePettyCashFund.is_active == 1,
            )
        }
        dept_ids = {
            f.department_id
            for f in db.query(ErpExpensePettyCashFund).filter(
                ErpExpensePettyCashFund.owner_type == "department",
                ErpExpensePettyCashFund.is_active == 1,
                ErpExpensePettyCashFund.department_id.isnot(None),
            )
        }
        currency = base_currency_for_region("DUBAI")
        created = 0
        for dept_id in sorted(dept_ids):
            if dept_id in existing:
                continue
            dept = db.query(ErpExpenseDepartment).filter(ErpExpenseDepartment.department_id == dept_id).first()
            db.add(
                ErpExpensePettyCashFund(
                    region_id=dubai.region_id,
                    owner_type="department",
                    department_id=dept_id,
                    currency=currency,
                    opening_balance=5000,
                    is_active=1,
                )
            )
            created += 1
            print(f"  + DUBAI {(dept.department_name if dept else dept_id)} limit=5000 {currency}")
        db.commit()
        print(f"Done. created={created} already={len(existing)}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
