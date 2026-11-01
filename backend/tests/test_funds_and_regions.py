"""Funds, remaining balance, top-up, and multi-region assignment."""
import json
import os

for _k in ("READER_DB_SERVER", "READER_DB_NAME", "READER_DB_USER", "READER_DB_PASSWORD"):
    os.environ.setdefault(_k, "test")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import (
    Base,
    ErpAuthExpenseUsers,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseHodAssignment,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpMasterExpenseRole,
)
from auth.security import resolve_local_department_id
from services.config_service import config_service
from services.fund_service import fund_service


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _setup(db):
    emp_role = ErpMasterExpenseRole(role_code="employee", role_name="Employee")
    hod_role = ErpMasterExpenseRole(role_code="hod", role_name="HOD")
    admin_role = ErpMasterExpenseRole(role_code="admin", role_name="Admin")
    fm_role = ErpMasterExpenseRole(role_code="finance_manager", role_name="Finance Manager")
    acc_role = ErpMasterExpenseRole(role_code="accountant", role_name="Accountant")
    db.add_all([emp_role, hod_role, admin_role, fm_role, acc_role])
    db.flush()
    sales = ErpExpenseDepartment(department_name="Sales")
    db.add(sales)
    db.flush()
    uae = ErpExpenseRegionConfig(
        region_code="UAE", region_name="UAE",
        approval_matrix_json=json.dumps({"stages": ["hod"]}),
        company_name="Blue Rhine UAE",
    )
    ksa = ErpExpenseRegionConfig(
        region_code="KSA", region_name="KSA",
        approval_matrix_json=json.dumps({"stages": ["hod"]}),
        company_name="Blue Rhine KSA",
    )
    db.add_all([uae, ksa])
    db.flush()
    employee = ErpAuthExpenseUsers(
        user_name="surya", display_name="Surya Sales", password_hash="x",
        role_id=emp_role.role_id, department_id=sales.department_id,
    )
    hod = ErpAuthExpenseUsers(
        user_name="priya", display_name="Priya HOD", password_hash="x",
        role_id=hod_role.role_id, department_id=sales.department_id,
    )
    admin = ErpAuthExpenseUsers(
        user_name="arjun", display_name="Arjun Admin", password_hash="x",
        role_id=admin_role.role_id,
    )
    fm = ErpAuthExpenseUsers(
        user_name="meera", display_name="Meera Finance", password_hash="x",
        role_id=fm_role.role_id,
    )
    accountant = ErpAuthExpenseUsers(
        user_name="nisha", display_name="Nisha Accounts", password_hash="x",
        role_id=acc_role.role_id,
    )
    db.add_all([employee, hod, admin, fm, accountant])
    db.commit()
    employee.department = sales
    employee.role = emp_role
    hod.role = hod_role
    admin.role = admin_role
    fm.role = fm_role
    accountant.role = acc_role
    return employee, hod, admin, fm, uae, ksa, sales, accountant


def test_assign_user_to_two_regions(db):
    employee, _, admin, _, uae, ksa, _, _ = _setup(db)
    out = config_service.set_user_regions(db, employee.user_id, ["UAE", "KSA"], assigned_by=admin.user_id)
    assert sorted(out["region_codes"]) == ["KSA", "UAE"]
    page = config_service.list_users(db, region_code="KSA", limit=25, offset=0)
    assert page["total"] >= 1
    assert any(u["id"] == employee.user_id for u in page["items"])
    empty = config_service.list_users(db, region_code="KSA", q="zzzz-no-match", limit=25, offset=0)
    assert empty["total"] == 0
    assert empty["items"] == []
    detail = config_service.get_user(db, employee.user_id)
    assert detail["id"] == employee.user_id
    assert "KSA" in detail["region_codes"]


def test_opening_and_remaining_for_department_and_individual(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    dept = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    individual = fund_service.create(
        db, region_id=uae.region_id, owner_type="employee",
        opening_balance=1000, employee_id=employee.user_id,
    )
    assert dept["opening_balance"] == 5000
    assert dept["remaining"] == 5000
    assert individual["opening_balance"] == 1000
    assert individual["remaining"] == 1000
    mine = fund_service.list_mine(db, employee)
    assert {f["owner_type"] for f in mine} == {"department", "employee"}


def test_individual_spend_does_not_hit_department_pot(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    fund_service.create(
        db, region_id=uae.region_id, owner_type="employee",
        opening_balance=1000, employee_id=employee.user_id,
    )
    db.add(ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=cat.category_id,
        type="petty_cash", status="approved", amount=100, total_amount=100, currency="AED",
    ))
    db.commit()
    mine = {f["owner_type"]: f for f in fund_service.list_mine(db, employee)}
    assert mine["employee"]["remaining"] == 900
    assert mine["department"]["remaining"] == 5000


def test_topup_without_spend_does_not_raise_limit(db):
    employee, hod, _, fm, uae, _, sales, accountant = _setup(db)
    dept = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    req = fund_service.request_topup(db, hod, dept["id"], 2000, "low balance")
    assert req["status"] == "submitted"
    fund_service.verify_topup(db, accountant, req["id"], None)
    decided = fund_service.decide_topup(db, fm, req["id"], True, None)
    assert decided["status"] == "approved"
    mine = {f["owner_type"]: f for f in fund_service.list_mine(db, employee)}
    assert mine["department"]["remaining"] == 5000
    assert mine["department"]["approved_limit"] == 5000


def test_hod_cannot_topup_another_departments_fund(db):
    _, hod, _, _, uae, _, _, _ = _setup(db)
    it = ErpExpenseDepartment(department_name="IT")
    db.add(it)
    db.flush()
    other = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=1000, department_id=it.department_id,
    )
    with pytest.raises(PermissionError):
        fund_service.request_topup(db, hod, other["id"], 200, None)


def test_ksa_fund_defaults_to_sar(db):
    _, _, _, _, _, ksa, sales, _ = _setup(db)
    fund = fund_service.create(
        db, region_id=ksa.region_id, owner_type="department",
        opening_balance=1000, department_id=sales.department_id,
    )
    assert fund["currency"] == "SAR"


def test_dubai_fund_defaults_to_aed(db):
    _, _, _, _, _, _, sales, _ = _setup(db)
    dubai = ErpExpenseRegionConfig(
        region_code="DUBAI", region_name="Dubai",
        approval_matrix_json=json.dumps({"stages": ["hod"]}),
        company_name="Blue Rhine Industries",
    )
    db.add(dubai)
    db.commit()
    fund = fund_service.create(
        db, region_id=dubai.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    assert fund["currency"] == "AED"


def test_department_funds_list_includes_unfunded(db):
    _, _, _, _, uae, _, sales, _ = _setup(db)
    it = ErpExpenseDepartment(department_name="IT")
    db.add(it)
    db.commit()
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    rows = {r["department_name"]: r for r in fund_service.list_department_funds(db, uae.region_id)}
    assert rows["Sales"]["fund"]["remaining"] == 5000
    assert rows["IT"]["fund"] is None


def test_admin_can_change_opening(db):
    _, _, _, _, uae, _, sales, _ = _setup(db)
    fund = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    changed = fund_service.update_opening(db, fund["id"], 8000)
    assert changed["opening_balance"] == 8000
    assert changed["remaining"] == 8000


def test_admin_can_request_topup_on_departments_behalf(db):
    _, _, admin, _, uae, _, sales, _ = _setup(db)
    fund = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    req = fund_service.request_topup(db, admin, fund["id"], 1500, "month top-up")
    assert req["status"] == "submitted"
    assert req["requester_name"] == "Arjun Admin"


def test_employee_cannot_request_topup(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    fund = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    with pytest.raises(PermissionError, match="HOD or Admin"):
        fund_service.request_topup(db, employee, fund["id"], 100, None)


def test_hod_assignment_allows_topup_for_other_department(db):
    _, hod, _, fm, uae, _, _, accountant = _setup(db)
    it = ErpExpenseDepartment(department_name="IT")
    db.add(it)
    db.flush()
    db.add(ErpExpenseHodAssignment(user_id=hod.user_id, department_id=it.department_id, is_active=1))
    db.commit()
    fund = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=1000, department_id=it.department_id,
    )
    req = fund_service.request_topup(db, hod, fund["id"], 200, None)
    fund_service.verify_topup(db, accountant, req["id"], None)
    fund_service.decide_topup(db, fm, req["id"], True, None)
    mine = {f["department_name"]: f for f in fund_service.list_mine(db, hod)}
    assert mine["IT"]["remaining"] == 1000


def test_department_spend_reduces_remaining(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=10000, department_id=sales.department_id,
    )
    db.add(ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=cat.category_id,
        type="petty_cash", status="approved", amount=200, total_amount=200, currency="AED",
    ))
    db.commit()
    mine = fund_service.list_mine(db, employee)
    assert mine[0]["opening_balance"] == 10000
    assert mine[0]["remaining"] == 9800


def test_submitted_bill_is_reserved_not_deducted(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=1000, department_id=sales.department_id,
    )
    txn = ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=cat.category_id,
        type="petty_cash", status="submitted", amount=300, total_amount=300, currency="AED",
    )
    db.add(txn)
    db.commit()
    mine = fund_service.list_mine(db, employee)[0]
    assert mine["remaining"] == 1000
    assert mine["pending_bills"] == 300
    assert mine["uncommitted"] == 700
    with pytest.raises(ValueError, match="exceeds available petty cash"):
        fund_service.require_petty_cash_within_limit(db, employee, uae.region_id, 700.01)

    txn.status = "approved"
    db.commit()
    mine = fund_service.list_mine(db, employee)[0]
    assert mine["remaining"] == 700
    assert mine["spent"] == 300
    assert mine["pending_bills"] == 0


def test_foreign_currency_bill_is_converted_to_fund_currency(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=1000, department_id=sales.department_id,
    )
    db.add(ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=cat.category_id,
        type="petty_cash", status="approved", amount=100, total_amount=100, currency="USD",
        exchange_rate=3.6725,
    ))
    db.commit()
    mine = fund_service.list_mine(db, employee)[0]
    assert mine["spent"] == pytest.approx(367.25)
    assert mine["remaining"] == pytest.approx(632.75)


def test_resolve_local_department_reuses_row(db):
    first = resolve_local_department_id(db, "Acrylic")
    second = resolve_local_department_id(db, "acrylic")
    assert first == second
    assert resolve_local_department_id(db, "  ") is None


def test_bri_pca_limit_restored_after_bill_backed_topup(db):
    employee, hod, _, fm, _, _, sales, accountant = _setup(db)
    dubai = ErpExpenseRegionConfig(
        region_code="DUBAI", region_name="Dubai",
        approval_matrix_json=json.dumps({"stages": ["hod"]}),
        company_name="Blue Rhine Industries",
    )
    db.add(dubai)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    fund = fund_service.create(
        db, region_id=dubai.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    tx = ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=dubai.region_id, category_id=cat.category_id,
        type="petty_cash", status="submitted", amount=1000, total_amount=1000, currency="AED",
    )
    db.add(tx)
    db.commit()
    assert fund_service.list_replenishable_bills(db, hod, fund["id"]) == []
    with pytest.raises(ValueError, match="fully approved"):
        fund_service.request_topup(
            db, hod, fund["id"], None, "PCA replenishment", transaction_ids=[tx.transaction_id]
        )
    tx.status = "approved"
    db.commit()
    mine = fund_service.list_mine(db, employee)[0]
    assert mine["remaining"] == 4000
    assert mine["unreplenished_spend"] == 1000
    bills = fund_service.list_replenishable_bills(db, hod, fund["id"])
    assert [b["id"] for b in bills] == [tx.transaction_id]
    req = fund_service.request_topup(
        db, hod, fund["id"], None, "PCA replenishment", transaction_ids=[tx.transaction_id]
    )
    assert req["amount"] == 1000
    assert req["status"] == "submitted"
    with pytest.raises(ValueError):
        fund_service.decide_topup(db, fm, req["id"], True, None)
    verified = fund_service.verify_topup(db, accountant, req["id"], None)
    assert verified["status"] == "verified"
    decided = fund_service.decide_topup(db, fm, req["id"], True, None, payment_reference="TRF-1")
    assert decided["status"] == "approved"
    assert decided["payment_reference"] == "TRF-1"
    after = fund_service.list_mine(db, employee)[0]
    assert after["approved_limit"] == 5000
    assert after["remaining"] == 5000
    assert after["unreplenished_spend"] == 0


def test_petty_cash_claim_cannot_be_marked_paid(db):
    from auth.security import CurrentUser
    from services.transaction_service import transaction_service

    employee, _, _, fm, uae, _, _, _ = _setup(db)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    txn = ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=cat.category_id,
        type="petty_cash", status="approved", amount=50, total_amount=50, currency="AED",
    )
    db.add(txn)
    db.commit()
    fm_user = CurrentUser(id=fm.user_id, display_name="Meera", role="finance_manager", region_code="UAE")
    with pytest.raises(ValueError, match="no payment step"):
        transaction_service.mark_paid(db, fm_user, txn.transaction_id, None)
    db.refresh(txn)
    assert txn.status == "approved"


def test_my_claims_can_be_filtered_by_company(db):
    from auth.security import CurrentUser
    from services.transaction_service import transaction_service

    employee, _, _, _, uae, ksa, _, _ = _setup(db)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    for region, amount in ((uae, 10), (ksa, 20), (ksa, 30)):
        db.add(ErpExpenseTransaction(
            employee_id=employee.user_id, region_id=region.region_id, category_id=cat.category_id,
            type="reimbursement", status="draft", amount=amount, total_amount=amount, currency="AED",
        ))
    db.commit()
    me = CurrentUser(id=employee.user_id, display_name="Surya", role="employee", region_code="UAE")
    assert transaction_service.list_mine(db, me, limit=10)["total"] == 3
    assert transaction_service.list_mine(db, me, limit=10, region_code="ksa")["total"] == 2
    assert transaction_service.list_mine(db, me, limit=10, region_code="UAE")["total"] == 1
    assert transaction_service.list_mine(db, me, limit=10, region_code="OMAN")["total"] == 0


def test_reimbursement_does_not_debit_department_pot(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    db.add(ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=cat.category_id,
        type="reimbursement", status="submitted", amount=1000, total_amount=1000, currency="AED",
    ))
    db.commit()
    mine = fund_service.list_mine(db, employee)[0]
    assert mine["remaining"] == 5000
    assert mine["spent"] == 0


def test_petty_cash_over_limit_is_blocked(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=500, department_id=sales.department_id,
    )
    with pytest.raises(ValueError, match="exceeds available petty cash"):
        fund_service.require_petty_cash_within_limit(db, employee, uae.region_id, 500.01)
    fund_service.require_petty_cash_within_limit(db, employee, uae.region_id, 500)


def test_petty_cash_blocked_when_no_department_fund(db):
    employee, _, _, _, uae, _, _, _ = _setup(db)
    with pytest.raises(ValueError, match="No petty cash limit"):
        fund_service.require_petty_cash_within_limit(db, employee, uae.region_id, 10)


def test_petty_cash_limit_excludes_current_submitted_bill(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=500, department_id=sales.department_id,
    )
    txn = ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=cat.category_id,
        type="petty_cash", status="submitted", amount=400, total_amount=400, currency="AED",
    )
    db.add(txn)
    db.commit()
    with pytest.raises(ValueError, match="exceeds available petty cash"):
        fund_service.require_petty_cash_within_limit(db, employee, uae.region_id, 400)
    fund_service.require_petty_cash_within_limit(
        db, employee, uae.region_id, 400, exclude_transaction_id=txn.transaction_id,
    )


def _it_setup(db, uae, sales):
    """IT department with its own fund + HOD, and an IT-owned category."""
    it = ErpExpenseDepartment(department_name="IT")
    db.add(it)
    db.flush()
    hod_role = db.query(ErpMasterExpenseRole).filter(ErpMasterExpenseRole.role_code == "hod").one()
    it_hod = ErpAuthExpenseUsers(
        user_name="vikram", display_name="Vikram IT HOD", password_hash="x",
        role_id=hod_role.role_id, department_id=it.department_id,
    )
    food = ErpExpenseCategory(category_name="Food")
    it_kit = ErpExpenseCategory(category_name="IT Equipment", owning_department_id=it.department_id)
    db.add_all([it_hod, food, it_kit])
    db.flush()
    db.add(ErpExpenseHodAssignment(user_id=it_hod.user_id, department_id=it.department_id, is_active=1))
    db.commit()
    it_hod.role = hod_role
    sales_fund = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=1000, department_id=sales.department_id,
    )
    it_fund = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=500, department_id=it.department_id,
    )
    return it, it_hod, food, it_kit, sales_fund, it_fund


def _split_bill(db, employee, uae, food, it_kit, food_amount, it_amount, status="approved", currency="AED", rate=1.0):
    from database.models import ErpExpenseLineItem

    txn = ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=food.category_id,
        type="petty_cash", status=status, amount=food_amount + it_amount,
        total_amount=food_amount + it_amount, currency=currency, exchange_rate=rate,
    )
    txn.line_items = [
        ErpExpenseLineItem(line_no=1, description="Lunch", amount=food_amount, category_id=food.category_id),
        ErpExpenseLineItem(line_no=2, description="Mouse", amount=it_amount, category_id=it_kit.category_id),
    ]
    db.add(txn)
    db.commit()
    return txn


def _funds_by_department(db, uae):
    return {r["department_name"]: r["fund"] for r in fund_service.list_department_funds(db, uae.region_id)}


def test_it_lines_on_sales_bill_come_out_of_it_fund(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    _, _, food, it_kit, _, _ = _it_setup(db, uae, sales)
    _split_bill(db, employee, uae, food, it_kit, 300, 120)

    funds = _funds_by_department(db, uae)
    assert funds["Sales"]["spent"] == 300
    assert funds["Sales"]["remaining"] == 700
    assert funds["IT"]["spent"] == 120
    assert funds["IT"]["remaining"] == 380


def test_single_item_it_bill_from_sales_comes_out_of_it_fund(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    _, _, _, it_kit, _, _ = _it_setup(db, uae, sales)
    db.add(ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=uae.region_id, category_id=it_kit.category_id,
        type="petty_cash", status="approved", amount=200, total_amount=200, currency="AED",
    ))
    db.commit()
    funds = _funds_by_department(db, uae)
    assert funds["Sales"]["spent"] == 0
    assert funds["IT"]["spent"] == 200


def test_split_bill_is_converted_before_splitting(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    _, _, food, it_kit, _, _ = _it_setup(db, uae, sales)
    _split_bill(db, employee, uae, food, it_kit, 75, 25, currency="USD", rate=3.6725)
    funds = _funds_by_department(db, uae)
    assert funds["Sales"]["spent"] + funds["IT"]["spent"] == pytest.approx(367.25)
    assert funds["IT"]["spent"] == pytest.approx(91.81)


def test_it_part_over_it_fund_limit_is_blocked(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    _, _, food, it_kit, _, _ = _it_setup(db, uae, sales)
    txn = _split_bill(db, employee, uae, food, it_kit, 100, 500.01, status="draft")
    with pytest.raises(ValueError, match="IT items on this bill"):
        fund_service.require_bill_within_limits(db, employee, txn, "AED")
    txn.line_items[1].amount = 500
    txn.total_amount = 600
    db.commit()
    fund_service.require_bill_within_limits(db, employee, txn, "AED")


def test_it_part_blocked_when_it_has_no_fund(db):
    employee, _, _, _, uae, _, sales, _ = _setup(db)
    it = ErpExpenseDepartment(department_name="IT")
    db.add(it)
    db.flush()
    food = ErpExpenseCategory(category_name="Food")
    it_kit = ErpExpenseCategory(category_name="IT Equipment", owning_department_id=it.department_id)
    db.add_all([food, it_kit])
    db.commit()
    fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=1000, department_id=sales.department_id,
    )
    txn = _split_bill(db, employee, uae, food, it_kit, 100, 20, status="draft")
    with pytest.raises(ValueError, match="no petty cash limit is set for IT"):
        fund_service.require_bill_within_limits(db, employee, txn, "AED")


def test_it_hod_tops_up_only_the_it_part(db):
    employee, hod, _, fm, uae, _, sales, accountant = _setup(db)
    _, it_hod, food, it_kit, sales_fund, it_fund = _it_setup(db, uae, sales)
    txn = _split_bill(db, employee, uae, food, it_kit, 300, 120)

    it_bills = fund_service.list_replenishable_bills(db, it_hod, it_fund["id"])
    assert [(b["id"], b["amount"], b["bill_total"]) for b in it_bills] == [(txn.transaction_id, 120, 420)]
    req = fund_service.request_topup(db, it_hod, it_fund["id"], None, None, transaction_ids=[txn.transaction_id])
    assert req["amount"] == 120

    # The Sales part of the same bill is still open for the Sales HOD's own top-up.
    sales_bills = fund_service.list_replenishable_bills(db, hod, sales_fund["id"])
    assert [(b["id"], b["amount"]) for b in sales_bills] == [(txn.transaction_id, 300)]
    sales_req = fund_service.request_topup(db, hod, sales_fund["id"], None, None, transaction_ids=[txn.transaction_id])
    assert sales_req["amount"] == 300

    fund_service.verify_topup(db, accountant, req["id"], None)
    fund_service.decide_topup(db, fm, req["id"], True, None)
    assert _funds_by_department(db, uae)["IT"]["remaining"] == 500


def test_submitting_split_bill_checks_it_fund(db):
    from auth.security import CurrentUser
    from services.transaction_service import transaction_service

    employee, _, _, _, uae, _, sales, _ = _setup(db)
    _, _, food, it_kit, _, _ = _it_setup(db, uae, sales)
    me = CurrentUser(id=employee.user_id, display_name="Surya", role="employee", region_code="UAE")

    def submit(it_amount, bill_number):
        return transaction_service.create_claim(
            db, me, vendor="Sharaf DG", amount=0, currency="AED", bill_date="2026-10-30",
            category_id=food.category_id, region_code="UAE", type="petty_cash", project_id=None,
            op_number=None, bill_number=bill_number, remarks=None, receipt_id=None, s3_key=None,
            line_items=[
                {"description": "Lunch", "amount": 50, "category_id": food.category_id},
                {"description": "Keyboard", "amount": it_amount, "category_id": it_kit.category_id},
            ],
        )

    with pytest.raises(ValueError, match="IT items on this bill"):
        submit(600, "INV-1")
    db.rollback()
    out = submit(200, "INV-2")
    it_line = next(li for li in out["line_items"] if li["description"] == "Keyboard")
    assert it_line["owning_department_name"] == "IT"
    assert _funds_by_department(db, uae)["IT"]["pending_bills"] == 200


def test_dubai_rejects_individual_fund(db):
    employee, _, _, _, _, _, sales, _ = _setup(db)
    dubai = ErpExpenseRegionConfig(
        region_code="DUBAI", region_name="Dubai",
        approval_matrix_json=json.dumps({"stages": ["hod"]}),
        company_name="Blue Rhine Industries",
    )
    db.add(dubai)
    db.commit()
    with pytest.raises(ValueError, match="department petty cash only"):
        fund_service.create(
            db, region_id=dubai.region_id, owner_type="employee",
            opening_balance=1000, employee_id=employee.user_id,
        )
