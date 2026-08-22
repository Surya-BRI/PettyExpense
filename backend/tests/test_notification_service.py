import json
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import (
    Base,
    ErpAuthExpenseUsers,
    ErpExpenseApproverDelegation,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseNotification,
    ErpExpenseNotificationPreference,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpExpenseVendor,
    ErpMasterExpenseRole,
)
from services import approval_service, notification_service


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _role(db, code):
    role = ErpMasterExpenseRole(role_code=code, role_name=code)
    db.add(role)
    db.commit()
    return role


def _user(db, role, email, department_id=None, language_preference="en"):
    user = ErpAuthExpenseUsers(
        user_name=email,
        display_name=email,
        password_hash="x",
        role_id=role.role_id,
        department_id=department_id,
        email=email,
        language_preference=language_preference,
    )
    db.add(user)
    db.commit()
    return user


def _region(db, stages):
    region = ErpExpenseRegionConfig(
        region_code="UAE",
        region_name="UAE",
        approval_matrix_json=json.dumps({"stages": stages, "sla_hours": {}, "bulk_approve_threshold": 500.0}),
    )
    db.add(region)
    db.commit()
    return region


@pytest.fixture
def scenario(db):
    # employee -> hod -> finance_manager, a real sequential chain, not a flat "everyone" broadcast.
    employee_role = _role(db, "employee")
    hod_role = _role(db, "hod")
    finance_role = _role(db, "finance_manager")
    dept = ErpExpenseDepartment(department_name="Sales")
    db.add(dept)
    db.commit()
    employee = _user(db, employee_role, "employee@example.com", department_id=dept.department_id)
    hod = _user(db, hod_role, "hod@example.com", department_id=dept.department_id)
    finance = _user(db, finance_role, "finance@example.com")
    from database.models import ErpExpenseHodAssignment

    db.add(ErpExpenseHodAssignment(user_id=hod.user_id, department_id=dept.department_id))
    region = _region(db, ["hod", "finance_manager"])
    category = ErpExpenseCategory(category_name="Travel")
    db.add(category)
    vendor = ErpExpenseVendor(vendor_name="Acme")
    db.add(vendor)
    db.commit()
    txn = ErpExpenseTransaction(
        employee_id=employee.user_id,
        region_id=region.region_id,
        category_id=category.category_id,
        vendor_id=vendor.vendor_id,
        currency="AED",
        amount=100.0,
        total_amount=100.0,
        status="submitted",
    )
    db.add(txn)
    db.commit()
    return {"employee": employee, "hod": hod, "finance": finance, "txn": txn}


@pytest.fixture(autouse=True)
def fake_email(monkeypatch):
    sent = []

    def fake_notify(to_email, subject, body):
        sent.append((to_email, subject, body))
        return True

    monkeypatch.setattr(notification_service.email_service, "notify", fake_notify)
    return sent


def test_submit_notifies_only_the_current_stage_approver_not_everyone(db, scenario, fake_email):
    txn = scenario["txn"]
    approver = approval_service.resolve_current_approver(db, txn)
    assert approver.user_id == scenario["hod"].user_id  # the bug this fixes: finance must not hear about a claim at hod stage
    notification_service.send(db, approver, "submission", txn.transaction_id, "s-en", "s-ar", "b-en", "b-ar")
    assert len(fake_email) == 1
    assert fake_email[0][0] == "hod@example.com"


def test_approve_advances_to_next_stage_approver(db, scenario, fake_email):
    from auth.security import CurrentUser

    txn = scenario["txn"]
    hod_user = CurrentUser(scenario["hod"].user_id, "hod", "hod", "hod@example.com", scenario["hod"].department_id)
    approval_service.advance(db, hod_user, txn.transaction_id, "approve", None)
    next_approver = approval_service.resolve_current_approver(db, txn)
    assert next_approver.user_id == scenario["finance"].user_id


def test_approve_on_last_stage_notifies_employee_not_an_approver(db, scenario, fake_email):
    from auth.security import CurrentUser

    txn = scenario["txn"]
    hod_user = CurrentUser(scenario["hod"].user_id, "hod", "hod", "hod@example.com", scenario["hod"].department_id)
    finance_user = CurrentUser(scenario["finance"].user_id, "finance", "finance_manager", "finance@example.com")
    approval_service.advance(db, hod_user, txn.transaction_id, "approve", None)
    fake_email.clear()
    approval_service.advance(db, finance_user, txn.transaction_id, "approve", None)
    assert len(fake_email) == 1
    assert fake_email[0][0] == "employee@example.com"


def test_reject_notifies_employee_with_comment(db, scenario, fake_email):
    from auth.security import CurrentUser

    txn = scenario["txn"]
    hod_user = CurrentUser(scenario["hod"].user_id, "hod", "hod", "hod@example.com", scenario["hod"].department_id)
    approval_service.advance(db, hod_user, txn.transaction_id, "reject", "missing invoice")
    assert len(fake_email) == 1
    assert fake_email[0][0] == "employee@example.com"
    assert "missing invoice" in fake_email[0][2]


def test_dispute_notifies_employee_with_comment(db, scenario, fake_email):
    from auth.security import CurrentUser

    txn = scenario["txn"]
    hod_user = CurrentUser(scenario["hod"].user_id, "hod", "hod", "hod@example.com", scenario["hod"].department_id)
    approval_service.advance(db, hod_user, txn.transaction_id, "dispute", "wrong amount")
    assert len(fake_email) == 1
    assert fake_email[0][0] == "employee@example.com"
    assert "wrong amount" in fake_email[0][2]


def test_resubmit_notifies_the_same_approver_that_disputed_it(db, scenario, fake_email):
    from auth.security import CurrentUser

    txn = scenario["txn"]
    hod_user = CurrentUser(scenario["hod"].user_id, "hod", "hod", "hod@example.com", scenario["hod"].department_id)
    employee_user = CurrentUser(scenario["employee"].user_id, "employee", "employee", "employee@example.com")
    approval_service.advance(db, hod_user, txn.transaction_id, "dispute", "fix this")
    fake_email.clear()
    approval_service.resubmit_after_dispute(db, employee_user, txn.transaction_id)
    assert len(fake_email) == 1
    assert fake_email[0][0] == "hod@example.com"  # same stage, not restarted from the top


def test_delegation_redirects_to_backup(db, scenario, fake_email):
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    backup = _user(db, scenario["hod"].role, "backup@example.com")
    db.add(
        ErpExpenseApproverDelegation(
            approver_id=scenario["hod"].user_id, backup_id=backup.user_id, start_date=today, end_date=tomorrow
        )
    )
    db.commit()
    approver = approval_service.resolve_current_approver(db, scenario["txn"])
    assert approver.user_id == backup.user_id


def test_idempotent_send_does_not_duplicate(db, scenario, fake_email):
    txn = scenario["txn"]
    hod = scenario["hod"]
    notification_service.send(db, hod, "submission", txn.transaction_id, "s", "s", "b", "b")
    notification_service.send(db, hod, "submission", txn.transaction_id, "s", "s", "b", "b")
    assert len(fake_email) == 1
    rows = db.query(ErpExpenseNotification).filter(ErpExpenseNotification.transaction_id == txn.transaction_id).all()
    assert len(rows) == 2  # one email row + one in_app row, never doubled


def test_disabled_preference_skips_that_channel_only(db, scenario, fake_email):
    txn = scenario["txn"]
    hod = scenario["hod"]
    db.add(ErpExpenseNotificationPreference(user_id=hod.user_id, channel="email", category="submission", is_enabled=0))
    db.commit()
    notification_service.send(db, hod, "submission", txn.transaction_id, "s", "s", "b", "b")
    assert len(fake_email) == 0
    rows = db.query(ErpExpenseNotification).filter(ErpExpenseNotification.transaction_id == txn.transaction_id).all()
    assert len(rows) == 1
    assert rows[0].channel == "in_app"


def test_arabic_preference_picks_arabic_content(db, scenario, fake_email):
    txn = scenario["txn"]
    hod = scenario["hod"]
    hod.language_preference = "ar"
    db.commit()
    notification_service.send(db, hod, "submission", txn.transaction_id, "English subject", "Arabic subject", "English body", "Arabic body")
    assert fake_email[0][1] == "Arabic subject"
    assert fake_email[0][2] == "Arabic body"


def test_notify_failure_never_raises(db, scenario, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("Graph is down")

    monkeypatch.setattr(notification_service.email_service, "notify", boom)
    notification_service.send(db, scenario["hod"], "submission", scenario["txn"].transaction_id, "s", "s", "b", "b")
    row = (
        db.query(ErpExpenseNotification)
        .filter(ErpExpenseNotification.channel == "in_app", ErpExpenseNotification.user_id == scenario["hod"].user_id)
        .first()
    )
    assert row is not None  # in_app still recorded even though the email channel raised


def test_in_app_list_read_and_unread_count(db, scenario, fake_email):
    txn = scenario["txn"]
    hod = scenario["hod"]
    notification_service.send(db, hod, "submission", txn.transaction_id, "s", "s", "b", "b")
    assert notification_service.unread_count(db, hod.user_id) == 1
    rows = notification_service.list_for_user(db, hod.user_id)
    assert len(rows) == 1
    notification_service.mark_read(db, hod.user_id, rows[0].notification_id)
    assert notification_service.unread_count(db, hod.user_id) == 0


def test_send_test_bypasses_idempotency(db, scenario, fake_email):
    hod = scenario["hod"]
    notification_service.send_test(db, hod, "email", "subject", "body")
    notification_service.send_test(db, hod, "email", "subject", "body")
    assert len(fake_email) == 2  # unlike send(), a test send always attempts delivery
