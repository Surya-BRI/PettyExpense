"""Regression fixture for a real parsing failure seen on an ENOC (UAE fuel
station) receipt: 'VAT % 5' was being read as the VAT amount, and 'Cash
AED10.00' / 'Change AED4.00' were competing with the real total.

This is a REGRESSION TEST ONLY. Every assertion below is reached purely
through generic label-concept matching (VAT_TAX_RATE vs VAT_TAX_AMOUNT,
TOTAL, CASH, CHANGE) and the tendered-change-total arithmetic identity — the
engine never branches on the string "ENOC", or on any vendor/brand name. See
test_no_vendor_literals.py for a structural guardrail against regressing
this.
"""
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
