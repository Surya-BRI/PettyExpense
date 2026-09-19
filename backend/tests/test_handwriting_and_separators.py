"""Regression tests for a real ksa2.png bug: the recognizer misreads a handwritten '/' as '1' ("45/." -> "451.") before any Python code sees it, so no text-level fix can recover it — the real fix is flagging low recognition confidence (see select.py's LOW_OCR_CONFIDENCE_THRESHOLD) instead of trusting the number outright."""
import pytest

from extraction.normalize import parse_amount
from extraction.pipeline import extract
from extraction.reference_data import ReferenceData
from extraction.select import LOW_OCR_CONFIDENCE_THRESHOLD
from tests.fixtures.ocr_lines import line, receipt


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("45/.", 45.0),
        ("45/", 45.0),
        ("45.", 45.0),
        # Regression guard: currency-glued and plain decimal formats must still parse correctly.
        ("AED0.29", 0.29),
        ("AED6.00", 6.0),
        ("6.00", 6.0),
        ("0.29", 0.29),
    ],
)
def test_separator_and_currency_formats_parse_correctly(raw, expected):
    assert parse_amount(raw) == pytest.approx(expected)


def test_handwritten_misread_total_is_flagged_not_confidently_wrong():
    # Simulates the real ksa2.png failure in isolation: a misread, unlabeled, low-confidence total with no other evidence to correct it must never come back as confidently correct.
    lines = receipt(
        line("Some Vendor", confidence=0.98, order=0),
        line("451.", confidence=0.836, order=1),  # the misread; no label anywhere nearby
    )
    result = extract(lines, ReferenceData())
    assert result.fields["total_amount"].value == pytest.approx(451.0)
    assert result.fields["total_amount"].low_confidence is True
    assert result.fields["total_amount"].warning == "low_ocr_confidence_possible_handwriting"


def test_correctly_read_handwritten_total_is_still_flagged_for_review():
    # Even when label evidence picks the CORRECT value, the underlying handwritten recognition was still low-confidence and must be flagged for review.
    lines = receipt(
        line("Some Vendor", confidence=0.98, order=0),
        line("Total 45/.", confidence=0.848, order=1),  # label + the correctly-read handwritten value
    )
    result = extract(lines, ReferenceData())
    assert result.fields["total_amount"].value == pytest.approx(45.0)
    assert result.fields["total_amount"].low_confidence is True
    assert result.fields["total_amount"].warning == "low_ocr_confidence_possible_handwriting"


def test_normal_printed_total_is_not_flagged():
    # Regression guard: an ordinary well-recognized printed total (0.93+, matching real receipts) must NOT be dragged down to low-confidence.
    assert 0.95 >= LOW_OCR_CONFIDENCE_THRESHOLD  # sanity: the fixture below is meant to clear the bar
    lines = receipt(
        line("Some Vendor", confidence=0.98, order=0),
        line("Total AED 45.00", confidence=0.98, order=1),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["total_amount"].value == pytest.approx(45.0)
    assert result.fields["total_amount"].low_confidence is False
    assert result.fields["total_amount"].warning is None


def test_recognizer_slash_misread_does_not_fabricate_a_date():
    # The same '/' -> '1' misread hit a real handwritten date: "25/06/26" -> "25106/26", leaving only one slash, so the DD/MM/YY(YY) pattern can't match — must resolve to no date, not a wrong guess.
    lines = receipt(line("Date 25106/26", order=0))
    result = extract(lines, ReferenceData())
    assert result.fields["date"].value is None
