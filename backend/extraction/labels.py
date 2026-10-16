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
    DELIVERY_NOTE_NUMBER = "delivery_note_number"
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


# OCR often reads a letter as a digit inside a short label word ("Bi11" for "Bill", "B11 No"); matching is
# also tried on a copy of the text with those digits turned back into letters (same length, so spans line up).
_FOLDABLE_WORD = re.compile(r"^[a-z][a-z01589]{1,5}[:.]?$")
_FOLD_TABLE = str.maketrans({"1": "l", "0": "o", "5": "s", "8": "b"})


def _ocr_fold(lowered: str) -> str:
    def fold(m: re.Match) -> str:
        word = m.group(0)
        if _FOLDABLE_WORD.match(word) and any(c.isdigit() for c in word):
            return word.translate(_FOLD_TABLE)
        return word

    return re.sub(r"\S+", fold, lowered)


def match_label_concepts(
    line_text: str, vocab: LabelVocabulary, exclusions: Optional[LabelVocabulary] = None
) -> list[LabelMatch]:
    """Returns at most one (the best) match per concept found in line_text."""
    if not line_text:
        return []
    lowered = line_text.lower()
    matches = _match_on(lowered, vocab, exclusions or {})
    folded = _ocr_fold(lowered)
    if folded != lowered:
        found = {m.concept for m in matches}
        for m in _match_on(folded, vocab, exclusions or {}):
            if m.concept not in found:
                matches.append(LabelMatch(m.concept, m.matched_synonym, m.span, fuzzy=True))
    return _suppress_shorter_overlapping_matches(matches)


def _match_on(
    lowered: str, vocab: LabelVocabulary, exclusions: LabelVocabulary
) -> list[LabelMatch]:
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
            if syn_lower.startswith("re:"):
                # Word-boundary / positional labels ("Inv:", a bare "No." at line start) that a plain substring can't express safely.
                rm = re.search(syn_lower[3:], lowered)
                if rm and not _is_excluded_followup(lowered, rm.end(), concept_exclusions):
                    if best is None or best.fuzzy or (rm.end() - rm.start()) > (best.span[1] - best.span[0]):
                        best = LabelMatch(concept, synonym, (rm.start(), rm.end()), fuzzy=False)
                continue
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
    return matches


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
