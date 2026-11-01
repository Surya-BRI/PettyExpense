"""Sales employee + IT Equipment must route Sales HOD → IT HOD → Accountant → FM.

The IT category is owned by the IT department, so after the employee's own HOD
the claim goes to that owning department's HOD before Finance.
"""
import os

for _k in ("READER_DB_SERVER", "READER_DB_NAME", "READER_DB_USER", "READER_DB_PASSWORD"):
    os.environ.setdefault(_k, "test")

import json  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from database.models import (  # noqa: E402
    Base,
    ErpAuthExpenseUsers,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseHodAssignment,
    ErpExpenseLineItem,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpMasterExpenseRole,
)
from services.approval_service import resolve_stage_labels, resolve_stage_sequence  # noqa: E402


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
    db.add_all([emp_role, hod_role])
    db.flush()
    sales = ErpExpenseDepartment(department_name="Sales")
    it = ErpExpenseDepartment(department_name="IT")
    db.add_all([sales, it])
    db.flush()
    employee = ErpAuthExpenseUsers(
        user_name="surya_sales_emp", display_name="Surya Sales", password_hash="x",
        role_id=emp_role.role_id, department_id=sales.department_id,
    )
    sales_hod = ErpAuthExpenseUsers(
        user_name="priya_sales_hod", display_name="Priya Sales HOD", password_hash="x",
        role_id=hod_role.role_id, department_id=sales.department_id,
    )
    it_hod = ErpAuthExpenseUsers(
        user_name="vikram_it_hod", display_name="Vikram IT HOD", password_hash="x",
        role_id=hod_role.role_id, department_id=it.department_id,
    )
    db.add_all([employee, sales_hod, it_hod])
    db.flush()
    db.add_all([
        ErpExpenseHodAssignment(user_id=sales_hod.user_id, department_id=sales.department_id),
        ErpExpenseHodAssignment(user_id=it_hod.user_id, department_id=it.department_id),
    ])
    food = ErpExpenseCategory(category_name="Food")
    it_kit = ErpExpenseCategory(category_name="IT Equipment", owning_department_id=it.department_id)
    region = ErpExpenseRegionConfig(
        region_code="UAE", region_name="UAE",
        approval_matrix_json=json.dumps({"stages": ["hod", "accountant", "finance_manager"]}),
    )
    db.add_all([food, it_kit, region])
    db.commit()
    employee.department = sales
    it_kit.owning_department = it
    return employee, food, it_kit, region


def _txn(db, employee, category, region):
    txn = ErpExpenseTransaction(
        employee_id=employee.user_id,
        category_id=category.category_id,
        region_id=region.region_id,
        amount=100,
        status="submitted",
    )
    db.add(txn)
    db.commit()
    txn.employee = employee
    txn.category = category
    txn.region = region
    return txn


def test_sales_it_equipment_inserts_it_hod_after_sales_hod(db):
    employee, _, it_kit, region = _setup(db)
    txn = _txn(db, employee, it_kit, region)
    it_stage = f"department_hod:{it_kit.owning_department_id}"

    assert resolve_stage_sequence(db, txn) == [
        "hod", it_stage, "accountant", "finance_manager",
    ]
    labels = resolve_stage_labels(txn)
    assert labels["hod"] == "Sales HOD"
    assert labels[it_stage] == "IT HOD"
    assert [labels[s] for s in resolve_stage_sequence(db, txn)] == [
        "Sales HOD", "IT HOD", "Accountant", "Finance Manager",
    ]


def _add_lines(db, txn, *lines):
    for i, (category, amount) in enumerate(lines, start=1):
        txn.line_items.append(ErpExpenseLineItem(
            line_no=i, description=f"item {i}", amount=amount, category_id=category.category_id,
        ))
    txn.total_amount = sum(a for _, a in lines)
    db.commit()
    for li, (category, _) in zip(txn.line_items, lines):
        li.category = category


def test_it_line_on_a_sales_food_bill_goes_to_it_hod(db):
    """Main category Food, but one IT line: the IT HOD must still approve."""
    employee, food, it_kit, region = _setup(db)
    txn = _txn(db, employee, food, region)
    _add_lines(db, txn, (food, 80), (it_kit, 20))

    it_stage = f"department_hod:{it_kit.owning_department_id}"
    assert resolve_stage_sequence(db, txn) == ["hod", it_stage, "accountant", "finance_manager"]
    assert resolve_stage_labels(txn)[it_stage] == "IT HOD"


def test_lines_from_two_other_departments_add_two_hod_stages(db):
    employee, food, it_kit, region = _setup(db)
    admin_dept = ErpExpenseDepartment(department_name="Admin")
    db.add(admin_dept)
    db.flush()
    hod_role = db.query(ErpMasterExpenseRole).filter(ErpMasterExpenseRole.role_code == "hod").one()
    admin_hod = ErpAuthExpenseUsers(
        user_name="admin_hod", display_name="Admin HOD", password_hash="x",
        role_id=hod_role.role_id, department_id=admin_dept.department_id,
    )
    db.add(admin_hod)
    db.flush()
    db.add(ErpExpenseHodAssignment(user_id=admin_hod.user_id, department_id=admin_dept.department_id))
    facilities = ErpExpenseCategory(category_name="Facilities", owning_department_id=admin_dept.department_id)
    db.add(facilities)
    db.commit()
    facilities.owning_department = admin_dept

    txn = _txn(db, employee, food, region)
    _add_lines(db, txn, (food, 50), (it_kit, 30), (facilities, 20))

    assert resolve_stage_sequence(db, txn) == [
        "hod",
        f"department_hod:{it_kit.owning_department_id}",
        f"department_hod:{admin_dept.department_id}",
        "accountant",
        "finance_manager",
    ]


def test_it_hod_approves_then_claim_moves_to_accountant(db):
    from auth.security import CurrentUser
    from services.approval_service import advance, list_queue

    employee, food, it_kit, region = _setup(db)
    sales_hod = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_name == "priya_sales_hod").one()
    it_hod = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_name == "vikram_it_hod").one()
    txn = _txn(db, employee, food, region)
    _add_lines(db, txn, (food, 80), (it_kit, 20))

    as_sales_hod = CurrentUser(id=sales_hod.user_id, display_name="Priya", role="hod")
    as_it_hod = CurrentUser(id=it_hod.user_id, display_name="Vikram", role="hod")
    out = advance(db, as_sales_hod, txn.transaction_id, "approve", None)
    assert out["current_stage"] == "department_hod"
    assert out["current_stage_key"] == f"department_hod:{it_kit.owning_department_id}"

    assert [c["id"] for c in list_queue(db, as_it_hod, "department_hod")] == [txn.transaction_id]
    assert list_queue(db, as_sales_hod, "department_hod") == []
    with pytest.raises(PermissionError):
        advance(db, as_sales_hod, txn.transaction_id, "approve", None)

    out = advance(db, as_it_hod, txn.transaction_id, "approve", None)
    assert out["current_stage"] == "accountant"


def test_claim_staged_before_department_keys_still_routes(db):
    """In-flight claims saved with a plain 'department_hod' stage keep working."""
    from auth.security import CurrentUser
    from services.approval_service import advance

    employee, _, it_kit, region = _setup(db)
    it_hod = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_name == "vikram_it_hod").one()
    txn = _txn(db, employee, it_kit, region)
    txn.current_stage = "department_hod"
    db.commit()

    out = advance(db, CurrentUser(id=it_hod.user_id, display_name="Vikram", role="hod"), txn.transaction_id, "approve", None)
    assert out["current_stage"] == "accountant"


def test_same_department_it_bill_skips_extra_hod(db):
    """An IT employee claiming IT Equipment only needs their own HOD once."""
    _, _, it_kit, region = _setup(db)
    it = db.query(ErpExpenseDepartment).filter(ErpExpenseDepartment.department_name == "IT").one()
    emp_role = db.query(ErpMasterExpenseRole).filter(ErpMasterExpenseRole.role_code == "employee").one()
    it_emp = ErpAuthExpenseUsers(
        user_name="anjana_it_emp", display_name="Anjana IT", password_hash="x",
        role_id=emp_role.role_id, department_id=it.department_id,
    )
    db.add(it_emp)
    db.commit()
    it_emp.department = it
    txn = _txn(db, it_emp, it_kit, region)

    assert resolve_stage_sequence(db, txn) == ["hod", "accountant", "finance_manager"]
    assert resolve_stage_labels(txn)["hod"] == "IT HOD"


def _count_selects(db):
    from sqlalchemy import event

    counter = {"n": 0}

    def _on_execute(conn, cursor, statement, *args):
        if statement.lstrip().upper().startswith("SELECT"):
            counter["n"] += 1

    event.listen(db.get_bind(), "before_cursor_execute", _on_execute)
    return counter, lambda: event.remove(db.get_bind(), "before_cursor_execute", _on_execute)


def test_queue_load_looks_up_each_approver_set_once_not_per_claim(db):
    """HOD/delegation lookups are shared across the whole queue: 10 claims cost about the
    same as 1, and the result (who sees what, in what order) is unchanged."""
    from auth.security import CurrentUser
    from services.approval_service import list_queue

    employee, food, it_kit, region = _setup(db)
    sales_hod = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_name == "priya_sales_hod").one()
    as_sales_hod = CurrentUser(id=sales_hod.user_id, display_name="Priya", role="hod")

    def load_queue_with(n_claims):
        for _ in range(n_claims):
            txn = _txn(db, employee, food, region)
            _add_lines(db, txn, (food, 80), (it_kit, 20))
            txn.current_stage = "hod"
        db.commit()
        db.expire_all()
        counter, stop = _count_selects(db)
        try:
            out = list_queue(db, as_sales_hod, "hod")
        finally:
            stop()
        return out, counter["n"]

    one, one_queries = load_queue_with(1)
    assert [c["id"] for c in one] and one[0]["stage_sequence"][1].startswith("department_hod:")
    ten, ten_queries = load_queue_with(9)
    assert len(ten) == 10
    assert [c["stage_sequence"] for c in ten] == [one[0]["stage_sequence"]] * 10
    # Before the cache each claim added its own HOD + delegation lookups (several per row,
    # twice over). Now only the per-row eager loads grow -- not the approver lookups.
    assert ten_queries - one_queries <= 4, (one_queries, ten_queries)

    # The cache doesn't outlive the request: nothing is left on the session.
    from services.approval_service import _CACHE_KEY
    assert _CACHE_KEY not in db.info


def test_food_from_sales_has_no_department_hod(db):
    employee, food, _, region = _setup(db)
    txn = _txn(db, employee, food, region)
    assert resolve_stage_sequence(db, txn) == ["hod", "accountant", "finance_manager"]
