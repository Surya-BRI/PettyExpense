"""Seed one dev ERP user per region, for testing the region-driven logo/branding
(see ERP_SUBSIDIARY_TO_REGION_CODE and resolve_default_region_code in auth/security.py).

Unlike seed_dev_erp_users.py, this does NOT invent ErpMasterSubsidiary/ErpMasterRegion rows
-- those tables' full schema isn't known here and they're shared ERP reference data, so
making one up risks violating constraints we can't see. Instead this looks up a REAL
existing subsidiary/region row for each of UAE/KSA/OMAN and points a dev employee's
ErpMasterEmployee.regionId at it. A region prints as "not found" (and is skipped) if
ERP-Dev has no subsidiary matching that code yet.

Dev userIds start at 9010 to avoid colliding with seed_dev_erp_users.py (9001-9005).
Script is fully idempotent: re-running it is safe.

Usage:
    cd backend
    python -m scripts.seed_dev_region_users
"""

from sqlalchemy import text

from auth.security import ERP_SUBSIDIARY_TO_REGION_CODE, hash_password
from database.models import SessionLocal

DEV_PASSWORD = "Test@1234"

# One subsidiary code to try per region we want a dev login for (first match wins when a
# region has more than one subsidiary, e.g. KSA).
REGION_DEV_USERS = [
    ("UAE", 9010, "dev_uae", "Dev", "UAE", "dev_uae@expense.local"),
    ("KSA", 9011, "dev_ksa", "Dev", "KSA", "dev_ksa@expense.local"),
    ("OMAN", 9012, "dev_oman", "Dev", "OMAN", "dev_oman@expense.local"),
]


def _find_region_id(db, region_code: str):
    codes = [c for c, r in ERP_SUBSIDIARY_TO_REGION_CODE.items() if r == region_code]
    for code in codes:
        row = db.execute(
            text(
                "SELECT TOP 1 r.regionId "
                "FROM ErpMasterSubsidiary s "
                "JOIN ErpMasterRegion r ON r.subsidiaryId = s.subsidiaryId "
                "WHERE s.subsidiaryCode = :code"
            ),
            {"code": code},
        ).first()
        if row:
            return row.regionId
    return None


def seed_dev_region_users() -> None:
    db = SessionLocal()
    pw_hash = hash_password(DEV_PASSWORD)
    try:
        print("Dev region users:")
        for region_code, user_id, user_name, first, last, email in REGION_DEV_USERS:
            region_id = _find_region_id(db, region_code)
            if region_id is None:
                print(f"  {user_name:<12} SKIPPED -- no ErpMasterSubsidiary/ErpMasterRegion row found for region {region_code}")
                continue

            existing_auth = db.execute(
                text("SELECT userId FROM ErpAuthUsers WHERE userId = :id"), {"id": user_id}
            ).first()
            if existing_auth:
                db.execute(
                    text("UPDATE ErpAuthUsers SET password = :pw WHERE userId = :id"),
                    {"pw": pw_hash, "id": user_id},
                )
            else:
                db.execute(
                    text(
                        "SET IDENTITY_INSERT ErpAuthUsers ON; "
                        "INSERT INTO ErpAuthUsers (userId, userName, password, isActive, isDeleted) "
                        "VALUES (:id, :uname, :pw, 1, 0); "
                        "SET IDENTITY_INSERT ErpAuthUsers OFF"
                    ),
                    {"id": user_id, "uname": user_name, "pw": pw_hash},
                )

            existing_emp = db.execute(
                text("SELECT employeeId FROM ErpMasterEmployee WHERE userId = :id"), {"id": user_id}
            ).first()
            if existing_emp:
                db.execute(
                    text(
                        "UPDATE ErpMasterEmployee "
                        "SET firstName=:f, lastName=:l, emailId=:e, isAllowLogin=1, regionId=:rid "
                        "WHERE userId=:id"
                    ),
                    {"f": first, "l": last, "e": email, "id": user_id, "rid": region_id},
                )
            else:
                db.execute(
                    text(
                        "SET IDENTITY_INSERT ErpMasterEmployee ON; "
                        "INSERT INTO ErpMasterEmployee "
                        "(employeeId, userId, firstName, lastName, emailId, isAllowLogin, isActive, isDeleted, regionId) "
                        "VALUES (:emp_id, :id, :f, :l, :e, 1, 1, 0, :rid); "
                        "SET IDENTITY_INSERT ErpMasterEmployee OFF"
                    ),
                    {"emp_id": user_id, "id": user_id, "f": first, "l": last, "e": email, "rid": region_id},
                )

            db.commit()
            print(f"  {user_name:<12} password={DEV_PASSWORD!r}  role=employee  region={region_code} (regionId={region_id})")
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    seed_dev_region_users()
