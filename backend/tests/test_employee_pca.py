"""Professional Signs (KSA) employee petty cash advances -- PCA_Professional_Documentation.pdf.

Advance: HOD proposes -> Accounts Manager approves -> Accounts Manager pays. One advance per
employee, used for all their projects.
Bills (each with a project OP code): Employee -> own HOD -> Accounts Manager (books EJV/EJVB).
Top-up: employee raises with approved bills -> HOD -> Accounts Manager verifies -> Accounts
Manager pays (cash withdrawal from bank, or direct payment).
Dubai/UAE (department model) must behave exactly as before.
"""
import json

import pytest

from auth.security import CurrentUser
from database.models import (
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseHodAssignment,
    ErpExpenseLineItem,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
)
from services import approval_service
from services import fund_service as fund_module
from services.department_split import cross_department_ids, department_shares
from services.employee_pca_service import employee_pca_service as pca
from services.fund_service import check_low_funds_for_bill, fund_service, require_bill_projects
from services.payment_service import payment_service
from services.region_policy import EMPLOYEE_PCA_SETTINGS, apply_employee_settings
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
    ksa.approval_matrix_json = json.dumps(EMPLOYEE_PCA_SETTINGS)
    uae.approval_matrix_json = json.dumps({"stages": ["hod", "accountant", "finance_manager"]})
    it = ErpExpenseDepartment(department_name="IT")
    db.add(it)
    db.flush()
    db.add(ErpExpenseHodAssignment(user_id=hod.user_id, department_id=sales.department_id, is_active=1))
    food = ErpExpenseCategory(category_name="Food")
    it_kit = ErpExpenseCategory(category_name="IT Equipment", owning_department_id=it.department_id)
    db.add_all([food, it_kit])
    db.commit()
    return dict(employee=employee, hod=hod, admin=admin, fm=fm, accountant=accountant,
                uae=uae, ksa=ksa, sales=sales, it=it, food=food, it_kit=it_kit)


def _pay(user, db, request_id, source="bank"):  # noqa: F811
    return pca.pay(db, user, request_id, payment_source=source, payment_method="bank_transfer",
                   payment_reference="TRF-1", payment_date="2026-11-01")


def _set(db, w, amount=10000, by=None, employee=None):  # noqa: F811
    return pca.set_advance(db, by or w["hod"], region_id=w["ksa"].region_id,
                           employee_id=(employee or w["employee"]).user_id, amount=amount)


def _give_advance(db, w, amount=10000, employee=None):  # noqa: F811
    return _set(db, w, amount, employee=employee, by=w["admin"] if employee else None)


def _check(db, w, amount):  # noqa: F811
    fund_service.require_petty_cash_within_limit(db, w["employee"], w["ksa"].region_id, amount)


def _bill(db, w, amount, status="approved", category=None, region=None, op="OP-2201", employee=None,
          type_="petty_cash"):  # noqa: F811
    region = region or w["ksa"]
    tx = ErpExpenseTransaction(
        employee_id=(employee or w["employee"]).user_id, region_id=region.region_id,
        category_id=(category or w["food"]).category_id, type=type_, status=status,
        amount=amount, total_amount=amount, currency="SAR", base_currency="SAR", total_amount_base=amount,
        op_number=op,
    )
    db.add(tx)
    db.commit()
    return tx


def _names(sent, prefix):
    return sorted({name for name, type_, _ in sent if type_.startswith(prefix)})


# ---- company settings --------------------------------------------------------------------


def test_seed_overwrites_old_ksa_settings_once_then_keeps_admin_edits(db, w):  # noqa: F811
    ksa: ErpExpenseRegionConfig = w["ksa"]
    old = {"stages": ["hod", "accountant", "finance_manager"], "pca_model": "employee",
           "journal_required_at": "accountant", "payer_roles": ["accountant", "finance_manager"]}
    ksa.approval_matrix_json = json.dumps(old)
    assert apply_employee_settings(ksa)
    m = json.loads(ksa.approval_matrix_json)
    assert (m["stages"], m["journal_required_at"], m["payer_roles"]) == (
        ["hod", "finance_manager"], "finance_manager", ["finance_manager"])
    # Admin later changes something: the seed leaves it alone.
    m["pca_reminder_ratio"] = 0.6
    ksa.approval_matrix_json = json.dumps(m)
    assert not apply_employee_settings(ksa)
    assert json.loads(ksa.approval_matrix_json)["pca_reminder_ratio"] == 0.6


def test_bills_left_at_the_old_accountant_step_move_to_the_accounts_manager(db, w):  # noqa: F811
    waiting = _bill(db, w, 100, status="submitted")
    waiting.current_stage = "accountant"  # staged before KSA dropped the Accountant step
    approval_service._history(db, waiting.transaction_id, w["hod"].user_id, "hod", "approve", None)
    uae_bill = _bill(db, w, 100, status="submitted", region=w["uae"])
    uae_bill.current_stage = "accountant"
    db.commit()
    assert approval_service.realign_open_bills(db, w["ksa"].region_id) == 1
    assert approval_service.realign_open_bills(db, w["uae"].region_id) == 0
    assert (waiting.current_stage, uae_bill.current_stage) == ("finance_manager", "accountant")


# ---- advance -----------------------------------------------------------------------------


def test_hod_sets_the_pca_and_it_is_live_at_once(db, w, sent):  # noqa: F811
    with pytest.raises(ValueError, match="reimbursement"):
        _check(db, w, 100)  # nothing set yet
    out = _set(db, w, 10000)
    assert (out["kind"], out["status"], out["amount"]) == ("advance", "set", 10000)
    assert out["fund"]["op_number"] is None  # not tied to a project
    assert (out["fund"]["approved_limit"], out["fund"]["available"]) == (10000, 10000)
    _check(db, w, 5000)  # usable straight away (up to the 50% hard limit): no approval or payment
    assert _names(sent, f"pca_advance_set_{out['id']}") == ["surya"]  # the HOD set it themselves
    assert [h["action"] for h in out["history"]] == ["set"]
    assert out["history"][0]["comment"] == "Set to SAR 10,000.00 (was 0.00)"


def test_only_the_employees_hod_or_admin_sets_the_pca(db, w):  # noqa: F811
    for who in ("employee", "fm", "accountant"):
        with pytest.raises(PermissionError):
            _set(db, w, 500, by=w[who])
    _set(db, w, 500, by=w["admin"])
    with pytest.raises(ValueError, match="already SAR 500.00"):
        _set(db, w, 500)
    # The Set screen's list shows each person's current amount, and never the HOD themselves.
    staff = {s["id"]: s for s in pca.staff(db, w["hod"], w["ksa"].region_id)}
    assert staff[w["employee"].user_id]["advance"] == 500
    assert w["hod"].user_id not in staff
    if w["hod"].department_id in {w["sales"].department_id}:
        with pytest.raises(PermissionError, match="your own petty cash"):
            _set(db, w, 100, by=w["hod"], employee=w["hod"])


def test_advances_only_in_employee_model_company(db, w):  # noqa: F811
    with pytest.raises(ValueError, match="doesn't use employee petty cash advances"):
        pca.set_advance(db, w["hod"], region_id=w["uae"].region_id,
                        employee_id=w["employee"].user_id, amount=500)
    with pytest.raises(ValueError, match="advances to employees, not departments"):
        fund_service.create(db, region_id=w["ksa"].region_id, owner_type="department",
                            opening_balance=5000, department_id=w["sales"].department_id)


def test_changing_the_pca_keeps_one_advance_and_not_below_its_bills(db, w):  # noqa: F811
    first = _set(db, w, 10000)
    _bill(db, w, 3000)
    _bill(db, w, 1000, status="submitted")
    with pytest.raises(ValueError, match="can't be lower than that"):
        _set(db, w, 3999)
    out = _set(db, w, 5000)
    assert out["amount"] == -5000  # the log records the change
    assert out["fund"]["id"] == first["fund"]["id"]
    assert (out["fund"]["approved_limit"], out["fund"]["available"]) == (5000, 2000)
    assert len(pca.list_advances(db, w["employee"])) == 1


# ---- bills against the advance -----------------------------------------------------------


def test_one_advance_pays_bills_of_any_project(db, w):  # noqa: F811
    _give_advance(db, w, 10000)
    _bill(db, w, 3000, op="OP-2201")
    _bill(db, w, 1000, op="OP-2215")
    [advance] = pca.list_advances(db, w["employee"])
    assert (advance["spent"], advance["available"]) == (4000, 6000)
    assert advance["label"] == "Surya Sales · advance"


def test_without_an_advance_bills_are_reimbursements(db, w):  # noqa: F811
    with pytest.raises(ValueError, match="don't have a petty cash advance"):
        _check(db, w, 100)


def test_every_ksa_bill_names_its_project(db, w):  # noqa: F811
    tx = _bill(db, w, 300, status="draft", op=None)
    with pytest.raises(ValueError, match="project OP code"):
        require_bill_projects(tx)
    # Lines may name different projects -- all from the one advance.
    db.add_all([
        ErpExpenseLineItem(transaction_id=tx.transaction_id, line_no=1, description="Paint", amount=100,
                           op_number="OP-2201"),
        ErpExpenseLineItem(transaction_id=tx.transaction_id, line_no=2, description="Screws", amount=200,
                           op_number="OP-2215"),
    ])
    db.commit()
    db.refresh(tx)
    require_bill_projects(tx)
    assert fund_module.project_shares(tx) == {"OP-2201": 100, "OP-2215": 200}


def _fm(w):  # noqa: F811
    return CurrentUser(w["fm"].user_id, "Meera Finance", "finance_manager")


def _pay_bill(db, w, tx, source="bank"):  # noqa: F811
    return payment_service.record_payment(
        db, _fm(w), tx.transaction_id, payment_source=source,
        payment_reference="WD-77", payment_date="2026-11-01", notify=False,
    )


def test_only_half_the_pca_can_be_used_until_the_bills_are_paid(db, w):  # noqa: F811
    _give_advance(db, w, 10000)
    approved = _bill(db, w, 3000)
    _bill(db, w, 1000, status="submitted")  # in approval counts too
    _check(db, w, 1000)  # 3,000 + 1,000 + 1,000 = 5,000 = 50%
    with pytest.raises(ValueError, match="only SAR 5,000.00 of your petty cash until your approved bills are paid"):
        _check(db, w, 1001)
    [adv] = pca.list_advances(db, w["employee"])
    assert (adv["spend_limit"], adv["uncommitted"], adv["available"]) == (5000, 1000, 7000)

    # The Accounts Manager pays the approved bill: that part is free again.
    _pay_bill(db, w, approved)
    _check(db, w, 4000)  # 1,000 in approval + 4,000 = 5,000
    with pytest.raises(ValueError, match="until your approved bills are paid"):
        _check(db, w, 4001)


def test_uae_individual_pots_have_no_half_limit(db, w):  # noqa: F811
    fund = fund_service.create(db, region_id=w["uae"].region_id, owner_type="employee",
                               opening_balance=1000, employee_id=w["employee"].user_id)
    assert fund["spend_limit"] is None
    assert fund["uncommitted"] == 1000


def test_other_department_items_stay_with_the_employee_in_ksa_only(db, w):  # noqa: F811
    for region, expect_split in ((w["ksa"], False), (w["uae"], True)):
        tx = _bill(db, w, 300, status="submitted", category=w["food"], region=region)
        db.add_all([
            ErpExpenseLineItem(transaction_id=tx.transaction_id, line_no=1, description="Lunch",
                               amount=100, category_id=w["food"].category_id),
            ErpExpenseLineItem(transaction_id=tx.transaction_id, line_no=2, description="Mouse",
                               amount=200, category_id=w["it_kit"].category_id),
        ])
        db.commit()
        db.refresh(tx)
        if expect_split:
            assert cross_department_ids(tx) == [w["it"].department_id]
            assert set(department_shares(tx)) == {None, w["it"].department_id}
        else:
            assert cross_department_ids(tx) == []
            assert department_shares(tx) == {None: 300}
            assert approval_service.resolve_stage_sequence(db, tx) == ["hod", "finance_manager"]


def test_ksa_bill_goes_hod_then_accounts_manager_with_journal(db, w):  # noqa: F811
    tx = _bill(db, w, 100, status="submitted")
    tx.current_stage = "hod"
    db.commit()
    labels = approval_service.resolve_stage_labels(tx)
    assert labels["finance_manager"] == "Accounts Manager"

    hod = CurrentUser(w["hod"].user_id, "Priya HOD", "hod")
    out = approval_service.advance(db, hod, tx.transaction_id, "approve", None)
    assert out["current_stage"] == "finance_manager"  # no Accountant step

    fm = CurrentUser(w["fm"].user_id, "Meera FM", "finance_manager")
    with pytest.raises(ValueError, match="EJV"):
        approval_service.advance(db, fm, tx.transaction_id, "approve", None)
    with pytest.raises(ValueError, match="number"):
        approval_service.advance(db, fm, tx.transaction_id, "approve", None, journal_type="ejvb")
    # Bulk approve can't enter a journal, so it skips the bill.
    bulk = approval_service.bulk_approve(db, fm, [tx.transaction_id])
    assert bulk["skipped"] == [{"id": tx.transaction_id, "reason": "journal_required"}]

    out = approval_service.advance(db, fm, tx.transaction_id, "approve", "ok",
                                   journal_type="ejvb", journal_reference="EJVB-2211")
    assert (out["journal_type"], out["journal_reference"]) == ("EJVB", "EJVB-2211")
    assert out["status"] == "approved"
    assert out["history"][-1]["remarks"] == "EJVB EJVB-2211 · ok"


def test_uae_accountant_approves_without_a_journal(db, w):  # noqa: F811
    tx = _bill(db, w, 100, status="submitted", region=w["uae"])
    tx.current_stage = "accountant"
    db.commit()
    acc = CurrentUser(w["accountant"].user_id, "Nisha Accounts", "accountant")
    out = approval_service.advance(db, acc, tx.transaction_id, "approve", None)
    assert out["current_stage"] == "finance_manager"
    assert out["journal_type"] is None


# ---- paying approved bills (PDF section 7) -----------------------------------------------


def test_approved_petty_cash_bill_is_paid_from_payments_and_refills_the_pca(db, w):  # noqa: F811
    fund_id = _give_advance(db, w, 10000)["fund"]["id"]
    tx = _bill(db, w, 3000)
    uae_petty = _bill(db, w, 50, region=w["uae"])  # Dubai petty cash never comes to Payments

    page = payment_service.list_claims(db, _fm(w), status="unpaid")
    ids = [i["id"] for i in page["items"]]
    assert tx.transaction_id in ids and uae_petty.transaction_id not in ids

    with pytest.raises(ValueError, match="Process 1"):
        payment_service.record_payment(db, _fm(w), tx.transaction_id, payment_reference="X",
                                       payment_date="2026-11-01", notify=False)
    # Process 2 comes out of the Accounts Department's petty cash, which Admin sets up first.
    from services.accounts_cash_service import accounts_cash_service

    accounts_cash_service.set_limit(db, w["admin"], w["ksa"].region_id, 5000)
    out = _pay_bill(db, w, tx, source="accounts_petty_cash")  # Process 2
    assert (out["payment_source"], out["payment_method_label"], out["amount"]) == (
        "accounts_petty_cash", "Direct payment by Accounts Department", 3000)

    [adv] = pca.list_advances(db, w["employee"])
    assert (adv["spent"], adv["unreplenished_spend"], adv["available"]) == (3000, 0, 10000)
    # The refill is logged as a paid top-up of that bill.
    [topup] = [r for r in pca.list_requests(db, w["fm"]) if r["kind"] == "topup"]
    assert (topup["status"], topup["amount"], topup["payment_source"]) == ("paid", 3000, "accounts_petty_cash")
    assert topup["transaction_ids"] == [tx.transaction_id]
    assert topup["fund_id"] == fund_id

    with pytest.raises(ValueError, match="already been paid"):
        _pay_bill(db, w, tx)
    with pytest.raises(ValueError, match="no payment step"):
        _pay_bill(db, w, uae_petty)


def test_batch_pays_several_bills_with_one_withdrawal(db, w):  # noqa: F811
    _give_advance(db, w, 10000)
    a, b = _bill(db, w, 1000), _bill(db, w, 1500)
    out = payment_service.record_batch(db, _fm(w), [a.transaction_id, b.transaction_id],
                                       payment_source="bank", payment_reference="WD-9",
                                       payment_date="2026-11-01")
    assert len(out["paid"]) == 2 and out["skipped"] == []
    [adv] = pca.list_advances(db, w["employee"])
    assert adv["available"] == 10000


def test_no_separate_topup_request_in_ksa(db, w):  # noqa: F811
    fund_id = _give_advance(db, w)["fund"]["id"]
    tx = _bill(db, w, 2000)
    with pytest.raises(ValueError, match="No top-up request is needed"):
        pca.request_topup(db, w["employee"], fund_id, [tx.transaction_id])


def test_department_topup_steps_refuse_an_employee_advance(db, w):  # noqa: F811
    fund_id = _give_advance(db, w)["fund"]["id"]
    with pytest.raises(ValueError, match="employee petty cash advances"):
        fund_service.request_topup(db, w["admin"], fund_id, 100, None)


def test_reminder_once_half_the_advance_is_spent(db, w, sent):  # noqa: F811
    fund_id = _give_advance(db, w, 10000)["fund"]["id"]
    tx = _bill(db, w, 4000)
    check_low_funds_for_bill(db, tx)
    assert not _names(sent, f"pca_reminder_{fund_id}_")
    tx = _bill(db, w, 1000, op="OP-2215")  # 5,000 of 10,000, across projects
    check_low_funds_for_bill(db, tx)
    # Employee, HOD and the Accounts Manager (who pays the bills).
    assert _names(sent, f"pca_reminder_{fund_id}_0") == ["meera", "priya", "surya"]


def test_lists_are_scoped(db, w):  # noqa: F811
    _give_advance(db, w)
    assert [a["employee_id"] for a in pca.list_advances(db, w["employee"])] == [w["employee"].user_id]
    assert len(pca.list_advances(db, w["hod"])) == 1
    assert len(pca.list_advances(db, w["fm"])) == 1
    assert [r["kind"] for r in pca.list_requests(db, w["employee"])] == ["advance"]
    # The department Top-ups list doesn't show employee advances.
    assert fund_service.list_topups(db, user=w["admin"]) == []


def test_summary_by_department_and_by_project_from_the_bills(db, w):  # noqa: F811
    from database.models import ErpAuthExpenseUsers

    ravi = ErpAuthExpenseUsers(user_name="ravi", display_name="Ravi IT", password_hash="x",
                               role_id=w["employee"].role_id, department_id=w["it"].department_id)
    db.add(ravi)
    db.commit()
    _give_advance(db, w, 10000)
    _bill(db, w, 2000, op="OP-2201")
    _bill(db, w, 500, op="OP-2215", status="submitted")  # still in approval
    _bill(db, w, 700, op="OP-2201", type_="reimbursement")  # not from the advance
    _give_advance(db, w, 3000, employee=ravi)  # set by Admin

    out = pca.summary(db, w["admin"], w["ksa"].region_id)
    assert out["currency"] == "SAR"
    t = out["totals"]
    # Every employee of the company is listed (6 in the fixture); 2 have petty cash set.
    assert (t["employee_count"], t["advance_count"], t["project_count"]) == (6, 2, 2)
    everyone = {e["employee_name"]: e for d in out["by_department"] for e in d["employees"]}
    nobody = everyone[w["fm"].display_name]
    assert (nobody["fund_id"], nobody["advance"], nobody["available"]) == (None, 0, 0)
    assert (t["advance"], t["advance_waiting"], t["spent"], t["available"]) == (13000, 0, 2000, 11000)

    depts = {d["department_name"]: d for d in out["by_department"]}
    surya = next(e for e in depts["Sales"]["employees"] if e["employee_name"] == "Surya Sales")
    assert (surya["advance"], surya["available"]) == (10000, 8000)
    assert depts["IT"]["advance"] == 3000

    projects = {p["op_number"]: p for p in out["by_project"]}
    assert set(projects) == {"OP-2201", "OP-2215"}
    assert (projects["OP-2201"]["spent"], projects["OP-2201"]["pending_bills"]) == (2000, 0)
    assert (projects["OP-2215"]["spent"], projects["OP-2215"]["pending_bills"]) == (0, 500)
    assert [e["employee_name"] for e in projects["OP-2201"]["employees"]] == ["Surya Sales"]

    # Employees tab: light department list, then one department's people on demand.
    deps = {d["department_name"]: d for d in pca.departments(db, w["admin"], w["ksa"].region_id)["departments"]}
    it = deps["IT"]
    assert (it["employee_count"], it["with_petty_cash"], it["not_set"], it["total_limit"]) == (1, 1, 0, 3000)
    assert sum(d["employee_count"] for d in deps.values()) == 6
    sales = pca.department_employees(db, w["admin"], w["ksa"].region_id, w["sales"].department_id)
    rows = {e["employee_name"]: e for e in sales["employees"]}
    assert (rows["Surya Sales"]["advance"], rows["Surya Sales"]["available"]) == (10000, 8000)
    assert all(e["employee_name"] != "Ravi IT" for e in sales["employees"])
    hod_deps = pca.departments(db, w["hod"], w["ksa"].region_id)["departments"]
    assert [d["department_name"] for d in hod_deps] == ["Sales"]

    # Who can be proposed for: the Sales HOD's staff only; Admin anyone; not the employee.
    hod_ids = [s["id"] for s in pca.staff(db, w["hod"], w["ksa"].region_id)]
    assert w["employee"].user_id in hod_ids and ravi.user_id not in hod_ids
    assert ravi.user_id in [s["id"] for s in pca.staff(db, w["admin"], w["ksa"].region_id)]
    with pytest.raises(PermissionError):
        pca.staff(db, w["employee"], w["ksa"].region_id)

    # The Sales HOD only sees their own staff.
    mine = pca.summary(db, w["hod"], w["ksa"].region_id)
    assert [d["department_name"] for d in mine["by_department"]] == ["Sales"]
    with pytest.raises(ValueError, match="doesn't use employee petty cash advances"):
        pca.summary(db, w["admin"], w["uae"].region_id)


def test_notifications_carry_the_company_they_are_about(db, w):  # noqa: F811
    """The app switches to this company before opening a notification."""
    from types import SimpleNamespace

    from api.routes_notifications import _regions_for

    adv = _give_advance(db, w)
    fund_id, req_id = adv["fund"]["id"], adv["id"]
    tx = _bill(db, w, 10, region=w["uae"])
    tx.region = w["uae"]
    rows = [
        SimpleNamespace(notification_id=1, transaction_id=None, type=f"pca_advance_paid_{req_id}"),
        SimpleNamespace(notification_id=2, transaction_id=None, type=f"pca_reminder_{fund_id}_0"),
        SimpleNamespace(notification_id=3, transaction_id=tx.transaction_id, type="approval"),
        SimpleNamespace(notification_id=4, transaction_id=None, type="test"),
    ]
    out = _regions_for(db, rows, {tx.transaction_id: tx})
    assert out == {1: "KSA", 2: "KSA", 3: "UAE", 4: None}


# ---- reimbursement payments --------------------------------------------------------------


def test_only_the_accounts_manager_pays_reimbursements_in_ksa(db, w):  # noqa: F811
    acc = CurrentUser(w["accountant"].user_id, "Nisha Accounts", "accountant")
    fm = CurrentUser(w["fm"].user_id, "Meera FM", "finance_manager")
    for region in (w["ksa"], w["uae"]):
        for payer, allowed in ((acc, False), (fm, True)):
            tx = _bill(db, w, 50, region=region, type_="reimbursement")
            # KSA records the PDF process; Dubai the payment method, as before.
            call = lambda: payment_service.record_payment(  # noqa: E731
                db, payer, tx.transaction_id, payment_method="bank_transfer",
                payment_source="bank" if region is w["ksa"] else None,
                payment_reference="TRF-7", payment_date="2026-11-01", notify=False,
            )
            if allowed:
                assert call()["payment_reference"] == "TRF-7"
            else:
                with pytest.raises(PermissionError):
                    call()
