"""Regression fixture for a real ENOC parsing failure ('VAT % 5' read as the VAT amount; 'Cash'/'Change' competing with the total) — every assertion below is reached purely via generic label-concept matching, never a branch on "ENOC" or any vendor name."""
import pytest

from extraction.pipeline import extract
from extraction.reference_data import ReferenceData
from tests.fixtures.ocr_lines import line, receipt


@pytest.fixture
def enoc_like_receipt():
    return receipt(
        line("ENOC Sale", bbox=(0, 0, 150, 20), order=0),
        line("Fuel Station - Sheikh Zayed Rd", bbox=(0, 20, 220, 40), order=1),
        line("Date 15/03/2026", bbox=(0, 40, 150, 60), order=2),
        line("VAT % 5", bbox=(0, 80, 100, 100), order=3),
        line("VAT Amt AED0.29", bbox=(0, 100, 150, 120), order=4),
        line("TOTAL AED6.00", bbox=(0, 160, 150, 180), order=5),
        line("Cash AED10.00", bbox=(0, 180, 150, 200), order=6),
        line("Change AED4.00", bbox=(0, 200, 150, 220), order=7),
        line("Terms & Conditions apply. No refund on fuel.", bbox=(0, 300, 300, 320), order=8),
    )


def test_vat_rate_vs_vat_amount_distinguished(enoc_like_receipt):
    result = extract(enoc_like_receipt, ReferenceData())
    assert result.fields["vat_rate"].value == pytest.approx(5.0)
    assert result.fields["vat_amount"].value == pytest.approx(0.29)


def test_total_not_confused_with_cash_or_change(enoc_like_receipt):
    result = extract(enoc_like_receipt, ReferenceData())
    assert result.fields["total_amount"].value == pytest.approx(6.00)
    assert result.fields["cash_tendered"].value == pytest.approx(10.00)
    assert result.fields["change"].value == pytest.approx(4.00)


def test_tendered_change_total_arithmetic_signal_present(enoc_like_receipt):
    result = extract(enoc_like_receipt, ReferenceData())
    assert "tendered_change_total_arithmetic" in result.fields["total_amount"].signals


def test_full_enoc_checklist_transaction_number_and_vendor():
    # The complete field checklist (vendor, transaction number, VAT/total/cash/change) for the full real-receipt result this pipeline was verified against.
    lines = receipt(
        line("ENOC RETAIL LLC", bbox=(0, 0, 200, 20), order=0),
        line("Date 15/03/2026", bbox=(0, 40, 150, 60), order=1),
        line("VAT % 5", bbox=(0, 80, 100, 100), order=2),
        line("VAT Amt AED0.29", bbox=(0, 100, 150, 120), order=3),
        line("TOTAL AED6.00", bbox=(0, 160, 150, 180), order=4),
        line("Cash AED10.00", bbox=(0, 180, 150, 200), order=5),
        line("Change AED4.00", bbox=(0, 200, 150, 220), order=6),
        line("TRAN 584439", bbox=(0, 220, 150, 240), order=7),
    )
    result = extract(lines, ReferenceData())
    assert result.fields["vendor"].value == "ENOC RETAIL LLC"
    assert result.fields["currency"].value == "AED"
    assert result.fields["vat_rate"].value == pytest.approx(5.0)
    assert result.fields["vat_amount"].value == pytest.approx(0.29)
    assert result.fields["total_amount"].value == pytest.approx(6.00)
    assert result.fields["cash_tendered"].value == pytest.approx(10.00)
    assert result.fields["change"].value == pytest.approx(4.00)
    assert result.fields["transaction_number"].value == "584439"
