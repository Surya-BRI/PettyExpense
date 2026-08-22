"""Stage 7: cross-field validation — generic arithmetic/shape checks driven by injected reference data, never a hard-coded vendor/rate."""
from extraction.reference_data import ReferenceData
from extraction.types import FieldCandidate

RECONCILE_TOLERANCE = 0.02
ARITH_TOLERANCE = 0.15


def _group_by_field(candidates: list[FieldCandidate]) -> dict[str, list[FieldCandidate]]:
    grouped: dict[str, list[FieldCandidate]] = {}
    for c in candidates:
        grouped.setdefault(c.field_name, []).append(c)
    return grouped


def _demote_rate_like_vat_amounts(by_field: dict[str, list[FieldCandidate]], reference_data: ReferenceData) -> None:
    # A bare-integer vat_amount matching a plausible VAT rate is probably the rate misread as an amount — demote it, add a vat_rate candidate.
    vat_amounts = by_field.get("vat_amount", [])
    vat_rates = by_field.setdefault("vat_rate", [])
    for c in vat_amounts:
        if (
            isinstance(c.value, (int, float))
            and float(c.value) in reference_data.plausible_vat_rates
            and "no_decimal_point" in c.signals
        ):
            c.confidence *= 0.3
            if "looks_like_rate_not_amount" not in c.signals:
                c.signals.append("looks_like_rate_not_amount")
            already_covered = any(r.value == c.value and r.source_text == c.source_text for r in vat_rates)
            if not already_covered:
                vat_rates.append(
                    FieldCandidate(
                        field_name="vat_rate",
                        value=c.value,
                        source_text=c.source_text,
                        confidence=max(c.confidence, 0.4),
                        page=c.page,
                        bounding_box=c.bounding_box,
                        signals=["derived_from_vat_amount_demotion"],
                        reading_order=c.reading_order,
                    )
                )


def _cross_check_arithmetic(by_field: dict[str, list[FieldCandidate]]) -> bool:
    # Checks tax-exclusive and tax-inclusive conventions; whichever reconciles boosts its candidates, neither reconciling flags a mismatch.
    amounts = by_field.get("amount", [])
    totals = by_field.get("total_amount", [])
    vats = by_field.get("vat_amount", [])
    discounts = by_field.get("discount", [])
    services = by_field.get("service_charge", [])
    rates = by_field.get("vat_rate", [])
    if not (amounts and totals):
        return False

    reconciled = False
    for a in amounts:
        for tot in totals:
            for v in vats or [None]:
                for d in discounts or [None]:
                    for s in services or [None]:
                        vat_val = v.value if v else 0.0
                        disc_val = d.value if d else 0.0
                        svc_val = s.value if s else 0.0
                        expected = a.value - disc_val + svc_val + vat_val
                        if abs(expected - tot.value) <= RECONCILE_TOLERANCE:
                            for cand in filter(None, (a, tot, v, d, s)):
                                # Guard the boost itself (not just the signal) so a duplicate pairing can't reward the same candidate twice.
                                if "arithmetic_reconciled_exclusive" not in cand.signals:
                                    cand.confidence = min(1.0, cand.confidence + 0.15)
                                    cand.signals.append("arithmetic_reconciled_exclusive")
                            reconciled = True
                for r in rates:
                    if not r.value or r.value <= 0:
                        continue
                    implied_vat = tot.value - tot.value / (1 + r.value / 100.0)
                    implied_amount = tot.value - implied_vat
                    vat_val = v.value if v else None
                    vat_ok = vat_val is None or abs(implied_vat - vat_val) <= ARITH_TOLERANCE
                    amount_ok = abs(implied_amount - a.value) <= ARITH_TOLERANCE
                    if vat_ok and amount_ok:
                        for cand in filter(None, (a, tot, v, r)):
                            if "arithmetic_reconciled_inclusive" not in cand.signals:
                                cand.confidence = min(1.0, cand.confidence + 0.15)
                                cand.signals.append("arithmetic_reconciled_inclusive")
                        reconciled = True

    if not reconciled and vats:
        for group in (amounts, vats, totals):
            for c in group:
                c.confidence *= 0.85
                if "reconciliation_mismatch" not in c.signals:
                    c.signals.append("reconciliation_mismatch")
        return True
    return False


def _cash_change_vs_total(by_field: dict[str, list[FieldCandidate]]) -> None:
    tendered_list = by_field.get("cash_tendered", [])
    change_list = by_field.get("change", [])
    total_list = by_field.get("total_amount", [])
    if not (tendered_list and change_list and total_list):
        return
    for tendered in tendered_list:
        for change in change_list:
            for total in total_list:
                if abs((tendered.value - change.value) - total.value) > RECONCILE_TOLERANCE:
                    continue
                for cand in (tendered, change, total):
                    if "tendered_change_total_arithmetic" not in cand.signals:
                        cand.confidence = min(1.0, cand.confidence + 0.15)
                        cand.signals.append("tendered_change_total_arithmetic")
                for other in total_list:
                    if other is total:
                        continue
                    if other.value in (tendered.value, change.value) and not any(
                        s.endswith("_label") for s in other.signals
                    ):
                        other.confidence *= 0.4
                        if "looks_like_cash_or_change_not_total" not in other.signals:
                            other.signals.append("looks_like_cash_or_change_not_total")


def validate_and_adjust(
    candidates: list[FieldCandidate], reference_data: ReferenceData
) -> tuple[list[FieldCandidate], bool]:
    by_field = _group_by_field(candidates)
    _demote_rate_like_vat_amounts(by_field, reference_data)
    reconciliation_mismatch = _cross_check_arithmetic(by_field)
    _cash_change_vs_total(by_field)
    return [c for group in by_field.values() for c in group], reconciliation_mismatch
