"""Regression tests for general Arabic-receipt support — synthetic mocked OCR lines only, no real images or vendor-specific literals in any assertion."""
import pytest

from extraction.labels import LabelConcept, match_label_concepts
from extraction.pipeline import extract
from extraction.reference_data import ReferenceData
from tests.fixtures.ocr_lines import line, receipt


def test_generic_arabic_business_word_alone_is_not_a_vendor():
    # "شركة" ("Company") alone is too generic to be a vendor name — a real vendor candidate lower down should win instead.
    lines = receipt(
        line("شركة", order=0),
        line("قمة الخليج المحدودة للأجرة العامة", order=1),
        line("Total AED 45.00", order=2),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["vendor"].value != "شركة"


def test_generic_word_inside_a_real_name_is_not_rejected():
    # The same generic word as PART of a longer real name must not be rejected — only a candidate that is JUST the generic word is excluded.
    lines = receipt(
        line("Qamar Alhuda Aljadeed General Trading L.L.C", order=0),
        line("Total AED 45.00", order=1),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["vendor"].value == "Qamar Alhuda Aljadeed General Trading L.L.C"


@pytest.mark.parametrize(
    "amount_text, expected_currency",
    [
        ("45.00 ريال", "SAR"),
        ("45.00 ر.س", "SAR"),
    ],
)
def test_riyal_variants_map_to_sar(amount_text, expected_currency):
    lines = receipt(line(f"Total {amount_text}", order=0))
    result = extract(lines, ReferenceData())
    assert result.fields["currency"].value == expected_currency


@pytest.mark.parametrize(
    "label_text",
    ["المجموع فقط", "الإجمالي", "المبلغ الإجمالي"],
)
def test_arabic_total_label_synonyms_recognized(label_text):
    matches = match_label_concepts(f"{label_text} 45.00", ReferenceData().label_vocabulary)
    assert LabelConcept.TOTAL in {m.concept for m in matches}


def test_arabic_receipt_no_vat_evidence_reports_zero_not_null():
    lines = receipt(
        line("قمة الخليج المحدودة للأجرة العامة", order=0),
        line("المجموع فقط 45.00", order=1),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["total_amount"].value == pytest.approx(45.00)
    assert result.fields["vat_amount"].value == pytest.approx(0.0)
    assert result.fields["vat_amount"].low_confidence is False
    assert result.fields["amount"].value == pytest.approx(45.00)


def test_arabic_bill_one_full_business_result():
    # "Arabic Bill 1": complete vendor name (not a bare generic prefix), SAR currency, no-VAT total that also becomes the amount, no mismatch.
    lines = receipt(
        line("قمة الخليج المحدودة للأجرة العامة", order=0, lang="ar"),
        line("المجموع فقط 45.00 SAR", order=1, lang="ar"),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["vendor"].value != "شركة"
    assert len(result.fields["vendor"].value or "") > len("شركة")
    assert result.fields["currency"].value == "SAR"
    assert result.fields["amount"].value == pytest.approx(45.0)
    assert result.fields["vat_amount"].value == pytest.approx(0.0)
    assert result.fields["total_amount"].value == pytest.approx(45.0)
    assert result.reconciliation_mismatch is False


def test_arabic_bill_two_full_business_result():
    # "Arabic Bill 2": exact two-line-wrapped vendor name, SAR, no-VAT total==amount, no mismatch. Date/invoice number aren't asserted — not reliably recoverable on the real receipt, and inventing them would violate "low confidence rather than invented".
    lines = receipt(
        line("شركة سلطان منير الحارثي وشريكه", bbox=(126, 35, 574, 95), order=0, lang="ar"),
        line("للأجرة العامة", bbox=(268, 87, 429, 136), order=1, lang="ar"),
        line("المجموع فقط 45", bbox=(100, 400, 400, 440), order=2, lang="ar"),
        line("SAR", bbox=(100, 440, 200, 470), order=3, lang="ar"),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["vendor"].value == "شركة سلطان منير الحارثي وشريكه للأجرة العامة"
    assert result.fields["currency"].value == "SAR"
    assert result.fields["amount"].value == pytest.approx(45.0)
    assert result.fields["vat_amount"].value == pytest.approx(0.0)
    assert result.fields["total_amount"].value == pytest.approx(45.0)
    assert result.reconciliation_mismatch is False


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("25 / 06 / 26", "25/06/26"),
        ("25/ 06 /26", "25/06/26"),
    ],
)
def test_date_slash_spacing_normalized(raw, expected):
    from extraction.normalize import normalize_text

    assert normalize_text(raw) == expected


def test_date_rejects_month_over_12_in_dmy_order():
    # 25/13/26: "month" 13 is invalid in DD/MM/YY order — must be rejected (an old loose check only required both parts <=31, wrongly accepting this).
    lines = receipt(line("Date 25/13/26", order=0))
    result = extract(lines, ReferenceData())
    assert result.fields["date"].value != "25/13/26"


def test_date_accepts_valid_dmy():
    lines = receipt(line("Date 25/06/26", order=0))
    result = extract(lines, ReferenceData())
    assert result.fields["date"].value == "25/06/26"


def test_date_accepts_valid_dmy_four_digit_year():
    lines = receipt(line("التاريخ 25/06/2026", order=0, lang="ar"))
    result = extract(lines, ReferenceData())
    assert result.fields["date"].value == "25/06/2026"


def test_unknown_currency_does_not_default_to_aed():
    # No recognizable currency evidence anywhere — must come back null (forcing manual selection), never silently default to AED.
    lines = receipt(
        line("Some Vendor", order=0),
        line("Total 45.00", order=1),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["currency"].value is None
    assert result.fields["currency"].value != "AED"


def test_arabic_vendor_text_is_not_reversed():
    original = "شركة سلطان منير الحارثي وشريكه"
    lines = receipt(line(original, order=0, lang="ar"), line("Total SAR 45.00", order=1))
    result = extract(lines, ReferenceData())
    assert result.fields["vendor"].value == original
    assert result.fields["vendor"].value != original[::-1]


def test_reconciliation_not_flagged_when_a_required_field_is_missing():
    # A real vat_amount with no printed total anywhere would get flagged as a candidate-level mismatch — but once total_amount resolves to null, there's nothing to compare against, so it must not surface.
    lines = receipt(
        line("VAT Amount 12.34", order=0),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["total_amount"].value is None
    assert result.reconciliation_mismatch is False


def test_multiline_vendor_header_merges_top_to_bottom():
    # Two stacked, aligned lines with no digits/comma — a wrapped vendor name plus its legal-entity suffix — merge into one candidate, top line first.
    lines = receipt(
        line("Bright Sands Trading", bbox=(10, 10, 300, 50), order=0),
        line("General Est", bbox=(10, 50, 300, 90), order=1),
        line("Total AED 45.00", bbox=(10, 400, 300, 440), order=2),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["vendor"].value == "Bright Sands Trading General Est"


def test_multiline_merge_does_not_swallow_an_address_line():
    # A digit-dominated P.O.-Box line sits between the vendor name and a city line — merge must stop at the vendor name, not skip past or absorb it.
    lines = receipt(
        line("Bright Sands Trading", bbox=(10, 10, 300, 50), order=0),
        line("P.O. Box 5589", bbox=(10, 52, 300, 90), order=1),
        line("Some City", bbox=(10, 92, 300, 130), order=2),
        line("Total AED 45.00", bbox=(10, 400, 300, 440), order=3),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["vendor"].value == "Bright Sands Trading"
