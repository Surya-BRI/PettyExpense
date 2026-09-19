from extraction.reference_data import ReferenceData
from extraction.types import FieldCandidate
from extraction.validation import validate_and_adjust


def test_bare_rate_like_vat_amount_is_demoted_and_rate_candidate_added():
    candidates = [
        FieldCandidate("vat_amount", 5.0, "VAT 5", 0.6, signals=["vat_tax_amount_label", "same_line", "currency_value", "no_decimal_point"]),
        FieldCandidate("total_amount", 105.0, "Total 105.00", 0.9, signals=["total_label", "same_line", "currency_value"]),
    ]
    adjusted, _ = validate_and_adjust(candidates, ReferenceData())
    vat_amount_candidates = [c for c in adjusted if c.field_name == "vat_amount"]
    vat_rate_candidates = [c for c in adjusted if c.field_name == "vat_rate"]
    assert vat_amount_candidates[0].confidence < 0.6
    assert "looks_like_rate_not_amount" in vat_amount_candidates[0].signals
    assert any(r.value == 5.0 for r in vat_rate_candidates)


def test_tax_exclusive_reconciliation_boosts_and_clears_mismatch():
    candidates = [
        FieldCandidate("amount", 100.0, "Amount 100.00", 0.5, signals=["subtotal_label"]),
        FieldCandidate("vat_amount", 5.0, "VAT 5.00", 0.5, signals=["vat_tax_amount_label"]),
        FieldCandidate("total_amount", 105.0, "Total 105.00", 0.5, signals=["total_label"]),
    ]
    adjusted, mismatch = validate_and_adjust(candidates, ReferenceData())
    assert mismatch is False
    amount = next(c for c in adjusted if c.field_name == "amount")
    assert "arithmetic_reconciled_exclusive" in amount.signals
    assert amount.confidence > 0.5


def test_reconciliation_mismatch_when_neither_convention_fits():
    candidates = [
        FieldCandidate("amount", 100.0, "Amount 100.00", 0.5, signals=["subtotal_label"]),
        FieldCandidate("vat_amount", 5.0, "VAT 5.00", 0.5, signals=["vat_tax_amount_label"]),
        FieldCandidate("total_amount", 999.0, "Total 999.00", 0.5, signals=["total_label"]),
    ]
    _, mismatch = validate_and_adjust(candidates, ReferenceData())
    assert mismatch is True


def test_cash_and_change_do_not_win_total_slot():
    candidates = [
        FieldCandidate("total_amount", 40.0, "Total AED 40.00", 0.5, signals=["total_label", "same_line"]),
        FieldCandidate("total_amount", 50.0, "Cash AED 50.00", 0.3, signals=["no_label_bare_number"]),  # spurious
        FieldCandidate("cash_tendered", 50.0, "Cash AED 50.00", 0.5, signals=["cash_label", "same_line"]),
        FieldCandidate("change", 10.0, "Change AED 10.00", 0.5, signals=["change_label", "same_line"]),
    ]
    adjusted, _ = validate_and_adjust(candidates, ReferenceData())
    totals = sorted((c for c in adjusted if c.field_name == "total_amount"), key=lambda c: c.confidence, reverse=True)
    assert totals[0].value == 40.0
    spurious = next(c for c in totals if c.value == 50.0)
    assert "looks_like_cash_or_change_not_total" in spurious.signals
