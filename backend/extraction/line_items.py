"""Bill line-item extraction: turns the OCR lines of an itemised bill into
{description, quantity, amount} rows for the "Multiple items" claim flow.

Works on the same OcrLines the field pipeline uses. Generic, layout-based rules
only -- no vendor-specific matching:

0. group_into_lines() (shared with the single-field pipeline) splits a wide table
   row into several OcrLines whenever a column gap exceeds its page-wide threshold
   -- correct for unrelated side-by-side blocks, wrong inside an item table. Those
   fragments are chained back into one row by y-proximity first (_merge_row_fragments),
   rebuilding each row's text by re-sorting all of its words by x.
1. The item table starts after a header row ("Qty", "Description", "Item", ...)
   and ends at the first totals row ("Total", "Net Total", "Bill Amount", "VAT", ...).
2. Inside it, each row's money values are its decimal numbers; the LAST one is the
   line amount, and with two or more the FIRST is the quantity. Long digit runs
   (barcodes, item codes) are ignored.
3. OCR often splits one printed row into a numbers line and a name line a few
   pixels apart (or reads "0.00" as "0 00"); those are rejoined by vertical
   proximity before reading the row.

The output is a suggestion: the employee always reviews, edits, adds or deletes
lines before submitting.
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import Optional

from extraction.labels import LabelConcept, match_label_concepts
from extraction.reference_data import ReferenceData
from extraction.types import OcrLine

MAX_LINES = 60

# Concepts that end the item table.
_END_CONCEPTS = {
    LabelConcept.TOTAL,
    LabelConcept.SUBTOTAL,
    LabelConcept.VAT_TAX_AMOUNT,
    LabelConcept.DISCOUNT,
    LabelConcept.SERVICE_CHARGE,
    LabelConcept.CASH,
    LabelConcept.CARD,
    LabelConcept.CHANGE,
    LabelConcept.TENDERED,
}

# Words that mark the item table header even when the vocabulary's item_table_header misses them.
_HEADER_WORDS = re.compile(
    r"\b(qty|quantity|description|item|items|particulars|product|prod|rate|unit\s*price|price)\b", re.IGNORECASE
)
# A row that is really the table's own summary ("Qty: 5.59", "Items: 6") ends the table too.
_SUMMARY_ROW = re.compile(r"^\W*(q[tl]y|items?|no\.?\s*of\s*items?)\s*[:=]", re.IGNORECASE)
# Totals rows the vocabulary deliberately doesn't map to TOTAL ("Total Qty") or that OCR garbled
# ("B111 Amount" for "Bill Amount"): item names on a bill practically never contain these words.
# "vat" is included directly because the concept matcher misses a bare percentage-suffixed
# reading like "VAT 5%" (vs. a standalone "VAT" line, which it does catch).
_END_WORDS = re.compile(r"\b(total|subtotal|grand|amount|balance|payable|rounding|vat)\b", re.IGNORECASE)

# OCR reads "0.00" / "38.00" as "0 00" / "38 00": rejoin a 1-4 digit group followed by two or three digits
# (some Gulf invoices print 3-decimal fils/baisa amounts, e.g. "480.000").
_SPLIT_DECIMAL = re.compile(r"(?<![\d.,])(\d{1,4})\s(\d{2,3})(?![\d.,%])")
# Money values: 2- or 3-decimal numbers that are not glued to letters ("1.25CMX5M" is a size, not a price).
_DECIMAL = re.compile(r"(?<![\d.,A-Za-z])\d{1,6}[.,]\d{2,3}(?![\dA-Za-z])")
# OCR sometimes drops the last digit of the row's final amount ("14.3"); accepted only as the last token.
_TRAILING_ONE_DECIMAL = re.compile(r"(?<![\d.,A-Za-z])(\d{1,6}[.,]\d)\s*$")
_INTEGER = re.compile(r"(?<![\d.,])\d+(?![\d.,])")
_LETTERS = re.compile(r"[A-Za-z؀-ۿ]")


@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: Optional[float]
    amount: Optional[float]
    confidence: float

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "amount": self.amount,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class _Row:
    y: float
    text: str
    decimals: list[float]
    description: str
    confidence: float
    used: bool = False

    @property
    def has_numbers(self) -> bool:
        return bool(self.decimals)

    @property
    def has_text(self) -> bool:
        return bool(self.description)


def _y(line: OcrLine, fallback: float) -> float:
    return float(line.bounding_box[1]) if line.bounding_box else fallback


def _height(line: OcrLine) -> Optional[float]:
    if not line.bounding_box:
        return None
    return float(line.bounding_box[3] - line.bounding_box[1])


def _concepts(text: str, reference_data: ReferenceData) -> set[LabelConcept]:
    return {m.concept for m in match_label_concepts(text, reference_data.label_vocabulary, reference_data.label_exclusions)}


def _is_header(text: str, reference_data: ReferenceData) -> bool:
    if LabelConcept.ITEM_TABLE_HEADER in _concepts(text, reference_data):
        return True
    # Header rows are words, not values: at least one header word and no money amounts.
    return bool(_HEADER_WORDS.search(text)) and not _DECIMAL.search(_SPLIT_DECIMAL.sub(r"\1.\2", text))


def _is_end(text: str, reference_data: ReferenceData) -> bool:
    if _SUMMARY_ROW.search(text) or _END_WORDS.search(text):
        return True
    return bool(_concepts(text, reference_data) & _END_CONCEPTS)


def _parse_row(line: OcrLine, y: float) -> _Row:
    text = _SPLIT_DECIMAL.sub(r"\1.\2", line.text)
    decimals = [float(m.group(0).replace(",", ".")) for m in _DECIMAL.finditer(text)]
    trailing = _TRAILING_ONE_DECIMAL.search(text)
    if trailing:
        decimals.append(float(trailing.group(1).replace(",", ".")))
    # Description: the words that carry letters, up to the first money value.
    money_positions = [m.start() for m in _DECIMAL.finditer(text)] + ([trailing.start(1)] if trailing else [])
    first_money_at = min(money_positions) if money_positions else None
    head = text[:first_money_at] if first_money_at is not None else text
    words = []
    for token in head.split():
        if _LETTERS.search(token):
            words.append(token)
        elif _INTEGER.fullmatch(token) and len(token) >= 4:
            continue  # item codes / barcodes
        elif words:
            words.append(token)  # e.g. "6 INCH", "50G" pieces that belong to the name
    description = " ".join(words).strip(" -:|")
    # A trailing run of codes after the name (e.g. "... 55507116 9999") is not part of it.
    description = re.sub(r"(\s+\d{4,})+$", "", description).strip()
    # OCR noise like "0 oo" or "Le pi" is not a product name: require a few real letters.
    if len(_LETTERS.findall(description)) < 3:
        description = ""
    return _Row(y=y, text=text, decimals=decimals, description=description, confidence=line.confidence)


def _x0(bbox: Optional[tuple[float, float, float, float]]) -> float:
    return bbox[0] if bbox else 0.0


def _merge_row_fragments(lines: list[OcrLine], threshold: float) -> list[OcrLine]:
    """Chains lines back into one row whenever a line sits close enough vertically to the
    row being built (within about one row-height) AND starts to the right of everything
    read into that row so far -- the left-to-right column order one printed row reads in.
    A line that restarts near the left margin never merges by this rule, whether it's
    really the next row or a wrapped second line of the row above's description -- the
    pair-rejoin step below (matching by nearest-y, not reading order) already handles
    gluing those back to a row, and blindly chaining on y-gap alone would instead bridge
    two unrelated complete rows together through that left-restarting line in between."""
    if not lines:
        return []
    ordered = sorted(enumerate(lines), key=lambda p: (_y(p[1], p[0]), p[0]))

    bands: list[list[OcrLine]] = []
    prev_y: Optional[float] = None
    band_right: Optional[float] = None
    for idx, ln in ordered:
        if ln.bounding_box is None:
            # No geometry to merge on (e.g. a geometry-less plain-text OCR source) -- each
            # line already represents one full printed row; leave it untouched rather than
            # falling back to a shared coordinate that would make every such line collide.
            bands.append([ln])
            prev_y = None
            band_right = None
            continue
        y = ln.bounding_box[1]
        x0 = ln.bounding_box[0]
        x1 = ln.bounding_box[2]
        if prev_y is not None and y - prev_y <= threshold and band_right is not None and x0 >= band_right:
            bands[-1].append(ln)
            band_right = max(band_right, x1)
        else:
            bands.append([ln])
            band_right = x1
        prev_y = y

    merged: list[OcrLine] = []
    for band in bands:
        if len(band) == 1:
            merged.append(band[0])
            continue
        words = sorted((w for ln in band for w in ln.words), key=lambda w: _x0(w.bounding_box))
        text = " ".join(w.text for w in words if w.text)
        boxes = [ln.bounding_box for ln in band if ln.bounding_box]
        bbox = (
            (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
            if boxes
            else None
        )
        merged.append(
            OcrLine(
                text=text,
                words=tuple(words),
                confidence=min(ln.confidence for ln in band),
                bounding_box=bbox,
                page=band[0].page,
                reading_order=min(ln.reading_order for ln in band),
            )
        )
    return merged


def _amount_and_qty(decimals: list[float]) -> tuple[Optional[float], Optional[float]]:
    if not decimals:
        return None, None
    amount: Optional[float] = decimals[-1]
    qty: Optional[float] = decimals[0] if len(decimals) >= 2 else None
    if qty is not None and not (0 < qty <= 1000):
        qty = None
    # "2.00 0.00" with the real amount cut off the photo: a 0 last value next to other
    # numbers is the VAT/discount column, not a line total -- leave the amount for the user.
    if amount == 0 and len(decimals) >= 2:
        amount = None
    return amount, qty


def extract_line_items(lines: list[OcrLine], reference_data: ReferenceData) -> list[LineItem]:
    if not lines:
        return []
    ordered = sorted(enumerate(lines), key=lambda p: (_y(p[1], p[0]), p[0]))
    ys = [_y(ln, i) for i, ln in ordered]
    heights = [h for h in (_height(ln) for _, ln in ordered) if h and h > 0]
    line_h = statistics.median(heights) if heights else 12.0
    # Name and numbers of one printed row land within about one line height of each other.
    pair_gap = max(line_h * 1.1, 6.0)

    # 1. Find the table: after the last header row of the first header cluster, before the first end row.
    #    Header/end detection runs on the UNMERGED lines so a header's own text fragments can't
    #    accidentally chain-merge with unrelated page content above the table.
    start = None
    for idx, (_, ln) in enumerate(ordered):
        if _is_header(ln.text, reference_data):
            start = idx
            # Header rows can wrap onto several OCR lines ("Qty Amount" / "Description").
            while start + 1 < len(ordered) and ys[start + 1] - ys[idx] <= line_h * 2.5 and _is_header(ordered[start + 1][1].text, reference_data):
                start += 1
            break
    if start is None:
        return []

    body_lines: list[OcrLine] = []
    seen_item = False
    for idx in range(start + 1, len(ordered)):
        _, ln = ordered[idx]
        # A wrapped multi-row header often has its own stray "VAT"/"Total" column label
        # (e.g. "Incl.VAT(AED) Total"), which otherwise reads as an end-of-table marker
        # before any item has actually been seen -- an end marker can't appear before item 1.
        if _is_end(ln.text, reference_data) and seen_item:
            break
        body_lines.append(ln)
        if not seen_item and _parse_row(ln, ys[idx]).has_numbers:
            seen_item = True

    # group_into_lines() splits a wide row into several lines whenever a column gap exceeds its
    # page-wide threshold -- wrong inside a table. Chain fragments back into rows by y-proximity,
    # scoped to this already-bounded body so it can't bleed into page content above the header.
    merged_body = sorted(_merge_row_fragments(body_lines, max(line_h * 0.9, 4.0)), key=lambda ln: _y(ln, 0))
    body: list[_Row] = [_parse_row(ln, _y(ln, 0)) for ln in merged_body]

    # 2. Rejoin split rows: a numbers-only row takes the nearest unused names-only row within pair_gap.
    items: list[tuple[float, LineItem]] = []
    for row in body:
        if row.used or not row.has_numbers:
            continue
        description = row.description
        confidence = row.confidence
        if not description:
            partner = min(
                (r for r in body if not r.used and r is not row and r.has_text and not r.has_numbers and abs(r.y - row.y) <= pair_gap),
                key=lambda r: abs(r.y - row.y),
                default=None,
            )
            if partner is None:
                continue
            partner.used = True
            description = partner.description
            confidence = min(confidence, partner.confidence)
        row.used = True
        amount, qty = _amount_and_qty(row.decimals)
        if len(description) < 2:
            continue
        items.append((row.y, LineItem(description=description, quantity=qty, amount=amount, confidence=confidence)))

    # 3. A names-only row with a numbers row just below it that already had its own name
    #    is a wrapped description -- left alone; the user can merge it if needed.
    items.sort(key=lambda p: p[0])
    return [it for _, it in _drop_duplicate_readings(items, line_h)][:MAX_LINES]


def _drop_duplicate_readings(items: list[tuple[float, LineItem]], line_h: float) -> list[tuple[float, LineItem]]:
    """The English and Arabic recognizer passes can both read the same printed row
    ("CKUMEER" / "CKCREER"): same height on the page, same amount. Keep the better-read one."""
    kept: list[tuple[float, LineItem]] = []
    for y, item in items:
        twin = next(
            (k for k in kept if abs(k[0] - y) <= line_h * 0.6 and (k[1].amount == item.amount or None in (k[1].amount, item.amount))),
            None,
        )
        if twin is None:
            kept.append((y, item))
        elif item.confidence > twin[1].confidence:
            kept[kept.index(twin)] = (y, item)
    return kept
