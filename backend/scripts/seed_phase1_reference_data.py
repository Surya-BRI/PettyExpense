"""Idempotent seed data for Phase 1 (config) + Phase 2 (approval) demo gates.

Call order (see main.py on_startup):
    seed_reference_data()   -- roles, departments, region config, categories, vendors, caches
    seed_users()            -- from auth.security; needs roles + departments to exist
    seed_hod_assignments()  -- needs both users and departments to exist
"""
import json

from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseEmployeeCache,
    ErpExpenseHodAssignment,
    ErpExpenseProjectCache,
    ErpExpenseRegionConfig,
    ErpExpenseVendor,
    ErpMasterExpenseRole,
    SessionLocal,
)
from auth.security import ROLE_CODES

DEFAULT_APPROVAL_MATRIX = {
    "stages": ["hod", "accountant", "finance_manager"],
    "bulk_approve_threshold": 500.0,
    "sla_hours": {"hod": 24, "department_hod": 24, "accountant": 48, "finance_manager": 48},
}

# App scope is UAE/KSA (see README) — UAE is the default region. IN is kept seeded
# for existing pre-UAE/KSA data; not part of the app's actual scope going forward.
# Same approval matrix for all three to start; regions can diverge later if the
# business needs differ (e.g. different SLA/thresholds per country).
REGIONS = [
    ("UAE", "United Arab Emirates"),
    ("KSA", "Kingdom of Saudi Arabia"),
    ("IN", "India"),
]

ROLE_NAMES = {
    "employee": "Employee",
    "hod": "Head of Department",
    "accountant": "Accountant",
    "finance_manager": "Finance Manager",
    "admin": "Admin",
}

DEPARTMENTS = ["Sales", "IT", "Accounts", "Admin"]

CATEGORIES = [
    ("Food", None, "IN"),
    ("Fuel", None, "IN"),
    ("IT Equipment", "IT", "IN"),
    ("Other", None, "IN"),
]

VENDORS = ["Al Futtaim Fuel Station", "City Mart Supplies", "Tech Bazaar Electronics"]

PROJECTS = [
    ("PRJ-1001", "Site Alpha", "OP-2201"),
    ("PRJ-1002", "Site Beta", "OP-2208"),
    ("PRJ-1003", "Warehouse Gamma", "OP-2215"),
]


def seed_reference_data() -> None:
    db = SessionLocal()
    try:
        # Roles
        existing_roles = {r.role_code for r in db.query(ErpMasterExpenseRole).all()}
        for code in ROLE_CODES:
            if code in existing_roles:
                continue
            db.add(ErpMasterExpenseRole(role_code=code, role_name=ROLE_NAMES[code], is_active=1))
        db.commit()

        # Departments
        existing_depts = {d.department_name for d in db.query(ErpExpenseDepartment).all()}
        for name in DEPARTMENTS:
            if name in existing_depts:
                continue
            db.add(ErpExpenseDepartment(department_name=name, is_active=1))
        db.commit()
        dept_by_name = {d.department_name: d for d in db.query(ErpExpenseDepartment).all()}

        # Region config
        for region_code, region_name in REGIONS:
            if not db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_code == region_code).first():
                db.add(
                    ErpExpenseRegionConfig(
                        region_code=region_code,
                        region_name=region_name,
                        allocation_model="petty_cash",
                        approval_matrix_json=json.dumps(DEFAULT_APPROVAL_MATRIX),
                        petty_cash_hard_limit_enabled=0,
                        company_name="Expense Receipt App",
                        is_active=1,
                    )
                )
        db.commit()
        region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_code == "UAE").first()

        # Categories
        existing_categories = {c.category_name for c in db.query(ErpExpenseCategory).all()}
        for name, owning_dept_name, _region_code in CATEGORIES:
            if name in existing_categories:
                continue
            owning_dept = dept_by_name.get(owning_dept_name) if owning_dept_name else None
            db.add(
                ErpExpenseCategory(
                    category_name=name,
                    owning_department_id=owning_dept.department_id if owning_dept else None,
                    is_active=1,
                )
            )
        db.commit()

        # Vendors
        existing_vendors = {v.vendor_name for v in db.query(ErpExpenseVendor).all()}
        for name in VENDORS:
            if name in existing_vendors:
                continue
            db.add(ErpExpenseVendor(vendor_name=name, source="manual", is_active=1))
        db.commit()

        # Project cache (replaces the old hardcoded routes_projects.py stub list)
        existing_projects = {p.middleware_project_id for p in db.query(ErpExpenseProjectCache).all()}
        for code, name, op_number in PROJECTS:
            if code in existing_projects:
                continue
            db.add(
                ErpExpenseProjectCache(
                    middleware_project_id=code,
                    project_name=name,
                    op_number=op_number,
                    region_id=region.region_id if region else None,
                )
            )
        db.commit()

        # Employee cache — mirrors the seed users (admin-populated placeholder, not live-synced)
        existing_employees = {e.employee_name for e in db.query(ErpExpenseEmployeeCache).all()}
        for username, display_name, dept_name in [
            ("surya", "Surya", "Sales"),
            ("raghu", "Raghu", "Sales"),
            ("denny", "Denny", "IT"),
            ("vikram", "Vikram", "IT"),
            ("sajeesh", "Sajeesh", "Sales"),
        ]:
            if display_name in existing_employees:
                continue
            dept = dept_by_name.get(dept_name)
            db.add(
                ErpExpenseEmployeeCache(
                    middleware_employee_id=username,
                    employee_name=display_name,
                    department_id=dept.department_id if dept else None,
                    region_id=region.region_id if region else None,
                )
            )
        db.commit()
    finally:
        db.close()


def seed_hod_assignments() -> None:
    """Run after seed_reference_data() and auth.security.seed_users()."""
    db = SessionLocal()
    try:
        dept_by_name = {d.department_name: d for d in db.query(ErpExpenseDepartment).all()}
        assignments = [
            ("sajeesh", "Sales"),
            ("denny", "IT"),
        ]
        for username, dept_name in assignments:
            user = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_name == username).first()
            dept = dept_by_name.get(dept_name)
            if not user or not dept:
                continue
            existing = (
                db.query(ErpExpenseHodAssignment)
                .filter(
                    ErpExpenseHodAssignment.user_id == user.user_id,
                    ErpExpenseHodAssignment.department_id == dept.department_id,
                )
                .first()
            )
            if existing:
                continue
            db.add(ErpExpenseHodAssignment(user_id=user.user_id, department_id=dept.department_id, is_active=1))
        db.commit()
    finally:
        db.close()
