from extraction.labels import LabelConcept, match_label_concepts
from extraction.reference_data import ReferenceData


def _vocab():
    return ReferenceData().label_vocabulary


def _exclusions():
    return ReferenceData().label_exclusions


def test_exact_substring_match():
    matches = match_label_concepts("Total AED 45.00", _vocab())
    concepts = {m.concept for m in matches}
    assert LabelConcept.TOTAL in concepts
    total_match = next(m for m in matches if m.concept == LabelConcept.TOTAL)
    assert total_match.fuzzy is False


def test_vat_rate_vs_vat_amount_distinct_concepts():
    rate_matches = {m.concept for m in match_label_concepts("VAT % 5", _vocab())}
    amount_matches = {m.concept for m in match_label_concepts("VAT Amt AED0.29", _vocab())}
    assert LabelConcept.VAT_TAX_RATE in rate_matches
    assert LabelConcept.VAT_TAX_RATE not in amount_matches
    assert LabelConcept.VAT_TAX_AMOUNT in amount_matches


def test_fuzzy_match_catches_ocr_garbling():
    matches = match_label_concepts("Aaount Due 45.00", _vocab())
    # "Aaount" is a garbled "Amount" -> should still fuzzy-match TOTAL's "amount due" synonym
    assert any(m.concept == LabelConcept.TOTAL and m.fuzzy for m in matches)


def test_no_false_match_on_unrelated_text():
    matches = match_label_concepts("Fresh Bananas 2kg", _vocab())
    assert matches == []


def test_arabic_synonym_matches():
    matches = match_label_concepts("الإجمالي 45.00", _vocab())
    assert any(m.concept == LabelConcept.TOTAL for m in matches)


def test_negated_label_is_not_matched():
    # Boilerplate policy text ("No Cash Refund") must not be read as a "cash paid" label — the same footer-vs-content distinction, via negation words.
    matches = match_label_concepts("No Cash Refund, Thank You, Visit Again", _vocab())
    assert LabelConcept.CASH not in {m.concept for m in matches}


def test_total_savings_and_total_qty_are_not_the_grand_total():
    savings = match_label_concepts("Total savings: AED0.00", _vocab(), _exclusions())
    qty = match_label_concepts("Total Qty: 6.05", _vocab(), _exclusions())
    assert LabelConcept.TOTAL not in {m.concept for m in savings}
    assert LabelConcept.TOTAL not in {m.concept for m in qty}


def test_vat_registration_number_is_not_a_vat_amount_label():
    matches = match_label_concepts("VAT Reg Number: 100221692500003", _vocab())
    concepts = {m.concept for m in matches}
    assert LabelConcept.VAT_TAX_AMOUNT not in concepts
    assert LabelConcept.TAX_REGISTRATION_NUMBER in concepts
