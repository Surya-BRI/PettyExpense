"""Orchestrates the full extraction pipeline and adapts its output to the
legacy result-dict shape existing callers (services/ocr_service.py's public
surface) already depend on.
"""
from typing import Any

from extraction.candidates import generate_candidates
from extraction.dedupe import dedupe_lines
from extraction.normalize import group_into_lines, lines_from_text, normalize_text
from extraction.reference_data import ReferenceData
from extraction.scoring import build_scoring_context, score_candidates
from extraction.select import select_fields
from extraction.types import ExtractionResult, FieldCandidate, OcrLine, OcrWord
from extraction.validation import validate_and_adjust


def _group_by_field(candidates: list[FieldCandidate]) -> dict[str, list[FieldCandidate]]:
    grouped: dict[str, list[FieldCandidate]] = {}
    for c in candidates:
        grouped.setdefault(c.field_name, []).append(c)
    return grouped


def _normalize_line_text(lines: list[OcrLine]) -> list[OcrLine]:
    """Normalization (stage 2) is idempotent, so re-applying it here makes
    `extract()` robust regardless of whether `lines` already went through
    normalize.group_into_lines (real OCR input) or were built directly
    (tests, or callers assembling lines from some other source)."""
    return [
        OcrLine(
            text=normalize_text(ln.text), words=ln.words, confidence=ln.confidence,
            bounding_box=ln.bounding_box, page=ln.page, reading_order=ln.reading_order,
        )
        for ln in lines
    ]


def extract(lines: list[OcrLine], reference_data: ReferenceData) -> ExtractionResult:
    lines = _normalize_line_text(lines)
    candidates = generate_candidates(lines, reference_data)
    context = build_scoring_context(lines, reference_data)
    candidates = score_candidates(candidates, context)
    candidates, reconciliation_mismatch = validate_and_adjust(candidates, reference_data)
    fields = select_fields(candidates)

    confidences = [f.confidence for f in fields.values()]
    overall = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    raw_text = "\n".join(ln.text for ln in lines)

    return ExtractionResult(
        fields=fields,
        overall_confidence=overall,
        reconciliation_mismatch=reconciliation_mismatch,
        raw_text=raw_text,
        all_candidates=_group_by_field(candidates),
    )


def extract_from_words(words: list[OcrWord], reference_data: ReferenceData) -> ExtractionResult:
    lines = dedupe_lines(group_into_lines(list(words)))
    return extract(lines, reference_data)


def extract_from_text_input(text: str, reference_data: ReferenceData) -> ExtractionResult:
    lines = dedupe_lines(lines_from_text(text))
    return extract(lines, reference_data)


def to_legacy_dict(result: ExtractionResult) -> dict[str, Any]:
    fields = result.fields
    legacy_fields = {}
    for name, sf in fields.items():
        entry: dict[str, Any] = {
            "value": sf.value,
            "confidence": sf.confidence,
            "evidence": sf.evidence,
            "signals": sf.signals,
            "low": sf.low_confidence,
        }
        if sf.warning:
            entry["warning"] = sf.warning
        legacy_fields[name] = entry

    return {
        "vendor": fields["vendor"].value or "",
        "expense_type": fields["expense_category"].value,
        "amount": fields["amount"].value,
        "vat_amount": fields["vat_amount"].value,
        "total_amount": fields["total_amount"].value,
        "currency": fields["currency"].value,
        "date": fields["date"].value or "",
        "confidence": result.overall_confidence,
        "field_confidence": {name: sf.confidence for name, sf in fields.items()},
        "low_confidence_fields": [name for name, sf in fields.items() if sf.low_confidence],
        "reconciliation_mismatch": result.reconciliation_mismatch,
        "fields": legacy_fields,
    }
