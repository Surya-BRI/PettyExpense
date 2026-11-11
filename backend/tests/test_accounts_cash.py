"""Professional Signs (KSA): the Accounts Department's own petty cash account (PCA PDF section 6).

Admin sets its amount; every Process 2 payment ("Direct payment by Accounts Department") takes
from it; the Accounts Manager refills it from the bank. Process 1 (bank) never touches it.
"""
import pytest

from services.accounts_cash_service import accounts_cash_service as cash
from services.employee_pca_service import employee_pca_service as pca
from services.payment_service import payment_service
from tests.test_employee_pca import _bill, _fm, _give_advance, _pay_bill, sent, w  # noqa: F401
from tests.test_funds_and_regions import db  # noqa: F401


def _view(db, w, who="fm"):  # noqa: F811
    return cash.view(db, w[who], w["ksa"].region_id)


def test_process_2_needs_the_account_set_up_first(db, w):  # noqa: F811
    _give_advance(db, w, 10000)
    tx = _bill(db, w, 1000)
    assert _view(db, w)["configured"] is False
    with pytest.raises(ValueError, match="isn't set up yet"):
        _pay_bill(db, w, tx, source="accounts_petty_cash")
    _pay_bill(db, w, tx, source="bank")  # Process 1 still works
    assert _view(db, w)["paid_out"] == 0


def test_admin_or_accounts_manager_sets_the_amount_and_not_below_what_is_out(db, w, sent):  # noqa: F811
    for who in ("employee", "hod", "accountant"):
        with pytest.raises(PermissionError):
            cash.set_limit(db, w[who], w["ksa"].region_id, 5000)
    out = cash.set_limit(db, w["fm"], w["ksa"].region_id, 4000, "month-end float")  # the Accounts Manager can
    assert (out["limit"], out["can_set"]) == (4000, True)
    # Admin is told whenever the Accounts Manager changes it.
    [(to, _, subject)] = [s for s in sent if s[1].startswith("pca_accounts_cash_set_")]
    assert (to, subject) == (w["admin"].user_name, "Accounts Department petty cash amount changed")
    out = cash.set_limit(db, w["admin"], w["ksa"].region_id, 5000)
    # ...but not when Admin changes it themselves.
    assert len([s for s in sent if s[1].startswith("pca_accounts_cash_set_")]) == 1
    assert (out["configured"], out["limit"], out["available"], out["currency"]) == (True, 5000, 5000, "SAR")
    assert out["entries"][0]["kind"] == "set"

    _give_advance(db, w, 10000)
    _pay_bill(db, w, _bill(db, w, 3000), source="accounts_petty_cash")
    with pytest.raises(ValueError, match="can't be lower"):
        cash.set_limit(db, w["admin"], w["ksa"].region_id, 2999)
    out = cash.set_limit(db, w["admin"], w["ksa"].region_id, 8000)
    assert (out["limit"], out["to_refill"], out["available"]) == (8000, 3000, 5000)


def test_process_2_payments_take_from_it_and_are_blocked_when_short(db, w):  # noqa: F811
    cash.set_limit(db, w["admin"], w["ksa"].region_id, 5000)
    _give_advance(db, w, 10000)
    a, b, c = _bill(db, w, 3000), _bill(db, w, 1500), _bill(db, w, 600)
    _pay_bill(db, w, a, source="accounts_petty_cash")
    _pay_bill(db, w, b, source="bank")  # Process 1: not from the account
    out = _view(db, w)
    assert (out["paid_out"], out["available"]) == (3000, 2000)
    assert out["entries"][0]["transaction_id"] == a.transaction_id

    # Batch: each bill is checked against what's left after the ones before it.
    d = _bill(db, w, 1500)
    res = payment_service.record_batch(db, _fm(w), [d.transaction_id, c.transaction_id],
                                       payment_source="accounts_petty_cash", payment_reference="AC-2",
                                       payment_date="2026-11-01")
    assert [p["transaction_id"] for p in res["paid"]] == [d.transaction_id]
    assert res["skipped"][0]["id"] == c.transaction_id and "only SAR 500.00 left" in res["skipped"][0]["reason"]
    db.refresh(c)
    assert c.status == "approved"  # not paid, nothing half-saved


def test_refill_puts_it_back_and_low_alert_fires_once_per_cycle(db, w, sent):  # noqa: F811
    cash.set_limit(db, w["admin"], w["ksa"].region_id, 5000)
    _give_advance(db, w, 10000)
    _pay_bill(db, w, _bill(db, w, 4500), source="accounts_petty_cash")  # 500 left < 20%
    low = [t for _, t, _ in sent if t.startswith("pca_accounts_cash_low_")]
    assert low and len(set(low)) == 1

    with pytest.raises(ValueError, match="can't be more"):
        cash.refill(db, w["fm"], w["ksa"].region_id, amount=4501, reference="WD-1")
    with pytest.raises(ValueError, match="bank reference"):
        cash.refill(db, w["fm"], w["ksa"].region_id, amount=None, reference=" ")
    with pytest.raises(PermissionError):
        cash.refill(db, w["employee"], w["ksa"].region_id, amount=None, reference="WD-1")
    out = cash.refill(db, w["fm"], w["ksa"].region_id, amount=None, reference="WD-1", refill_date="2026-11-02")
    assert (out["refilled"], out["to_refill"], out["available"], out["low"]) == (4500, 0, 5000, False)
    with pytest.raises(ValueError, match="Nothing to refill"):
        cash.refill(db, w["fm"], w["ksa"].region_id, amount=None, reference="WD-2")

    # Low again after the refill: a new alert (new cycle).
    _pay_bill(db, w, _bill(db, w, 4200), source="accounts_petty_cash")
    assert len({t for _, t, _ in sent if t.startswith("pca_accounts_cash_low_")}) == 2


def test_old_advance_request_paid_by_process_2_takes_from_it(db, w):  # noqa: F811
    from database.models import ErpExpenseFundTopupRequest

    cash.set_limit(db, w["admin"], w["ksa"].region_id, 5000)
    fund_id = _give_advance(db, w, 1000)["fund"]["id"]
    row = ErpExpenseFundTopupRequest(fund_id=fund_id, kind="advance", amount=2000,
                                     requester_id=w["hod"].user_id, status="approved", is_active=1)
    db.add(row)
    db.commit()
    pca.pay(db, w["fm"], row.topup_id, payment_source="accounts_petty_cash", payment_method="cash",
            payment_reference="AC-9", payment_date="2026-11-01")
    out = _view(db, w)
    assert (out["paid_out"], out["available"]) == (2000, 3000)
    assert out["entries"][0]["topup_id"] == row.topup_id


def test_who_can_see_it(db, w):  # noqa: F811
    cash.set_limit(db, w["admin"], w["ksa"].region_id, 5000)
    assert _view(db, w, "fm")["can_refill"] is True
    assert _view(db, w, "admin")["can_set"] is True
    for who in ("employee", "hod"):
        with pytest.raises(PermissionError):
            _view(db, w, who)
    with pytest.raises(ValueError, match="no Accounts Department petty cash"):
        cash.view(db, w["admin"], w["uae"].region_id)
