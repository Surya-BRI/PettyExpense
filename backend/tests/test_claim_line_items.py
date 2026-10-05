"""Saving "Multiple items" claims: lines are stored, totals come from the lines, edits replace them.

Runs the real service code against the real SQLAlchemy models on a throwaway in-memory
SQLite database (the app itself only ever uses SQL Server).
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
    session.add_all([ErpExpenseCategory(category_name="First aid"), ErpExpenseCategory(category_name="Stationery")])
    session.commit()
    # No notification/approver side effects in these tests.
    monkeypatch.setattr(transaction_service, "_notify_finance_on_submit", lambda *a, **k: None)
    yield session
    session.close()


def _user(db) -> CurrentUser:
    u = db.query(ErpAuthExpenseUsers).first()
    return CurrentUser(u.user_id, u.display_name, "employee")


def _create(db, **overrides):
    args = dict(
        vendor="Bab Al Hayat Pharmacy",
        amount=0.0,
        vat_amount=0.0,
        total_amount=None,
        currency="AED",
        bill_date="06/07/2026",
        category_id=1,
        region_code="UAE",
        project_id=None,
        op_number=None,
        remarks=None,
        receipt_id=None,
        s3_key=None,
        submit=False,
    )
    args.update(overrides)
    return transaction_service.create_claim(db, _user(db), **args)


def test_total_is_the_sum_of_the_lines_and_amount_excludes_vat(db):
    claim = _create(
        db,
        vat_amount=1.50,
        # Whatever the client sent for amount/total is replaced by the line-derived values.
        amount=999.0,
        total_amount=999.0,
        line_items=[
            {"description": "Gauze swab", "quantity": 5, "amount": 23.94, "category_id": 1},
            {"description": "Scissor", "quantity": 1, "amount": 7.66, "category_id": 2},
        ],
    )
    assert claim["line_mode"] == "multiple"
    assert claim["total_amount"] == 31.60
    assert claim["amount"] == 30.10
    assert [(li["line_no"], li["description"], li["category_name"]) for li in claim["line_items"]] == [
        (1, "Gauze swab", "First aid"),
        (2, "Scissor", "Stationery"),
    ]


def test_single_item_claim_has_no_lines(db):
    claim = _create(db, amount=100.0, vat_amount=5.0)
    assert claim["line_mode"] == "single"
    assert claim["line_items"] == []
    assert claim["total_amount"] == 105.0


def test_editing_a_draft_replaces_its_lines_and_recomputes(db):
    claim = _create(db, line_items=[{"description": "Gauze swab", "amount": 23.94, "category_id": 1}])
    updated = transaction_service.update_draft(
        db,
        _user(db),
        claim["id"],
        {"line_items": [
            {"description": "Cotton wool", "amount": 10.00, "category_id": 1},
            {"description": "Plaster", "amount": 2.87, "category_id": 1},
        ]},
    )
    assert [li["description"] for li in updated["line_items"]] == ["Cotton wool", "Plaster"]
    assert updated["total_amount"] == 12.87


@pytest.mark.parametrize(
    "bad_line, message",
    [
        ({"description": "  ", "amount": 5.0}, "description"),
        ({"description": "Swab", "amount": -1.0}, "amount"),
        ({"description": "Swab", "amount": None}, "amount"),
        ({"description": "Swab", "amount": 5.0, "category_id": 999}, "category"),
    ],
)
def test_invalid_lines_are_rejected(db, bad_line, message):
    with pytest.raises(ValueError, match=message):
        _create(db, line_items=[bad_line])


def test_vat_larger_than_the_lines_is_rejected(db):
    with pytest.raises(ValueError, match="VAT"):
        _create(db, vat_amount=50.0, line_items=[{"description": "Swab", "amount": 10.0}])
