"""Stage 8: pick the best candidate per field and explain the choice. Weak or
tied evidence degrades to a low-confidence/warning result rather than a
fabricated value.
"""
from extraction.types import FIELD_NAMES, FieldCandidate, SelectedField

AMBIGUITY_MARGIN = 0.12
HIGH_CONFIDENCE = 0.75
LOW_CONFIDENCE_FLOOR = 0.20


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

    return SelectedField(
        value=best.value, confidence=best.confidence, evidence=best.source_text,
        signals=list(best.signals), low_confidence=low_confidence, warning=warning,
    )


def _apply_derived_fallback(selected: dict[str, SelectedField]) -> None:
    """Last-resort pure arithmetic derivation when a money field is missing —
    always capped at a low confidence and tagged 'derived', so a real printed
    value (any real candidate, however weak) still outranks it. Covers both
    tax-exclusive (amount = total - vat) and tax-inclusive (vat derived from
    total + rate when no vat_amount was found at all) conventions."""
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
    _apply_derived_fallback(selected)
    return selected
