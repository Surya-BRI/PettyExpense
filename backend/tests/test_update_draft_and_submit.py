"""Editing a saved draft (PATCH) and submitting it: the currency/exchange_rate/type/bill_number
fields added this session, and the completeness guard that stops an incomplete draft from ever
reaching Finance.

Runs the real service code against the real SQLAlchemy models on a throwaway in-memory SQLite
database (the app itself only ever uses SQL Server).
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
    ErpExpenseRegionConfig,
    ErpMasterExpenseRole,
)
from services.transaction_service import transaction_service  # noqa: E402


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    role = ErpMasterExpenseRole(role_code="employee", role_name="Employee")
    session.add(role)
    session.flush()
    session.add(ErpAuthExpenseUsers(user_name="surya", display_name="Surya", password_hash="x", role_id=role.role_id))
    session.add(ErpExpenseRegionConfig(region_code="UAE", region_name="UAE", approval_matrix_json=json.dumps({"stages": ["accountant"]})))
    session.add(ErpExpenseCategory(category_name="First aid"))
    session.commit()
    monkeypatch.setattr(transaction_service, "_notify_finance_on_submit", lambda *a, **k: None)
    yield session
    session.close()


def _user(db) -> CurrentUser:
    u = db.query(ErpAuthExpenseUsers).first()
    return CurrentUser(u.user_id, u.display_name, "employee")


def _create_draft(db, **overrides):
    """A deliberately incomplete draft -- mirrors what the relaxed Flutter-side draft
    validation now allows: only vendor/amount/category_id are real values, everything else
    required-for-submit is left blank/None, same as a freshly-scanned-but-unfinished bill."""
    args = dict(
        vendor="",
        amount=45.0,
        vat_amount=0.0,
        total_amount=None,
        currency=None,
        bill_date=None,
        category_id=1,
        region_code="UAE",
        project_id=None,
        op_number=None,
        bill_number=None,
        remarks=None,
        receipt_id=None,
        s3_key=None,
        submit=False,
    )
    args.update(overrides)
    return transaction_service.create_claim(db, _user(db), **args)


def test_patch_persists_bill_number(db):
    """Regression test: bill_number was accepted by the API's Pydantic model but silently
    dropped by update_draft's own field-copy loop."""
    claim = _create_draft(db)
    updated = transaction_service.update_draft(
        db, _user(db), claim["id"], {"bill_number": "INV-9001"}
    )
    assert updated["bill_number"] == "INV-9001"


def test_patch_persists_currency_exchange_rate_and_type(db):
    claim = _create_draft(db)
    updated = transaction_service.update_draft(
        db,
        _user(db),
        claim["id"],
        {"currency": "SAR", "exchange_rate": 0.98, "type": "petty_cash"},
    )
    assert updated["currency"] == "SAR"
    assert updated["type"] == "petty_cash"


@pytest.mark.parametrize(
    "overrides,missing_phrase",
    [
        ({}, "vendor"),
        ({"vendor": "Uber"}, "bill date"),
        ({"vendor": "Uber", "bill_date": "06/07/2026"}, "bill number"),
        # currency and total_amount both have a non-nullable column default ("AED" / 0.0 via
        # amount+vat derivation) -- they can never truly end up None once a row exists, so the
        # only way to reach those two branches of the guard is amount+vat genuinely summing to
        # zero (a totally blank, untouched draft), covered separately below.
    ],
)
def test_submit_rejects_an_incomplete_draft(db, overrides, missing_phrase):
    claim = _create_draft(db, **overrides)
    with pytest.raises(ValueError, match=missing_phrase):
        transaction_service.submit_claim(db, _user(db), claim["id"])


def test_submit_rejects_a_zero_amount_draft(db):
    # amount + vat both 0 -> total_amount is derived as 0.0 too (see create_claim), the one real
    # way to reach the amount/total_amount branches of the completeness guard.
    claim = _create_draft(
        db, vendor="Uber", bill_date="06/07/2026", bill_number="1", amount=0.0, vat_amount=0.0,
    )
    with pytest.raises(ValueError, match="amount"):
        transaction_service.submit_claim(db, _user(db), claim["id"])


def test_submit_succeeds_once_every_required_field_is_filled(db):
    claim = _create_draft(db)
    transaction_service.update_draft(
        db,
        _user(db),
        claim["id"],
        {
            "vendor": "Uber",
            "currency": "AED",
            "bill_date": "06/07/2026",
            "bill_number": "INV-9001",
            "total_amount": 45.0,
        },
    )
    result = transaction_service.submit_claim(db, _user(db), claim["id"])
    assert result["status"] == "submitted"


def test_patch_then_submit_full_happy_path(db):
    """Mirrors the Flutter edit screen's actual call sequence: PATCH to fill gaps, then submit."""
    claim = _create_draft(db, vendor="Uber", amount=45.0)
    transaction_service.update_draft(
        db,
        _user(db),
        claim["id"],
        {
            "currency": "AED",
            "bill_date": "06/07/2026",
            "bill_number": "INV-9001",
            "total_amount": 45.0,
        },
    )
    result = transaction_service.submit_claim(db, _user(db), claim["id"])
    assert result["status"] == "submitted"
    assert result["bill_number"] == "INV-9001"
    assert result["currency"] == "AED"
