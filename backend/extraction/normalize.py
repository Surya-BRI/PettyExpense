"""Stage 2: generic normalization — whitespace, punctuation, common OCR digit
errors, currency symbols, decimal formats. Nothing here is vendor/layout
specific; every transform applies uniformly to any receipt in any language.
"""
import re
import unicodedata
from typing import Optional

from extraction.types import OcrLine, OcrWord

_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩" "۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)

# Single-character currency symbols are unambiguous and safe to normalize
# in free text. Multi-character abbreviations (SR, AED, SAR, ...) are
# ambiguous with ordinary words, so they're only matched as whole tokens by
# the candidate generator, not blindly substituted here.
CURRENCY_SYMBOL_MAP: dict[str, str] = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "₹": "INR",
    "﷼": "SAR",
    "SR": "SAR",
    "AED": "AED",
    "SAR": "SAR",
    "USD": "USD",
    "EUR": "EUR",
    "GBP": "GBP",
    "INR": "INR",
    "QAR": "QAR",
    "KWD": "KWD",
    "OMR": "OMR",
    "BHD": "BHD",
    "EGP": "EGP",
    "د.إ": "AED",
    "ر.س": "SAR",
}

_SINGLE_CHAR_CURRENCY_RE = re.compile("|".join(re.escape(sym) for sym in "$€£₹﷼"))

# Multi-character abbreviations that are unambiguous once whitespace-delimited
# (unlike bare "SR"/"AED" glued to a following digit, which is left alone —
# candidate generation still finds the ISO code text itself in that case).
_MULTI_CHAR_CURRENCY_MAP = {"SR": "SAR", "ر.س": "SAR", "د.إ": "AED"}
_MULTI_CHAR_CURRENCY_RE = re.compile(
    "|".join(r"(?<!\S)" + re.escape(k) + r"(?!\S)" for k in _MULTI_CHAR_CURRENCY_MAP)
)

# OCR digit/letter confusions — only ever applied to a token already believed
# to be numeric (see repair_numeric_ocr_errors), never to arbitrary text.
_DIGIT_CONFUSION = {
    "O": "0", "o": "0", "D": "0", "Q": "0",
    "l": "1", "I": "1", "i": "1",
    "Z": "2", "z": "2",
    "S": "5", "s": "5",
    "G": "6", "b": "6",
    "T": "7",
    "B": "8",
    "g": "9", "q": "9",
}


def normalize_text(s: str) -> str:
    if not s:
        return s
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_DIGIT_TRANSLATION)
    s = _normalize_percent_signs(s)
    # A '0' misread as the letter 'O'/'o' is a common thermal-print OCR
    # confusion, especially right after a currency code in a decimal amount
    # ("AED0.29" read as "AEDO.29"). Repaired only where an O sits between a
    # letter and a decimal point followed by digits — a position no real word
    # occupies — never a blanket O->0 swap that could corrupt actual text.
    s = re.sub(r"(?<=[A-Za-z])[Oo](?=\.\s*\d)", "0", s)
    # OCR sometimes inserts a stray space around the decimal point itself
    # ("0. 29" instead of "0.29") — collapse it generically wherever a short
    # (1-2 digit) trailing group follows a lone decimal point.
    s = re.sub(r"(\d)\.\s+(\d{1,2})(?!\d)", r"\1.\2", s)
    s = _SINGLE_CHAR_CURRENCY_RE.sub(lambda m: f" {CURRENCY_SYMBOL_MAP[m.group(0)]} ", s)
    s = _MULTI_CHAR_CURRENCY_RE.sub(lambda m: f" {_MULTI_CHAR_CURRENCY_MAP[m.group(0)]} ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"([.\-:|])\1{1,}", r"\1", s)
    s = re.sub(r"\s*[\-:|]\s*$", "", s).strip()
    return s


def _normalize_percent_signs(s: str) -> str:
    # Arabic percent sign, and a "°" glued to a 1-2 digit number (a common OCR
    # misread of "%"), both become a canonical "%".
    s = s.replace("٪", "%")
    s = re.sub(r"(?<=\d)\s*°(?=\s|$|[^\d])", "%", s)
    return s


def repair_numeric_ocr_errors(token: str) -> Optional[str]:
    """Bounded (<=1 substitution) digit-confusion repair for a token that
    otherwise fails to parse as a number, e.g. 'l5.00' -> '15.00'."""
    if not token or re.fullmatch(r"[\d.,]+", token):
        return token
    repaired = []
    substitutions = 0
    for ch in token:
        if ch.isdigit() or ch in ".,":
            repaired.append(ch)
        elif ch in _DIGIT_CONFUSION:
            repaired.append(_DIGIT_CONFUSION[ch])
            substitutions += 1
        else:
            return None
    if substitutions > 1:
        return None
    return "".join(repaired)


def parse_amount(token: str) -> Optional[float]:
    """Parses a numeric token that may use either '.' or ',' as the decimal
    marker and/or thousands grouping, without assuming a fixed locale: the
    last separator followed by exactly 1-2 digits is treated as the decimal
    point; a last separator followed by 3+ digits is treated as a thousands
    grouping (no fractional part)."""
    if token is None:
        return None
    cleaned = re.sub(r"[^\d,.\s]", "", token).replace(" ", "")
    if not cleaned:
        repaired = repair_numeric_ocr_errors(token.strip())
        if repaired is None:
            return None
        cleaned = re.sub(r"[^\d,.\s]", "", repaired).replace(" ", "")
        if not cleaned:
            return None
    seps = [i for i, c in enumerate(cleaned) if c in ",."]
    if not seps:
        try:
            return float(cleaned)
        except ValueError:
            return None
    last_sep = seps[-1]
    tail = cleaned[last_sep + 1 :]
    head = cleaned[:last_sep]
    try:
        if len(tail) in (1, 2):
            integer_part = re.sub(r"[,.]", "", head) or "0"
            return float(f"{integer_part}.{tail}")
        digits = re.sub(r"[,.]", "", cleaned)
        return float(digits) if digits else None
    except ValueError:
        return None


def normalize_word(word: OcrWord) -> OcrWord:
    return OcrWord(
        text=normalize_text(word.text),
        confidence=word.confidence,
        lang=word.lang,
        bounding_box=word.bounding_box,
        page=word.page,
        reading_order=word.reading_order,
        source_pass=word.source_pass,
    )


def _y_center(bbox) -> float:
    return (bbox[1] + bbox[3]) / 2.0


def _height(bbox) -> float:
    return max(bbox[3] - bbox[1], 1e-6)


_MAX_LINE_GAP_HEIGHT_RATIO = 4.0


def _split_by_horizontal_gap(band: list[OcrWord], median_height: float) -> list[list[OcrWord]]:
    boxed = sorted((w for w in band if w.bounding_box is not None), key=lambda w: w.bounding_box[0])
    unboxed = [w for w in band if w.bounding_box is None]
    if not boxed:
        return [band] if band else []
    gap_threshold = max(_MAX_LINE_GAP_HEIGHT_RATIO * median_height, 1e-6)
    groups = [[boxed[0]]]
    for prev, curr in zip(boxed, boxed[1:]):
        gap = curr.bounding_box[0] - prev.bounding_box[2]
        if gap > gap_threshold:
            groups.append([curr])
        else:
            groups[-1].append(curr)
    if unboxed:
        groups[0] = groups[0] + unboxed
    return groups


def _word_bbox_iou(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


_WORD_DEDUP_IOU = 0.4
_WORD_DEDUP_CONFIDENCE_MARGIN = 0.1


def _better_of_overlapping_words(a: OcrWord, b: OcrWord) -> OcrWord:
    """Confidence is the primary signal — a low-confidence 'longer' reading is
    usually just noise (garbled glyphs, stray punctuation), not a more
    complete one. Only when both readings are close in confidence does the
    longer text win, since a *confident* partial misread that drops a leading
    glyph is a real, common failure mode pure confidence wouldn't catch."""
    if abs(a.confidence - b.confidence) < _WORD_DEDUP_CONFIDENCE_MARGIN:
        return a if len(a.text) >= len(b.text) else b
    return a if a.confidence >= b.confidence else b


def _dedup_overlapping_words(words: list[OcrWord]) -> list[OcrWord]:
    """Separate EN/AR OCR passes often both detect the same glyph region
    (a logo, a stylized header) with different bounding boxes and different
    text — without this, both readings survive into the same line's text
    (e.g. one pass drops a leading glyph the other pass caught, producing a
    line with both the full and the truncated reading glued together)."""
    boxed = [w for w in words if w.bounding_box is not None]
    unboxed = [w for w in words if w.bounding_box is None]
    used = [False] * len(boxed)
    kept: list[OcrWord] = []
    for i, w in enumerate(boxed):
        if used[i]:
            continue
        used[i] = True
        best = w
        for j in range(i + 1, len(boxed)):
            if used[j]:
                continue
            other = boxed[j]
            if _word_bbox_iou(best.bounding_box, other.bounding_box) >= _WORD_DEDUP_IOU:
                used[j] = True
                best = _better_of_overlapping_words(best, other)
        kept.append(best)
    return kept + unboxed


def group_into_lines(words: list[OcrWord]) -> list[OcrLine]:
    """Groups words into lines using bounding-box vertical proximity. When no
    word carries geometry (today's PaddleOCR wrapper output, or text-only
    input), each word is already a full OCR-emitted line, so it degrades to a
    1:1 wrap — no line-grouping heuristic is needed or safe to guess at."""
    if not words:
        return []

    normalized = [normalize_word(w) for w in words]
    has_any_bbox = any(w.bounding_box is not None for w in normalized)
    if not has_any_bbox:
        return [
            OcrLine(
                text=w.text,
                words=(w,),
                confidence=w.confidence,
                bounding_box=None,
                page=w.page,
                reading_order=w.reading_order,
            )
            for w in normalized
        ]

    heights = [_height(w.bounding_box) for w in normalized if w.bounding_box is not None]
    heights.sort()
    median_height = heights[len(heights) // 2]
    threshold = 0.5 * median_height

    ordered = sorted(normalized, key=lambda w: w.reading_order)
    used = [False] * len(ordered)
    y_bands: list[list[OcrWord]] = []
    for i, w in enumerate(ordered):
        if used[i]:
            continue
        band = [w]
        used[i] = True
        if w.bounding_box is not None:
            wy = _y_center(w.bounding_box)
            for j in range(i + 1, len(ordered)):
                if used[j]:
                    continue
                other = ordered[j]
                if other.bounding_box is None:
                    continue
                if abs(_y_center(other.bounding_box) - wy) <= threshold:
                    band.append(other)
                    used[j] = True
        y_bands.append(band)

    # A PaddleOCR "word" is typically already a full detected text region (a
    # label, a table cell, a short phrase) — several unrelated regions can sit
    # in the same y-band on a wide page (a multi-column table row, or two
    # receipts scanned side by side). Sharing a row isn't enough evidence they
    # belong to the same line; also require them not to be separated by a gap
    # far larger than normal word-spacing, or split them into distinct lines.
    groups: list[list[OcrWord]] = []
    for band in y_bands:
        groups.extend(_split_by_horizontal_gap(band, median_height))

    lines = []
    for group in groups:
        group = _dedup_overlapping_words(group)
        group_sorted = sorted(group, key=lambda w: (w.bounding_box[0] if w.bounding_box else 0.0))
        text = " ".join(w.text for w in group_sorted if w.text)
        boxes = [w.bounding_box for w in group_sorted if w.bounding_box is not None]
        bbox = (
            (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
            if boxes
            else None
        )
        confidence = min((w.confidence for w in group_sorted), default=0.0)
        lines.append(
            OcrLine(
                text=text,
                words=tuple(group_sorted),
                confidence=confidence,
                bounding_box=bbox,
                page=group_sorted[0].page,
                reading_order=min(w.reading_order for w in group_sorted),
            )
        )
    lines.sort(key=lambda l: l.reading_order)
    return lines


def words_from_text(text: str) -> list[OcrWord]:
    """Builds geometry-less, uniform-confidence OcrWords from a plain text
    blob (one word per newline) — used when the caller has raw OCR text but
    no per-line confidence/geometry at all."""
    words = []
    for i, raw_line in enumerate(text.splitlines()):
        stripped = raw_line.strip()
        if not stripped:
            continue
        words.append(OcrWord(text=stripped, confidence=1.0, lang="en", bounding_box=None, page=1, reading_order=i))
    return words


def lines_from_text(text: str) -> list[OcrLine]:
    """Builds geometry-less OcrLines from a plain text blob (one line per
    newline) — used by OcrService.extract_from_text for callers that only
    have raw OCR text, not word/box geometry."""
    return group_into_lines(words_from_text(text))
