"""Runs the real production OCR pipeline (services.ocr_service.run) against actual
full-resolution phone photos pulled read-only from S3 (assets/real_uploads/, gitignored,
not committed -- someone's real uploaded data). The synthetic-fixture tests elsewhere in
this suite only ever exercise extraction/pipeline.py with hand-authored bounding boxes;
none of them run a real image through OCR end to end, so none of them could have caught
the vendor-extraction failures documented below. These are real, deterministic (RapidOCR
has zero variance across runs on this input) production images, not curated samples.
"""
from pathlib import Path

import pytest

from services.ocr_service import ocr_service

REAL_UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "real_uploads"

pytestmark = pytest.mark.skipif(
    not REAL_UPLOADS_DIR.exists(), reason="assets/real_uploads/ not present locally -- pull with scripts/ocr_compare's S3 download, not part of the repo"
)


def _run(filename: str) -> dict:
    path = REAL_UPLOADS_DIR / filename
    return ocr_service.run(path.read_bytes(), filename, mode="auto")


def test_enoc_receipt_975482b3_full_resolution():
    result = _run("975482b33a9e45869ba2bf6ea1bf2da0.jpg")
    assert "ENOC" in (result["vendor"] or "")
    assert result["amount"] == pytest.approx(6.0)
    assert result["total_amount"] == pytest.approx(6.0)
    assert result["currency"] == "AED"
    assert result["date"] == "8/18/2026"
    assert result["fields"]["cash_tendered"]["value"] == pytest.approx(10.0)
    assert result["fields"]["change"]["value"] == pytest.approx(4.0)
    assert result["fields"]["transaction_number"]["value"] == "584439"


def test_enoc_receipt_cd3a9f8d_full_resolution():
    result = _run("cd3a9f8de5a64788943634c22f90c967.jpg")
    assert "ENOC" in (result["vendor"] or "")
    assert result["amount"] == pytest.approx(6.0)
    assert result["currency"] == "AED"
    assert result["date"] == "8/18/2026"


def test_f6473b2c_pipeline_runs_and_extracts_a_total():
    # No independently-verified ground truth vendor for this one -- this is a regression
    # anchor (locks in today's actual behavior so a future change shows up as a diff),
    # not a claim that "الشارقة" is the correct vendor.
    result = _run("f6473b2cc8f9425bbb457c26ccc0005e.jpg")
    assert result["amount"] == pytest.approx(208.0)
    assert result["total_amount"] == pytest.approx(208.0)


def test_enoc_receipt_e66a83d5_vendor_no_longer_picks_the_status_fragment():
    # Was: _vendor_candidates() had no positive signal for "looks like a business name",
    # so a UI/status fragment ("S:Stan", conf 0.99) sitting above the real header won purely
    # for being first. Fixed by scoring shape (letter ratio, multi-word length, no leading
    # clock/label-colon pattern, relative line height) instead of trusting position alone.
    result = _run("e66a83d5e8024ef1af5c9330ccf9e659.jpg")
    assert "ENOC" in (result["vendor"] or "")


def test_non_receipt_screenshot_vendor_no_longer_picks_the_status_clock():
    # This image is a ride-payment screenshot, not a photographed receipt -- there is no real
    # vendor name to find. The bug was specifically the phone's status-bar clock ("13:59",
    # misread as "13:591<=*") winning the vendor slot; this only asserts that fragment no
    # longer wins, not that a "correct" vendor now exists for a document that has none.
    result = _run("70a968a35c9042ce965f29940b832820.jpg")
    assert result["vendor"] not in (None, "", "13:591≤·")
