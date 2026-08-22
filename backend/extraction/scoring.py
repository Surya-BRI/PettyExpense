"""Stage 6: score candidates using generic signals (label, position, OCR confidence, format, reference-data match); every signal is recorded for explainability."""
from dataclasses import dataclass
from typing import Optional

from extraction.reference_data import ReferenceData
from extraction.types import FieldCandidate, OcrLine

_LOWER_ON_PAGE_FIELDS = {
    "total_amount", "amount", "vat_amount", "discount", "service_charge",
    "tip", "cash_tendered", "card_amount", "change",
}
_UPPER_ON_PAGE_FIELDS = {"vendor", "date", "invoice_number", "transaction_number", "currency"}
_MONEY_FIELDS = _LOWER_ON_PAGE_FIELDS - {"vat_amount"} | {"vat_amount"}


@dataclass
class ScoringContext:
    page_height: Optional[float]
    max_reading_order: int
    reference_data: ReferenceData


def build_scoring_context(lines: list[OcrLine], reference_data: ReferenceData) -> ScoringContext:
    boxes = [ln.bounding_box for ln in lines if ln.bounding_box is not None]
    page_height = max((b[3] for b in boxes), default=None)
    max_reading_order = max((ln.reading_order for ln in lines), default=0)
    return ScoringContext(page_height=page_height, max_reading_order=max_reading_order, reference_data=reference_data)


def _looks_like_phone_or_id(value) -> bool:
    if not isinstance(value, (int, float)) or value != int(value):
        return False
    digits = str(int(value))
    return len(digits) >= 5 and value >= 10000


def _normalized_position(candidate: FieldCandidate, context: ScoringContext) -> Optional[float]:
    if candidate.bounding_box is not None and context.page_height:
        y_center = (candidate.bounding_box[1] + candidate.bounding_box[3]) / 2.0
        return min(1.0, max(0.0, y_center / context.page_height))
    if context.max_reading_order > 0:
        return min(1.0, candidate.reading_order / context.max_reading_order)
    return None


def _position_prior(candidate: FieldCandidate, context: ScoringContext) -> tuple[float, Optional[str]]:
    pos = _normalized_position(candidate, context)
    if pos is None:
        return 0.0, None
    if candidate.field_name in _LOWER_ON_PAGE_FIELDS:
        return 0.15 * pos, "position_prior_lower"
    if candidate.field_name in _UPPER_ON_PAGE_FIELDS:
        return 0.15 * (1.0 - pos), "position_prior_upper"
    return 0.0, None


def _format_plausibility(candidate: FieldCandidate) -> tuple[float, Optional[str]]:
    field = candidate.field_name
    if field in _LOWER_ON_PAGE_FIELDS:
        value = candidate.value
        if value is None:
            return 0.0, None
        if _looks_like_phone_or_id(value):
            return -0.2, "format_penalty_id_like"
        has_decimal = "no_decimal_point" not in candidate.signals
        return (0.15, "format_decimal_money") if has_decimal else (0.07, "format_integer_money")
    if field == "vat_rate":
        if "known_vat_rate" in candidate.signals:
            return 0.15, "format_known_vat_rate"
        if isinstance(candidate.value, (int, float)) and 0 <= candidate.value <= 100:
            return 0.06, "format_plausible_rate"
        return -0.1, "format_penalty_implausible_rate"
    if field == "date":
        return 0.1, "format_date_shape"
    return 0.0, None


def _label_and_location_weight(candidate: FieldCandidate) -> tuple[float, list[str]]:
    signals = candidate.signals
    # A currency CODE match ("SAR", "AED") is direct evidence on its own, so it earns the same weight a real "_label" signal would.
    has_label = any(s.endswith("_label") for s in signals) or "currency_code_match" in signals
    has_fuzzy = "fuzzy_label_match" in signals
    added: list[str] = []
    weight = 0.0
    if has_label:
        weight += 0.20 if has_fuzzy else 0.35
    if "same_line" in signals:
        weight += 0.10
    elif "same_row" in signals:
        weight += 0.10
    elif "previous_line_label" in signals:
        weight += 0.06
    if "no_label_bare_number" in signals:
        weight -= 0.15
    return weight, added


def _reference_match_weight(candidate: FieldCandidate) -> tuple[float, Optional[str]]:
    if "known_vendor_match" in candidate.signals:
        return 0.25, "known_reference_match"
    if "keyword_match" in candidate.signals or "name_match" in candidate.signals:
        return 0.25, "known_reference_match"
    return 0.0, None


def score_candidate(candidate: FieldCandidate, context: ScoringContext) -> float:
    breakdown: dict[str, float] = {}
    base = candidate.confidence * 0.15
    breakdown["ocr_confidence"] = base

    label_weight, extra_signals = _label_and_location_weight(candidate)
    breakdown["label_and_location"] = label_weight
    candidate.signals.extend(s for s in extra_signals if s not in candidate.signals)

    position_weight, position_signal = _position_prior(candidate, context)
    breakdown["position_prior"] = position_weight
    if position_signal and position_signal not in candidate.signals:
        candidate.signals.append(position_signal)

    format_weight, format_signal = _format_plausibility(candidate)
    breakdown["format_plausibility"] = format_weight
    if format_signal and format_signal not in candidate.signals:
        candidate.signals.append(format_signal)

    reference_weight, reference_signal = _reference_match_weight(candidate)
    breakdown["known_reference_match"] = reference_weight
    if reference_signal and reference_signal not in candidate.signals:
        candidate.signals.append(reference_signal)

    score = max(0.0, min(1.0, sum(breakdown.values())))
    candidate.raw_score_breakdown = breakdown
    return score


def score_candidates(candidates: list[FieldCandidate], context: ScoringContext) -> list[FieldCandidate]:
    for candidate in candidates:
        candidate.confidence = score_candidate(candidate, context)
    return candidates
