"""Stage 4: candidate generation — turns OCR lines into many FieldCandidate proposals per field; disambiguation happens later, not here."""
import difflib
import re
from datetime import date
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
    # A delivery note's own number is the document number when there is no invoice number, but loses to a real "Invoice No." on the same page.
    LabelConcept.DELIVERY_NOTE_NUMBER: "invoice_number",
}
# A line whose own label is a document/reference-number concept is not a plausible source for an UNLABELED money value.
_ID_LIKE_CONCEPTS = {
    LabelConcept.INVOICE_NUMBER,
    LabelConcept.TRANSACTION_NUMBER,
    LabelConcept.DELIVERY_NOTE_NUMBER,
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
# A document's own generic title -- a phone-app screen header ("Ride details", "Trip summary") or
# a printed receipt's own heading ("Tax Invoice", "Delivery Note", "Credit Note") -- shared chrome
# across countless vendors, never the vendor name itself. Short (<=3 words) and ends on one of
# these nouns -- a real business name ending in "invoice"/"note" this short and generic is
# implausible.
_DOCUMENT_TITLE_RE = re.compile(
    # "invoise" is a confirmed real OCR misread of "invoice" (c/s confusion), seen verbatim on a
    # real sample bill ("Customer Invoise") -- kept as a literal alternate, same as other
    # known-misread handling elsewhere in this module.
    r"^(?:[A-Za-z]+\s+){0,2}(?:details|summary|receipt|invoice|invoise|history|note|slip|voucher|statement)$",
    re.IGNORECASE,
)
_NON_MONEY_NUMBER_CONTEXT_PATTERNS = _DATE_PATTERNS + (_TIME_PATTERN,)
_ID_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9][A-Za-z0-9\-/]{2,20}(?![A-Za-z0-9])")


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


# A quantity cell's own unit suffix ("558 PCS", "76 NOS" -- the same word list line_items.py uses
# for the identical purpose on its own, separate quantity column) or a physical dimension's unit
# ("100 CM", "1.2 MM", a product's size, never a price) -- either way, not a money value.
_QTY_UNIT_SUFFIX_RE = re.compile(
    r"^\s*(?:pcs|pc|nos|mtr|mtrs|kg|kgs|ctn|ctns|box|boxes|unit|units|ea|ltr|ltrs"
    r"|cm|mm|m|inch|inches|in|ft|yd|km)\b",
    re.IGNORECASE,
)


_ZONE_CODE_PREFIX_RE = re.compile(r"\b[A-Z]{2,6}\s*$")


def _looks_like_non_money(
    text: str,
    token: "_NumericToken",
    currency_codes: tuple[str, ...],
    line_label_matches: tuple["LabelMatch", ...] = (),
    has_money_label_context: bool = False,
) -> bool:
    # A number glued directly to letters with no gap ("14*17*1.2MM", "558PCS", "5CM") is a
    # dimension or a quantity's own unit suffix, not a money value -- unless those letters are
    # themselves a currency code ("100AED"), the one case where a glued suffix is legitimate.
    after = text[token.end :]
    if after[:1].isalpha():
        tail_match = re.match(r"[^\W\d_]+", after)
        tail = tail_match.group(0) if tail_match else after[:1]
        if currency_codes and tail.upper() in {c.upper() for c in currency_codes}:
            return False
        # A single stray letter glued on, sitting in a column/row whose own header is a
        # recognised money label ("Amount", "Fare"...), is more likely a misread punctuation mark
        # (a handwritten "/" or "." read as "f"/"l") than a genuine unit suffix -- a real unit
        # word is 2+ letters (_QTY_UNIT_SUFFIX_RE below already requires that), so this only
        # relaxes the single-character case, never "PCS"/"CM"/etc.
        if has_money_label_context and len(tail) == 1 and not _QTY_UNIT_SUFFIX_RE.match(after):
            return False
        return True
    if _QTY_UNIT_SUFFIX_RE.match(after):
        return True
    # A short all-caps letter code directly before the number ("KAFD 2.08", "DQ 1.02") is a
    # location/zone code (common on handwritten taxi-receipt "to/from" notes), not a money value --
    # unless that code is a currency code ("SAR 45.00") or itself a recognised money label
    # ("VAT 5.00", "CASH 45.00"), both of which are legitimate labelled amounts.
    before = text[: token.start]
    prefix_match = _ZONE_CODE_PREFIX_RE.search(before)
    if prefix_match:
        code = prefix_match.group(0).strip()
        code_start = prefix_match.start()
        code_end = code_start + len(code)
        is_currency = bool(currency_codes) and code.upper() in {c.upper() for c in currency_codes}
        is_label = any(m.span[0] < code_end and code_start < m.span[1] for m in line_label_matches)
        if not is_currency and not is_label:
            return True
    return False


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

        has_money_label_context = bool(same_line or same_row or prev_line)
        tokens = [
            t
            for t in _iter_numeric_tokens(line.text, reference_data.valid_currency_codes)
            if t.value > 0 and not _looks_like_phone_or_id(t.value) and not _overlaps_any(t.start, t.end, date_spans)
            and not _looks_like_non_money(
                line.text, t, reference_data.valid_currency_codes, tuple(label_matches_by_line[i]),
                has_money_label_context,
            )
        ]
        if not tokens:
            continue

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


_CURRENCY_LABEL_RE = re.compile(r"(?i)(?:currency|curr\.?|\u0627\u0644\u0639\u0645\u0644\u0629|\u0639\u0645\u0644\u0629)\s*[:\-]?\s*$")


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
        header_words = len(re.findall(r"(?i)\b(?:product|unit|qty|quantity|description|item|rate)\b", line.text))
        has_number = any(t.value > 0 for t in _iter_numeric_tokens(line.text))
        for m in pattern.finditer(line.text):
            labelled = bool(_CURRENCY_LABEL_RE.search(line.text[: m.start()]))
            # A code on a table-header line ("SR# PRODUCT UNIT ..." read as "SAR PRODUCT UNIT ...") is a garbled word, not a currency.
            if header_words >= 2 and not labelled and not has_number:
                continue
            signals = ["currency_code_match"]
            if has_number:
                signals.append("same_line")
            if labelled:
                signals.append("currency_labelled")
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


_YEAR_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")


def _check_year(raw: str) -> tuple[Optional[str], bool]:
    # A 4-digit year outside a sane window is an OCR misread ("1016" for 2026), not a real date. Returns
    # (repaired date text or None, year_is_implausible). The repair is spell-correction style: the one
    # plausible year (this year or last) within 2 digit positions of what was read -- never a free guess.
    m = _YEAR_RE.search(raw)
    if not m:
        return None, False
    this_year = date.today().year
    read = m.group(1)
    if 1300 <= int(read) <= 1500:
        return None, False  # a Hijri-calendar year (1447 ~ 2025/26), printed on many Saudi bills -- not a misread
    if this_year - 6 <= int(read) <= this_year + 1:
        return None, False
    near = [str(y) for y in (this_year, this_year - 1) if sum(a != b for a, b in zip(read, str(y))) <= 2]
    if len(near) != 1:
        return None, True
    return raw[: m.start(1)] + near[0] + raw[m.end(1):], True


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
                repaired, implausible = _check_year(raw)
                if implausible:
                    signals.append("implausible_year")
                candidates.append(
                    FieldCandidate(
                        "date", raw, line.text, line.confidence, line.page, line.bounding_box, signals,
                        reading_order=line.reading_order,
                    )
                )
                if repaired is not None:
                    candidates.append(
                        FieldCandidate(
                            "date", repaired, line.text, line.confidence * 0.9, line.page, line.bounding_box,
                            [x for x in signals if x != "implausible_year"] + ["year_repaired"],
                            reading_order=line.reading_order,
                        )
                    )
    return candidates


def _nearest_aligned_line_below(lines: list[OcrLine], i: int, min_gap: float = 0.0) -> Optional[int]:
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
        if gap <= min_gap:
            continue
        if not _horizontally_aligned(current, other):
            continue
        if best_gap is None or gap < best_gap:
            best_gap, best_idx = gap, j
    return best_idx


_PHONE_CONTEXT_RE = re.compile(r"(?i)(?:tel|mob|mobile|phone|ph|fax|whatsapp)[^\d]{0,8}$")
_MOBILE_RE = re.compile(r"0\d{9}|(?:00)?(?:971|966|968|974|965|973)\d{8,9}")


# Words that mark a nearby number as something other than a document number: phone/fax lines, bank
# details, certifications, delivery notes, addresses, and customer/PO-style reference ids.
_ID_BLOCK_BEFORE_RE = re.compile(
    r"(?i)(?<![a-z])(?:tel|telephone|phone|fax|mob|mobile|whatsapp|a/c|acc|account|iban|bank|swift|iso|lpo|po\s?box"
    r"|p\.\s?o\.?\s?box|d\.o|zip|pin|date|dated|licen[cs]e|هاتف|تلفون|تليفون|جوال|موبايل|فاكس|ص\.?\s?ب|حساب|ايبان|آيبان|التاريخ)(?![a-z])"
    r"(?:\s*(?:no|number|name|code|id)\b)?\s*[:.\-#]*\s*(?:\+?\d{1,4}\s*)?$"
)
_ID_BLOCK_AFTER_RE = re.compile(
    r"(?i)^[^a-z0-9]{0,3}(?:[a-z0-9.,&']+\s+){0,3}?(?:street|st\.|road|rd\.|near|building|bldg|floor|flat|suite|p\.?\s?o\.?\s?box)(?![a-z])"
)
_ID_BLOCK_PREFIX_RE = re.compile(r"(?i)^(?:cust|customer|acc|account|lpo|po|ref)[-/]")


def _has_strong_id_shape(token: str) -> bool:
    # What a number borrowed from a neighbouring line's label must look like to be trusted: a code
    # with separators, a letter+digit mix, or a long digit run -- not a bare 4-digit figure.
    digits = sum(c.isdigit() for c in token)
    letters = sum(c.isalpha() for c in token)
    return ("-" in token or "/" in token) or (letters and digits and len(token) >= 5) or digits >= 7


def _is_non_id_token(token: str, before: str, currency_codes: tuple[str, ...]) -> bool:
    # Shapes that sit next to an "invoice no" label on real bills but are never a document number.
    digits = sum(c.isdigit() for c in token)
    letters = sum(c.isalpha() for c in token)
    code_shaped = "-" in token or "/" in token
    if digits < 2 and not code_shaped:
        return True  # a word with one stray digit ("Invo1ce", "Telbole6")
    if re.fullmatch(r"[A-Za-z]{2}\d{2}[A-Za-z0-9]{11,30}", token):
        return True  # an IBAN ("AE42 0400 ...")
    if before.endswith("@"):
        return True
    if re.fullmatch(r"[A-Za-z]{3}\d+", token) and token[:3].upper() in currency_codes:
        return True  # an amount glued to its currency code ("SAR72")
    if letters == 0:
        if digits >= 14:
            return True  # tax registration number / barcode length
        if _MOBILE_RE.fullmatch(token) or _PHONE_CONTEXT_RE.search(before) or before.rstrip().endswith("+"):
            return True  # a phone number
    return False


_DOTTED_ID_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9]*(?:[\-/.][A-Za-z0-9]+){2,}(?![A-Za-z0-9])")
_ID_STOP_PREFIX = frozenset({
    "no", "invoice", "bill", "date", "dated", "inv", "tax", "cash", "credit", "ref", "number", "tel", "mob", "fax", "of", "to", "by",
})


def _span_box(line: OcrLine, span: tuple[int, int]) -> Optional[tuple[float, float, float, float]]:
    # x/y box of a character span in a line: the union of the words it falls on, interpolated by character offset
    # inside a word box (the OCR engine often returns several tokens as one box).
    xs, ys = [], []
    offset = 0
    for w in line.words:
        if not w.text:
            continue
        start, end = offset, offset + len(w.text)
        offset = end + 1
        if w.bounding_box is None or end <= span[0] or start >= span[1]:
            continue
        x0, y0, x1, y1 = w.bounding_box
        width, n = x1 - x0, max(end - start, 1)
        xs += [x0 + width * (max(span[0], start) - start) / n, x0 + width * (min(span[1], end) - start) / n]
        ys += [y0, y1]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _fix_letter_zero(token: str) -> str:
    # "000P0SDIP2000039678": a zero sandwiched between letters inside a mostly-alphabetic code is an O.
    if sum(c.isalpha() for c in token) < 5:
        return token
    chars = list(token)
    for i in range(1, len(chars) - 1):
        if chars[i] == "0" and chars[i - 1].isalpha() and chars[i + 1].isalpha():
            chars[i] = "O"
    return "".join(chars)


def _id_value_ok(token: str, before: str, after: str, date_spans, start: int, end: int, currency_codes) -> bool:
    digits = sum(c.isdigit() for c in token)
    if digits < 2 or re.fullmatch(r"[0\-/]+", token):
        return False
    if re.fullmatch(r"\d{1,2}[\-/]\d{1,4}", token):
        return False  # a piece of a date ("08-15" from "2026–08-15"), not a number
    overlap = sum(max(0, min(end, e) - max(start, st)) for st, e in date_spans)
    if overlap and not (any(c.isalpha() for c in token) and overlap < 0.6 * (end - start)):
        return False  # a date string is never an invoice/transaction number, however near a matching label
    if _is_non_id_token(token, before, currency_codes):
        return False
    if _ID_BLOCK_BEFORE_RE.search(before[-40:]) or _ID_BLOCK_AFTER_RE.match(after) or _ID_BLOCK_PREFIX_RE.match(token):
        return False
    if after.startswith("@"):
        return False  # the local part of an e-mail address
    return True


def _id_tokens(text: str) -> list[tuple[str, int, int]]:
    # Candidate id-shaped tokens with their span; "RB 26/01008" is one number, and a token cut out of the middle of a
    # decimal ("210.0000", "24.007024.00") is never one.
    out = []
    dotted = [
        (m.group(0), m.start(), m.end())
        for m in _DOTTED_ID_RE.finditer(text)
        if "." in m.group(0) and "-" in m.group(0) and any(c.isalpha() for c in m.group(0))
        and text[m.end(): m.end() + 1] != "."  # cut off at the end of an OCR box
    ]
    for m in _ID_TOKEN_RE.finditer(text):
        token, start, end = m.group(0), m.start(), m.end()
        if re.search(r"\d[.,]$", text[:start]) or re.match(r"[.,]\d", text[end:]):
            continue
        if re.search(r"(?<![A-Za-z])\.$", text[:start]):
            continue  # the tail of a dotted code or amount cut across OCR boxes (" .15-02324")
        prefix = re.search(r"(?<![A-Za-z0-9])([A-Z]{1,6})\s$", text[:start])
        if prefix and prefix.group(1).lower() not in _ID_STOP_PREFIX and ("/" in token or "-" in token):
            token, start = prefix.group(1) + " " + token, prefix.start(1)
        if any(ds <= start < de or ds < end <= de for _t, ds, de in dotted):
            continue
        out.append((token, start, end))
    return out + dotted


def _id_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], currency_codes: tuple[str, ...] = ()
) -> list[FieldCandidate]:
    candidates: list[FieldCandidate] = []
    seen: set[tuple] = set()

    def add(line: OcrLine, token: str, concept_match: LabelMatch, signals: list[str]) -> None:
        field_name = _ID_CONCEPT_TO_FIELD[concept_match.concept]
        sig = [f"{concept_match.concept.value}_label"] + signals
        if concept_match.fuzzy:
            sig.append("fuzzy_label_match")
        if concept_match.concept == LabelConcept.DELIVERY_NOTE_NUMBER:
            sig.append("secondary_label")
        key = (field_name, token, tuple(sig))
        if key in seen:
            return
        seen.add(key)
        candidates.append(
            FieldCandidate(
                field_name, _fix_letter_zero(token), line.text, line.confidence, line.page, line.bounding_box, sig,
                reading_order=line.reading_order,
            )
        )

    squash = lambda t: re.sub(r"[\s:#.\-]+", "", t)

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
        # The number printed right after a "TRN" label is a tax registration number, never a document number ("TRN1003... TAX INVOICE No. 22860").
        trn_spans = [
            (m.span[0], m.span[1] + 24)
            for m in label_matches_by_line[i]
            if m.concept == LabelConcept.TAX_REGISTRATION_NUMBER
        ]
        for token, start, end in _id_tokens(line.text):
            if any(ts <= start < te and not any(c.isalpha() for c in token[3:]) for ts, te in trn_spans):
                continue
            before, after = line.text[:start], line.text[end: end + 40]
            if not _id_value_ok(token, before, after, date_spans, start, end, currency_codes):
                continue
            adjacent = any(0 <= start - lm.span[1] <= 3 or 0 <= lm.span[0] - end <= 3 for lm in same_line)
            rest = squash(line.text.replace(token, "", 1))
            lone_value_line = not any(c.isalpha() for c in rest) or not rest
            digits = sum(c.isdigit() for c in token)
            if not adjacent and not (_has_strong_id_shape(token) or lone_value_line):
                continue
            # A code inside a descriptive sentence ("NTRL BR-TZ231 Label Cassette") is a product code, not a document number.
            if not adjacent and len(re.findall(r"[A-Za-z]{3,}", line.text.replace(token.split(" ")[-1], " ", 1))) >= 3:
                continue
            if not any(c.isalpha() for c in token) and digits < (3 if adjacent else 4):
                continue
            for concept_match in matches:
                signals = []
                if concept_match in same_line:
                    signals.append("same_line")
                    if adjacent:
                        signals.append("adjacent_to_label")
                add(line, token, concept_match, signals)

    # A value printed directly BELOW its label, in the same column ("Invoice No." / "CASH/SHT/1205 29-Jul-26"),
    # found from word positions so it works across merged or interleaved OCR lines.
    for i, line in enumerate(lines):
        if any(m.concept in _MONEY_CONCEPTS for m in label_matches_by_line[i]):
            continue
        for lm in (m for m in label_matches_by_line[i] if m.concept in _ID_CONCEPT_TO_FIELD):
            box = _span_box(line, lm.span)
            if box is None:
                continue
            found = _nearest_id_below(lines, i, box, currency_codes)
            if found is not None:
                add(found[0], found[1], lm, ["below_label"])
    return candidates


def _nearest_id_below(
    lines: list[OcrLine], label_line_idx: int, label_box: tuple[float, float, float, float], currency_codes
) -> Optional[tuple[OcrLine, str]]:
    # Shared by the "value below its label" case above and _bill_column_header_candidates below:
    # among every id-shaped token on the page, find the one sitting in the same column, just under label_box.
    lx0, ly0, lx1, ly1 = label_box
    h = max(ly1 - ly0, 1.0)
    pad = 0.5 * max(lx1 - lx0, h)
    best = None
    for j, other in enumerate(lines):
        if j == label_line_idx or other.bounding_box is None:
            continue
        o_date = _date_span_ranges(other.text)
        for token, start, end in _id_tokens(other.text):
            tb = _span_box(other, (start, end))
            if tb is None:
                continue
            # centre-to-centre, so a slightly tilted page (value line starting above the label's bottom edge) still counts
            dy = (tb[1] + tb[3]) / 2.0 - (ly0 + ly1) / 2.0
            if dy < 0.25 * h or dy > 3.6 * h:
                continue
            if tb[2] < lx0 - pad or tb[0] > lx1 + pad:
                continue
            before, after = other.text[:start], other.text[end: end + 40]
            if not _id_value_ok(token, before, after, o_date, start, end, currency_codes):
                continue
            if not any(c.isalpha() for c in token) and sum(c.isdigit() for c in token) < 3:
                continue
            dx = max(0.0, max(lx0 - tb[2], tb[0] - lx1))
            rank = (max(dy, 0.0) + dx, j)
            if best is None or rank < best[0]:
                best = (rank, other, token)
    return (best[1], best[2]) if best is not None else None


_BARE_BILL_HEADER_RE = re.compile(r"\bbill\b", re.IGNORECASE)
_BARE_BILL_HEADER_CONTEXT_RE = re.compile(r"\bpos\b", re.IGNORECASE)
_BARE_BILL_HEADER_DATE_TIME_RE = re.compile(r"\bdate\b|\btime\b", re.IGNORECASE)


def _bill_column_header_candidates(lines: list[OcrLine], currency_codes: tuple[str, ...] = ()) -> list[FieldCandidate]:
    # A POS receipt's own number sometimes sits under a plain table-column header
    # ("Date  Time  Store  POS  Bill") rather than next to a "Bill No:"-style label.
    # label_vocabulary.yaml deliberately has no bare "bill" synonym for invoice_number — it would
    # false-positive on every "Bill To" line — so this looks for the narrow, specific header shape
    # instead: a bare "Bill" word sharing a line with "POS" and a "Date"/"Time" column, a combination
    # only a real table header row has.
    candidates: list[FieldCandidate] = []
    for i, line in enumerate(lines):
        if line.bounding_box is None:
            continue
        if not (
            _BARE_BILL_HEADER_CONTEXT_RE.search(line.text)
            and _BARE_BILL_HEADER_DATE_TIME_RE.search(line.text)
        ):
            continue
        bill_match = _BARE_BILL_HEADER_RE.search(line.text)
        if bill_match is None:
            continue
        box = _span_box(line, bill_match.span())
        if box is None:
            continue
        found = _nearest_id_below(lines, i, box, currency_codes)
        if found is None:
            continue
        other, token = found
        candidates.append(
            FieldCandidate(
                "invoice_number", _fix_letter_zero(token), other.text, other.confidence, other.page,
                other.bounding_box, ["bill_column_header_label", "below_label"], reading_order=other.reading_order,
            )
        )
    return candidates


def _line_label_coverage(text: str, matches: list[LabelMatch]) -> float:
    covered = sum(m.span[1] - m.span[0] for m in matches)
    return covered / max(len(text), 1)


_CODE_LABEL_SHAPE_RE = re.compile(r"^[A-Za-z]{1,3}\s*[:.]\s*\S")


def _is_vendor_eligible_line(text: str, matches: list[LabelMatch]) -> bool:
    if len(text) < 3 or re.fullmatch(r"[\d\s.\-/:]+", text):
        return False
    if matches and _line_label_coverage(text, matches) > 0.4:
        return False  # this line is mostly a recognized label/value line, not a vendor name
    if _TIME_PATTERN.match(text):
        return False  # a clock reading is never a business name, in any language
    if _DOCUMENT_TITLE_RE.match(text):
        return False  # the document's own generic title, not the vendor name
    return True


def _letter_ratio(text: str) -> float:
    stripped = re.sub(r"\s+", "", text)
    if not stripped:
        return 0.0
    letters = sum(1 for c in stripped if c.isalpha())  # unicode-aware -- counts Arabic letters too
    return letters / len(stripped)


def _median_line_height(lines: list[OcrLine]) -> Optional[float]:
    heights = [ln.bounding_box[3] - ln.bounding_box[1] for ln in lines if ln.bounding_box is not None]
    if not heights:
        return None
    heights.sort()
    mid = len(heights) // 2
    return heights[mid] if len(heights) % 2 else (heights[mid - 1] + heights[mid]) / 2.0


def _vendor_shape_signals(text: str, line: OcrLine, median_height: Optional[float]) -> list[str]:
    # Positive/negative signals for "does this look like a business name", entirely generic --
    # shape and typography only, never a specific brand/vendor literal.
    signals = []
    if _CODE_LABEL_SHAPE_RE.match(text):
        signals.append("label_colon_code_shape")  # "S:Standard", "Z:Zero" -- a legend/code fragment, not a name
    if _digit_dominated(text):
        signals.append("digit_dominated_line")
    letter_ratio = _letter_ratio(text)
    word_count = sum(1 for tok in text.split() if sum(c.isalpha() for c in tok) >= 2)
    stripped_len = len(text.strip())
    if letter_ratio >= 0.6 and word_count >= 1 and stripped_len >= 4 and not signals:
        signals.append("business_name_shape")
        # A single short word is as likely a logo fragment/watermark as a real name; a real
        # business name is almost always multiple words or a genuinely long single one.
        if word_count >= 2 and stripped_len >= 10:
            signals.append("multi_word_name_shape")
    if median_height and line.bounding_box is not None:
        height = line.bounding_box[3] - line.bounding_box[1]
        if height >= median_height * 1.3:
            signals.append("larger_than_median_line_height")
    return signals


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
    text_lower = text.lower()
    best_ratio = max(
        (difflib.SequenceMatcher(None, text_lower, v.lower()).ratio() for v in reference_data.known_vendors),
        default=0.0,
    )
    if best_ratio >= 0.85:
        return 0.25, ["known_vendor_match"]
    # A known vendor name as its own word/prefix inside a longer line ("UberX Saver reserve" ->
    # "Uber") -- common on app-receipt screenshots where the brand is embedded in a longer status
    # line rather than printed alone. Require 4+ letters so short names (e.g. "GO") can't false-hit
    # on unrelated words.
    for vendor in reference_data.known_vendors:
        vendor_lower = vendor.lower()
        if len(vendor_lower) >= 4 and re.search(rf"\b{re.escape(vendor_lower)}", text_lower):
            return 0.2, ["known_vendor_substring_match"]
    return 0.0, []


def _vendor_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], reference_data: ReferenceData
) -> list[FieldCandidate]:
    candidates = []
    # A generous window -- real headers on noisy real-world photos can sit a few lines past
    # index 0. Position and shape signals (scoring.py) do the actual ranking work now, not
    # this window size, so widening it is low-risk.
    top_n = min(8, len(lines))
    eligible = [
        _is_vendor_eligible_line(lines[i].text.strip(), label_matches_by_line[i]) for i in range(top_n)
    ]
    median_height = _median_line_height(lines)

    for i in range(top_n):
        if not eligible[i]:
            continue
        line = lines[i]
        text = line.text.strip()
        signals = ["top_of_receipt"] + _vendor_shape_signals(text, line, median_height)
        confidence = max(0.1, line.confidence * (1.0 - i * 0.12))
        bonus, bonus_signals = _vendor_known_match_bonus(text, reference_data)
        confidence = min(1.0, confidence + bonus)
        signals += bonus_signals
        candidates.append(
            FieldCandidate(
                "vendor", text, line.text, confidence, line.page, line.bounding_box, signals,
                reading_order=line.reading_order, ocr_confidence=line.confidence,
            )
        )

    # A known vendor's name can appear embedded in a longer status line well past the header
    # window (e.g. a ride-hailing app receipt screenshot: "UberX Saver reserve" sits mid-page,
    # not in the header). This is a narrow, bounded extra pass -- only lines with an actual
    # known-vendor substring hit are considered, so it can't surface generic noise the way
    # widening the whole window would on other receipt shapes.
    for i in range(top_n, len(lines)):
        text = lines[i].text.strip()
        if not _is_vendor_eligible_line(text, label_matches_by_line[i]):
            continue
        bonus, bonus_signals = _vendor_known_match_bonus(text, reference_data)
        if "known_vendor_substring_match" not in bonus_signals:
            continue
        line = lines[i]
        candidates.append(
            FieldCandidate(
                "vendor", text, line.text, min(1.0, 0.3 + bonus), line.page, line.bounding_box,
                _vendor_shape_signals(text, line, median_height) + bonus_signals,
                reading_order=line.reading_order, ocr_confidence=line.confidence,
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
        # A short fragment (garbled OCR noise, a document-type header like "Tax Invoice"
        # mangled beyond label-matching) shouldn't anchor a merge and drag a real name into
        # it -- it can still stand as its own low-scored candidate, just not glue onto one.
        if not eligible[i] or i in continuations or len(lines[i].text.strip()) < 8:
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
                shape_signals = _vendor_shape_signals(merged_text, lines[i], median_height)
                candidates.append(
                    FieldCandidate(
                        "vendor", merged_text, merged_text, confidence, lines[i].page, merged_bbox,
                        ["top_of_receipt", "multiline_header_merge"] + shape_signals + bonus_signals,
                        reading_order=lines[i].reading_order, ocr_confidence=lines[i].confidence,
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


_VAT_CUE_CONCEPTS = (LabelConcept.VAT_TAX_AMOUNT, LabelConcept.VAT_TAX_RATE)
_MAX_SUMMARY_TRIPLES = 3


def _vat_breakdown_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], reference_data: ReferenceData
) -> list[FieldCandidate]:
    # A tax summary row ("5%  45.21  2.28  47.49") is identified by accounting arithmetic, not by
    # labels or column geometry (both are routinely garbled/fragmented by OCR): amount + vat == total
    # and vat ~= rate * amount for a plausible nonzero rate. Needs 2 of the 3 numbers to read cleanly --
    # the third is derived (a garbled "4u.84" amount is recovered as total - vat) -- and a rate cue
    # on the row (a printed "5%" or a VAT label) so unrelated number pairs can't match by chance.
    rates = [r for r in reference_data.plausible_vat_rates if r > 0]
    if not rates:
        return []
    candidates: list[FieldCandidate] = []
    triples: dict[tuple[float, float, float], Optional[float]] = {}
    seen_groups: set[frozenset[int]] = set()
    for i, line in enumerate(lines):
        group = [i]
        if line.bounding_box is not None:
            group += [
                j for j, other in enumerate(lines)
                if j != i and other.bounding_box is not None and _same_row(line.bounding_box, other.bounding_box)
            ]
        key = frozenset(group)
        if key in seen_groups:
            continue
        seen_groups.add(key)

        decimals: dict[float, OcrLine] = {}
        percent_cue = False
        for j in group:
            member = lines[j]
            date_spans = _date_span_ranges(member.text)
            for t in _iter_numeric_tokens(member.text, reference_data.valid_currency_codes):
                if _overlaps_any(t.start, t.end, date_spans):
                    continue
                if t.near_percent and not t.has_decimal and t.value in rates:
                    percent_cue = True
                elif t.has_decimal and t.value > 0 and not _looks_like_phone_or_id(t.value):
                    decimals.setdefault(round(t.value, 2), member)
        if len(decimals) < 2 or len(decimals) > 6:
            continue

        label_cue = False
        for j in group:
            label_cue = label_cue or any(m.concept in _VAT_CUE_CONCEPTS for m in label_matches_by_line[j])
        if not label_cue:
            if line.bounding_box is not None:
                above = _nearest_aligned_line_above(lines, i)
            else:
                above = i - 1 if i > 0 and lines[i - 1].bounding_box is None else None
            if above is not None:
                label_cue = any(m.concept in _VAT_CUE_CONCEPTS for m in label_matches_by_line[above])
        if not (percent_cue or label_cue):
            continue

        values = sorted(decimals)
        solutions: dict[tuple[float, float, float], float] = {}
        for x_idx, x in enumerate(values):
            for y in values[x_idx + 1:]:
                diff = round(y - x, 2)
                if diff <= 0:
                    continue
                # (vat, amount, total) readings: x is the VAT (amount derived) or x is the amount (VAT derived).
                for vat, amount in ((x, diff), (diff, x)):
                    for rate in rates:
                        if abs(vat - amount * rate / 100.0) <= max(0.03, 0.0012 * amount):
                            solutions[(round(amount, 2), round(vat, 2), round(y, 2))] = rate
        # Also a fully-read triple whose total sits among the numbers is already covered by the pair
        # search; ambiguity (several different readings) means no safe call, so emit nothing.
        if len(solutions) > 1:
            # A reading whose three numbers were all actually printed beats ones needing a derived value.
            fully_printed = {k: r for k, r in solutions.items() if all(round(v, 2) in decimals for v in k)}
            solutions = fully_printed
        if len(solutions) != 1:
            continue
        (amount, vat, total), rate = next(iter(solutions.items()))
        src = max(group, key=lambda j: sum(1 for _ in _iter_numeric_tokens(lines[j].text)))
        src_line = lines[src]
        triples[(amount, vat, total)] = src_line.bounding_box[1] if src_line.bounding_box else None
        for field_name, value in (("amount", amount), ("vat_amount", vat), ("total_amount", total)):
            printed = round(value, 2) in decimals
            candidates.append(
                FieldCandidate(
                    field_name=field_name,
                    value=value,
                    source_text=src_line.text,
                    confidence=src_line.confidence,
                    page=src_line.page,
                    bounding_box=src_line.bounding_box,
                    signals=["vat_breakdown_arithmetic", "currency_value"]
                    + ([] if printed else ["derived_from_breakdown"]),
                    reading_order=src_line.reading_order,
                    ocr_confidence=src_line.confidence,
                )
            )
    # Every row of an itemised invoice table (taxable | VAT% | VAT | total) reconciles on its own, so
    # three or more distinct reconciling rows means an item table, not a tax summary. Picking one row
    # (the lowest) would report a single item as the whole invoice; the table's own sum is the invoice
    # figure instead. Two rows are still allowed: stacked receipts on one image (tie-broken in select.py).
    # But when the bill also prints its own summary row, that row is the invoice figure and nothing is
    # summed twice. It is the largest total, at least the sum of the other rows, and sits below all of them
    # (item row 1 can out-total the rest of the table by coincidence, but it is the topmost row).
    if len(triples) < _MAX_SUMMARY_TRIPLES:
        return candidates
    top = max(triples, key=lambda t: t[2])
    others = [t for t in triples if t != top]
    below_all = triples[top] is not None and all(
        triples[t] is not None and triples[top] > triples[t] for t in others
    )
    has_summary_row = top[2] >= sum(t[2] for t in others) - 0.05 and below_all
    if not has_summary_row:
        anchor = candidates[0]
        sums = (
            ("amount", sum(t[0] for t in triples)),
            ("vat_amount", sum(t[1] for t in triples)),
            ("total_amount", sum(t[2] for t in triples)),
        )
        return [
            FieldCandidate(
                field_name=name,
                value=round(value, 2),
                source_text=anchor.source_text,
                confidence=anchor.confidence,
                page=anchor.page,
                bounding_box=anchor.bounding_box,
                signals=["vat_breakdown_arithmetic", "currency_value", "derived_from_breakdown", "item_table_sum"],
                reading_order=anchor.reading_order,
                ocr_confidence=anchor.ocr_confidence,
            )
            for name, value in sums
        ]
    return candidates


_TOTAL_LABEL_CONCEPTS = (LabelConcept.TOTAL, LabelConcept.SUBTOTAL)


def _plain_numbers(line: OcrLine, reference_data: ReferenceData) -> list[float]:
    spans = _date_span_ranges(line.text)
    return [
        t.value for t in _iter_numeric_tokens(line.text, reference_data.valid_currency_codes)
        if t.value > 0 and not _overlaps_any(t.start, t.end, spans)
    ]


def _stacked_totals_candidates(
    lines: list[OcrLine], label_matches_by_line: list[list[LabelMatch]], reference_data: ReferenceData
) -> list[FieldCandidate]:
    # A totals block printed one figure per line -- "Total 330" / "VAT 5% 16.50" / "Grand Total 346.50" --
    # is the same accounting identity as a one-row tax summary, but hand-filled forms lose decimals and
    # garble digits ("330", "16 so", "bE 6"), so the printed numbers can't be trusted individually. The
    # subtotal above a "VAT r%" line plus that printed rate pins the block down: vat = subtotal * r and
    # grand total = subtotal + vat. Needs the VAT line's own garbled reading (or the grand total) to
    # agree with the derived value, so an unrelated "Total" + "VAT 5%" pair can't invent numbers.
    rates = [r for r in reference_data.plausible_vat_rates if r > 0]
    if not rates:
        return []
    out: list[FieldCandidate] = []
    for v, vline in enumerate(lines):
        if not any(m.concept in _VAT_CUE_CONCEPTS for m in label_matches_by_line[v]):
            continue
        vat_tokens = [
            t for t in _iter_numeric_tokens(vline.text, reference_data.valid_currency_codes)
        ]
        rate = next((t.value for t in vat_tokens if t.near_percent and not t.has_decimal and t.value in rates), None)
        if rate is None:
            continue
        if vline.bounding_box is not None:
            row = [vline] + [
                o for j, o in enumerate(lines)
                if j != v and o.bounding_box is not None and _same_row(vline.bounding_box, o.bounding_box)
            ]
            above = _nearest_aligned_line_above(lines, v)
            below = _nearest_aligned_line_below(lines, v, min_gap=(vline.bounding_box[3] - vline.bounding_box[1]) * 0.6)
        else:
            row = [vline]
            above = v - 1 if v > 0 and lines[v - 1].bounding_box is None else None
            below = v + 1 if v + 1 < len(lines) and lines[v + 1].bounding_box is None else None
        if above is None or not any(m.concept in _TOTAL_LABEL_CONCEPTS for m in label_matches_by_line[above]):
            continue
        subtotal_numbers = _plain_numbers(lines[above], reference_data)
        if not subtotal_numbers:
            continue
        subtotal = subtotal_numbers[0]

        vat_read = [
            t.value for line in row for t in _iter_numeric_tokens(line.text, reference_data.valid_currency_codes)
            if not (t.near_percent and not t.has_decimal and t.value in rates) and t.value > 0
        ]
        total_read = (
            _plain_numbers(lines[below], reference_data)
            if below is not None and any(m.concept == LabelConcept.TOTAL for m in label_matches_by_line[below])
            else []
        )
        vat = round(subtotal * rate / 100.0, 2)
        total = round(subtotal + vat, 2)
        # Decimals are routinely dropped from hand-filled figures ("16" for 16.50), so agreement is within 1.
        corroborated = any(abs(x - vat) <= 1.0 for x in vat_read) or any(abs(x - total) <= 1.0 for x in total_read)
        if not corroborated:
            continue
        src = vline
        for field_name, value in (("amount", subtotal), ("vat_amount", vat), ("total_amount", total)):
            out.append(
                FieldCandidate(
                    field_name=field_name, value=value, source_text=src.text, confidence=src.confidence,
                    page=src.page, bounding_box=src.bounding_box,
                    signals=["vat_breakdown_arithmetic", "derived_from_breakdown", "stacked_totals_block", "currency_value"],
                    reading_order=src.reading_order, ocr_confidence=src.confidence,
                )
            )
    return out


def generate_candidates(lines: list[OcrLine], reference_data: ReferenceData) -> list[FieldCandidate]:
    label_matches_by_line = [
        match_label_concepts(ln.text, reference_data.label_vocabulary, reference_data.label_exclusions)
        for ln in lines
    ]
    candidates: list[FieldCandidate] = []
    candidates += _money_field_candidates(lines, label_matches_by_line, reference_data)
    candidates += _vat_breakdown_candidates(lines, label_matches_by_line, reference_data)
    candidates += _stacked_totals_candidates(lines, label_matches_by_line, reference_data)
    candidates += _vat_rate_candidates(lines, label_matches_by_line, reference_data)
    candidates += _currency_candidates(lines, reference_data)
    candidates += _date_candidates(lines, label_matches_by_line)
    candidates += _id_candidates(lines, label_matches_by_line, reference_data.valid_currency_codes)
    candidates += _bill_column_header_candidates(lines, reference_data.valid_currency_codes)
    candidates += _vendor_candidates(lines, label_matches_by_line, reference_data)
    candidates += _category_candidates(lines, reference_data)
    return candidates
