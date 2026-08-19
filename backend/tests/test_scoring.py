from extraction.reference_data import ReferenceData
from extraction.scoring import ScoringContext, score_candidate
from extraction.types import FieldCandidate


def _ctx(**overrides):
    defaults = dict(page_height=None, max_reading_order=10, reference_data=ReferenceData())
    defaults.update(overrides)
    return ScoringContext(**defaults)


def test_labeled_candidate_scores_higher_than_unlabeled():
    labeled = FieldCandidate("total_amount", 45.0, "Total AED 45.00", 0.9, signals=["total_label", "same_line", "currency_value"])
    unlabeled = FieldCandidate("total_amount", 45.0, "45.00", 0.9, signals=["no_label_bare_number", "currency_value"])
    labeled_score = score_candidate(labeled, _ctx())
    unlabeled_score = score_candidate(unlabeled, _ctx())
    assert labeled_score > unlabeled_score


def test_fuzzy_label_scores_lower_than_exact_label():
    exact = FieldCandidate("total_amount", 45.0, "Total 45.00", 0.9, signals=["total_label", "same_line", "currency_value"])
    fuzzy = FieldCandidate("total_amount", 45.0, "Aaount 45.00", 0.9, signals=["total_label", "same_line", "fuzzy_label_match", "currency_value"])
    assert score_candidate(exact, _ctx()) > score_candidate(fuzzy, _ctx())


def test_known_vendor_match_boosts_score():
    plain = FieldCandidate("vendor", "Zzyzxx Mart", "Zzyzxx Mart", 0.8, signals=["top_of_receipt"])
    known = FieldCandidate("vendor", "Zzyzxx Mart", "Zzyzxx Mart", 0.8, signals=["top_of_receipt", "known_vendor_match"])
    assert score_candidate(known, _ctx()) > score_candidate(plain, _ctx())


def test_phone_like_number_penalized_in_money_field():
    money = FieldCandidate("total_amount", 45.0, "Total 45.00", 0.9, signals=["total_label", "same_line", "currency_value"])
    phone_like = FieldCandidate("total_amount", 12345.0, "Total 12345", 0.9, signals=["total_label", "same_line", "currency_value", "no_decimal_point"])
    assert score_candidate(money, _ctx()) > score_candidate(phone_like, _ctx())
