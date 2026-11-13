"""Blue Rhine Contracting (UAE) site petty cash -- "PCA – Replenishment Process" (BRC).

No HODs. One petty cash per employee (for all their sites), set by the Accountant.
Bills (each naming its site's OP code): Employee -> Accountant -> Head of Accountant -> Finance
Manager; petty-cash bills come off the employee's petty cash.
Top-up: Accountant prepares from approved bills -> Head of Accountant approves -> Finance
Manager approves and records the bank withdrawal -> pot back to its limit.
"""
import json

import pytest

from auth.security import CurrentUser, mapped_app_role
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseCategory,
    ErpExpenseLineItem,
    ErpExpenseMultiRegionUserRegion,
    ErpExpenseTransaction,
    ErpMasterExpenseRole,
)
from services import approval_service
from services import fund_service as fund_module
from services.config_service import config_service
from services.fund_service import check_low_funds_for_bill, fund_service
from services.region_policy import SITE_PCA_SETTINGS, apply_site_settings, is_site_model, pca_model
from services.site_pca_service import site_pca_service as site
from tests.test_funds_and_regions import _setup, db  # noqa: F401  (db fixture)


@pytest.fixture
def sent(monkeypatch):
    out = []
    monkeypatch.setattr(
        fund_module, "send",
        lambda _db, user, type_, _txn, **kw: out.append((user.user_name, type_, kw["subject_en"])),
    )
    return out


@pytest.fixture
def w(db):  # noqa: F811
    employee, hod, admin, fm, uae, ksa, sales, accountant = _setup(db)
    uae.approval_matrix_json = json.dumps(SITE_PCA_SETTINGS)
    uae.base_currency = "AED"
    head_role = ErpMasterExpenseRole(role_code="head_accountant", role_name="Head of Accountant")
    db.add(head_role)
    db.flush()
    head = ErpAuthExpenseUsers(user_name="roshan", display_name="Roshan Head", password_hash="x", role_id=head_role.role_id)
    other = ErpAuthExpenseUsers(
        user_name="aisha", display_name="Aisha Site", password_hash="x",
        role_id=employee.role_id, department_id=sales.department_id,
    )
    food = ErpExpenseCategory(category_name="Food")
    db.add_all([head, other, food])
    db.flush()
    # BRC people: Surya's home company is BRC; Aisha is ticked for BRC in People.
    employee.home_region_id = uae.region_id
    db.add(ErpExpenseMultiRegionUserRegion(user_id=other.user_id, region_id=uae.region_id, is_active=1))
    db.commit()
    head.role = head_role
    return dict(employee=employee, other=other, hod=hod, admin=admin, fm=fm, accountant=accountant,
                head=head, uae=uae, ksa=ksa, food=food)


def _cu(u: ErpAuthExpenseUsers) -> CurrentUser:
    return CurrentUser(u.user_id, u.display_name, u.role.role_code, None, u.department_id, "UAE")


def _set(db, w, amount=5000, employee=None, by=None):  # noqa: F811
    return site.set_pot(db, by or w["accountant"], region_id=w["uae"].region_id,
                        employee_id=(employee or w["employee"]).user_id, amount=amount)


def _bill(db, w, amount, op="OP-100", status="approved", lines=None, employee=None):  # noqa: F811
    tx = ErpExpenseTransaction(
        employee_id=(employee or w["employee"]).user_id, region_id=w["uae"].region_id,
        category_id=w["food"].category_id, type="petty_cash", status=status,
        amount=amount, total_amount=amount, currency="AED", base_currency="AED", total_amount_base=amount,
        op_number=op,
    )
    db.add(tx)
    db.flush()
    for i, (line_op, line_amount) in enumerate(lines or [], start=1):
        db.add(ErpExpenseLineItem(transaction_id=tx.transaction_id, line_no=i, description=f"item {i}",
                                  amount=line_amount, op_number=line_op, category_id=w["food"].category_id))
    db.commit()
    db.refresh(tx)
    return tx


def _pot(db, w, employee=None):  # noqa: F811
    pot = fund_service.employee_advance(db, (employee or w["employee"]).user_id, w["uae"].region_id)
    return fund_module.fund_to_dict(db, pot)


def _check(db, w, tx):  # noqa: F811
    fund_service.require_bill_within_limits(db, w["employee"], tx, "AED")


# ---- company settings and roles ----------------------------------------------------------


def test_seed_switches_uae_to_site_model_and_moves_hod_bills_to_the_accountant(db, w):  # noqa: F811
    uae = w["uae"]
    uae.approval_matrix_json = json.dumps({"stages": ["hod", "accountant", "finance_manager"]})
    waiting = _bill(db, w, 100, status="submitted")
    waiting.current_stage = "hod"
    db.commit()
    assert apply_site_settings(uae)
    assert (pca_model(uae), is_site_model(uae)) == ("site", True)
    assert json.loads(uae.approval_matrix_json)["stages"] == ["accountant", "head_accountant", "finance_manager"]
    assert approval_service.realign_open_bills(db, uae.region_id) == 1
    assert waiting.current_stage == "accountant"
    assert not apply_site_settings(uae)  # second start-up: nothing to change


def test_head_of_accountant_role_from_erp_name_or_admin(db, w):  # noqa: F811
    assert mapped_app_role(555, "Head of Accounts") == "head_accountant"
    assert mapped_app_role(555, "Accountant") == "employee"  # by id (102055) only
    out = config_service.set_user_role(db, w["other"].user_id, "head_accountant", set_by=w["admin"].user_id)
    assert out["role"] == "head_accountant"
    with pytest.raises(ValueError, match="Role must be"):
        config_service.set_user_role(db, w["other"].user_id, "admin", set_by=w["admin"].user_id)
    with pytest.raises(ValueError, match="own role"):
        config_service.set_user_role(db, w["admin"].user_id, "employee", set_by=w["admin"].user_id)


def test_bill_goes_accountant_then_head_of_accountant_then_finance_manager(db, w):  # noqa: F811
    _set(db, w, amount=5000)
    tx = _bill(db, w, 1000, status="submitted")
    assert approval_service.resolve_stage_sequence(db, tx) == ["accountant", "head_accountant", "finance_manager"]
    assert approval_service.resolve_stage_labels(tx)["head_accountant"] == "Head of Accountant"
    tx.current_stage = "accountant"
    db.commit()
    for approver, stage in [(w["accountant"], "accountant"), (w["head"], "head_accountant"), (w["fm"], "finance_manager")]:
        assert [a.user_id for a in approval_service.resolve_stage_approvers(db, tx, stage)] == [approver.user_id]
        with pytest.raises(PermissionError):
            approval_service.advance(db, _cu(w["hod"]), tx.transaction_id, "approve", None)
        approval_service.advance(db, _cu(approver), tx.transaction_id, "approve", None)
        tx = db.get(ErpExpenseTransaction, tx.transaction_id)
    assert tx.status == "approved"
    assert _pot(db, w)["available"] == 4000  # PDF: 5,000 - 1,000


# ---- pots --------------------------------------------------------------------------------


def test_accountant_sets_one_petty_cash_per_employee(db, w, sent):  # noqa: F811
    with pytest.raises(PermissionError):
        _set(db, w, by=w["hod"])  # the Head of Accountant may (see the test below); an HOD may not
    out = _set(db, w, amount=5000)
    assert (out["kind"], out["status"], out["amount"]) == ("advance", "set", 5000)
    assert (out["fund"]["approved_limit"], out["fund"]["label"]) == (5000, "Surya Sales · petty cash")
    _set(db, w, amount=2000, employee=w["other"])
    assert [(p["employee_name"], p["approved_limit"]) for p in site.pots(db, w["employee"])] == [("Surya Sales", 5000)]
    assert len(site.pots(db, w["accountant"], w["uae"].region_id)) == 2
    assert len(site.pots(db, w["head"], w["uae"].region_id)) == 2
    people = {p["id"]: p["advance"] for p in site.people(db, w["accountant"], w["uae"].region_id)}
    assert people[w["employee"].user_id] == 5000
    # Changing it sets the new total (same fund) and logs the change.
    again = _set(db, w, amount=6000)
    assert again["fund"]["id"] == out["fund"]["id"]
    assert (again["amount"], again["history"][0]["comment"]) == (1000, "Set to AED 6,000.00 (was 5,000.00)")
    assert ("surya", f"pca_site_set_{out['id']}", "Your petty cash") in sent
    with pytest.raises(ValueError, match="already"):
        _set(db, w, amount=6000)


def test_accountant_sees_only_brc_people(db, w):  # noqa: F811
    # In the list: home company BRC (Surya) and ticked for BRC (Aisha). Not in it: Admin,
    # people with no company recorded (Priya HOD, Meera FM, the Accountant, Roshan) and
    # people of another company only.
    ksa_only = ErpAuthExpenseUsers(user_name="omar", display_name="Omar KSA", password_hash="x",
                                   role_id=w["employee"].role_id, home_region_id=w["ksa"].region_id)
    db.add(ksa_only)
    w["admin"].home_region_id = w["uae"].region_id
    db.commit()
    names = [p["display_name"] for p in site.people(db, w["accountant"], w["uae"].region_id)]
    assert names == ["Aisha Site", "Surya Sales"]
    for outsider in (ksa_only, w["hod"], w["admin"]):
        with pytest.raises(ValueError, match="isn't in this company"):
            _set(db, w, employee=outsider)


def test_head_of_accountant_sets_petty_cash_but_does_not_prepare_top_ups(db, w, sent):  # noqa: F811
    out = _set(db, w, amount=3000, by=w["head"])
    assert _pot(db, w)["opening_balance"] == 3000
    _bill(db, w, 500)
    with pytest.raises(PermissionError, match="prepare a top-up"):
        site.request_topup(db, w["head"], out["fund"]["id"], [], None)
    for outsider in ("fm", "employee"):
        with pytest.raises(PermissionError, match="Head of Accountant or Admin can set"):
            _set(db, w, amount=4000, by=w[outsider])


def test_employees_list_and_an_employees_bills(db, w):  # noqa: F811
    # Accounts at every level (and Admin) see the company's people; an employee doesn't.
    for viewer in ("accountant", "head", "fm", "admin"):
        assert [p["display_name"] for p in site.people(db, w[viewer], w["uae"].region_id)] == ["Aisha Site", "Surya Sales"]
    with pytest.raises(PermissionError):
        site.people(db, w["employee"], w["uae"].region_id)
    # One employee's bills in this company, newest first, no drafts; not another company's.
    first = _bill(db, w, 100)
    second = _bill(db, w, 200, status="submitted")
    _bill(db, w, 300, status="draft")
    other = _bill(db, w, 400, employee=w["other"])
    elsewhere = _bill(db, w, 500)
    elsewhere.region_id = w["ksa"].region_id
    db.commit()
    ids = [b["id"] for b in site.employee_bills(db, w["accountant"], w["uae"].region_id, w["employee"].user_id)]
    assert ids == [second.transaction_id, first.transaction_id]
    assert len(site.employee_bills(db, w["employee"], w["uae"].region_id, w["employee"].user_id)) == 2  # own
    with pytest.raises(PermissionError):
        site.employee_bills(db, w["employee"], w["uae"].region_id, w["other"].user_id)
    assert [b["id"] for b in site.employee_bills(db, w["head"], w["uae"].region_id, w["other"].user_id)] == [
        other.transaction_id
    ]


def test_pot_cannot_go_below_bills_not_topped_up(db, w):  # noqa: F811
    _set(db, w, amount=5000)
    _bill(db, w, 1500)
    _bill(db, w, 500, status="submitted")
    with pytest.raises(ValueError, match="2,000.00"):
        _set(db, w, amount=1999)
    _set(db, w, amount=2000)


def test_bill_must_fit_the_employees_petty_cash(db, w):  # noqa: F811
    with pytest.raises(ValueError, match="don't have petty cash"):
        _check(db, w, _bill(db, w, 100, status="draft"))
    _set(db, w, amount=1000)
    _check(db, w, _bill(db, w, 600, op="OP-999", status="draft"))  # any site
    _bill(db, w, 600, status="submitted")  # in approval: reserved
    with pytest.raises(ValueError, match="400.00 left"):
        _check(db, w, _bill(db, w, 600, status="draft"))


def test_bills_on_any_site_come_off_the_one_petty_cash(db, w):  # noqa: F811
    _set(db, w, amount=2000)
    _bill(db, w, 300, op="OP-100")
    _bill(db, w, 900, op="OP-100", lines=[("OP-100", 300), ("OP-200", 600)])
    pot = _pot(db, w)
    assert (pot["spent"], pot["available"]) == (1200, 800)


def test_department_pots_and_department_topups_are_off_in_brc(db, w):  # noqa: F811
    with pytest.raises(ValueError, match="each employee one petty cash, not departments"):
        fund_service.create(db, region_id=w["uae"].region_id, owner_type="department",
                            department_id=w["employee"].department_id, opening_balance=5000)
    _set(db, w, amount=5000)
    with pytest.raises(ValueError, match="site top-up steps"):
        fund_module._require_department_model(fund_service.employee_advance(db, w["employee"].user_id, w["uae"].region_id))


# ---- top-up ------------------------------------------------------------------------------


def test_topup_accountant_prepares_head_approves_finance_pays(db, w, sent):  # noqa: F811
    _set(db, w, amount=5000)
    b1, b2 = _bill(db, w, 600), _bill(db, w, 400)
    pot = _pot(db, w)
    assert (pot["available"], pot["spent"]) == (4000, 1000)
    bills = site.replenishable_bills(db, w["accountant"], pot["id"])
    assert sorted(b["id"] for b in bills) == sorted([b1.transaction_id, b2.transaction_id])
    with pytest.raises(PermissionError):
        site.request_topup(db, w["employee"], pot["id"], [b1.transaction_id])
    req = site.request_topup(db, w["accountant"], pot["id"], [b1.transaction_id, b2.transaction_id], "Nov bills")
    assert (req["status"], req["amount"]) == ("submitted", 1000)
    assert _names(sent, f"pca_site_requested_{req['id']}") == ["roshan"]
    with pytest.raises(ValueError, match="another top-up"):
        site.request_topup(db, w["accountant"], pot["id"], [b1.transaction_id])
    # Order is enforced: Finance can't pay before the Head of Accountant approves.
    with pytest.raises(ValueError, match="Head of Accountant must approve"):
        site.pay(db, w["fm"], req["id"], payment_method="bank_transfer", payment_reference="WD-1")
    with pytest.raises(PermissionError):
        site.approve(db, w["accountant"], req["id"])
    req = site.approve(db, w["head"], req["id"], "Checked")
    assert (req["status"], req["verified_by_name"]) == ("verified", "Roshan Head")
    assert _names(sent, f"pca_site_verified_{req['id']}") == ["meera"]
    with pytest.raises(PermissionError):
        site.pay(db, w["head"], req["id"], payment_method="bank_transfer", payment_reference="WD-1")
    with pytest.raises(ValueError, match="reference"):
        site.pay(db, w["fm"], req["id"], payment_method="bank_transfer", payment_reference=" ")
    req = site.pay(db, w["fm"], req["id"], payment_method="bank_transfer",
                   payment_reference="WD-1", payment_date="2026-11-12")
    assert (req["status"], req["payment_reference"], req["paid_by_name"]) == ("paid", "WD-1", "Meera Finance")
    assert [h["action"] for h in req["history"]] == ["requested", "verified", "paid"]
    pot = _pot(db, w)
    assert (pot["available"], pot["approved_limit"]) == (5000, 5000)  # PDF: back to 5,000
    assert site.replenishable_bills(db, w["accountant"], pot["id"]) == []
    assert set(_names(sent, f"pca_site_paid_{req['id']}")) == {"surya", "nisha"}


def test_rejected_topup_frees_the_bills(db, w):  # noqa: F811
    _set(db, w, amount=5000)
    b1 = _bill(db, w, 600)
    pot_id = _pot(db, w)["id"]
    req = site.request_topup(db, w["accountant"], pot_id, [b1.transaction_id])
    with pytest.raises(ValueError, match="why"):
        site.reject(db, w["head"], req["id"], " ")
    with pytest.raises(PermissionError):
        site.reject(db, w["fm"], req["id"], "not yours yet")
    out = site.reject(db, w["head"], req["id"], "Receipt missing")
    assert out["status"] == "rejected"
    assert [b["id"] for b in site.replenishable_bills(db, w["accountant"], pot_id)] == [b1.transaction_id]


def test_low_pot_alerts_employee_and_accountant(db, w, sent):  # noqa: F811
    _set(db, w, amount=1000)
    tx = _bill(db, w, 850)
    check_low_funds_for_bill(db, tx)
    assert set(_names(sent, "fund_low_")) == {"surya", "nisha"}


def test_ksa_and_dubai_unaffected(db, w):  # noqa: F811
    assert pca_model(w["ksa"]) == "department"
    assert not is_site_model(w["ksa"])
    with pytest.raises(ValueError, match="doesn't use this petty cash flow"):
        site.set_pot(db, w["accountant"], region_id=w["ksa"].region_id, employee_id=w["employee"].user_id, amount=100)


def _names(sent, prefix):
    return sorted({name for name, type_, _ in sent if type_.startswith(prefix)})
