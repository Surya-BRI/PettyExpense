"""Phase A (bill converted to the company's base currency, rate locked at first submit),
Phase B (Accountant / Finance Manager / HOD only see bills of companies they cover, Admin
fallback) and Phase C (the reimbursement payment step).
"""
import os

for _k in ("READER_DB_SERVER", "READER_DB_NAME", "READER_DB_USER", "READER_DB_PASSWORD"):
    os.environ.setdefault(_k, "test")

import importlib  # noqa: E402
import json  # noqa: E402
from datetime import date, timedelta  # noqa: E402

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
    ErpExpenseMultiRegionUserRegion,
    ErpExpensePaymentRecord,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpMasterExpenseRole,
)
from services.approval_service import resolve_stage_approvers  # noqa: E402
from services.fund_service import _tx_amount  # noqa: E402
from services.payment_service import payment_service  # noqa: E402
from services.transaction_service import _stamp_exchange_rate, transaction_service  # noqa: E402

_txn_mod = importlib.import_module("services.transaction_service")

RATES = {("SAR", "AED"): 0.98, ("AED", "SAR"): 1.02, ("OMR", "AED"): 9.54}


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    monkeypatch.setattr(transaction_service, "_notify_finance_on_submit", lambda *a, **k: None)

    def _fake_lookup(bill, base, _date=None, **kwargs):
        b, t = (bill or "").upper(), (base or "").upper()
        if b == t:
            return {"rate": 1.0, "as_of": "2026-10-30", "source": "same_currency"}
        return {"rate": RATES[(b, t)], "as_of": "2026-10-30", "source": "test"}

    monkeypatch.setattr(_txn_mod, "lookup_rate", _fake_lookup)
    yield session
    session.close()


def _roles(db):
    roles = {
        code: ErpMasterExpenseRole(role_code=code, role_name=code)
        for code in ("employee", "hod", "accountant", "finance_manager", "admin")
    }
    db.add_all(roles.values())
    db.flush()
    return roles


def _region(db, code, stages=("accountant", "finance_manager")):
    r = ErpExpenseRegionConfig(
        region_code=code, region_name=code, approval_matrix_json=json.dumps({"stages": list(stages)})
    )
    db.add(r)
    db.flush()
    return r


def _person(db, name, role, region=None, department=None):
    u = ErpAuthExpenseUsers(
        user_name=name, display_name=name, password_hash="x", role_id=role.role_id,
        home_region_id=region.region_id if region else None,
        department_id=department.department_id if department else None,
    )
    db.add(u)
    db.flush()
    return u


def _as(u: ErpAuthExpenseUsers, role: str, region_code=None) -> CurrentUser:
    return CurrentUser(u.user_id, u.display_name, role, region_code=region_code)


@pytest.fixture
def world(db):
    roles = _roles(db)
    uae, ksa = _region(db, "UAE"), _region(db, "KSA")
    sales = ErpExpenseDepartment(department_name="Sales")
    db.add(sales)
    db.flush()
    cat = ErpExpenseCategory(category_name="Travel")
    db.add(cat)
    w = {
        "roles": roles, "uae": uae, "ksa": ksa, "sales": sales, "cat": cat,
        "emp": _person(db, "emp", roles["employee"], uae, sales),
        "acc_uae": _person(db, "acc_uae", roles["accountant"], uae),
        "acc_ksa": _person(db, "acc_ksa", roles["accountant"], ksa),
        "fm_uae": _person(db, "fm_uae", roles["finance_manager"], uae),
        "admin": _person(db, "admin", roles["admin"]),
    }
    db.commit()
    return w


def _claim(db, w, *, currency="SAR", total=1000.0, region="UAE", submit=True, **kw):
    args = dict(
        vendor="Hotel", amount=total, vat_amount=0.0, total_amount=total, currency=currency,
        exchange_rate=None, bill_date="30/10/2026", category_id=w["cat"].category_id,
        region_code=region, project_id=None, op_number=None, bill_number=f"B-{currency}-{total}-{region}",
        remarks=None, receipt_id=None, s3_key=None, submit=submit,
    )
    args.update(kw)
    return transaction_service.create_claim(db, _as(w["emp"], "employee", "UAE"), **args)


def _txn(db, claim) -> ErpExpenseTransaction:
    return db.query(ErpExpenseTransaction).filter(ErpExpenseTransaction.transaction_id == claim["id"]).one()


# -- Phase A: currency -------------------------------------------------------------------


def test_foreign_bill_is_converted_into_company_base_at_submit(db, world):
    claim = _claim(db, world, currency="SAR", total=1000.0)
    assert claim["currency"] == "SAR"
    assert claim["base_currency"] == "AED"
    assert claim["exchange_rate"] == 0.98
    assert claim["exchange_rate_date"] == "2026-10-30"
    assert claim["total_amount_base"] == pytest.approx(980.0)


def test_same_currency_bill_has_rate_one_and_equal_base(db, world):
    claim = _claim(db, world, currency="AED", total=250.0)
    assert claim["exchange_rate"] == 1.0
    assert claim["total_amount_base"] == pytest.approx(250.0)


def test_ksa_company_converts_into_sar(db, world):
    db.add(ErpExpenseMultiRegionUserRegion(user_id=world["emp"].user_id, region_id=world["ksa"].region_id))
    db.commit()
    claim = _claim(db, world, currency="AED", total=100.0, region="KSA")
    assert claim["base_currency"] == "SAR"
    assert claim["total_amount_base"] == pytest.approx(102.0)


def test_fund_math_uses_converted_total(db, world):
    txn = _txn(db, _claim(db, world, currency="SAR", total=1000.0))
    assert _tx_amount(txn, "AED") == pytest.approx(980.0)


def test_rate_stays_locked_through_dispute_edit_and_resubmit(db, world):
    txn = _txn(db, _claim(db, world, currency="SAR", total=1000.0))
    txn.status = "disputed"
    db.commit()
    RATES[("SAR", "AED")] = 0.5
    try:
        out = transaction_service.update_draft(
            db, _as(world["emp"], "employee", "UAE"), txn.transaction_id, {"total_amount": 2000.0, "amount": 2000.0}
        )
        assert out["exchange_rate"] == 0.98
        assert out["total_amount_base"] == pytest.approx(1960.0)
        _stamp_exchange_rate(txn, required=True, keep_locked=True)
        assert txn.exchange_rate == 0.98
    finally:
        RATES[("SAR", "AED")] = 0.98


def test_changing_bill_currency_on_dispute_requotes(db, world):
    txn = _txn(db, _claim(db, world, currency="SAR", total=10.0))
    txn.status = "disputed"
    db.commit()
    out = transaction_service.update_draft(
        db, _as(world["emp"], "employee", "UAE"), txn.transaction_id, {"currency": "OMR"}
    )
    assert out["exchange_rate"] == 9.54
    assert out["total_amount_base"] == pytest.approx(95.4)


def test_employee_cannot_file_under_a_company_not_assigned(db, world):
    with pytest.raises(ValueError, match="own company"):
        _claim(db, world, currency="AED", total=10.0, region="KSA")


# -- Phase B: region-scoped approvers ----------------------------------------------------


def test_ksa_bill_goes_only_to_ksa_accountant(db, world):
    db.add(ErpExpenseMultiRegionUserRegion(user_id=world["emp"].user_id, region_id=world["ksa"].region_id))
    db.commit()
    txn = _txn(db, _claim(db, world, currency="SAR", total=10.0, region="KSA"))
    ids = {u.user_id for u in resolve_stage_approvers(db, txn, "accountant")}
    assert ids == {world["acc_ksa"].user_id}


def test_admin_assigned_region_adds_coverage(db, world):
    db.add(ErpExpenseMultiRegionUserRegion(user_id=world["acc_uae"].user_id, region_id=world["ksa"].region_id))
    db.add(ErpExpenseMultiRegionUserRegion(user_id=world["emp"].user_id, region_id=world["ksa"].region_id))
    db.commit()
    txn = _txn(db, _claim(db, world, currency="SAR", total=10.0, region="KSA"))
    ids = {u.user_id for u in resolve_stage_approvers(db, txn, "accountant")}
    assert ids == {world["acc_ksa"].user_id, world["acc_uae"].user_id}


def test_hod_covers_ksa_only_after_admin_assigns_it(db, world):
    w = world
    hod = _person(db, "hod", w["roles"]["hod"], w["uae"], w["sales"])
    db.add(ErpExpenseHodAssignment(user_id=hod.user_id, department_id=w["sales"].department_id))
    db.add(ErpExpenseMultiRegionUserRegion(user_id=w["emp"].user_id, region_id=w["ksa"].region_id))
    w["ksa"].approval_matrix_json = json.dumps({"stages": ["hod", "accountant"]})
    db.commit()
    txn = _txn(db, _claim(db, w, currency="SAR", total=10.0, region="KSA"))

    assert [u.user_id for u in resolve_stage_approvers(db, txn, "hod")] == [w["admin"].user_id]

    db.add(ErpExpenseMultiRegionUserRegion(user_id=hod.user_id, region_id=w["ksa"].region_id))
    db.commit()
    assert [u.user_id for u in resolve_stage_approvers(db, txn, "hod")] == [hod.user_id]


def test_it_line_needs_it_hod_of_the_bills_company(db, world):
    """Cross-department step is scoped too: an IT HOD of another company doesn't approve
    it (Admin does) until Admin assigns that company to them — the step is never skipped."""
    from services.approval_service import resolve_stage_sequence

    w = world
    it = ErpExpenseDepartment(department_name="IT")
    db.add(it)
    db.flush()
    sales_hod = _person(db, "sales_hod", w["roles"]["hod"], w["uae"], w["sales"])
    it_hod = _person(db, "it_hod", w["roles"]["hod"], w["ksa"], it)
    db.add_all([
        ErpExpenseHodAssignment(user_id=sales_hod.user_id, department_id=w["sales"].department_id),
        ErpExpenseHodAssignment(user_id=it_hod.user_id, department_id=it.department_id),
    ])
    it_kit = ErpExpenseCategory(category_name="IT Equipment", owning_department_id=it.department_id)
    db.add(it_kit)
    w["uae"].approval_matrix_json = json.dumps({"stages": ["hod", "accountant", "finance_manager"]})
    db.commit()
    txn = _txn(db, _claim(db, w, currency="AED", total=50.0, category_id=it_kit.category_id))
    it_stage = f"department_hod:{it.department_id}"

    assert resolve_stage_sequence(db, txn) == ["hod", it_stage, "accountant", "finance_manager"]
    assert [u.user_id for u in resolve_stage_approvers(db, txn, "hod")] == [sales_hod.user_id]
    assert [u.user_id for u in resolve_stage_approvers(db, txn, it_stage)] == [w["admin"].user_id]

    db.add(ErpExpenseMultiRegionUserRegion(user_id=it_hod.user_id, region_id=w["uae"].region_id))
    db.commit()
    assert [u.user_id for u in resolve_stage_approvers(db, txn, it_stage)] == [it_hod.user_id]


def test_empty_role_in_company_falls_back_to_admin(db, world):
    db.add(ErpExpenseMultiRegionUserRegion(user_id=world["emp"].user_id, region_id=world["ksa"].region_id))
    db.commit()
    txn = _txn(db, _claim(db, world, currency="SAR", total=10.0, region="KSA"))
    assert [u.user_id for u in resolve_stage_approvers(db, txn, "finance_manager")] == [world["admin"].user_id]


def test_person_with_no_company_set_still_covers_everything(db, world):
    legacy = _person(db, "legacy_fm", world["roles"]["finance_manager"])
    db.add(ErpExpenseMultiRegionUserRegion(user_id=world["emp"].user_id, region_id=world["ksa"].region_id))
    db.commit()
    txn = _txn(db, _claim(db, world, currency="SAR", total=10.0, region="KSA"))
    assert [u.user_id for u in resolve_stage_approvers(db, txn, "finance_manager")] == [legacy.user_id]


# -- Phase C: payment step ---------------------------------------------------------------


@pytest.fixture
def approved(db, world, monkeypatch):
    sent = []
    monkeypatch.setattr(transaction_service, "_notify_employee", lambda _db, txn, action, _r: sent.append(action))
    txn = _txn(db, _claim(db, world, currency="SAR", total=1000.0))
    txn.status = "approved"
    db.commit()
    return txn, sent


def _pay(db, user, txn_id, **kw):
    args = dict(payment_method="bank_transfer", payment_reference="TRX-1", payment_date=None)
    args.update(kw)
    return payment_service.record_payment(db, user, txn_id, **args)


def test_approved_reimbursement_shows_unpaid(db, world, approved):
    txn, _ = approved
    assert _txn_mod.payment_status(txn) == "unpaid"
    listed = payment_service.list_claims(db, _as(world["fm_uae"], "finance_manager"))
    assert [c["id"] for c in listed["items"]] == [txn.transaction_id]
    assert listed["totals"] == {"AED": pytest.approx(980.0)}


def test_totals_include_old_claims_without_a_stored_base_amount(db, world, approved):
    """A claim approved before base amounts were stored still counts in the totals, with
    the same figure its row shows (bill total x its stamped rate)."""
    txn, _ = approved
    old = _txn(db, _claim(db, world, currency="SAR", total=500.0))
    old.status = "approved"
    old.base_currency = old.amount_base = old.vat_amount_base = old.total_amount_base = None
    db.commit()

    listed = payment_service.list_claims(db, _as(world["fm_uae"], "finance_manager"))
    rows = {c["id"]: c["payable_amount"] for c in listed["items"]}
    assert rows[old.transaction_id] == pytest.approx(490.0)
    assert listed["totals"] == {"AED": pytest.approx(sum(rows.values()))}
    assert listed["totals"]["AED"] == pytest.approx(980.0 + 490.0)


def test_recording_payment_marks_paid_and_notifies_once(db, world, approved):
    txn, sent = approved
    day = (date.today() - timedelta(days=1)).isoformat()
    rec = _pay(db, _as(world["fm_uae"], "finance_manager"), txn.transaction_id, payment_date=day)
    assert rec["amount"] == pytest.approx(980.0)
    assert rec["currency"] == "AED"
    assert rec["payment_date"] == day
    db.refresh(txn)
    assert txn.status == "paid"
    assert _txn_mod.payment_status(txn) == "paid"
    assert sent == ["paid"]
    with pytest.raises(ValueError, match="already been paid"):
        _pay(db, _as(world["fm_uae"], "finance_manager"), txn.transaction_id)
    assert db.query(ErpExpensePaymentRecord).count() == 1


def test_payment_needs_reference_valid_method_and_past_date(db, world, approved):
    txn, _ = approved
    fm = _as(world["fm_uae"], "finance_manager")
    with pytest.raises(ValueError, match="reference"):
        _pay(db, fm, txn.transaction_id, payment_reference="  ")
    with pytest.raises(ValueError, match="Payment method"):
        _pay(db, fm, txn.transaction_id, payment_method="crypto")
    with pytest.raises(ValueError, match="future"):
        _pay(db, fm, txn.transaction_id, payment_date=(date.today() + timedelta(days=2)).isoformat())


def test_petty_cash_and_unapproved_claims_cannot_be_paid(db, world, approved):
    txn, _ = approved
    fm = _as(world["fm_uae"], "finance_manager")
    txn.status = "submitted"
    db.commit()
    with pytest.raises(ValueError, match="Only approved"):
        _pay(db, fm, txn.transaction_id)
    txn.status = "approved"
    txn.type = "petty_cash"
    db.commit()
    with pytest.raises(ValueError, match="Petty cash"):
        _pay(db, fm, txn.transaction_id)


def test_only_the_companys_finance_manager_or_admin_can_pay(db, world, approved):
    txn, _ = approved
    ksa_fm = _person(db, "fm_ksa", world["roles"]["finance_manager"], world["ksa"])
    db.commit()
    with pytest.raises(PermissionError):
        _pay(db, _as(ksa_fm, "finance_manager"), txn.transaction_id)
    assert payment_service.list_claims(db, _as(ksa_fm, "finance_manager"))["items"] == []
    with pytest.raises(PermissionError):
        _pay(db, _as(world["acc_uae"], "accountant"), txn.transaction_id)
    _pay(db, _as(world["admin"], "admin"), txn.transaction_id)


def test_old_mark_paid_route_still_works(db, world, approved):
    txn, sent = approved
    out = transaction_service.mark_paid(db, _as(world["fm_uae"], "finance_manager"), txn.transaction_id, "REF-9")
    assert out["status"] == "paid"
    assert out["payment"]["payment_reference"] == "REF-9"
    assert sent == ["paid"]


def test_paid_email_lists_payment_and_converted_total(db, world, approved):
    from services import email_templates

    txn, _ = approved
    _pay(db, _as(world["fm_uae"], "finance_manager"), txn.transaction_id, payment_reference="TRX-77")
    db.refresh(txn)
    mail = email_templates.paid_email(email_templates.build_context(txn))
    assert "TRX-77" in mail.html and "Bank transfer" in mail.html
    assert "Total in AED" in mail.html
