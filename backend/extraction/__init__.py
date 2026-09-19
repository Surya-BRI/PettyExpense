from extraction.dedupe import dedupe_lines
from extraction.normalize import group_into_lines, words_from_text
from extraction.pipeline import extract, extract_from_text_input, extract_from_words, to_legacy_dict
from extraction.reference_data import CategoryRef, ReferenceData, default_tax_rules_for_region
from extraction.types import ExtractionResult, FieldCandidate, OcrLine, OcrWord, SelectedField

__all__ = [
    "extract",
    "extract_from_text_input",
    "extract_from_words",
    "to_legacy_dict",
    "dedupe_lines",
    "group_into_lines",
    "words_from_text",
    "default_tax_rules_for_region",
    "CategoryRef",
    "ReferenceData",
    "ExtractionResult",
    "FieldCandidate",
    "OcrLine",
    "OcrWord",
    "SelectedField",
]
