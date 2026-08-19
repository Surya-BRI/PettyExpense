import pytest

from extraction.pipeline import extract
from extraction.reference_data import CategoryRef, ReferenceData
from tests.fixtures.ocr_lines import line, receipt


def test_unknown_vendor_still_extracted_via_positional_heuristics():
    lines = receipt(
        line("Zzyzxx Mart Pte Ltd 88291", order=0),
        line("Total AED 45.00", order=1),
    )
    result = extract(lines, ReferenceData(known_vendors=()))
    assert result.fields["vendor"].value == "Zzyzxx Mart Pte Ltd 88291"
    assert "known_vendor_match" not in result.fields["vendor"].signals


def test_known_vendor_boosts_confidence_but_is_not_required():
    lines = receipt(
        line("Zzyzxx Mart Pte Ltd 88291", order=0),
        line("Total AED 45.00", order=1),
    )
    without = extract(lines, ReferenceData(known_vendors=())).fields["vendor"]
    with_known = extract(lines, ReferenceData(known_vendors=("Zzyzxx Mart Pte Ltd 88291",))).fields["vendor"]
    assert with_known.confidence >= without.confidence
    assert "known_vendor_match" in with_known.signals


def test_novel_category_resolves_purely_from_injected_keyword():
    lines = receipt(
        line("Office World", order=0),
        line("Printer cartridges x2", order=1),
        line("Total AED 90.00", order=2),
    )
    reference_data = ReferenceData(categories=(CategoryRef(name="Office Supplies", keywords=("printer",)),))
    result = extract(lines, reference_data)
    assert result.fields["expense_category"].value == "Office Supplies"


def test_no_categories_configured_resolves_to_none():
    lines = receipt(line("Printer cartridges x2", order=0), line("Total AED 90.00", order=1))
    result = extract(lines, ReferenceData(categories=()))
    assert result.fields["expense_category"].value is None
    assert result.fields["expense_category"].warning == "no_evidence"
