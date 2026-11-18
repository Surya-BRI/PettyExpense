"""Backup approvers (Spec 5.2): set by Admin or by the approver, bills route to the backup
during the dates, and the backup can act on them from their own queue."""
import json
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth.security import CurrentUser
from database.models import (
    Base,
    ErpAuthExpenseUsers,
    ErpExpenseApproverDelegation,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseHodAssignment,
    ErpExpenseNotification,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpExpenseVendor,
    ErpMasterExpenseRole,
)
from services import approval_service, delegation_service, notification_service


@pytest.fixture
def db():
    # One shared connection usable from TestClient's worker thread too.
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def fake_email(monkeypatch):
    sent = []
    monkeypatch.setattr(
        notification_service.email_service, "notify", lambda to, s, b, html_body=None: sent.append((to, s)) or True
    )
    return sent


def _region(db, code, stages):
    r = ErpExpenseRegionConfig(
        region_code=code,
        region_name=code,
        approval_matrix_json=json.dumps({"stages": stages, "sla_hours": {}, "bulk_approve_threshold": 500.0}),
    )
    db.add(r)
    db.commit()
    return r


@pytest.fixture
def ksa(db):
    """Professional Signs style: Employee -> HOD -> Accounts Manager (finance_manager)."""
    roles = {}
    for code in ("employee", "hod", "finance_manager", "accountant", "admin"):
        roles[code] = ErpMasterExpenseRole(role_code=code, role_name=code)
        db.add(roles[code])
    region = _region(db, "KSA", ["hod", "finance_manager"])
    other = _region(db, "DUBAI", ["hod", "accountant", "finance_manager"])
    sales = ErpExpenseDepartment(department_name="Sales")
    it = ErpExpenseDepartment(department_name="IT")
    db.add_all([sales, it])
    db.commit()

    def user(name, role, dept=None, region_id=region.region_id):
        u = ErpAuthExpenseUsers(
            user_name=name, display_name=name, password_hash="x", role_id=roles[role].role_id,
            department_id=dept.department_id if dept else None, email=f"{name}@x.com", home_region_id=region_id,
        )
        db.add(u)
        db.commit()
        return u

    s = {
        "employee": user("emp", "employee", sales),
        "hod": user("salesHod", "hod", sales),
        "it_hod": user("itHod", "hod", it),
        "hod2": user("salesHod2", "hod", sales),
        "accountant": user("ksaAccountant", "accountant"),
        "am": user("accountsMgr", "finance_manager"),
        "dubai_hod": user("dubaiHod", "hod", sales, region_id=other.region_id),
        "region": region,
    }
    db.add(ErpExpenseHodAssignment(user_id=s["hod"].user_id, department_id=sales.department_id))
    db.add(ErpExpenseHodAssignment(user_id=s["it_hod"].user_id, department_id=it.department_id))
    db.add(ErpExpenseHodAssignment(user_id=s["hod2"].user_id, department_id=sales.department_id))
    category = ErpExpenseCategory(category_name="Food")
    vendor = ErpExpenseVendor(vendor_name="Acme")
    db.add_all([category, vendor])
    db.commit()
    txn = ErpExpenseTransaction(
        employee_id=s["employee"].user_id, region_id=region.region_id, currency="SAR",
        category_id=category.category_id, vendor_id=vendor.vendor_id,
        amount=100.0, total_amount=100.0, status="submitted",
    )
    db.add(txn)
    db.commit()
    s["txn"] = txn
    return s


def _cu(u, role):
    return CurrentUser(u.user_id, u.display_name, role, u.email, u.department_id)


def _days(n):
    return (date.fromisoformat(delegation_service.today()) + timedelta(days=n)).isoformat()


def test_backup_gets_the_bill_and_can_approve_it_then_it_goes_back(db, ksa):
    # The Sales department's second HOD is dropped here so salesHod is the only one on the bill.
    db.query(ErpExpenseHodAssignment).filter(ErpExpenseHodAssignment.user_id == ksa["hod2"].user_id).delete()
    db.commit()
    hod, backup, txn = ksa["hod"], ksa["accountant"], ksa["txn"]
    d = delegation_service.create(db, hod.user_id, backup.user_id, _days(0), _days(3))
    assert d["is_active"] and d["backup"]["display_name"] == "ksaAccountant"

    # Routed to the backup, not the HOD on leave.
    assert [a.user_id for a in approval_service.resolve_current_approvers(db, txn)] == [backup.user_id]
    queue = approval_service.list_queue(db, _cu(backup, "accountant"), "accountant")
    assert [r["id"] for r in queue] == [txn.transaction_id]
    assert queue[0]["covering_for"] == ["salesHod"]
    assert approval_service.list_queue(db, _cu(hod, "hod"), "hod") == []

    # Removing the backup sends it straight back.
    delegation_service.remove(db, d["id"], approver_id=hod.user_id)
    assert [a.user_id for a in approval_service.resolve_current_approvers(db, txn)] == [hod.user_id]


def test_backup_with_a_different_role_sees_the_bill_in_their_own_queue(db, ksa):
    """Accounts Manager covers the HOD: the bill is at the HOD step, but the Accounts Manager's
    app only opens the finance_manager queue -- it must show there and be approvable."""
    hod, am, txn = ksa["hod"], ksa["am"], ksa["txn"]
    delegation_service.create(db, hod.user_id, am.user_id, _days(0), _days(1))

    queue = approval_service.list_queue(db, _cu(am, "finance_manager"), "finance_manager")
    assert [r["id"] for r in queue] == [txn.transaction_id]
    assert queue[0]["covering_for"] == ["salesHod"]

    approval_service.advance(db, _cu(am, "finance_manager"), txn.transaction_id, "approve", None)
    db.refresh(txn)
    assert txn.current_stage == "finance_manager"
    # Now at the Accounts Manager's own step: listed normally, no "covering" tag, no duplicate.
    queue = approval_service.list_queue(db, _cu(am, "finance_manager"), "finance_manager")
    assert [r["id"] for r in queue] == [txn.transaction_id]
    assert "covering_for" not in queue[0]


def test_future_backup_does_not_route_yet(db, ksa):
    delegation_service.create(db, ksa["hod"].user_id, ksa["accountant"].user_id, _days(2), _days(4))
    assert ksa["accountant"].user_id not in {
        a.user_id for a in approval_service.resolve_current_approvers(db, ksa["txn"])
    }
    assert approval_service.list_queue(db, _cu(ksa["accountant"], "accountant"), "accountant") == []


def test_backup_must_be_same_level_or_higher(db, ksa):
    # Finance Manager (top level): only other Finance Managers -- here there are none in KSA.
    assert delegation_service.candidates(db, ksa["am"].user_id) == []
    with pytest.raises(ValueError, match="same level or higher"):
        delegation_service.create(db, ksa["am"].user_id, ksa["hod"].user_id, _days(0), _days(1))
    # Accountant: Accountant and above, never an HOD.
    assert {c["display_name"] for c in delegation_service.candidates(db, ksa["accountant"].user_id)} == {
        "accountsMgr"
    }


def test_backup_is_told(db, ksa, fake_email):
    d = delegation_service.create(db, ksa["hod"].user_id, ksa["am"].user_id, _days(0), _days(1))
    assert ("accountsMgr@x.com", "You are the backup approver for salesHod") in fake_email
    rows = db.query(ErpExpenseNotification).filter(ErpExpenseNotification.type == f"delegation_{d['id']}").all()
    assert {r.channel for r in rows} == {"email", "in_app"}


@pytest.mark.parametrize(
    "backup_key, start, end, message",
    [
        ("hod", 0, 1, "someone else"),
        ("employee", 0, 1, "same company"),
        ("dubai_hod", 0, 1, "same company"),
        ("it_hod", 0, 1, "same department"),
        ("hod2", 2, 1, "on or after the start date"),
        ("hod2", -3, -1, "already passed"),
    ],
)
def test_bad_backups_are_refused(db, ksa, backup_key, start, end, message):
    with pytest.raises(ValueError, match=message):
        delegation_service.create(db, ksa["hod"].user_id, ksa[backup_key].user_id, _days(start), _days(end))


def test_overlapping_dates_are_refused(db, ksa):
    delegation_service.create(db, ksa["hod"].user_id, ksa["hod2"].user_id, _days(0), _days(5))
    with pytest.raises(ValueError, match="already has a backup"):
        delegation_service.create(db, ksa["hod"].user_id, ksa["am"].user_id, _days(3), _days(7))
    # Right after it ends is fine.
    delegation_service.create(db, ksa["hod"].user_id, ksa["am"].user_id, _days(6), _days(7))


def test_employee_cannot_have_a_backup(db, ksa):
    with pytest.raises(ValueError, match="can have a backup"):
        delegation_service.create(db, ksa["employee"].user_id, ksa["hod"].user_id, _days(0), _days(1))


def test_approver_can_only_remove_their_own_backup(db, ksa):
    d = delegation_service.create(db, ksa["hod"].user_id, ksa["hod2"].user_id, _days(0), _days(1))
    with pytest.raises(LookupError):
        delegation_service.remove(db, d["id"], approver_id=ksa["hod2"].user_id)
    assert db.query(ErpExpenseApproverDelegation).count() == 1


def test_candidates_are_other_approvers_in_the_same_company(db, ksa):
    names = {c["display_name"] for c in delegation_service.candidates(db, ksa["hod"].user_id)}
    assert names == {"salesHod2", "ksaAccountant", "accountsMgr"}


def test_list_hides_finished_backups(db, ksa):
    db.add(
        ErpExpenseApproverDelegation(
            approver_id=ksa["hod"].user_id, backup_id=ksa["hod2"].user_id, start_date=_days(-5), end_date=_days(-1)
        )
    )
    db.commit()
    delegation_service.create(db, ksa["hod"].user_id, ksa["am"].user_id, _days(0), _days(1))
    assert [d["backup"]["display_name"] for d in delegation_service.list_for(db, ksa["hod"].user_id)] == ["accountsMgr"]


def test_my_backup_endpoints(db, ksa, monkeypatch):
    from fastapi.testclient import TestClient

    from auth.security import get_current_user
    from database.models import get_db
    from main import app

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: _cu(ksa["hod"], "hod")
    try:
        client = TestClient(app)
        r = client.get("/api/approvals/backup")
        assert r.status_code == 200
        assert {c["display_name"] for c in r.json()["candidates"]} == {"salesHod2", "ksaAccountant", "accountsMgr"}

        r = client.post(
            "/api/approvals/backup",
            json={"backup_id": ksa["am"].user_id, "start_date": _days(0), "end_date": _days(2)},
        )
        assert r.status_code == 200, r.text
        bid = r.json()["id"]

        r = client.post(
            "/api/approvals/backup",
            json={"backup_id": ksa["hod2"].user_id, "start_date": _days(1), "end_date": _days(2)},
        )
        assert r.status_code == 422 and "already has a backup" in r.json()["detail"]

        assert client.delete(f"/api/approvals/backup/{bid}").status_code == 200
        assert client.get("/api/approvals/backup").json()["backups"] == []
    finally:
        app.dependency_overrides.clear()
