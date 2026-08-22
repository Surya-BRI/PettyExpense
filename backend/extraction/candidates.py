"""Stage 4: candidate generation — turns OCR lines into many FieldCandidate proposals per field; disambiguation happens later, not here."""
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
# A line whose own label is a document/reference-number concept is not a plausible source for an UNLABELED money value.
_ID_LIKE_CONCEPTS = {
    LabelConcept.INVOICE_NUMBER,
    LabelConcept.TRANSACTION_NUMBER,
    LabelConcept.TAX_REGISTRATION_NUMBER,
    LabelConcept.DOCUMENT_TYPE_HEADER,
}

# Digit-only boundary (not alnum) — a number glued to a currency code ("AED0.29") is common and must match; an adjacent digit disqualifies it.
_NUMBER_TOKEN_RE = re.compile(r"(?<!\d)\d[\d.,]{0,9}\d(?!\d)|(?<!\d)\d(?!\d)")
_DATE_PATTERNS = (
    re.compile(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b"),
    re.compile(r"\b\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}\b"),
    re.compile(
        r"\b\d{1,2}[\s\-.]*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\-.]*\d{2,4}\b",
        re.IGNORECASE,
    ),
    # Month-name-then-day order ("Feb 8") — no trailing year required, so the day number is still excluded from money candidates.
    re.compile(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s.\-]*\d{1,2}\b(?:[\s,]*\d{2,4}\b)?",
        re.IGNORECASE,
    ),
)
# Clock times ("8:09 AM") are numeric but never a money value — excluded the same way dates are.
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
    # True unless geometry proves these two lines are in different columns (prevents pairing a label with a value from a different column). Permissive when a box is unknown.
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
    # Closest horizontally-aligned line above lines[i] — a column-aware "previous line" for table-style header/value rows.
    current = lines[i].bounding_box
    if current is None:
        return None
    current_center = (current[1] + current[3]) / 2.0
    best_idx, best_gap = None, None
    for j in range(i):
        other = lines[j].bounding_box
        if other is None:
            continue
        # Compare row centers, not edges — adjacent boxes commonly overlap by a few pixels (detection imprecision).
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

        # Union every location tier instead of picking one — a merged-column box can legitimately be both a same-line label AND a value row for another header.
        tiered_matches: list[tuple[LabelMatch, str]] = [(m, "same_line") for m in same_line]
        tiered_matches += [(m, "same_row") for m in same_row if m not in same_line]
        tiered_matches += [
            (m, "previous_line_label") for m in prev_line if m not in same_line and m not in same_row
        ]

        money_tokens = [t for t in tokens if not t.near_percent or not _token_only_percent_context(t)]
        if tiered_matches:
            # Every label pairs with every token here (not label-order-with-value-order) — order-based pairing was tried and reverted as net-negative on garbled real receipts.
            for match, location in tiered_matches:
                field_name = _MONEY_CONCEPT_TO_FIELD[match.concept]
                # same_row/previous_line_label is positional evidence only — a bare single digit there is likely an OCR fragment, so require 2+ digits or a decimal (same_line doesn't need this).
                usable_tokens = (
                    money_tokens
                    if location == "same_line"
                    else [t for t in money_tokens if t.has_decimal or t.value >= 10]
                )
                for token in usable_tokens:
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
                            ocr_confidence=line.confidence,
                        )
                    )
        elif not has_item_table and not any(m.concept in _ID_LIKE_CONCEPTS for m in label_matches_by_line[i]):
            for token in money_tokens:
                # A bare number next to an actual currency code ("SAR72.90") is much stronger evidence than any other bare digit on the page.
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
                            ocr_confidence=line.confidence,
                        )
                    )
    return candidates


def _token_only_percent_context(token: _NumericToken) -> bool:
    # Excludes a number only when it's a bare 1-3 digit integer next to a '%' (e.g. the '5' in "VAT % 5") — never a real money value.
    return not token.has_decimal and token.value <= 100


def _vat_rate_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], reference_data: ReferenceData
) -> list[FieldCandidate]:
    candidates = []
    rate_concepts = (LabelConcept.VAT_TAX_RATE, LabelConcept.VAT_TAX_AMOUNT)
    for i, line in enumerate(lines):
        matches = [m for m in label_matches_by_line[i] if m.concept in rate_concepts]
        if not matches and line.bounding_box is not None:
            # A "VAT % | Sale Amt | VAT Amt" header row often sits above its value row, not on the same line — same column-aware lookup as money fields.
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
    # Digit-safe boundary (not \b) — a currency code glued to an amount ("SAR72.90") is common; only an adjacent LETTER disqualifies a match.
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


def _date_is_plausible_dmy(raw: str) -> bool:
    # DD/MM/YY check for the numeric d/d/d pattern: accepts day-first OR month-first (real receipts print both), rejects only when neither works.
    nums = re.findall(r"\d+", raw)
    if len(nums) < 2:
        return True
    a, b = int(nums[0]), int(nums[1])
    if a > 31 or b > 31:
        return False
    return a <= 12 or b <= 12


def _date_candidates(lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]]) -> list[FieldCandidate]:
    candidates = []
    for i, line in enumerate(lines):
        for pattern_index, pattern in enumerate(_DATE_PATTERNS):
            for m in pattern.finditer(line.text):
                raw = m.group(0)
                plausible = _date_is_plausible_dmy(raw) if pattern_index == 0 else _date_is_plausible(raw)
                if not plausible:
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


def _nearest_aligned_line_below(lines: list[OcrLine], i: int) -> Optional[int]:
    # Mirror of _nearest_aligned_line_above — an ID label often sits below its number, so ID candidates need both directions too.
    current = lines[i].bounding_box
    if current is None:
        return None
    current_center = (current[1] + current[3]) / 2.0
    best_idx, best_gap = None, None
    for j in range(i + 1, len(lines)):
        other = lines[j].bounding_box
        if other is None:
            continue
        other_center = (other[1] + other[3]) / 2.0
        gap = other_center - current_center
        if gap <= 0:
            continue
        if not _horizontally_aligned(current, other):
            continue
        if best_gap is None or gap < best_gap:
            best_gap, best_idx = gap, j
    return best_idx


def _id_candidates(lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]]) -> list[FieldCandidate]:
    candidates = []
    for i, line in enumerate(lines):
        same_line = [m for m in label_matches_by_line[i] if m.concept in _ID_CONCEPT_TO_FIELD]
        matches = list(same_line)
        # A line with its OWN money label (e.g. "Change AED4.00") is a value line, not a document number — skip cross-line ID borrowing for it.
        has_own_money_label = any(m.concept in _MONEY_CONCEPTS for m in label_matches_by_line[i])
        if has_own_money_label:
            pass
        elif line.bounding_box is not None:
            for j, other in enumerate(lines):
                if j == i or other.bounding_box is None:
                    continue
                if _same_row(line.bounding_box, other.bounding_box):
                    matches += [
                        m for m in label_matches_by_line[j] if m.concept in _ID_CONCEPT_TO_FIELD and m not in matches
                    ]
            for neighbor_idx in (_nearest_aligned_line_above(lines, i), _nearest_aligned_line_below(lines, i)):
                if neighbor_idx is None:
                    continue
                matches += [
                    m
                    for m in label_matches_by_line[neighbor_idx]
                    if m.concept in _ID_CONCEPT_TO_FIELD and m not in matches
                ]
        elif i > 0 and lines[i - 1].bounding_box is None:
            matches += [
                m for m in label_matches_by_line[i - 1] if m.concept in _ID_CONCEPT_TO_FIELD and m not in matches
            ]
        if not matches:
            continue
        date_spans = _date_span_ranges(line.text)
        for m in _ID_TOKEN_RE.finditer(line.text):
            token = m.group(0)
            if _overlaps_any(m.start(), m.end(), date_spans):
                continue  # a date string is never an invoice/transaction number, however near a matching label
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


def _line_label_coverage(text: str, matches: list[LabelMatch]) -> float:
    covered = sum(m.span[1] - m.span[0] for m in matches)
    return covered / max(len(text), 1)


def _is_vendor_eligible_line(text: str, matches: list[LabelMatch]) -> bool:
    if len(text) < 3 or re.fullmatch(r"[\d\s.\-/:]+", text):
        return False
    if matches and _line_label_coverage(text, matches) > 0.4:
        return False  # this line is mostly a recognized label/value line, not a vendor name
    return True


_MAX_HEADER_LINE_GAP_HEIGHT_RATIO = 1.6
_MAX_HEADER_MERGE_LINES = 2


def _vertically_adjacent_and_aligned(a: OcrLine, b: OcrLine) -> bool:
    # True when two lines look like one wrapped header block: close vertical spacing + overlapping horizontal extent. Permissive when a box is unknown.
    if a.bounding_box is None or b.bounding_box is None:
        return True
    a_x0, a_y0, a_x1, a_y1 = a.bounding_box
    b_x0, b_y0, b_x1, b_y1 = b.bounding_box
    height = max(a_y1 - a_y0, 1e-6)
    gap = b_y0 - a_y1
    vertically_close = gap <= _MAX_HEADER_LINE_GAP_HEIGHT_RATIO * height
    horizontally_aligned = not (a_x1 < b_x0 or b_x1 < a_x0)
    return vertically_close and horizontally_aligned


def _digit_dominated(text: str) -> bool:
    # An address/phone/reference-number line can otherwise pass the adjacency check — this stops it being glued onto the vendor name as a false continuation.
    stripped = re.sub(r"\s+", "", text)
    if not stripped:
        return False
    digits = sum(c.isdigit() for c in stripped)
    return digits / len(stripped) > 0.25


def _looks_like_address_line(text: str) -> bool:
    # A "City, Country" style line is plausible on its own but is an address block line, not a vendor-name continuation — a comma is the tell.
    return "," in text


def _vendor_known_match_bonus(text: str, reference_data: ReferenceData) -> tuple[float, list[str]]:
    if not reference_data.known_vendors:
        return 0.0, []
    best_ratio = max(
        (difflib.SequenceMatcher(None, text.lower(), v.lower()).ratio() for v in reference_data.known_vendors),
        default=0.0,
    )
    return (0.25, ["known_vendor_match"]) if best_ratio >= 0.85 else (0.0, [])


def _vendor_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], reference_data: ReferenceData
) -> list[FieldCandidate]:
    candidates = []
    top_n = min(5, len(lines))
    eligible = [
        _is_vendor_eligible_line(lines[i].text.strip(), label_matches_by_line[i]) for i in range(top_n)
    ]

    for i in range(top_n):
        if not eligible[i]:
            continue
        line = lines[i]
        text = line.text.strip()
        signals = ["top_of_receipt"]
        confidence = max(0.1, line.confidence * (1.0 - i * 0.12))
        bonus, bonus_signals = _vendor_known_match_bonus(text, reference_data)
        confidence = min(1.0, confidence + bonus)
        signals += bonus_signals
        candidates.append(
            FieldCandidate(
                "vendor", text, line.text, confidence, line.page, line.bounding_box, signals,
                reading_order=line.reading_order,
            )
        )

    # Multi-line header merge: a vendor name wrapped across 2 stacked lines is one vendor. Chaining uses geometry + same language, not list-index adjacency (bilingual interleaving breaks that).
    def _line_lang(idx: int) -> str:
        words = lines[idx].words
        return words[0].lang if words else "en"

    def _next_header_line(i: int) -> Optional[int]:
        a = lines[i]
        a_lang = _line_lang(i)
        if a.bounding_box is None:
            # No geometry to confirm adjacency — merging on text order alone is unsafe, so header merging just doesn't apply without bboxes.
            return None
        # Nearest same-language line below `a`, among ALL top_n lines regardless of eligibility — never skip past a nearer non-eligible line to reach a further one.
        a_height = max(a.bounding_box[3] - a.bounding_box[1], 1e-6)
        best_idx, best_gap = None, None
        for j in range(top_n):
            if j == i or _line_lang(j) != a_lang:
                continue
            b = lines[j]
            if b.bounding_box is None:
                continue
            gap = b.bounding_box[1] - a.bounding_box[3]
            # Allow a small negative gap (detection boxes often overlap by a few pixels); only reject a gap negative enough to mean side-by-side rows.
            if gap < -0.3 * a_height or not _vertically_adjacent_and_aligned(a, b):
                continue
            if best_gap is None or gap < best_gap:
                best_gap, best_idx = gap, j
        if (
            best_idx is None
            or not eligible[best_idx]
            or _digit_dominated(lines[best_idx].text)
            or _looks_like_address_line(lines[best_idx].text)
        ):
            return None
        return best_idx

    continuations = set()
    for i in range(top_n):
        if not eligible[i] or i in continuations:
            continue
        chain = [i]
        cur = i
        while len(chain) < _MAX_HEADER_MERGE_LINES:
            # Cap at 2 lines (name + suffix, the only observed case) so the chain can't keep swallowing metadata lines further down.
            nxt = _next_header_line(cur)
            if nxt is None or nxt in chain:
                break
            chain.append(nxt)
            continuations.add(nxt)
            cur = nxt
        if len(chain) >= 2:
            merged_text = " ".join(lines[k].text.strip() for k in chain)
            merged_matches = match_label_concepts(
                merged_text, reference_data.label_vocabulary, reference_data.label_exclusions
            )
            if _is_vendor_eligible_line(merged_text, merged_matches):
                boxes = [lines[k].bounding_box for k in chain if lines[k].bounding_box is not None]
                merged_bbox = (
                    (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
                    if boxes
                    else None
                )
                base_confidence = max(0.1, lines[i].confidence * (1.0 - i * 0.12))
                bonus, bonus_signals = _vendor_known_match_bonus(merged_text, reference_data)
                confidence = min(1.0, base_confidence + 0.1 + bonus)
                candidates.append(
                    FieldCandidate(
                        "vendor", merged_text, merged_text, confidence, lines[i].page, merged_bbox,
                        ["top_of_receipt", "multiline_header_merge"] + bonus_signals,
                        reading_order=lines[i].reading_order,
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
