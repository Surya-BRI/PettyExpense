"""Stage 8: pick the best candidate per field; weak/tied evidence degrades to low-confidence rather than a fabricated value."""
from extraction.types import FIELD_NAMES, FieldCandidate, SelectedField

AMBIGUITY_MARGIN = 0.12
HIGH_CONFIDENCE = 0.75
LOW_CONFIDENCE_FLOOR = 0.20
# Below this OCR confidence, a value is flagged for user review instead of trusted outright (handwriting/smudges read low; clean print is 0.93+).
LOW_OCR_CONFIDENCE_THRESHOLD = 0.90


def _group_by_field(candidates: list[FieldCandidate]) -> dict[str, list[FieldCandidate]]:
    grouped: dict[str, list[FieldCandidate]] = {}
    for c in candidates:
        grouped.setdefault(c.field_name, []).append(c)
    return grouped


def _select_one(group: list[FieldCandidate]) -> SelectedField:
    if not group:
        return SelectedField(value=None, confidence=0.0, evidence="", signals=[], low_confidence=True, warning="no_evidence")

    ranked = sorted(group, key=lambda c: c.confidence, reverse=True)
    best = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None

    if best.confidence < LOW_CONFIDENCE_FLOOR:
        return SelectedField(
            value=None, confidence=best.confidence, evidence=best.source_text,
            signals=list(best.signals), low_confidence=True, warning="low_confidence_all_candidates",
        )

    low_confidence, warning = False, None
    if runner_up is not None and (best.confidence - runner_up.confidence) < AMBIGUITY_MARGIN and best.confidence < HIGH_CONFIDENCE:
        low_confidence, warning = True, "ambiguous_candidates"

    # A low-confidence read gets flagged for review even if it won outright — winning uncontested doesn't mean it was read correctly.
    if best.ocr_confidence < LOW_OCR_CONFIDENCE_THRESHOLD:
        low_confidence = True
        warning = warning or "low_ocr_confidence_possible_handwriting"

    return SelectedField(
        value=best.value, confidence=best.confidence, evidence=best.source_text,
        signals=list(best.signals), low_confidence=low_confidence, warning=warning,
    )


def _apply_no_vat_evidence_rule(selected: dict[str, SelectedField], by_field: dict[str, list[FieldCandidate]]) -> None:
    # No vat_amount/vat_rate candidate anywhere means genuinely no VAT (not just "couldn't read it") — report 0, and amount == total.
    if by_field.get("vat_amount") or by_field.get("vat_rate"):
        return

    selected["vat_amount"] = SelectedField(
        value=0.0, confidence=0.6, evidence="", signals=["no_vat_evidence_assumed_zero"],
        low_confidence=False, warning=None,
    )

    amount, total = selected.get("amount"), selected.get("total_amount")
    # An amount with no real label evidence (a stray bare number that won by default) doesn't count as real evidence either.
    amount_is_unevidenced = amount is None or amount.value is None or not any(
        s.endswith("_label") for s in amount.signals
    )
    if amount_is_unevidenced and total is not None and total.value is not None:
        selected["amount"] = SelectedField(
            value=total.value, confidence=total.confidence, evidence=total.evidence,
            signals=list(total.signals) + ["amount_equals_total_no_vat"],
            low_confidence=total.low_confidence, warning=total.warning,
        )


def _apply_derived_fallback(selected: dict[str, SelectedField]) -> None:
    # Last-resort arithmetic derivation when a money field is missing; always low-confidence so any real printed value outranks it.
    amount, total, vat, rate = selected.get("amount"), selected.get("total_amount"), selected.get("vat_amount"), selected.get("vat_rate")
    total_val = total.value if total and isinstance(total.value, (int, float)) else None
    vat_val = vat.value if vat and isinstance(vat.value, (int, float)) else None
    rate_val = rate.value if rate and isinstance(rate.value, (int, float)) else None
    amount_val = amount.value if amount and isinstance(amount.value, (int, float)) else None

    if vat_val is None and total_val is not None and rate_val:
        vat_val = round(total_val - total_val / (1 + rate_val / 100.0), 2)
        selected["vat_amount"] = SelectedField(
            value=vat_val, confidence=0.4, evidence=f"derived: {total.evidence} at {rate_val}%",
            signals=["derived_arithmetic", "derived_inclusive"], low_confidence=True, warning="derived_value",
        )

    if amount_val is None and total_val is not None:
        selected["amount"] = SelectedField(
            value=round(total_val - (vat_val or 0.0), 2), confidence=0.4,
            evidence=f"derived: {total.evidence}", signals=["derived_arithmetic"],
            low_confidence=True, warning="derived_value",
        )
    elif total_val is None and amount_val is not None:
        selected["total_amount"] = SelectedField(
            value=round(amount_val + (vat_val or 0.0), 2), confidence=0.4,
            evidence=f"derived: {amount.evidence}", signals=["derived_arithmetic"],
            low_confidence=True, warning="derived_value",
        )


def select_fields(candidates: list[FieldCandidate]) -> dict[str, SelectedField]:
    by_field = _group_by_field(candidates)
    selected = {field_name: _select_one(by_field.get(field_name, [])) for field_name in FIELD_NAMES}
    _apply_no_vat_evidence_rule(selected, by_field)
    _apply_derived_fallback(selected)
    return selected
