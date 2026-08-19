"""Stage 4: candidate generation — turns normalized OCR lines into multiple
FieldCandidate proposals per field. Generation is deliberately generous (many
candidates, generically triggered); disambiguation happens later in scoring
and validation, never here by picking "the one right answer" up front.
"""
import difflib
import re
from typing import Optional

from extraction.labels import LabelConcept, LabelMatch, match_label_concepts
from extraction.normalize import parse_amount
from extraction.reference_data import ReferenceData
from extraction.types import FieldCandidate, OcrLine

_MONEY_CONCEPT_TO_FIELD: dict[LabelConcept, str] = {
    LabelConcept.TOTAL: "total_amount",
    LabelConcept.SUBTOTAL: "amount",
    LabelConcept.VAT_TAX_AMOUNT: "vat_amount",
    LabelConcept.DISCOUNT: "discount",
    LabelConcept.SERVICE_CHARGE: "service_charge",
    LabelConcept.TIP: "tip",
    LabelConcept.CASH: "cash_tendered",
    LabelConcept.TENDERED: "cash_tendered",
    LabelConcept.CARD: "card_amount",
    LabelConcept.CHANGE: "change",
}
_MONEY_CONCEPTS = set(_MONEY_CONCEPT_TO_FIELD.keys())
_ID_CONCEPT_TO_FIELD = {
    LabelConcept.INVOICE_NUMBER: "invoice_number",
    LabelConcept.TRANSACTION_NUMBER: "transaction_number",
}

# Digit-only boundary (not alnum) — a number glued directly to a currency
# code/symbol ("AED0.29", "SR45.00") is extremely common on real receipts and
# must still be recognized; only an adjacent DIGIT (part of a longer run, e.g.
# a barcode/TRN) disqualifies a match.
_NUMBER_TOKEN_RE = re.compile(r"(?<!\d)\d[\d.,]{0,9}\d(?!\d)|(?<!\d)\d(?!\d)")
_DATE_PATTERNS = (
    re.compile(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b"),
    re.compile(r"\b\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}\b"),
    re.compile(
        r"\b\d{1,2}[\s\-.]*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\-.]*\d{2,4}\b",
        re.IGNORECASE,
    ),
    # Month-name-then-day order ("Feb 8"), common in app-generated receipts —
    # a trailing year isn't required, so a bare day number right after a month
    # name (e.g. the "8" in "Feb 8 7:10AM") is still recognized as part of a
    # date and excluded from money-candidate consideration.
    re.compile(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s.\-]*\d{1,2}\b(?:[\s,]*\d{2,4}\b)?",
        re.IGNORECASE,
    ),
)
# Clock times ("8:09 AM", "14:32") are numeric but never a money value —
# excluded from money-candidate consideration the same way dates are.
_TIME_PATTERN = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\b", re.IGNORECASE)
_NON_MONEY_NUMBER_CONTEXT_PATTERNS = _DATE_PATTERNS + (_TIME_PATTERN,)
_ID_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-/]{3,20}")


class _NumericToken:
    __slots__ = ("raw", "start", "end", "value", "has_decimal", "near_percent", "has_currency_marker")

    def __init__(
        self, raw: str, start: int, end: int, value: float, has_decimal: bool, near_percent: bool,
        has_currency_marker: bool = False,
    ):
        self.raw, self.start, self.end, self.value = raw, start, end, value
        self.has_decimal, self.near_percent = has_decimal, near_percent
        self.has_currency_marker = has_currency_marker


def _token_has_decimal(raw: str) -> bool:
    seps = [i for i, c in enumerate(raw) if c in ",."]
    if not seps:
        return False
    tail_len = len(raw) - seps[-1] - 1
    return tail_len in (1, 2)


def _looks_like_phone_or_id(value: float) -> bool:
    if value != int(value):
        return False
    digits = str(int(value))
    return len(digits) >= 5 and value >= 10000


def _iter_numeric_tokens(text: str, currency_codes: tuple[str, ...] = ()) -> list[_NumericToken]:
    tokens = []
    currency_re = (
        re.compile("|".join(re.escape(c) for c in currency_codes), re.IGNORECASE) if currency_codes else None
    )
    for m in _NUMBER_TOKEN_RE.finditer(text):
        raw = m.group(0)
        value = parse_amount(raw)
        if value is None:
            continue
        window = text[max(0, m.start() - 6) : m.end() + 3]
        has_currency = bool(currency_re and currency_re.search(text[max(0, m.start() - 8) : m.end() + 8]))
        tokens.append(_NumericToken(raw, m.start(), m.end(), value, _token_has_decimal(raw), "%" in window, has_currency))
    return tokens


def _same_row(a_bbox, b_bbox) -> bool:
    a_center = (a_bbox[1] + a_bbox[3]) / 2.0
    b_center = (b_bbox[1] + b_bbox[3]) / 2.0
    a_height = max(a_bbox[3] - a_bbox[1], 1e-6)
    return abs(a_center - b_center) <= 0.6 * a_height


def _horizontally_aligned(a_bbox, b_bbox) -> bool:
    """True when geometry doesn't contradict 'these two lines belong to the
    same column/document' — required before trusting the previous-line label
    fallback. Without this, a page containing two receipts side by side (or
    any multi-column layout) can pair a label from one column with a value
    from the other purely because they're adjacent in linear reading order.
    Degrades to permissive (True) when either box is unknown."""
    if a_bbox is None or b_bbox is None:
        return True
    a_x0, a_x1 = a_bbox[0], a_bbox[2]
    b_x0, b_x1 = b_bbox[0], b_bbox[2]
    return not (a_x1 < b_x0 or b_x1 < a_x0)


def _date_span_ranges(text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for pattern in _NON_MONEY_NUMBER_CONTEXT_PATTERNS for m in pattern.finditer(text)]


def _overlaps_any(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(not (end <= s or start >= e) for s, e in spans)


def _nearest_aligned_line_above(lines: list[OcrLine], i: int) -> Optional[int]:
    """Finds the closest line above (by vertical gap) that is horizontally
    aligned with lines[i] — a column-aware generalization of 'the previous
    line', needed because a header row (e.g. 'VAT % | Sale Amt | VAT Amt')
    and its value row often have other columns' cells sitting between a
    given header and its own value in flat reading order."""
    current = lines[i].bounding_box
    if current is None:
        return None
    current_center = (current[1] + current[3]) / 2.0
    best_idx, best_gap = None, None
    for j in range(i):
        other = lines[j].bounding_box
        if other is None:
            continue
        # Compare row centers, not edges — a header row and the value row
        # directly below it commonly have bounding boxes that overlap by a
        # few pixels (padding/detection imprecision), which an edge-based
        # "must end strictly above" check would wrongly disqualify.
        other_center = (other[1] + other[3]) / 2.0
        gap = current_center - other_center
        if gap <= 0:
            continue  # other isn't above current
        if not _horizontally_aligned(current, other):
            continue
        if best_gap is None or gap < best_gap:
            best_gap, best_idx = gap, j
    return best_idx


def _money_signal_list(match: LabelMatch, location: str, token: _NumericToken) -> list[str]:
    signals = [f"{match.concept.value}_label", location]
    if match.fuzzy:
        signals.append("fuzzy_label_match")
    signals.append("currency_value")
    if not token.has_decimal:
        signals.append("no_decimal_point")
    if token.near_percent:
        signals.append("near_percent_marker")
    return signals


def _money_field_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], reference_data: ReferenceData
) -> list[FieldCandidate]:
    candidates: list[FieldCandidate] = []
    has_item_table = any(
        any(m.concept == LabelConcept.ITEM_TABLE_HEADER for m in matches) for matches in label_matches_by_line
    )

    for i, line in enumerate(lines):
        date_spans = _date_span_ranges(line.text)
        tokens = [
            t
            for t in _iter_numeric_tokens(line.text, reference_data.valid_currency_codes)
            if t.value > 0 and not _looks_like_phone_or_id(t.value) and not _overlaps_any(t.start, t.end, date_spans)
        ]
        if not tokens:
            continue

        same_line = [m for m in label_matches_by_line[i] if m.concept in _MONEY_CONCEPTS]
        same_row: list[LabelMatch] = []
        if line.bounding_box is not None:
            for j, other in enumerate(lines):
                if j == i or other.bounding_box is None:
                    continue
                if _same_row(line.bounding_box, other.bounding_box):
                    same_row += [m for m in label_matches_by_line[j] if m.concept in _MONEY_CONCEPTS]
        if line.bounding_box is not None:
            nearest_idx = _nearest_aligned_line_above(lines, i)
            prev_line = (
                [m for m in label_matches_by_line[nearest_idx] if m.concept in _MONEY_CONCEPTS]
                if nearest_idx is not None
                else []
            )
        else:
            prev_line = (
                [m for m in label_matches_by_line[i - 1] if m.concept in _MONEY_CONCEPTS]
                if i > 0 and lines[i - 1].bounding_box is None
                else []
            )

        if same_line:
            money_matches, location = same_line, "same_line"
        elif same_row:
            money_matches, location = same_row, "same_row"
        elif prev_line:
            money_matches, location = prev_line, "previous_line_label"
        else:
            money_matches, location = [], None

        money_tokens = [t for t in tokens if not t.near_percent or not _token_only_percent_context(t)]
        if money_matches:
            # NOTE: a "VAT% | Taxable Amount | VAT | Total" style table row
            # carries several money-concept labels AND several numbers on the
            # same evidence. Positionally pairing labels-in-order with values-
            # in-order was tried here and reverted: on real multi-language
            # merged OCR text (en+ar dedup output), label/value ordering is
            # not reliable enough for order-based pairing — it fixed the clean
            # case but produced worse (implausible) values on garbled real
            # receipts than the current every-match-with-every-token approach.
            # A correct fix needs real column/x-position alignment between the
            # header row and the value row, not text order — left as a known
            # limitation rather than shipping a net-negative heuristic.
            for match in money_matches:
                field_name = _MONEY_CONCEPT_TO_FIELD[match.concept]
                for token in money_tokens:
                    candidates.append(
                        FieldCandidate(
                            field_name=field_name,
                            value=token.value,
                            source_text=line.text,
                            confidence=line.confidence,
                            page=line.page,
                            bounding_box=line.bounding_box,
                            signals=_money_signal_list(match, location, token),
                            reading_order=line.reading_order,
                        )
                    )
        elif not has_item_table:
            for token in money_tokens:
                # A bare number is much stronger evidence of being a money value
                # when an actual currency code/symbol sits right next to it
                # ("SAR72.90") than when it's just any digit on the page (e.g.
                # a terminal/unit number in an address line) — weight accordingly
                # instead of trusting every unlabeled number equally.
                base = line.confidence * (0.9 if token.has_currency_marker else 0.3)
                signals = ["no_label_bare_number"]
                signals.append("currency_marker_adjacent" if token.has_currency_marker else "currency_value")
                for field_name in ("total_amount", "amount"):
                    candidates.append(
                        FieldCandidate(
                            field_name=field_name,
                            value=token.value,
                            source_text=line.text,
                            confidence=base,
                            page=line.page,
                            bounding_box=line.bounding_box,
                            signals=list(signals),
                            reading_order=line.reading_order,
                        )
                    )
    return candidates


def _token_only_percent_context(token: _NumericToken) -> bool:
    """A number is excluded as a money candidate only when it's a bare 1-3
    digit integer sitting in a percent context (e.g. the '5' in 'VAT % 5') —
    a real money value never lacks a decimal AND sits next to a lone '%'."""
    return not token.has_decimal and token.value <= 100


def _vat_rate_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], reference_data: ReferenceData
) -> list[FieldCandidate]:
    candidates = []
    rate_concepts = (LabelConcept.VAT_TAX_RATE, LabelConcept.VAT_TAX_AMOUNT)
    for i, line in enumerate(lines):
        matches = [m for m in label_matches_by_line[i] if m.concept in rate_concepts]
        if not matches and line.bounding_box is not None:
            # A "VAT % | Sale Amt | VAT Amt" header row commonly sits above its
            # value row (e.g. a "5" for the Standard-rate category), not on
            # the same line as the value — same column-aware lookup used for
            # money fields, generalized to the rate field too.
            for j, other in enumerate(lines):
                if j == i or other.bounding_box is None:
                    continue
                if _same_row(line.bounding_box, other.bounding_box):
                    matches += [m for m in label_matches_by_line[j] if m.concept in rate_concepts]
            if not matches:
                nearest_idx = _nearest_aligned_line_above(lines, i)
                if nearest_idx is not None:
                    matches = [m for m in label_matches_by_line[nearest_idx] if m.concept in rate_concepts]
        if not matches:
            continue
        for token in _iter_numeric_tokens(line.text):
            if token.value <= 0 or token.value > 100 or token.has_decimal:
                continue
            if not (token.near_percent or token.value in reference_data.plausible_vat_rates):
                continue
            signals = [f"{m.concept.value}_label" for m in matches]
            if token.near_percent:
                signals.append("percent_marker")
            if token.value in reference_data.plausible_vat_rates:
                signals.append("known_vat_rate")
            candidates.append(
                FieldCandidate(
                    "vat_rate", token.value, line.text, line.confidence, line.page, line.bounding_box, signals,
                    reading_order=line.reading_order,
                )
            )
    return candidates


def _currency_candidates(lines: list[OcrLine], reference_data: ReferenceData) -> list[FieldCandidate]:
    candidates = []
    if not reference_data.valid_currency_codes:
        return candidates
    # Digit-only-safe boundary (not \b) — a currency code glued directly to an
    # amount with no space ("SAR72.90") is common, especially in app-generated
    # receipts; only an adjacent LETTER (part of a longer/different word,
    # e.g. "SARAH") disqualifies a match.
    pattern = re.compile(
        r"(?<![A-Za-z])(" + "|".join(re.escape(c) for c in reference_data.valid_currency_codes) + r")(?![A-Za-z])",
        re.IGNORECASE,
    )
    for line in lines:
        for m in pattern.finditer(line.text):
            signals = ["currency_code_match"]
            if any(t.value > 0 for t in _iter_numeric_tokens(line.text)):
                signals.append("same_line")
            candidates.append(
                FieldCandidate(
                    "currency", m.group(1).upper(), line.text, line.confidence, line.page, line.bounding_box, signals,
                    reading_order=line.reading_order,
                )
            )
    return candidates


def _date_is_plausible(raw: str) -> bool:
    nums = [int(n) for n in re.findall(r"\d+", raw)]
    numeric_parts = [n for n in nums if n < 100]
    if len(numeric_parts) < 2:
        return True
    a, b = numeric_parts[0], numeric_parts[1]
    return a <= 31 and b <= 31


def _date_candidates(lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]]) -> list[FieldCandidate]:
    candidates = []
    for i, line in enumerate(lines):
        for pattern in _DATE_PATTERNS:
            for m in pattern.finditer(line.text):
                raw = m.group(0)
                if not _date_is_plausible(raw):
                    continue
                date_matches = [x for x in label_matches_by_line[i] if x.concept == LabelConcept.DATE]
                signals = ["date_format_match"]
                if date_matches:
                    signals.append("date_label")
                    if any(x.fuzzy for x in date_matches):
                        signals.append("fuzzy_label_match")
                candidates.append(
                    FieldCandidate(
                        "date", raw, line.text, line.confidence, line.page, line.bounding_box, signals,
                        reading_order=line.reading_order,
                    )
                )
    return candidates


def _id_candidates(lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]]) -> list[FieldCandidate]:
    candidates = []
    for i, line in enumerate(lines):
        matches = [m for m in label_matches_by_line[i] if m.concept in _ID_CONCEPT_TO_FIELD]
        if not matches:
            continue
        for m in _ID_TOKEN_RE.finditer(line.text):
            token = m.group(0)
            has_letter = any(c.isalpha() for c in token)
            digit_count = sum(c.isdigit() for c in token)
            if digit_count == 0:
                continue
            if not has_letter and digit_count < 4:
                continue
            for concept_match in matches:
                field_name = _ID_CONCEPT_TO_FIELD[concept_match.concept]
                signals = [f"{concept_match.concept.value}_label"]
                if concept_match.fuzzy:
                    signals.append("fuzzy_label_match")
                candidates.append(
                    FieldCandidate(
                        field_name, token, line.text, line.confidence, line.page, line.bounding_box, signals,
                        reading_order=line.reading_order,
                    )
                )
    return candidates


def _vendor_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], reference_data: ReferenceData
) -> list[FieldCandidate]:
    candidates = []
    top_n = min(5, len(lines))
    for i in range(top_n):
        line = lines[i]
        text = line.text.strip()
        if len(text) < 3 or re.fullmatch(r"[\d\s.\-/:]+", text):
            continue
        matches = label_matches_by_line[i]
        covered = sum(m.span[1] - m.span[0] for m in matches)
        if matches and covered / max(len(text), 1) > 0.4:
            continue  # this line is mostly a recognized label/value line, not a vendor name

        signals = ["top_of_receipt"]
        confidence = max(0.1, line.confidence * (1.0 - i * 0.12))
        if reference_data.known_vendors:
            best_ratio = max(
                (difflib.SequenceMatcher(None, text.lower(), v.lower()).ratio() for v in reference_data.known_vendors),
                default=0.0,
            )
            if best_ratio >= 0.85:
                signals.append("known_vendor_match")
                confidence = min(1.0, confidence + 0.25)
        candidates.append(
            FieldCandidate(
                "vendor", text, line.text, confidence, line.page, line.bounding_box, signals,
                reading_order=line.reading_order,
            )
        )
    return candidates


def _category_candidates(lines: list[OcrLine], reference_data: ReferenceData) -> list[FieldCandidate]:
    candidates = []
    if not reference_data.categories:
        return candidates
    full_text = " ".join(ln.text for ln in lines).lower()
    for cat in reference_data.categories:
        score: Optional[float] = None
        matched_text = None
        for kw in cat.keywords:
            if kw and kw.lower() in full_text:
                score, matched_text = 0.9, kw
                break
        if score is None:
            for name in (cat.name, cat.name_ar):
                if name and name.lower() in full_text:
                    score, matched_text = 0.65, name
                    break
        if score is not None:
            signals = ["known_category_match"] + (["keyword_match"] if score >= 0.9 else ["name_match"])
            candidates.append(FieldCandidate("expense_category", cat.name, matched_text, score, 1, None, signals))
    return candidates


def generate_candidates(lines: list[OcrLine], reference_data: ReferenceData) -> list[FieldCandidate]:
    label_matches_by_line = [
        match_label_concepts(ln.text, reference_data.label_vocabulary, reference_data.label_exclusions)
        for ln in lines
    ]
    candidates: list[FieldCandidate] = []
    candidates += _money_field_candidates(lines, label_matches_by_line, reference_data)
    candidates += _vat_rate_candidates(lines, label_matches_by_line, reference_data)
    candidates += _currency_candidates(lines, reference_data)
    candidates += _date_candidates(lines, label_matches_by_line)
    candidates += _id_candidates(lines, label_matches_by_line)
    candidates += _vendor_candidates(lines, label_matches_by_line, reference_data)
    candidates += _category_candidates(lines, reference_data)
    return candidates
