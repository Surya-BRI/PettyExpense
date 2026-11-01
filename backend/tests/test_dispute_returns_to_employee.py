"""After HOD disputes, the bill sits with the employee — not in any approver queue.

Approving a disputed bill used to stay on the HOD screen, move current_stage
forward, and leave status as `disputed`, so HOD history looked 'Approved' while
Accountant never saw a submitted claim.
"""
import os

for _k in ("READER_DB_SERVER", "READER_DB_NAME", "READER_DB_USER", "READER_DB_PASSWORD"):
    os.environ.setdefault(_k, "test")

import json  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from auth.security import CurrentUser  # noqa: E402
from database.models import (  # noqa: E402
    Base,
    ErpAuthExpenseUsers,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseHodAssignment,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpMasterExpenseRole,
)
from services import approval_service  # noqa: E402
from services.transaction_service import transaction_service  # noqa: E402


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    monkeypatch.setattr(transaction_service, "_notify_finance_on_submit", lambda *a, **k: None)
    monkeypatch.setattr("services.notification_service.send", lambda *a, **k: None)
    yield session
    session.close()


def _cu(user, role):
    return CurrentUser(user.user_id, user.display_name, role)


@pytest.fixture
def world(db):
    roles = {code: ErpMasterExpenseRole(role_code=code, role_name=code) for code in
             ("employee", "hod", "accountant", "finance_manager")}
    db.add_all(roles.values())
    db.flush()
    sales = ErpExpenseDepartment(department_name="Sales")
    db.add(sales)
    db.flush()
    employee = ErpAuthExpenseUsers(
        user_name="surya_sales_emp", display_name="Surya Sales", password_hash="x",
        role_id=roles["employee"].role_id, department_id=sales.department_id,
    )
    hod = ErpAuthExpenseUsers(
        user_name="priya_sales_hod", display_name="Priya Sales HOD", password_hash="x",
        role_id=roles["hod"].role_id, department_id=sales.department_id,
    )
    accountant = ErpAuthExpenseUsers(
        user_name="ravi_accountant", display_name="Ravi Accountant", password_hash="x",
        role_id=roles["accountant"].role_id,
    )
    db.add_all([employee, hod, accountant])
    db.flush()
    db.add(ErpExpenseHodAssignment(user_id=hod.user_id, department_id=sales.department_id))
    db.add(ErpExpenseCategory(category_name="Food"))
    db.add(ErpExpenseRegionConfig(
        region_code="UAE", region_name="UAE",
        approval_matrix_json=json.dumps({"stages": ["hod", "accountant", "finance_manager"]}),
    ))
    db.commit()
    claim = transaction_service.create_claim(
        db, _cu(employee, "employee"),
        vendor="City Mart", amount=40, vat_amount=2, total_amount=42, currency="AED",
        bill_date="01/10/2026", category_id=1, region_code="UAE",
        project_id=None, op_number=None, bill_number="INV-DISP-1", remarks=None,
        receipt_id=None, s3_key=None, submit=True,
    )
    txn = db.query(ErpExpenseTransaction).filter(
        ErpExpenseTransaction.transaction_id == claim["id"]
    ).one()
    approval_service._ensure_stage(db, txn)
    return {"employee": employee, "hod": hod, "accountant": accountant, "txn": txn}


def _ids(queue):
    return {row["id"] for row in queue}


def test_dispute_leaves_hod_queue_and_blocks_approve_until_resubmit(db, world):
    hod = _cu(world["hod"], "hod")
    accountant = _cu(world["accountant"], "accountant")
    employee = _cu(world["employee"], "employee")
    tid = world["txn"].transaction_id

    assert tid in _ids(approval_service.list_queue(db, hod, "hod"))

    approval_service.advance(db, hod, tid, "dispute", "Wrong amount — please correct")
    txn = db.query(ErpExpenseTransaction).filter(ErpExpenseTransaction.transaction_id == tid).one()

    assert txn.status == "disputed"
    assert txn.current_stage == "hod"
    assert tid not in _ids(approval_service.list_queue(db, hod, "hod"))
    assert tid not in _ids(approval_service.list_queue(db, accountant, "accountant"))

    with pytest.raises(ValueError, match="not awaiting approval"):
        approval_service.advance(db, hod, tid, "approve", None)

    transaction_service.update_draft(db, employee, tid, {"amount": 35.0, "total_amount": 37.0})
    approval_service.resubmit_after_dispute(db, employee, tid)
    txn = db.query(ErpExpenseTransaction).filter(ErpExpenseTransaction.transaction_id == tid).one()

    assert txn.status == "submitted"
    assert txn.current_stage == "hod"
    assert tid in _ids(approval_service.list_queue(db, hod, "hod"))
    assert tid not in _ids(approval_service.list_queue(db, accountant, "accountant"))

    approval_service.advance(db, hod, tid, "approve", None)
    txn = db.query(ErpExpenseTransaction).filter(ErpExpenseTransaction.transaction_id == tid).one()

    assert txn.status == "submitted"
    assert txn.current_stage == "accountant"
    assert tid not in _ids(approval_service.list_queue(db, hod, "hod"))
    assert tid in _ids(approval_service.list_queue(db, accountant, "accountant"))
