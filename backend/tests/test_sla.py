"""Approval SLA (PG-10): overdue warning to the approver, escalation to the next step + Admin,
Admin-set time limits, and the Aging report."""
import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    ErpMasterExpenseRole,
)
from services import approval_service, notification_service, sla_service
from services.config_service import config_service


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def fake_email(monkeypatch):
    sent = []

    def fake_notify(to_email, subject, body, html_body=None):
        sent.append((to_email, subject, body))
        return True

    monkeypatch.setattr(notification_service.email_service, "notify", fake_notify)
    return sent


def _role(db, code):
    role = ErpMasterExpenseRole(role_code=code, role_name=code)
    db.add(role)
    db.commit()
    return role


def _user(db, role, email, department_id=None):
    user = ErpAuthExpenseUsers(
        user_name=email, display_name=email, password_hash="x", role_id=role.role_id,
        department_id=department_id, email=email, language_preference="en",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def w(db):
    """Employee -> HOD (24h) -> Finance Manager (48h), plus an Admin."""
    roles = {c: _role(db, c) for c in ("employee", "hod", "finance_manager", "admin")}
    dept = ErpExpenseDepartment(department_name="Sales")
    db.add(dept)
    db.commit()
    employee = _user(db, roles["employee"], "employee@x.com", dept.department_id)
    hod = _user(db, roles["hod"], "hod@x.com", dept.department_id)
    fm = _user(db, roles["finance_manager"], "fm@x.com")
    admin = _user(db, roles["admin"], "admin@x.com")
    db.add(ErpExpenseHodAssignment(user_id=hod.user_id, department_id=dept.department_id))
    region = ErpExpenseRegionConfig(
        region_code="DUBAI",
        region_name="Dubai",
        approval_matrix_json=json.dumps(
            {
                "stages": ["hod", "finance_manager"],
                "sla_hours": {"hod": 24, "finance_manager": 48},
                "bulk_approve_threshold": 500.0,
                "stage_labels": {},
            }
        ),
    )
    category = ErpExpenseCategory(category_name="Fuel")
    db.add_all([region, category])
    db.commit()
    txn = ErpExpenseTransaction(
        employee_id=employee.user_id, region_id=region.region_id, category_id=category.category_id,
        vendor_raw_text="ENOC", currency="AED", amount=150.0, total_amount=150.0, status="submitted",
        submitted_on=datetime.utcnow(),
    )
    db.add(txn)
    db.commit()
    approval_service.resolve_current_approvers(db, txn)  # puts it at the HOD step, starts the clock
    db.refresh(txn)
    return {"db": db, "employee": employee, "hod": hod, "fm": fm, "admin": admin, "region": region, "txn": txn}


def _as(user, role):
    return CurrentUser(user.user_id, user.display_name, role, user.email, user.department_id)


def _in_app(db, prefix):
    return {
        n.user_id
        for n in db.query(ErpExpenseNotification).filter(ErpExpenseNotification.channel == "in_app").all()
        if n.type.startswith(prefix)
    }


def test_clock_starts_at_hod_with_its_time_limit(w):
    txn = w["txn"]
    assert txn.current_stage == "hod"
    assert txn.stage_entered_at is not None
    assert txn.stage_due_at - txn.stage_entered_at == timedelta(hours=24)
    assert txn.sla_state == 0


def test_no_alert_before_the_time_limit(w, fake_email):
    result = sla_service.run_sla_check(w["db"], now=datetime.utcnow() + timedelta(hours=23))
    assert result["warned"] == 0
    assert fake_email == []


def test_warns_the_approver_once_after_the_time_limit(w, fake_email):
    db = w["db"]
    later = datetime.utcnow() + timedelta(hours=25)
    assert sla_service.run_sla_check(db, now=later)["warned"] == 1
    assert _in_app(db, "slaw_") == {w["hod"].user_id}
    assert [e[0] for e in fake_email] == ["hod@x.com"]
    assert "Overdue" in fake_email[0][1]
    db.refresh(w["txn"])
    assert w["txn"].sla_state == sla_service.SLA_WARNED

    fake_email.clear()
    assert sla_service.run_sla_check(db, now=later + timedelta(minutes=5))["warned"] == 0
    assert fake_email == []


def test_escalates_after_another_full_time_limit_to_next_step_and_admin(w, fake_email):
    db = w["db"]
    sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(hours=25))
    fake_email.clear()
    # 47h: past due but not yet one more full 24h period -> nothing new.
    assert sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(hours=47))["escalated"] == 0
    result = sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(hours=49))
    assert result["escalated"] == 1
    assert _in_app(db, "slae_") == {w["fm"].user_id, w["admin"].user_id}
    assert sorted(e[0] for e in fake_email) == ["admin@x.com", "fm@x.com"]
    db.refresh(w["txn"])
    assert w["txn"].sla_state == sla_service.SLA_ESCALATED
    # Escalated once only.
    fake_email.clear()
    sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(hours=60))
    assert fake_email == []


def test_job_down_for_a_while_warns_and_escalates_in_one_run(w):
    result = sla_service.run_sla_check(w["db"], now=datetime.utcnow() + timedelta(hours=50))
    assert result == {"checked": 1, "warned": 1, "escalated": 1}


def test_last_step_escalates_to_admin_only(w):
    db, txn = w["db"], w["txn"]
    approval_service.advance(db, _as(w["hod"], "hod"), txn.transaction_id, "approve", None)
    db.refresh(txn)
    assert txn.current_stage == "finance_manager"
    assert txn.stage_due_at - txn.stage_entered_at == timedelta(hours=48)
    sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(hours=97))
    assert _in_app(db, "slaw_") == {w["fm"].user_id}
    assert _in_app(db, "slae_") == {w["admin"].user_id}


def test_delegated_approver_warning_goes_to_backup(w):
    db = w["db"]
    backup = _user(db, w["hod"].role, "backup@x.com")
    today = datetime.utcnow().date()
    db.add(
        ErpExpenseApproverDelegation(
            approver_id=w["hod"].user_id, backup_id=backup.user_id,
            start_date=(today - timedelta(days=1)).isoformat(), end_date=(today + timedelta(days=5)).isoformat(),
        )
    )
    db.commit()
    sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(hours=25))
    assert _in_app(db, "slaw_") == {backup.user_id}


def test_dispute_stops_the_clock_and_resubmit_restarts_it(w):
    db, txn = w["db"], w["txn"]
    approval_service.advance(db, _as(w["hod"], "hod"), txn.transaction_id, "dispute", "fix the date")
    db.refresh(txn)
    assert txn.stage_due_at is None
    # A disputed bill sits with the employee: never counted as overdue.
    assert sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(days=10))["checked"] == 0

    approval_service.resubmit_after_dispute(db, _as(w["employee"], "employee"), txn.transaction_id)
    db.refresh(txn)
    assert txn.status == "submitted" and txn.current_stage == "hod"
    assert txn.stage_due_at > datetime.utcnow() + timedelta(hours=23)
    assert txn.sla_state == 0


def test_resubmitted_bill_can_be_warned_again(w):
    db, txn = w["db"], w["txn"]
    sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(hours=25))
    assert len(_in_app(db, "slaw_")) == 1
    approval_service.advance(db, _as(w["hod"], "hod"), txn.transaction_id, "dispute", "fix")
    # Make the new visit start at a different second than the first one.
    approval_service.resubmit_after_dispute(db, _as(w["employee"], "employee"), txn.transaction_id)
    db.refresh(txn)
    txn.stage_entered_at = txn.stage_entered_at + timedelta(seconds=5)
    db.commit()
    sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(hours=26))
    warn_types = {
        n.type for n in db.query(ErpExpenseNotification).filter(ErpExpenseNotification.type.like("slaw_%")).all()
    }
    assert len(warn_types) == 2  # a second, separate warning for the second visit


def test_reject_stops_the_clock(w):
    db, txn = w["db"], w["txn"]
    approval_service.advance(db, _as(w["hod"], "hod"), txn.transaction_id, "reject", "not allowed")
    db.refresh(txn)
    assert txn.stage_due_at is None
    assert sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(days=10))["checked"] == 0


def test_admin_sets_time_limit_and_keeps_other_settings(w):
    db, region = w["db"], w["region"]
    result = config_service.update_region_sla(db, region.region_id, {"hod": 0.25})
    by_stage = {s["stage"]: s["hours"] for s in result["stages"]}
    assert by_stage["hod"] == 0.25
    assert by_stage["finance_manager"] == 48
    db.refresh(region)
    saved = json.loads(region.approval_matrix_json)
    assert saved["stages"] == ["hod", "finance_manager"]
    assert saved["bulk_approve_threshold"] == 500.0
    assert saved["sla_hours"] == {"hod": 0.25, "finance_manager": 48}


def test_lowering_the_time_limit_moves_open_bills_due_time(w, fake_email):
    db, txn = w["db"], w["txn"]
    config_service.update_region_sla(db, w["region"].region_id, {"hod": 0.25})
    db.refresh(txn)
    assert txn.stage_due_at - txn.stage_entered_at == timedelta(minutes=15)
    # PG-10: 15 min -> warning, 30 min -> escalation.
    assert sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(minutes=16))["warned"] == 1
    assert sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(minutes=31))["escalated"] == 1


def test_raising_the_time_limit_puts_a_warned_bill_back_on_time(w):
    db, txn = w["db"], w["txn"]
    config_service.update_region_sla(db, w["region"].region_id, {"hod": 0.25})
    sla_service.run_sla_check(db, now=datetime.utcnow() + timedelta(minutes=16))
    db.refresh(txn)
    assert txn.sla_state == sla_service.SLA_WARNED
    config_service.update_region_sla(db, w["region"].region_id, {"hod": 24})
    db.refresh(txn)
    assert txn.sla_state == sla_service.SLA_ON_TIME


@pytest.mark.parametrize("bad", [{"hod": 0.01}, {"hod": 24 * 31}, {"accountant": 5}])
def test_rejects_bad_time_limits(w, bad):
    with pytest.raises(ValueError):
        config_service.update_region_sla(w["db"], w["region"].region_id, bad)


def test_sla_settings_list_the_company_steps(w):
    stages = [s["stage"] for s in config_service.region_sla(w["db"], w["region"].region_id)["stages"]]
    # Department split is on by default, so the other-department HOD step is listed too.
    assert stages == ["hod", "department_hod", "finance_manager"]


def test_aging_report_states_and_buckets(w):
    db, txn = w["db"], w["txn"]
    report = sla_service.aging_report(db)
    assert report["summary"]["pending"] == 1
    item = report["items"][0]
    assert item["sla_status"] == "on_time"
    assert item["age_bucket"] == "under_1_day"
    assert item["approvers"] == ["hod@x.com"]
    assert item["stage_label"] == "Sales HOD"

    # Two days at the HOD step with a 24h limit: breached and past one more period.
    txn.stage_entered_at = datetime.utcnow() - timedelta(days=2, hours=1)
    txn.stage_due_at = txn.stage_entered_at + timedelta(hours=24)
    db.commit()
    item = sla_service.aging_report(db)["items"][0]
    assert item["sla_status"] == "escalated"
    assert item["age_bucket"] == "1_3_days"
    assert item["overdue_minutes"] >= 25 * 60

    txn.stage_entered_at = datetime.utcnow() - timedelta(hours=30)
    txn.stage_due_at = txn.stage_entered_at + timedelta(hours=24)
    txn.sla_state = 1
    db.commit()
    report = sla_service.aging_report(db, region_id=w["region"].region_id)
    assert report["items"][0]["sla_status"] == "breached"
    assert report["summary"]["breached"] == 1
    assert sla_service.aging_report(db, region_id=999)["items"] == []


def test_format_duration():
    assert sla_service.format_duration(timedelta(minutes=14)) == "14 min"
    assert sla_service.format_duration(timedelta(hours=1)) == "1 hr"
    assert sla_service.format_duration(timedelta(hours=5, minutes=20)) == "5 hrs 20 min"
    assert sla_service.format_duration(timedelta(days=2, hours=3)) == "51 hrs"
