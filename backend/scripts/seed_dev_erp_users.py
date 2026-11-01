"""Seed dev ERP user accounts for local development and testing.

Inserts rows into the shared ERP tables that authenticate_user() reads
(ErpAuthUsers, ErpMasterEmployee, ErpAuthUserRoleMap, ErpMasterRole) so
the login flow works without a live ERP connection.

Dev userIds start at 9001 to avoid colliding with real ERP data.
Script is fully idempotent: re-running it is safe.

Usage:
    cd backend
    python -m scripts.seed_dev_erp_users          # Dubai dev users
    python -m scripts.seed_dev_erp_users --ksa    # KSA approver team
    python -m scripts.seed_dev_erp_users --uae    # UAE (Contracting) team + employee
"""

from sqlalchemy import text

from auth.security import ERP_SUBSIDIARY_TO_REGION_CODE, hash_password
from database.models import SessionLocal

# ── Dev account definitions ────────────────────────────────────────────────
# (userId, userName, firstName, lastName, email, erp_role_name, department_name)
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
#
# department_name (when set) is looked up against ErpExpenseDepartment and written onto
# this user's LOCAL ErpAuthExpenseUsers.department_id -- that field is admin-managed and
# authenticate_user() never overwrites it once the local row exists (see security.py), so
# seeding it here is exactly the "hand-managed" path the department routing logic expects,
# just made idempotent/reproducible instead of a one-off DB edit. The two HOD accounts
# (priya_sales_hod, vikram_it_hod) also get an ErpExpenseHodAssignment row below so the
# "hod" approval stage can actually resolve them as an approver.
#
# Home company is DUBAI (BRI UAE / Industries) so these logins show in Admin People and
# petty-cash bills hit the Industries department pot, not Contracting. Extra companies
# can still be ticked after first sign-in. Region-only accounts stay in
# seed_dev_region_users.py (dev_dubai / dev_uae / dev_ksa / dev_oman).

DEV_PASSWORD = "Test@1234"
DEV_HOME_REGION = "DUBAI"


def _find_region_id(db, region_code: str):
    codes = [c for c, mapped in ERP_SUBSIDIARY_TO_REGION_CODE.items() if mapped == region_code]
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

DEV_USERS = [
    (9001, "surya_sales_emp",     "Surya",  "Sales",      "surya_sales_emp@expense.local",     None,              "Sales"),
    (9002, "priya_sales_hod",     "Priya",  "Sales HOD",  "priya_sales_hod@expense.local",     "Department HOD", "Sales"),
    (9003, "ravi_accountant",     "Ravi",   "Accountant", "ravi_accountant@expense.local",     "Accountant",      None),
    (9004, "meera_finance_mgr",   "Meera",  "Finance",    "meera_finance_mgr@expense.local",   None,              None),  # pre-seeded below
    (9005, "arjun_admin",         "Arjun",  "Admin",      "arjun_admin@expense.local",         "Sub Admin",       None),
    (9006, "vikram_it_hod",       "Vikram", "IT HOD",     "vikram_it_hod@expense.local",       "Department HOD", "IT"),
    (9007, "deepa_accounts_emp",  "Deepa",  "Accounts",   "deepa_accounts_emp@expense.local",  None,              "Accounts"),
    (9008, "anjana_it_emp",       "Anjana", "IT",         "anjana_it_emp@expense.local",       None,              "IT"),
]

# (userId, department_name) -- who's the HOD of which department, for the "hod" approval
# stage to resolve an approver. See services/approval_service.py::_hod_for_department.
DEV_HOD_ASSIGNMENTS = [
    (9002, "Sales"),
    (9006, "IT"),
]
DEV_FINANCE_MANAGER_IDS = {9004}

# KSA approver team: home company KSA, so KSA bills route to them and not to the Dubai
# team. HOD of the same departments as the Dubai HODs (HOD is per department across
# companies; each handles only the companies they cover -- see services/region_scope.py).
KSA_HOME_REGION = "KSA"
KSA_USERS = [
    (9021, "ksa_sales_hod",    "Khalid", "Sales HOD KSA",  "ksa_sales_hod@expense.local",    "Department HOD", "Sales"),
    (9022, "ksa_it_hod",       "Omar",   "IT HOD KSA",     "ksa_it_hod@expense.local",       "Department HOD", "IT"),
    (9023, "ksa_accountant",   "Noura",  "Accountant KSA", "ksa_accountant@expense.local",   "Accountant",      None),
    (9024, "ksa_finance_mgr",  "Faisal", "Finance KSA",    "ksa_finance_mgr@expense.local",  None,              None),
]
KSA_HOD_ASSIGNMENTS = [
    (9021, "Sales"),
    (9022, "IT"),
]
KSA_FINANCE_MANAGER_IDS = {9024}

# UAE = Blue Rhine Contracting. No ERP subsidiary maps to it, so ERP can't give these users a
# UAE home company -- they get UAE as an Admin-style assigned company instead
# (ErpExpenseMultiRegionUserRegion), and sign in straight into UAE.
UAE_REGION = "UAE"
UAE_USERS = [
    (9031, "uae_sales_hod",    "Hamdan", "Sales HOD UAE",  "uae_sales_hod@expense.local",    "Department HOD", "Sales"),
    (9032, "uae_it_hod",       "Rashid", "IT HOD UAE",     "uae_it_hod@expense.local",       "Department HOD", "IT"),
    (9033, "uae_accountant",   "Mariam", "Accountant UAE", "uae_accountant@expense.local",   "Accountant",      None),
    (9034, "uae_finance_mgr",  "Sultan", "Finance UAE",    "uae_finance_mgr@expense.local",  None,              None),
    (9035, "uae_sales_emp",    "Aisha",  "Sales UAE",      "uae_sales_emp@expense.local",    None,              "Sales"),
]
UAE_HOD_ASSIGNMENTS = [
    (9031, "Sales"),
    (9032, "IT"),
]
UAE_FINANCE_MANAGER_IDS = {9034}

# erp_role_name -> local ErpAuthExpenseUsers.role_code. Used when THIS script has to
# pre-create a user's local row (see section 3) -- a first login would resolve the same
# mapping on its own via authenticate_user(), but a pre-created row never gets touched
# again, so it must start out correct.
ROLE_CODE_BY_ERP_ROLE_NAME = {
    "Department HOD": "hod",
    "Accountant": "accountant",
    "Sub Admin": "admin",
}

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
    _seed_users(DEV_USERS, DEV_HOD_ASSIGNMENTS, DEV_HOME_REGION, DEV_FINANCE_MANAGER_IDS)


def seed_dev_ksa_team() -> None:
    _seed_users(KSA_USERS, KSA_HOD_ASSIGNMENTS, KSA_HOME_REGION, KSA_FINANCE_MANAGER_IDS)


def seed_dev_uae_team() -> None:
    _seed_users(
        UAE_USERS, UAE_HOD_ASSIGNMENTS, UAE_REGION, UAE_FINANCE_MANAGER_IDS,
        assigned_region_codes=[UAE_REGION],
    )


def _seed_users(
    users,
    hod_assignments,
    home_region_code: str,
    finance_manager_ids: set[int],
    assigned_region_codes: tuple[str, ...] | list[str] = (),
) -> None:
    """assigned_region_codes: companies ticked for every user (as Admin -> People does), for a
    company ERP can't give as a home company (UAE / Contracting)."""
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
        home_region_id = _find_region_id(db, home_region_code)
        if home_region_id is None and not assigned_region_codes:
            print(f"  WARNING: no ERP subsidiary/region for {home_region_code} -- People/home company left unset")

        # ── 2. Insert / update ERP auth + employee rows ────────────────────
        for user_id, user_name, first, last, email, erp_role_name, _dept in users:
            # ErpAuthUsers
            existing_auth = db.execute(
                text("SELECT userId FROM ErpAuthUsers WHERE userId = :id"), {"id": user_id}
            ).first()
            if existing_auth:
                # userName included so a rename in DEV_USERS (e.g. dev_employee ->
                # dev_sales_employee) actually takes effect on a row seeded under the old name.
                db.execute(
                    text("UPDATE ErpAuthUsers SET userName = :uname, password = :pw WHERE userId = :id"),
                    {"uname": user_name, "pw": pw_hash, "id": user_id},
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
                        "SET firstName=:f, lastName=:l, emailId=:e, isAllowLogin=1, regionId=:rid "
                        "WHERE userId=:id"
                    ),
                    {"f": first, "l": last, "e": email, "id": user_id, "rid": home_region_id},
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
                    {"emp_id": user_id, "id": user_id, "f": first, "l": last, "e": email, "rid": home_region_id},
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

        # ── 3. Pre-seed/update local ErpAuthExpenseUsers rows ───────────────
        # department_id lives only on this local table and authenticate_user() never
        # overwrites it once the row exists (see security.py) -- so a user_name rename or a
        # department_id assignment has to happen here, not on the ERP-side tables above.
        # dev_finance additionally needs its role pre-set (finance_manager has no ERP role
        # mapping at all), which is why it's always force-created even with no department.
        from database.models import (
            ErpAuthExpenseUsers,
            ErpExpenseDepartment,
            ErpExpenseRegionConfig,
            ErpMasterExpenseRole,
        )

        dept_id_by_name = {d.department_name: d.department_id for d in db.query(ErpExpenseDepartment).all()}
        # App company id, saved as the local home company so approval routing knows it
        # before the user's first sign-in (login would save the same value).
        app_home_region_id = (
            db.query(ErpExpenseRegionConfig.region_id)
            .filter(ErpExpenseRegionConfig.region_code == home_region_code)
            .scalar()
            if home_region_id is not None
            else None
        )

        for user_id, user_name, first, last, email, erp_role_name, dept_name in users:
            dept_id = dept_id_by_name.get(dept_name) if dept_name else None
            if dept_name and dept_id is None:
                print(f"  WARNING: department {dept_name!r} not found -- {user_name} left without one")

            role_code = (
                "finance_manager"
                if user_id in finance_manager_ids
                else ROLE_CODE_BY_ERP_ROLE_NAME.get(erp_role_name, "employee")
            )
            role = db.query(ErpMasterExpenseRole).filter(ErpMasterExpenseRole.role_code == role_code).first()

            local = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == user_id).first()
            if local:
                local.user_name = user_name
                if dept_id is not None:
                    local.department_id = dept_id
                # This script owns these specific dev user IDs end to end, so unlike the
                # general admin-managed department_id, role IS kept in sync on every run --
                # this is what caught/fixes the IT HOD row that got pre-created as "employee".
                if role:
                    local.role_id = role.role_id
                if app_home_region_id is not None:
                    local.home_region_id = app_home_region_id
                db.commit()
            else:
                # Pre-created (not left to first login) so role, department and home company
                # are in place for approval routing straight away.
                if role:
                    db.execute(text("SET IDENTITY_INSERT ErpAuthExpenseUsers ON"))
                    db.add(
                        ErpAuthExpenseUsers(
                            user_id=user_id,
                            user_name=user_name,
                            display_name=f"{first} {last}".strip(),
                            password_hash=pw_hash,
                            role_id=role.role_id,
                            department_id=dept_id,
                            email=email,
                            home_region_id=app_home_region_id,
                            is_active=1,
                            is_deleted=0,
                        )
                    )
                    db.flush()
                    db.execute(text("SET IDENTITY_INSERT ErpAuthExpenseUsers OFF"))
                    db.commit()

        # ── 3b. Assigned companies (Admin -> People ticks) ─────────────────
        if assigned_region_codes:
            from database.models import ErpExpenseMultiRegionUserRegion

            assigned_ids = [
                rid
                for (rid,) in db.query(ErpExpenseRegionConfig.region_id).filter(
                    ErpExpenseRegionConfig.region_code.in_(list(assigned_region_codes))
                )
            ]
            for user_id, *_ in users:
                for rid in assigned_ids:
                    row = (
                        db.query(ErpExpenseMultiRegionUserRegion)
                        .filter(
                            ErpExpenseMultiRegionUserRegion.user_id == user_id,
                            ErpExpenseMultiRegionUserRegion.region_id == rid,
                        )
                        .first()
                    )
                    if row:
                        row.is_active = 1
                    else:
                        db.add(ErpExpenseMultiRegionUserRegion(user_id=user_id, region_id=rid, is_active=1))
            db.commit()

        # ── 4. HOD assignments -- who approves the "hod" stage per department ──
        from database.models import ErpExpenseHodAssignment

        for user_id, dept_name in hod_assignments:
            dept_id = dept_id_by_name.get(dept_name)
            if dept_id is None:
                print(f"  WARNING: department {dept_name!r} not found -- HOD assignment for user {user_id} skipped")
                continue
            existing = db.query(ErpExpenseHodAssignment).filter(
                ErpExpenseHodAssignment.user_id == user_id,
                ErpExpenseHodAssignment.department_id == dept_id,
            ).first()
            if not existing:
                db.add(ErpExpenseHodAssignment(user_id=user_id, department_id=dept_id, is_active=1))
        db.commit()

        print("Dev ERP users seeded:")
        for uid, uname, *_, erp_role, dept_name in users:
            app_role = (
                "finance_manager" if uid in finance_manager_ids else ROLE_CODE_BY_ERP_ROLE_NAME.get(erp_role, "employee")
            )
            dept_suffix = f"  dept={dept_name}" if dept_name else ""
            home = f"  home={home_region_code}" if home_region_id else ""
            assigned = f"  assigned={','.join(assigned_region_codes)}" if assigned_region_codes else ""
            print(f"  {uname:<22} password={DEV_PASSWORD!r}  role={app_role}{dept_suffix}{home}{assigned}")

    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    if "--ksa" in sys.argv:
        seed_dev_ksa_team()
    elif "--uae" in sys.argv:
        seed_dev_uae_team()
    else:
        seed_dev_erp_users()
