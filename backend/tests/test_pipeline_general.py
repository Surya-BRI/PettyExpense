import pytest

from extraction.pipeline import extract
from extraction.reference_data import ReferenceData
from tests.fixtures.ocr_lines import line, receipt


def test_label_and_value_same_line(default_reference_data):
    lines = receipt(
        line("SuperMart", order=0),
        line("Total AED 45.00", order=1),
        line("Date 12/03/2026", order=2),
    )
    result = extract(lines, default_reference_data)
    assert result.fields["total_amount"].value == pytest.approx(45.00)
    assert result.fields["total_amount"].evidence == "Total AED 45.00"
    assert any(s.endswith("_label") for s in result.fields["total_amount"].signals)


def test_value_on_following_line(default_reference_data):
    lines = receipt(line("Total", order=0), line("AED 45.00", order=1))
    result = extract(lines, default_reference_data)
    assert result.fields["total_amount"].value == pytest.approx(45.00)


def test_label_and_value_in_separate_bbox_regions(default_reference_data):
    lines = receipt(
        line("Total", bbox=(0, 0, 50, 20), order=0),
        line("AED 45.00", bbox=(200, 0, 260, 20), order=1),
    )
    result = extract(lines, default_reference_data)
    assert result.fields["total_amount"].value == pytest.approx(45.00)
    assert "same_row" in result.fields["total_amount"].signals


def test_tax_exclusive_total(default_reference_data):
    lines = receipt(
        line("Amount 100.00", order=0),
        line("VAT 5.00", order=1),
        line("Total 105.00", order=2),
    )
    result = extract(lines, default_reference_data)
    assert result.fields["amount"].value == pytest.approx(100.00)
    assert result.fields["vat_amount"].value == pytest.approx(5.00)
    assert result.fields["total_amount"].value == pytest.approx(105.00)
    assert result.reconciliation_mismatch is False


def test_tax_inclusive_total_derives_vat_and_subtotal(default_reference_data):
    lines = receipt(line("VAT Rate 5%", order=0), line("Total 105.00", order=1))
    result = extract(lines, default_reference_data)
    assert result.fields["vat_rate"].value == pytest.approx(5.0)
    assert result.fields["vat_amount"].value == pytest.approx(5.00)
    assert result.fields["amount"].value == pytest.approx(100.00)


def test_no_vat_receipt_leaves_vat_fields_empty(default_reference_data):
    lines = receipt(line("SuperMart", order=0), line("Total AED 45.00", order=1))
    result = extract(lines, default_reference_data)
    assert result.fields["vat_amount"].value is None
    assert result.fields["vat_amount"].warning == "no_evidence"
    assert result.fields["total_amount"].value == pytest.approx(45.00)


@pytest.mark.parametrize(
    "amount_text, expected_currency, expected_amount",
    [
        ("AED 1,234.56", "AED", 1234.56),
        ("€1.234,56", "EUR", 1234.56),
        ("SR 45.00", "SAR", 45.00),
        ("45,00 ر.س", "SAR", 45.00),
    ],
)
def test_multi_currency_and_decimal_formats(default_reference_data, amount_text, expected_currency, expected_amount):
    lines = receipt(line(f"Total {amount_text}", order=0))
    result = extract(lines, default_reference_data)
    assert result.fields["currency"].value == expected_currency
    assert result.fields["total_amount"].value == pytest.approx(expected_amount)


def test_multiple_dates_picks_labeled_transaction_date(default_reference_data):
    lines = receipt(
        line("Invoice Date 01/02/2026", order=0),
        line("Best Before 01/02/2027", order=1),
    )
    result = extract(lines, default_reference_data)
    assert result.fields["date"].value == "01/02/2026"


def test_cash_and_change_not_confused_with_total(default_reference_data):
    lines = receipt(
        line("Total AED 40.00", order=0),
        line("Cash AED 50.00", order=1),
        line("Change AED 10.00", order=2),
    )
    result = extract(lines, default_reference_data)
    assert result.fields["total_amount"].value == pytest.approx(40.00)
    assert result.fields["cash_tendered"].value == pytest.approx(50.00)
    assert result.fields["change"].value == pytest.approx(10.00)


def test_noisy_duplicated_ocr_output_does_not_break_extraction(default_reference_data):
    lines = receipt(
        line("Total AED45.00", order=0, confidence=0.9),
        line("Totai AED45,00", order=1, confidence=0.6),  # noisy duplicate of the same line
    )
    result = extract(lines, default_reference_data)
    assert result.fields["total_amount"].value == pytest.approx(45.00)
