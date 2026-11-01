"""Idempotent seed data for Phase 1 (config) + Phase 2 (approval) demo gates.

Called from main.py on_startup(): seed_reference_data() -- roles, departments, region
config, categories, vendors, caches. HOD assignments are admin-managed by hand against
real ERP users (see auth/security.py authenticate_user) rather than seeded here.
"""
import json

from sqlalchemy import text

from database.models import (
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseEmployeeCache,
    ErpExpensePettyCashFund,
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

# App scope is the GCC legal entities. India is no longer offered as a region.
# Same approval matrix for all to start; regions can diverge later if needed.
REGIONS = [
    ("DUBAI", "Dubai"),
    ("UAE", "United Arab Emirates"),
    ("KSA", "Kingdom of Saudi Arabia"),
    ("OMAN", "Oman"),
]

COMPANY_BY_REGION = {
    "DUBAI": "Blue Rhine Industries",
    "UAE": "Blue Rhine Contracting",
    "KSA": "Professional Signs",
}

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


def _sync_erp_departments(db) -> None:
    """Pull ErpMasterDepartment names into the local expense department table."""
    try:
        rows = db.execute(
            text(
                "SELECT departmentName FROM ErpMasterDepartment "
                "WHERE departmentName IS NOT NULL "
                "AND (isActive = 1 OR isActive IS NULL)"
            )
        ).all()
    except Exception:
        db.rollback()
        return
    existing = {(d.department_name or "").strip().lower(): d for d in db.query(ErpExpenseDepartment).all()}
    added = False
    for row in rows:
        name = (row[0] or "").strip()
        if not name or name.lower() in existing:
            continue
        db.add(ErpExpenseDepartment(department_name=name, is_active=1))
        existing[name.lower()] = True
        added = True
    if added:
        db.commit()


def seed_reference_data() -> None:
    try:
        from scripts.add_pca_topup_columns import ensure_pca_topup_columns

        ensure_pca_topup_columns()
    except Exception:
        pass
    try:
        from scripts.add_currency_region_payment_schema import ensure_columns

        ensure_columns()
    except Exception:
        pass
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
        _sync_erp_departments(db)
        dept_by_name = {d.department_name: d for d in db.query(ErpExpenseDepartment).all()}

        # Region config
        existing_regions = {
            (r.region_code or "").upper(): r for r in db.query(ErpExpenseRegionConfig).all()
        }
        for region_code, region_name in REGIONS:
            row = existing_regions.get(region_code.upper())
            company = COMPANY_BY_REGION.get(region_code)
            if not row:
                db.add(
                    ErpExpenseRegionConfig(
                        region_code=region_code,
                        region_name=region_name,
                        allocation_model="petty_cash",
                        approval_matrix_json=json.dumps(DEFAULT_APPROVAL_MATRIX),
                        petty_cash_hard_limit_enabled=0,
                        company_name=company or "Expense Receipt App",
                        is_active=1,
                    )
                )
            else:
                row.is_active = 1
                row.region_name = region_name
                if company:
                    row.company_name = company
        india = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_code == "IN").first()
        if india:
            india.is_active = 0
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

        try:
            from scripts.add_currency_region_payment_schema import backfill

            backfill(db)
        except Exception:
            db.rollback()
    finally:
        db.close()


def seed_department_pca_limits(db, amount: float = 5000.0) -> tuple[int, int]:
    """One-shot helper. Do not call from uvicorn startup — list_department_funds is too slow."""
    from services.currency import region_base_currency
    from services.fund_service import fund_service

    created = 0
    skipped = 0
    regions = (
        db.query(ErpExpenseRegionConfig)
        .filter(ErpExpenseRegionConfig.is_active == 1)
        .all()
    )
    for region in regions:
        currency = region_base_currency(region)
        rows = fund_service.list_department_funds(db, region.region_id)
        for row in rows:
            if row.get("fund"):
                skipped += 1
                continue
            db.add(
                ErpExpensePettyCashFund(
                    region_id=region.region_id,
                    owner_type="department",
                    department_id=row["department_id"],
                    currency=currency,
                    opening_balance=amount,
                    is_active=1,
                )
            )
            created += 1
        db.commit()
    return created, skipped
