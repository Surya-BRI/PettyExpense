"""Petty-cash top-up chain: HOD/Admin raise -> Accounts verify (or return) -> FM approve + pay.
Every step is logged and notifies the next person; a fund dropping below 20% alerts its HOD."""
import pytest

from database.models import (
    ErpExpenseCategory,
    ErpExpenseHodAssignment,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpMasterExpenseRole,
    ErpAuthExpenseUsers,
)
from services import fund_service as fund_module
from services.fund_service import check_low_fund, check_low_funds_for_bill, fund_service
from tests.test_funds_and_regions import _setup, db  # noqa: F401  (db fixture)


@pytest.fixture
def sent(monkeypatch):
    """Every notification as (user_name, type, subject)."""
    out = []
    monkeypatch.setattr(
        fund_module, "send",
        lambda _db, user, type_, _txn, **kw: out.append((user.user_name, type_, kw["subject_en"])),
    )
    return out


@pytest.fixture
def world(db):  # noqa: F811
    employee, hod, admin, fm, uae, ksa, sales, accountant = _setup(db)
    db.add(ErpExpenseHodAssignment(user_id=hod.user_id, department_id=sales.department_id, is_active=1))
    cat = ErpExpenseCategory(category_name="Food")
    db.add(cat)
    db.commit()
    fund = fund_service.create(
        db, region_id=uae.region_id, owner_type="department",
        opening_balance=5000, department_id=sales.department_id,
    )
    return dict(employee=employee, hod=hod, admin=admin, fm=fm, accountant=accountant,
                uae=uae, ksa=ksa, sales=sales, cat=cat, fund=fund)


def _bill(db, w, amount, status="approved"):  # noqa: F811
    tx = ErpExpenseTransaction(
        employee_id=w["employee"].user_id, region_id=w["uae"].region_id, category_id=w["cat"].category_id,
        type="petty_cash", status=status, amount=amount, total_amount=amount, currency="AED",
        base_currency="AED", total_amount_base=amount,
    )
    db.add(tx)
    db.commit()
    return tx


def _who(sent, type_prefix):
    return sorted({name for name, type_, _ in sent if type_.startswith(type_prefix)})


def test_full_chain_notifies_each_step_and_logs_history(db, world, sent):  # noqa: F811
    w = world
    tx = _bill(db, w, 1000)
    req = fund_service.request_topup(db, w["hod"], w["fund"]["id"], None, "Month-end", transaction_ids=[tx.transaction_id])
    # Request -> region Accountant + Admin (FYI); not the HOD who raised it.
    assert _who(sent, f"topup_requested_{req['id']}") == ["arjun", "nisha"]

    fund_service.verify_topup(db, w["accountant"], req["id"], "Bills checked")
    assert _who(sent, f"topup_verified_{req['id']}") == ["meera"]

    out = fund_service.decide_topup(db, w["fm"], req["id"], True, "OK", payment_reference="TRF-9")
    # Decision -> requester/department HOD + Admin (FYI).
    assert _who(sent, f"topup_approved_{req['id']}") == ["arjun", "priya"]

    assert [(h["action"], h["actor_name"]) for h in out["history"]] == [
        ("requested", "Priya HOD"),
        ("verified", "Nisha Accounts"),
        ("approved", "Meera Finance"),
    ]
    assert out["history"][0]["comment"] == "Month-end"
    assert out["history"][1]["comment"] == "Bills checked"
    assert "TRF-9" in out["history"][2]["comment"]
    # Step comments no longer pile up in the request's own remarks.
    assert out["remarks"] == "Month-end"
    mine = fund_service.list_mine(db, w["employee"])[0]
    assert mine["available"] == 5000  # restored to the limit


def test_admin_raises_and_hod_hears_the_outcome(db, world, sent):  # noqa: F811
    w = world
    req = fund_service.request_topup(db, w["admin"], w["fund"]["id"], 500, "HOD on leave")
    assert req["requester_name"] == "Arjun Admin"
    assert _who(sent, f"topup_requested_{req['id']}") == ["nisha"]  # Admin isn't told about their own request
    fund_service.verify_topup(db, w["accountant"], req["id"], None)
    fund_service.decide_topup(db, w["fm"], req["id"], False, "Not needed")
    # Admin (who raised it) and the department HOD both hear the outcome.
    assert _who(sent, f"topup_rejected_{req['id']}") == ["arjun", "priya"]


def test_no_accountant_for_the_company_sends_it_to_admin(db, world, sent):  # noqa: F811
    w = world
    # The only accountant covers KSA, not UAE.
    w["accountant"].home_region_id = w["ksa"].region_id
    db.commit()
    req = fund_service.request_topup(db, w["hod"], w["fund"]["id"], 300, None)
    assert _who(sent, f"topup_requested_{req['id']}") == ["arjun"]


def test_accounts_return_frees_the_bills_for_a_new_request(db, world, sent):  # noqa: F811
    w = world
    tx = _bill(db, w, 400)
    req = fund_service.request_topup(db, w["hod"], w["fund"]["id"], None, None, transaction_ids=[tx.transaction_id])

    with pytest.raises(ValueError, match="why"):
        fund_service.return_topup(db, w["accountant"], req["id"], "  ")
    with pytest.raises(PermissionError):
        fund_service.return_topup(db, w["fm"], req["id"], "nope")

    out = fund_service.return_topup(db, w["accountant"], req["id"], "Receipt missing for bill")
    assert out["status"] == "returned"
    assert _who(sent, f"topup_returned_{req['id']}") == ["priya"]
    assert out["history"][-1]["action"] == "returned"
    assert out["history"][-1]["comment"] == "Receipt missing for bill"
    # Returned top-ups don't count as pending, and the bill can go on a new request.
    assert fund_service.list_mine(db, w["hod"])[0]["pending_topup"] == 0
    again = fund_service.request_topup(db, w["hod"], w["fund"]["id"], None, "fixed", transaction_ids=[tx.transaction_id])
    assert again["status"] == "submitted"
    # A returned top-up can't be verified or decided any more.
    with pytest.raises(ValueError):
        fund_service.verify_topup(db, w["accountant"], req["id"], None)


def test_low_fund_alert_once_per_cycle(db, world):  # noqa: F811
    """Real notification service (its per-user dedup is what makes it 'once')."""
    from database.models import ErpExpenseNotification

    w = world
    fund_id = w["fund"]["id"]

    names = {u.user_id: u.user_name for u in db.query(ErpAuthExpenseUsers)}

    def alerts(cycle):
        """User names that got the in-app low-fund alert for this cycle."""
        return sorted(
            names[n.user_id]
            for n in db.query(ErpExpenseNotification).filter(
                ErpExpenseNotification.type == f"fund_low_{fund_id}_{cycle}",
                ErpExpenseNotification.channel == "in_app",
            )
        )

    _bill(db, w, 3500)  # 1500 left = 30%: fine
    assert check_low_fund(db, fund_id) is False
    _bill(db, w, 700)  # 800 left = 16%: low
    assert check_low_fund(db, fund_id) is True
    assert alerts(0) == ["arjun", "priya"]
    check_low_fund(db, fund_id)  # still low: no second alert this cycle
    assert len(alerts(0)) == 2

    # Replenish (approved top-up) -> the next drop alerts again under a new cycle.
    req = fund_service.request_topup(db, w["hod"], fund_id, 4200, None)
    fund_service.verify_topup(db, w["accountant"], req["id"], None)
    fund_service.decide_topup(db, w["fm"], req["id"], True, None)
    _bill(db, w, 4500)
    check_low_fund(db, fund_id)
    assert len(alerts(1)) == 2


def test_final_approval_of_a_petty_cash_bill_checks_its_fund(db, world, sent):  # noqa: F811
    w = world
    tx = _bill(db, w, 4300)
    tx.employee = w["employee"]
    check_low_funds_for_bill(db, tx)
    assert _who(sent, f"fund_low_{w['fund']['id']}_") == ["arjun", "priya"]


def test_legacy_topup_history_is_rebuilt_from_columns(db, world, sent):  # noqa: F811
    from database.models import ErpExpenseFundTopupRequest, ErpExpenseTopupHistory

    w = world
    req = fund_service.request_topup(db, w["hod"], w["fund"]["id"], 100, "old")
    db.query(ErpExpenseTopupHistory).delete()  # as if created before the history table
    db.commit()
    db.expire_all()
    out = fund_service.topup_to_dict(db, req["id"])
    assert [h["action"] for h in out["history"]] == ["requested"]
    assert out["history"][0]["actor_name"] == "Priya HOD"
