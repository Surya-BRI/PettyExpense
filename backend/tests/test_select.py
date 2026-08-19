from extraction.select import select_fields
from extraction.types import FieldCandidate


def test_no_candidates_returns_none_with_warning():
    selected = select_fields([])
    assert selected["total_amount"].value is None
    assert selected["total_amount"].warning == "no_evidence"


def test_single_strong_candidate_selected_confidently():
    candidates = [FieldCandidate("total_amount", 45.0, "Total 45.00", 0.9, signals=["total_label"])]
    selected = select_fields(candidates)
    assert selected["total_amount"].value == 45.0
    assert selected["total_amount"].low_confidence is False


def test_low_confidence_candidate_nulled_out():
    candidates = [FieldCandidate("total_amount", 45.0, "45.00", 0.1, signals=["no_label_bare_number"])]
    selected = select_fields(candidates)
    assert selected["total_amount"].value is None
    assert selected["total_amount"].warning == "low_confidence_all_candidates"


def test_ambiguous_close_candidates_kept_but_flagged():
    candidates = [
        FieldCandidate("total_amount", 45.0, "Total 45.00", 0.5, signals=["total_label"]),
        FieldCandidate("total_amount", 46.0, "Total 46.00", 0.48, signals=["total_label"]),
    ]
    selected = select_fields(candidates)
    assert selected["total_amount"].value == 45.0
    assert selected["total_amount"].low_confidence is True
    assert selected["total_amount"].warning == "ambiguous_candidates"


def test_derived_arithmetic_fallback_when_amount_missing():
    candidates = [
        FieldCandidate("total_amount", 105.0, "Total 105.00", 0.9, signals=["total_label"]),
        FieldCandidate("vat_amount", 5.0, "VAT 5.00", 0.9, signals=["vat_tax_amount_label"]),
    ]
    selected = select_fields(candidates)
    assert selected["amount"].value == 100.0
    assert selected["amount"].signals == ["derived_arithmetic"]
    assert selected["amount"].confidence <= 0.4
