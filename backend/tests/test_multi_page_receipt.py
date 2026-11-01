"""Multi-page bills: every page is stored, GPT gets all pages in one call, the claim lists them in order.

Same in-memory SQLite setup as test_claim_line_items.py; S3 and GPT are faked.
"""
import os

for _k in ("READER_DB_SERVER", "READER_DB_NAME", "READER_DB_USER", "READER_DB_PASSWORD"):
    os.environ.setdefault(_k, "test")

import json  # noqa: E402
import sys  # noqa: E402

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

txn_module = sys.modules["services.transaction_service"]


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
    session.add(ErpExpenseCategory(category_name="Stationery"))
    session.commit()
    monkeypatch.setattr(transaction_service, "_notify_finance_on_submit", lambda *a, **k: None)
    yield session
    session.close()


@pytest.fixture
def storage(monkeypatch):
    """In-memory S3: key -> bytes. Presigning fails so URLs fall back to the proxy paths."""
    blobs: dict[str, bytes] = {}

    def save_bytes(data, content_type="image/jpeg", ext="jpg"):
        key = f"test/{len(blobs) + 1}.{ext}"
        blobs[key] = data
        return key

    store = txn_module.storage_service
    monkeypatch.setattr(store, "save_bytes", save_bytes)
    monkeypatch.setattr(store, "read_bytes", lambda key: blobs.get(key))
    monkeypatch.setattr(store, "presigned_url", lambda key, expires_in=3600: None)
    monkeypatch.setattr(txn_module, "refresh_reference_data", lambda db: None)
    return blobs


def _user(db) -> CurrentUser:
    u = db.query(ErpAuthExpenseUsers).first()
    return CurrentUser(u.user_id, u.display_name, "employee")


def _store_three_pages(db):
    return transaction_service.store_receipt(
        db, b"page-1", "image/jpeg", "p1.jpg",
        extra_pages=[(b"page-2", "image/jpeg", "p2.jpg"), (b"page-3", "image/png", "p3.png")],
    )


def test_upload_stores_every_page_in_order(db, storage):
    stored = _store_three_pages(db)

    rid = stored["receipt_id"]
    assert stored["page_count"] == 3
    assert [p["page_no"] for p in stored["pages"]] == [1, 2, 3]
    assert stored["pages"][0]["image_url"] == f"/api/claims/receipts/{rid}/image"
    assert stored["pages"][2]["image_url"] == f"/api/claims/receipts/{rid}/pages/3/image"
    assert storage[transaction_service.get_receipt_page(db, rid, 3).s3_key] == b"page-3"


def test_single_page_upload_is_unchanged(db, storage):
    stored = transaction_service.store_receipt(db, b"only", "image/jpeg", "p.jpg")
    assert stored["page_count"] == 1 and len(storage) == 1


def test_analyze_sends_all_pages_to_gpt_in_one_call(db, storage, monkeypatch):
    calls = []

    def run(images, filename, mode="auto", region_code=None):
        calls.append(images)
        return {"vendor": "Jannat", "amount": 100.0, "vat_amount": 5.0, "total_amount": 105.0,
                "currency": "AED", "date": "2026-07-21", "confidence": 0.9, "raw_json": {}}

    monkeypatch.setattr(txn_module.ocr_service, "run", run)
    stored = _store_three_pages(db)
    result = transaction_service.analyze_receipt(db, stored["receipt_id"])

    assert calls == [[b"page-1", b"page-2", b"page-3"]]
    assert result["total_amount"] == 105.0 and result["page_count"] == 3


def test_claim_detail_lists_every_page(db, storage):
    stored = _store_three_pages(db)
    claim = transaction_service.create_claim(
        db, _user(db), vendor="Jannat", amount=100.0, vat_amount=5.0, total_amount=105.0, currency="AED",
        bill_date="21/07/2026", category_id=1, region_code="UAE", project_id=None, op_number=None,
        bill_number=None, remarks=None, receipt_id=stored["receipt_id"], s3_key=None, submit=False,
    )
    detail = transaction_service.get_claim(db, _user(db), claim["id"])

    assert [p["page_no"] for p in detail["receipt"]["pages"]] == [1, 2, 3]
    # List views skip pages so they don't load every claim's pages.
    mine = transaction_service.list_mine(db, _user(db))
    assert "pages" not in mine["items"][0]["receipt"]
