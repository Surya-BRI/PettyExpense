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

    # Exact confidence ties (common once arithmetic reconciliation saturates scores at 1.0, e.g. two
    # stacked receipts) fall back to the same "money lives lower on the page" prior scoring uses.
    lower_is_better = group[0].field_name in ("amount", "vat_amount", "total_amount")

    def _tiebreak(c: FieldCandidate) -> float:
        if lower_is_better and c.bounding_box is not None and "vat_breakdown_arithmetic" in c.signals:
            return (c.bounding_box[1] + c.bounding_box[3]) / 2.0
        return 0.0

    # A candidate from a verified amount + vat == total tax-summary row outranks any unverified one:
    # reconciliation boosts saturate many candidates at 1.0, and a verified triple must not lose that tie.
    ranked = sorted(
        group,
        key=lambda c: ("vat_breakdown_arithmetic" in c.signals, c.confidence, _tiebreak(c)),
        reverse=True,
    )
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

    if amount_val is None and total_val is not None and total_val - (vat_val or 0.0) > 0:
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


def _is_coherent(amount, vat, total, rates: tuple[float, ...]) -> bool:
    # amount + vat == total with vat either zero or a plausible percentage of the amount.
    if amount is None or vat is None or total is None or amount <= 0:
        return False
    if abs(amount + vat - total) > 0.02:
        return False
    if vat == 0:
        return True
    return any(abs(vat - amount * r / 100.0) <= max(0.03, 0.0012 * amount) for r in rates if r > 0)


def _enforce_arithmetic_consistency(
    selected: dict[str, SelectedField], by_field: dict[str, list[FieldCandidate]], rates: tuple[float, ...]
) -> None:
    # Fields are chosen independently, so a stray figure can win one of them and leave an impossible
    # triple (VAT >= total, total < amount, a "VAT" that is really a discount). When the picks don't
    # add up, look for the best triple among the candidates already collected that does -- never
    # inventing a value -- and flag it for review.
    names = ("amount", "vat_amount", "total_amount")
    current = tuple(selected[n].value if isinstance(selected[n].value, (int, float)) else None for n in names)
    if _is_coherent(*current, rates):
        return

    def top(field_name: str) -> dict[float, FieldCandidate]:
        best: dict[float, FieldCandidate] = {}
        for c in sorted(by_field.get(field_name, []), key=lambda c: -c.confidence)[:30]:
            if isinstance(c.value, (int, float)) and c.confidence >= LOW_CONFIDENCE_FLOOR:
                best.setdefault(round(float(c.value), 2), c)
        return dict(list(best.items())[:8])

    amounts, vats, totals = top("amount"), top("vat_amount"), top("total_amount")
    best_triple = None
    for a, ca in amounts.items():
        for t, ct in totals.items():
            if t < a:
                continue
            if abs(t - a) <= 0.02:
                options = [(0.0, vats.get(0.0))]
            else:
                options = [(v, cv) for v, cv in vats.items() if _is_coherent(a, v, t, rates)]
            for v, cv in options:
                if not _is_coherent(a, v, t, rates):
                    continue
                score = ca.confidence + ct.confidence + (cv.confidence if cv is not None else 0.35)
                if best_triple is None or score > best_triple[0]:
                    best_triple = (score, ca, cv, ct, v)
    if best_triple is None:
        return
    _score, ca, cv, ct, v = best_triple
    for name, cand in (("amount", ca), ("total_amount", ct)):
        selected[name] = SelectedField(
            value=cand.value, confidence=cand.confidence, evidence=cand.source_text,
            signals=list(cand.signals) + ["resolved_by_arithmetic_consistency"],
            low_confidence=True, warning="resolved_by_arithmetic_consistency",
        )
    selected["vat_amount"] = SelectedField(
        value=v, confidence=cv.confidence if cv is not None else 0.35,
        evidence=cv.source_text if cv is not None else "",
        signals=(list(cv.signals) if cv is not None else ["no_vat_assumed_zero"]) + ["resolved_by_arithmetic_consistency"],
        low_confidence=True, warning="resolved_by_arithmetic_consistency",
    )


def select_fields(
    candidates: list[FieldCandidate], plausible_vat_rates: tuple[float, ...] = (5.0, 15.0)
) -> dict[str, SelectedField]:
    by_field = _group_by_field(candidates)
    selected = {field_name: _select_one(by_field.get(field_name, [])) for field_name in FIELD_NAMES}
    _apply_no_vat_evidence_rule(selected, by_field)
    _apply_derived_fallback(selected)
    _enforce_arithmetic_consistency(selected, by_field, plausible_vat_rates)
    return selected
