"""Seed dev ERP user accounts for local development and testing.

Inserts rows into the shared ERP tables that authenticate_user() reads
(ErpAuthUsers, ErpMasterEmployee, ErpAuthUserRoleMap, ErpMasterRole) so
the login flow works without a live ERP connection.

Dev userIds start at 9001 to avoid colliding with real ERP data.
Script is fully idempotent: re-running it is safe.

Usage:
    cd backend
    python -m scripts.seed_dev_erp_users
"""

from sqlalchemy import text

from auth.security import hash_password
from database.models import SessionLocal

# ── Dev account definitions ────────────────────────────────────────────────
# (userId, userName, firstName, lastName, email, erp_role_name)
# erp_role_name is the ErpMasterRole.roleName of a role whose roleId is one of the
# real production IDs authenticate_user maps via ERP_ROLE_ID_TO_APP_ROLE (security.py):
#   roleId 102060 "Department HOD" → hod | 102055 "Accountant" → accountant
#   roleId 1 "Admin" / 102068 "Sub Admin" → admin | None / anything else → employee
# Dev rows MUST use these exact roleIds -- a fake/invented roleId won't be in that map
# and the account will silently fall back to "employee".
#
# finance_manager has NO ERP role mapping (by design — it's set by hand on
# the local ErpAuthExpenseUsers row). We give dev_finance the "employee"
# ERP role and pre-seed its ErpAuthExpenseUsers row with role finance_manager
# so the auth flow picks it up on first login.

DEV_PASSWORD = "Test@1234"

DEV_USERS = [
    (9001, "dev_employee",   "Dev",   "Employee",  "dev_employee@expense.local",   None),
    (9002, "dev_hod",        "Dev",   "HOD",       "dev_hod@expense.local",        "Department HOD"),
    (9003, "dev_accountant", "Dev",   "Accountant","dev_accountant@expense.local", "Accountant"),
    (9004, "dev_finance",    "Dev",   "Finance",   "dev_finance@expense.local",    None),   # pre-seeded below
    (9005, "dev_admin",      "Dev",   "Admin",     "dev_admin@expense.local",      "Sub Admin"),
]

# Real production roleIds from ERP_ROLE_ID_TO_APP_ROLE (security.py). Inserted into
# ErpMasterRole only if that roleId isn't already present -- on the shared ERP-Dev DB
# these almost certainly already exist with real data, so this is just a bootstrap
# fallback for a fresh/empty DB.
DEV_ERP_ROLES = [
    (102060, "Department HOD"),
    (102055, "Accountant"),
    (102068, "Sub Admin"),
]


def seed_dev_erp_users() -> None:
    db = SessionLocal()
    pw_hash = hash_password(DEV_PASSWORD)
    try:
        # ── 1. Ensure ErpMasterRole rows exist, keyed by the real roleId ───
        for role_id, role_name in DEV_ERP_ROLES:
            exists = db.execute(
                text("SELECT 1 FROM ErpMasterRole WHERE roleId = :id"), {"id": role_id}
            ).first()
            if not exists:
                db.execute(
                    text(
                        "SET IDENTITY_INSERT ErpMasterRole ON; "
                        "INSERT INTO ErpMasterRole (roleId, roleName, isActive, isDeleted) "
                        "VALUES (:id, :name, 1, 0); "
                        "SET IDENTITY_INSERT ErpMasterRole OFF"
                    ),
                    {"id": role_id, "name": role_name},
                )
        db.commit()

        # erp_role_name in DEV_USERS refers to these roleIds by name, so just use the
        # fixed mapping directly -- no need to look anything up by name.
        erp_role_id: dict[str, int] = {name: rid for rid, name in DEV_ERP_ROLES}

        # ── 2. Insert / update ERP auth + employee rows ────────────────────
        for user_id, user_name, first, last, email, erp_role_name in DEV_USERS:
            # ErpAuthUsers
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

            # ErpMasterEmployee — PK is employeeId, userId is a FK column
            existing_emp = db.execute(
                text("SELECT employeeId FROM ErpMasterEmployee WHERE userId = :id"), {"id": user_id}
            ).first()
            if existing_emp:
                db.execute(
                    text(
                        "UPDATE ErpMasterEmployee "
                        "SET firstName=:f, lastName=:l, emailId=:e, isAllowLogin=1 "
                        "WHERE userId=:id"
                    ),
                    {"f": first, "l": last, "e": email, "id": user_id},
                )
            else:
                db.execute(
                    text(
                        "SET IDENTITY_INSERT ErpMasterEmployee ON; "
                        "INSERT INTO ErpMasterEmployee (employeeId, userId, firstName, lastName, emailId, isAllowLogin, isActive, isDeleted) "
                        "VALUES (:emp_id, :id, :f, :l, :e, 1, 1, 0); "
                        "SET IDENTITY_INSERT ErpMasterEmployee OFF"
                    ),
                    {"emp_id": user_id, "id": user_id, "f": first, "l": last, "e": email},
                )

            # ErpAuthUserRoleMap — mapId is auto-identity, just insert userId+roleId
            if erp_role_name and erp_role_name in erp_role_id:
                rid = erp_role_id[erp_role_name]
                existing_map = db.execute(
                    text("SELECT mapId FROM ErpAuthUserRoleMap WHERE userId=:uid AND roleId=:rid"),
                    {"uid": user_id, "rid": rid},
                ).first()
                if not existing_map:
                    db.execute(
                        text("INSERT INTO ErpAuthUserRoleMap (userId, roleId, isActive) VALUES (:uid, :rid, 1)"),
                        {"uid": user_id, "rid": rid},
                    )

        db.commit()

        # ── 3. Pre-seed local ErpAuthExpenseUsers for dev_finance ──────────
        # finance_manager has no ERP role — seed the local row so the app role
        # is correct from the first login (authenticate_user won't overwrite it).
        from database.models import ErpAuthExpenseUsers, ErpMasterExpenseRole

        fm_user_id = 9004
        fm_local = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == fm_user_id).first()
        if not fm_local:
            fm_role = db.query(ErpMasterExpenseRole).filter(
                ErpMasterExpenseRole.role_code == "finance_manager"
            ).first()
            if fm_role:
                db.execute(text("SET IDENTITY_INSERT ErpAuthExpenseUsers ON"))
                db.add(
                    ErpAuthExpenseUsers(
                        user_id=fm_user_id,
                        user_name="dev_finance",
                        display_name="Dev Finance",
                        password_hash=pw_hash,
                        role_id=fm_role.role_id,
                        department_id=None,
                        email="dev_finance@expense.local",
                        is_active=1,
                        is_deleted=0,
                    )
                )
                db.flush()
                db.execute(text("SET IDENTITY_INSERT ErpAuthExpenseUsers OFF"))
                db.commit()

        print("Dev ERP users seeded:")
        for uid, uname, *_, erp_role in DEV_USERS:
            app_role = {
                "Department HOD": "hod",
                "Accountant": "accountant",
                "Sub Admin": "admin",
            }.get(erp_role or "", "employee" if uid != 9004 else "finance_manager")
            print(f"  {uname:<20} password={DEV_PASSWORD!r}  role={app_role}")

    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    seed_dev_erp_users()
