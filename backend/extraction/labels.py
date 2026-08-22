"""Stage 5: generic semantic-label detection — LabelConcept synonyms live in label_vocabulary.yaml, matched by substring then bounded fuzzy match."""
import difflib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from extraction.reference_data import LabelVocabulary

FUZZY_THRESHOLD = 0.85

# "No Cash Refund" etc. is boilerplate footer text — a negated word must not be treated as an affirmative label.
_NEGATION_WORDS = frozenset({"no", "not", "without", "لا", "بدون", "دون"})


def _is_negated(lowered: str, match_start: int) -> bool:
    prefix_words = lowered[max(0, match_start - 16) : match_start].split()
    return bool(prefix_words) and prefix_words[-1] in _NEGATION_WORDS


def _is_excluded_followup(lowered: str, match_end: int, exclusion_words: tuple[str, ...]) -> bool:
    # "Total Savings"/"Total Qty" contain a synonym as a substring but mean something else — checks label_exclusions.yaml's per-concept followup list.
    if not exclusion_words:
        return False
    followup_words = lowered[match_end : match_end + 20].split()
    return bool(followup_words) and followup_words[0].strip(":,-") in exclusion_words


class LabelConcept(str, Enum):
    TOTAL = "total"
    SUBTOTAL = "subtotal"
    VAT_TAX_AMOUNT = "vat_tax_amount"
    VAT_TAX_RATE = "vat_tax_rate"
    DISCOUNT = "discount"
    SERVICE_CHARGE = "service_charge"
    TIP = "tip"
    CASH = "cash"
    CARD = "card"
    CHANGE = "change"
    TENDERED = "tendered"
    DATE = "date"
    INVOICE_NUMBER = "invoice_number"
    TRANSACTION_NUMBER = "transaction_number"
    ITEM_TABLE_HEADER = "item_table_header"
    TAX_REGISTRATION_NUMBER = "tax_registration_number"
    DOCUMENT_TYPE_HEADER = "document_type_header"
    GENERIC_BUSINESS_ENTITY_WORD = "generic_business_entity_word"
    FROM_LOCATION = "from_location"
    TO_LOCATION = "to_location"
    NOTES = "notes"


@dataclass(frozen=True)
class LabelMatch:
    concept: LabelConcept
    matched_synonym: str
    span: tuple[int, int]
    fuzzy: bool


def match_label_concepts(
    line_text: str, vocab: LabelVocabulary, exclusions: Optional[LabelVocabulary] = None
) -> list[LabelMatch]:
    """Returns at most one (the best) match per concept found in line_text."""
    if not line_text:
        return []
    exclusions = exclusions or {}
    lowered = line_text.lower()
    tokens = list(re.finditer(r"\S+", lowered))
    matches: list[LabelMatch] = []

    for concept_value, synonyms in vocab.items():
        try:
            concept = LabelConcept(concept_value)
        except ValueError:
            continue  # unknown concept key in a customized vocabulary file — ignore, don't crash
        concept_exclusions = exclusions.get(concept_value, ())
        best: LabelMatch | None = None
        for synonym in synonyms:
            if not isinstance(synonym, str):
                continue  # a YAML-editing mistake (e.g. bare 'off' parsed as a bool) shouldn't crash extraction
            syn_lower = synonym.lower()
            idx = lowered.find(syn_lower)
            if idx != -1:
                end = idx + len(syn_lower)
                if _is_negated(lowered, idx) or _is_excluded_followup(lowered, end, concept_exclusions):
                    continue
                if best is None or best.fuzzy or (idx != -1 and len(syn_lower) > (best.span[1] - best.span[0])):
                    best = LabelMatch(concept, synonym, (idx, end), fuzzy=False)
                continue
            if best is not None and not best.fuzzy:
                continue
            if len(syn_lower) < 5:
                continue  # short synonyms ("vat%") fuzzy-match unrelated words too easily — require an exact substring for them
            syn_word_count = max(len(syn_lower.split()), 1)
            best_ratio, best_span = 0.0, None
            for i in range(max(len(tokens) - syn_word_count + 1, 0)):
                window = tokens[i : i + syn_word_count]
                window_text = " ".join(t.group(0) for t in window)
                ratio = difflib.SequenceMatcher(None, window_text, syn_lower).ratio()
                if (
                    ratio > best_ratio
                    and not _is_negated(lowered, window[0].start())
                    and not _is_excluded_followup(lowered, window[-1].end(), concept_exclusions)
                ):
                    best_ratio, best_span = ratio, (window[0].start(), window[-1].end())
            if best_ratio >= FUZZY_THRESHOLD and best_span is not None:
                best = LabelMatch(concept, synonym, best_span, fuzzy=True)
        if best is not None:
            matches.append(best)
    return _suppress_shorter_overlapping_matches(matches)


def _suppress_shorter_overlapping_matches(matches: list[LabelMatch]) -> list[LabelMatch]:
    # When two concepts match overlapping text, the longer/more specific match wins and the shorter fragment is dropped.
    kept = []
    for m in matches:
        m_len = m.span[1] - m.span[0]
        if any(
            (o.span[1] - o.span[0]) > m_len and o.span[0] <= m.span[0] and o.span[1] >= m.span[1]
            for o in matches
            if o is not m
        ):
            continue
        kept.append(m)
    return kept
