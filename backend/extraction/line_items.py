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

import difflib
import re
import statistics
from dataclasses import dataclass
from typing import Optional

from extraction.labels import LabelConcept, LabelMatch, match_label_concepts
from extraction.reference_data import ReferenceData
from extraction.types import OcrLine

MAX_LINES = 60

# Once this many body lines have been scanned past the header without a real item being found,
# the seen_item guard is lifted: an end-of-table marker can fire even though no item has yet been
# recognised. This lets a single-item bill whose amount format isn't matched by _DECIMAL (e.g.
# "AED6.00" glued directly to the currency code) still stop scanning at its own totals/VAT rows
# instead of running all the way into the footer. The guard still suppresses end-matches for the
# first few lines past the header to avoid stray column-label fragments in a wrapped multi-row
# header (e.g. "...Incl.VAT(AED) Total") from prematurely ending the table.
_MAX_HEADER_GUARD_LINES = 3

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
# A Tax Code column prints "VAT_AE:S" / "VAT AE:S" (OCR drops the underscore) on every item row. That is
# row data, not a "VAT" summary label: blank it out before end-of-table and description checks.
_TAX_CODE = re.compile(r"\bVAT[\s_-]*[A-Z]{2}\s*:\s*[A-Z]\b|(?<![A-Za-z])-?\s?U\.?A\.?E\b(?!\s*[,.]?\s*[A-Za-z])", re.IGNORECASE)
_END_WORDS = re.compile(r"\b(total|subtotal|grand|amount|balance|payable|rounding|vat)\b", re.IGNORECASE)

# Some invoices print the item quantity as a bare integer with a unit suffix ("50 Pcs",
# "1,000 Pc") rather than a decimal -- invisible to _DECIMAL below, which only sees the
# Rate/Amount columns' decimal values and otherwise leaves decimals[0] (the Rate) mistaken
# for the quantity. Matched separately so it can't collide with those money values.
_UNIT_WORDS = {
    "pcs", "pc", "nos", "mtr", "mtrs", "kg", "kgs", "ctn", "ctns", "box", "boxes", "unit", "units", "ea", "ltr", "ltrs",
    # Arabic: piece(s), item, box, carton, kg, litre, metre, unit, number, crate
    "قطعة", "قطع", "حبة", "علبة", "كرتون", "كجم", "كيلو", "لتر", "متر", "وحدة", "عدد", "صندوق",
}
_QTY_UNIT = re.compile(
    r"(?<![\d.,])(\d{1,3}(?:,\d{3})*)\s+(" + "|".join(_UNIT_WORDS) + r")\b", re.IGNORECASE
)

# OCR reads "0.00" / "38.00" as "0 00" / "38 00": rejoin a 1-4 digit group followed by two or three digits
# (some Gulf invoices print 3-decimal fils/baisa amounts, e.g. "480.000") -- but not when the second
# group is actually a bare quantity cell ("...20X100 50 Pcs..."): merging that into the item code
# ("20X100.50") destroys the one place the real quantity was readable.
_SPLIT_DECIMAL = re.compile(
    r"(?<![\d.,])(\d{1,4})\s(\d{2,3})(?![\d.,%])(?!\s*(?:" + "|".join(_UNIT_WORDS) + r")\b)", re.IGNORECASE
)
# Money values: 2- or 3-decimal numbers that are not glued to letters ("1.25CMX5M" is a size, not a price).
_DECIMAL = re.compile(r"(?<![\d.,A-Za-z])\d{1,6}[.,]\d{2,3}(?![\dA-Za-z])")
# OCR sometimes drops the last digit of the row's final amount ("14.3"); accepted only as the last token.
_TRAILING_ONE_DECIMAL = re.compile(r"(?<![\d.,A-Za-z])(\d{1,6}[.,]\d)\s*$")
_INTEGER = re.compile(r"(?<![\d.,])\d+(?![\d.,])")
_LETTERS = re.compile(r"[A-Za-z؀-ۿ]")

# A dense invoice table (Qty / Unit Rate / Unit Discount / Net Rate / Taxable Amount / VAT% /
# Tax Amount / Total Amount, 8 numeric columns) breaks the decimals[0]/decimals[-1] positional
# guess above -- there's no single "first"/"last" rule that holds for 5+ numeric columns. When
# real word geometry is available, the header row's own cell positions tell us exactly which
# x-band is Qty and which is the row's real Total, so a body row's matching number can be read
# directly off its position instead of guessed from reading order.
_QTY_HEADER_WORD = re.compile(r"^qty$|^quantity$|^الكمية$|^الكميه$|^كمية$|^العدد$", re.IGNORECASE)
_AMOUNT_HEADER_WORD = re.compile(r"total|amount|المجموع|الاجمالي|الإجمالي|اجمالي|إجمالي|المبلغ", re.IGNORECASE)
_WORD_NUMBER = re.compile(r"^\(?\d{1,3}(?:,\d{3})*(?:[.,]\d{1,3})?\)?$")

# A bill's VAT% column ("5 %", "5.00%") -- distinct from the Disc.%/other percentage columns some
# invoices also have, so only taken when it's the row's one percentage figure (ambiguous with two
# real percentages on a row; none of the sample bills so far print more than one).
_VAT_PERCENT = re.compile(r"(?<![\d.,])(\d{1,2}(?:\.\d{1,2})?)\s*%")


@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: Optional[float]
    amount: Optional[float]
    confidence: float
    vat_percent: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "amount": self.amount,
            "confidence": round(self.confidence, 2),
            "vat_percent": self.vat_percent,
        }


@dataclass
class _Row:
    y: float
    text: str
    decimals: list[float]
    description: str
    confidence: float
    int_qty: Optional[float] = None
    x_qty: Optional[float] = None
    x_amount: Optional[float] = None
    vat_percent: Optional[float] = None
    used: bool = False

    @property
    def has_numbers(self) -> bool:
        # x_qty/x_amount (read off real column geometry) count too -- a row can have a
        # resolvable quantity by position alone, with no decimals and no unit-suffixed
        # int_qty match of its own (e.g. a split-off row fragment whose Rate/Amount cells
        # ended up on a different fragment). Missing this let such a row's own real content
        # be silently treated as a bare, numberless "description" and handed to some
        # unrelated stray numbers row as its partner instead of becoming its own item.
        return bool(self.decimals) or self.int_qty is not None or self.x_qty is not None or self.x_amount is not None

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
    text = _TAX_CODE.sub(" ", text)
    if _SUMMARY_ROW.search(text) or _END_WORDS.search(text):
        return True
    matches = match_label_concepts(text, reference_data.label_vocabulary, reference_data.label_exclusions)
    return any(_is_end_concept_match(text, m) for m in matches if m.concept in _END_CONCEPTS)


def _is_end_concept_match(text: str, match: LabelMatch) -> bool:
    # A genuine summary/footer row leads with its own label ("CASH 49.25", "VAT@ 5%",
    # optionally after a leading SI number); a concept word first appearing after real
    # product text ("2 Receiving Card FS-LCE", "ADV MED GUIDANCE CARD...", a tax-code
    # column literally printing "VAT_AE:S" on every item row) is the word occurring
    # inside real item data, not a table-end marker -- don't let it end the table early.
    prefix_words = [w for w in text[: match.span[0]].split() if _LETTERS.search(w)]
    return not prefix_words


def _header_column_x(header_words: list, pattern: re.Pattern, pick_rightmost: bool) -> Optional[float]:
    # Returns the x-center of the header cell matching `pattern` -- the leftmost match for a
    # single-meaning column word (Qty), the rightmost for a word that repeats across several
    # columns (every money column's header can contain "Amount"; the row's own grand total is
    # always the rightmost one, "Total Amount"/"Total Incl VAT").
    best: Optional[float] = None
    for w in header_words:
        if not w.bounding_box:
            continue
        token = w.text.strip(" :.()")
        if not pattern.search(token):
            continue
        cx = (w.bounding_box[0] + w.bounding_box[2]) / 2
        if best is None or (pick_rightmost and cx > best) or (not pick_rightmost and cx < best):
            best = cx
    return best


def _nearest_column_number(line: OcrLine, col_x: Optional[float], tolerance: float) -> Optional[float]:
    # The number whose own word-level x-center falls closest to a known column position --
    # read directly off the table's real geometry instead of guessed from reading order.
    if col_x is None:
        return None
    best_val: Optional[float] = None
    best_dist: Optional[float] = None
    for w in line.words:
        if not w.bounding_box:
            continue
        token = w.text.strip().strip("()")
        value_text = token
        if not _WORD_NUMBER.match(token):
            # A quantity cell sometimes arrives as one OCR word fused with its unit ("50 Pcs",
            # no space in the engine's own box) -- invisible to the clean-number check above,
            # which would otherwise make the real Qty cell disappear from the column search
            # entirely and let the next-nearest number (another column) silently win instead.
            qty_match = _QTY_UNIT.match(token)
            if not qty_match or qty_match.end() != len(token):
                continue
            value_text = qty_match.group(1)
        cx = (w.bounding_box[0] + w.bounding_box[2]) / 2
        dist = abs(cx - col_x)
        if dist > tolerance or (best_dist is not None and dist >= best_dist):
            continue
        try:
            best_val, best_dist = float(value_text.strip("()").replace(",", "")), dist
        except ValueError:
            continue
    return best_val


def _leading_qty_match(text: str) -> Optional[re.Match]:
    # A real quantity cell either leads its row ("50 Pcs 4.73 ...", optionally after a leading
    # SI number) or follows the item's own description ("Bolt 20X100 50 Pcs 4.73 4.50 Pcs
    # 225.00 ..." -- description-before-quantity is the more common table layout across these
    # sample bills). "400 PCS" buried inside a wrapped packing note a row or two below the real
    # item ("1 PKT PER 400 PCS", "75 PKT X 400 PCS = 30000 PCS") is that note's own text, not a
    # second item's quantity -- those rows are pure arithmetic/packing prose with no Rate/Amount
    # columns of their own, so requiring a real decimal money value somewhere later on the row
    # (the Rate/Amount that always follows a genuine Qty cell) keeps rejecting them specifically.
    has_real_row_numbers = bool(_DECIMAL.search(text))
    for m in _QTY_UNIT.finditer(text):
        prefix_words = [w for w in text[: m.start()].split() if _LETTERS.search(w)]
        if not prefix_words or (has_real_row_numbers and _DECIMAL.search(text, m.end())):
            return m
    return None


def _parse_row(
    line: OcrLine, y: float, qty_col_x: Optional[float] = None, amount_col_x: Optional[float] = None, col_tolerance: float = 0.0
) -> _Row:
    text = _SPLIT_DECIMAL.sub(r"\1.\2", line.text)
    decimals = [float(m.group(0).replace(",", ".")) for m in _DECIMAL.finditer(text)]
    trailing = _TRAILING_ONE_DECIMAL.search(text)
    if trailing:
        decimals.append(float(trailing.group(1).replace(",", ".")))
    qty_match = _leading_qty_match(text)
    int_qty = float(qty_match.group(1).replace(",", "")) if qty_match else None
    x_qty = _nearest_column_number(line, qty_col_x, col_tolerance)
    x_amount = _nearest_column_number(line, amount_col_x, col_tolerance)
    vat_match = _VAT_PERCENT.search(text)
    vat_percent = float(vat_match.group(1)) if vat_match else None
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
    # The Tax Code and Unit columns ("NOS VAT_AE:S") sit left of the numbers on dense invoices and would
    # otherwise stand in as the product name -- strip them so the real name on the left is paired in.
    description = _TAX_CODE.sub(" ", description)
    tokens = description.split()
    while tokens and tokens[0].lower().strip(".:") in _UNIT_WORDS:
        tokens.pop(0)
    description = " ".join(tokens).strip(" -:|")
    # A trailing run of codes after the name (e.g. "... 55507116 9999") is not part of it.
    description = re.sub(r"(\s+\d{4,})+$", "", description).strip()
    # OCR noise like "0 oo" or "Le pi" is not a product name: require a few real letters.
    if len(_LETTERS.findall(description)) < 3:
        description = ""
    # A bare unit word ("Pcs") picked up as "the description" because it has >=3 letters
    # isn't a product name either -- clear it so the row can rejoin with its real
    # description on an adjacent line instead of keeping this as the final name.
    if int_qty is not None and description.strip().lower() in _UNIT_WORDS:
        description = ""
    return _Row(
        y=y, text=text, decimals=decimals, description=description, confidence=line.confidence,
        int_qty=int_qty, x_qty=x_qty, x_amount=x_amount, vat_percent=vat_percent,
    )


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
    two unrelated complete rows together through that left-restarting line in between.

    Tried and reverted: letting two lines merge purely on an extremely small y-gap,
    regardless of x, to handle a row's right-side columns legitimately landing at a
    smaller y than its own left-side description (confirmed on one real bill via its
    RunPod OCR reading). That broke two already-passing real-bill fixtures
    (tests/fixtures/line_item_bills.py) whose "numbers line, name a few px below" layout
    has gaps of the same 1-6px magnitude -- there is no threshold that catches one without
    the other by y-gap alone; doing this properly needs real column/x-band detection, not
    a y-gap exception. See assets/docs/MULTI_ITEM_LINE_ALLOCATION_AND_OCR_FINDINGS.md."""
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


def _split_multi_item_rows(rows: list[OcrLine]) -> list[OcrLine]:
    """A row genuinely has exactly one "<number> <unit>" quantity cell (its own Qty column) --
    on a dense table, group_into_lines()'s own y-banding (not _merge_row_fragments, which has
    already run by this point) can still weld two physically adjacent table rows into one
    detected line when their columns don't line up in y as cleanly as their descriptions do
    (confirmed on a real bill: one row's Qty/Rate cell sorts into the same OCR line as the row
    above's description). A second "<number> <unit>" match is that different row's own quantity
    bleeding in -- split the words at each extra match's start so each half is parsed as its own
    row (gaining a correct partial read, or correctly abstaining) instead of confidently reading
    one item's numbers as another's."""
    out: list[OcrLine] = []
    for ln in rows:
        matches = list(_QTY_UNIT.finditer(ln.text))
        if len(matches) < 2 or not ln.words:
            out.append(ln)
            continue
        split_at = [m.start() for m in matches[1:]]
        offset = 0
        word_starts = []
        for w in ln.words:
            word_starts.append(offset)
            offset += len(w.text) + 1
        parts: list[list] = [[]]
        next_split = 0
        for i, w in enumerate(ln.words):
            while next_split < len(split_at) and word_starts[i] >= split_at[next_split]:
                parts.append([])
                next_split += 1
            parts[-1].append(w)
        for part_words in parts:
            if not part_words:
                continue
            text = " ".join(w.text for w in part_words if w.text)
            boxes = [w.bounding_box for w in part_words if w.bounding_box]
            bbox = (
                (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
                if boxes
                else ln.bounding_box
            )
            out.append(
                OcrLine(
                    text=text, words=tuple(part_words), confidence=ln.confidence, bounding_box=bbox,
                    page=ln.page, reading_order=ln.reading_order,
                )
            )
    return out


def _attach_trailing_total_fragments(
    items: list[tuple[float, LineItem]], body: list["_Row"], line_h: float
) -> list[tuple[float, LineItem]]:
    """A row's own trailing VAT%/VAT-amount/Total cells sometimes print at a position that fails
    _merge_row_fragments's strict x-rightward rule -- the "row whose right-side columns sort
    out of x-order" jitter its own docstring describes -- and surface as a separate, description-
    less orphan a few pixels below the row they belong to (confirmed on a real bill: a row read
    as "...486.00" with its real Total "24.30 510.30" stranded in its own OcrLine right under it).

    Runs AFTER the ordinary partner-pairing step above, on whatever orphans that step left
    genuinely unused -- not before it. An orphan that still has decimals and no description at
    this point already had its chance to pair with a real nearby description and found none; only
    then is it attached to the nearest already-item-forming row above as that row's missing tail.
    Running this first instead (tried and reverted) stole rows that pairing would have correctly
    matched to their own real description -- e.g. a bare "2 19.15" row is item 1's own total on one
    real bill, not a continuation of the unrelated item 2 that merely happens to sit closest above.

    A page-level Subtotal/Grand-Total row that leaked past _is_end (it has no label text of its
    own, just a bare number, so the keyword check never catches it) looks exactly like an orphan
    too, but its value is the SUM of every item, not one row's VAT/Total -- confirmed on a real
    bill where it would otherwise have overwritten an already-correct last item's amount (173.25)
    with the table's 732.60 grand total. A genuine trailing Total is only moderately larger than
    the row's own partial amount (VAT added, rarely more than ~50%); a page total is typically
    several times larger -- so a target without an implausible jump in value is preferred."""
    gap = max(line_h * 0.9, 4.0) * 1.5
    orphans = sorted(
        (r for r in body if not r.used and not r.description and r.decimals and r.int_qty is None and len(r.decimals) <= 3),
        key=lambda r: r.y,
    )
    if not orphans:
        return items
    out = list(items)
    for orphan in orphans:
        if orphan.decimals[-1] == 0:
            continue  # 0.00 is VAT/discount column noise, not a real trailing total
        candidates = [
            (i, y) for i, (y, it) in enumerate(out)
            if 0 < orphan.y - y <= gap and (it.amount is None or it.amount <= 0 or orphan.decimals[-1] <= it.amount * 1.5)
        ]
        if not candidates:
            continue
        i, y = max(candidates, key=lambda c: c[1])
        it = out[i][1]
        out[i] = (y, LineItem(
            description=it.description, quantity=it.quantity, amount=orphan.decimals[-1],
            confidence=it.confidence, vat_percent=it.vat_percent,
        ))
        orphan.used = True
    return out


def _amount_and_qty(decimals: list[float]) -> tuple[Optional[float], Optional[float]]:
    if not decimals:
        return None, None
    amount: Optional[float] = decimals[-1]
    qty: Optional[float] = decimals[0] if len(decimals) >= 2 else None
    if qty is not None and not (0 < qty <= 1000):
        qty = None
    # A 0.00 last value is the VAT/discount column or a missed read, not a real line total.
    # Leave amount blank so the employee fills it in rather than submitting a wrong 0.
    if amount == 0:
        amount = None
    return amount, qty


_NAME_STOP = re.compile(r"serial|batch|lot\s*no", re.IGNORECASE)


def _append_wrapped_name(body: list["_Row"], first: "_Row", description: str, line_h: float) -> str:
    """A tall item prints its name over several lines ("LED" / "WH-10K-0.7W" / "LEDRAY LED MODULE") with the
    numbers on the first one. Chain the name-only rows directly below it up to its Serial/Batch line."""
    below = sorted((r for r in body if r.y > first.y and r is not first), key=lambda r: r.y)
    prev_y = first.y
    parts = [description]
    chain: list["_Row"] = []
    for r in below:
        if r.used or r.has_numbers or r.y - prev_y > line_h * 2.2:
            return description
        if _NAME_STOP.search(r.text):
            # Only a name closed off by its own Serial/Batch line is trusted as one item's wrapped name; any
            # other run of text below a row (footer, address, packing notes) is not part of it.
            for c in chain:
                c.used = True
                if c.description:
                    parts.append(c.description)
            return " ".join(parts).strip()[:120]
        chain.append(r)
        prev_y = r.y
    return description


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
    header_start = None
    for idx, (_, ln) in enumerate(ordered):
        if _is_header(ln.text, reference_data):
            start = header_start = idx
            # Header rows can wrap onto several OCR lines ("Qty Amount" / "Description").
            while start + 1 < len(ordered) and ys[start + 1] - ys[idx] <= line_h * 2.5 and _is_header(ordered[start + 1][1].text, reference_data):
                start += 1
            break
    if start is None:
        return []

    body_lines: list[OcrLine] = []
    seen_item = False
    first_item_idx = len(ordered)
    for idx in range(start + 1, len(ordered)):
        _, ln = ordered[idx]
        # A wrapped multi-row header often has its own stray "VAT"/"Total" column label
        # (e.g. "Incl.VAT(AED) Total"), which otherwise reads as an end-of-table marker
        # before any item has actually been seen -- an end marker can't appear before item 1.
        # But don't suppress end-markers forever: a single-item bill whose amount format isn't
        # matched by _DECIMAL (e.g. "AED6.00") would otherwise scan all the way into the footer.
        # After _MAX_HEADER_GUARD_LINES lines, lift the seen_item requirement.
        past_header_guard = (idx - start) > _MAX_HEADER_GUARD_LINES
        if _is_end(ln.text, reference_data) and (seen_item or past_header_guard):
            break
        body_lines.append(ln)
        if not seen_item and _parse_row(ln, ys[idx]).has_numbers:
            seen_item = True
            first_item_idx = idx

    # A dense table's header can wrap across several OCR fragments that don't all look like a
    # header by themselves (a stray "AMOUNT"/"TOTAL" column label with no qty/rate word of its
    # own doesn't match _is_header and ends up as a body_lines fragment before the first real
    # item) -- scan the whole header-to-first-item span, not just the recognized header cluster,
    # for the Qty/Total column's own x-position. Only meaningful with real word geometry.
    header_words = [w for i in range(header_start, first_item_idx) for w in ordered[i][1].words]
    qty_col_x = _header_column_x(header_words, _QTY_HEADER_WORD, pick_rightmost=False)
    amount_col_x = _header_column_x(header_words, _AMOUNT_HEADER_WORD, pick_rightmost=True)
    col_tolerance = max(line_h * 3, 60.0)

    # group_into_lines() splits a wide row into several lines whenever a column gap exceeds its
    # page-wide threshold -- wrong inside a table. Chain fragments back into rows by y-proximity,
    # scoped to this already-bounded body so it can't bleed into page content above the header.
    merged_body = sorted(_merge_row_fragments(body_lines, max(line_h * 0.9, 4.0)), key=lambda ln: _y(ln, 0))
    merged_body = _split_multi_item_rows(merged_body)
    body: list[_Row] = [_parse_row(ln, _y(ln, 0), qty_col_x, amount_col_x, col_tolerance) for ln in merged_body]

    # 2. Rejoin split rows: a numbers-only row takes the nearest unused names-only row within pair_gap.
    # A bill with no printed totals/VAT row at all (a pure delivery note) never trips _is_end,
    # so body_lines runs to the bottom of the page -- a stray OCR misread anywhere in the
    # signature/footer block below (e.g. a date glued into one decimal, "2026 12:56" ->
    # "2026.12") would otherwise surface as a trailing phantom item. Real table rows never
    # have a large vertical gap between them, so once a huge gap opens up after the last
    # real item, the rest of the body is footer, not more items.
    max_item_gap = max(line_h * 5, 80.0)
    items: list[tuple[float, LineItem]] = []
    last_item_y: Optional[float] = None
    for row in body:
        if row.used or not row.has_numbers:
            continue
        # A row with a full set of money columns is a real table row even after a tall gap (items with
        # wrapped names and Serial/Batch lines are 90-110px apart); a lone stray decimal is footer noise.
        if last_item_y is not None and row.y - last_item_y > max_item_gap and len(row.decimals) < 3:
            break
        description = row.description
        confidence = row.confidence
        if description and row.int_qty is None:
            description = _append_wrapped_name(body, row, description, line_h)
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
            description = _append_wrapped_name(body, partner, description, line_h)
        row.used = True
        amount, qty = _amount_and_qty(row.decimals)
        if row.int_qty is not None:
            qty = row.int_qty
        # Real column position beats both the reading-order guesses above when we have it --
        # the only one of the three that still works once a table has more than 2-3 numeric
        # columns (a bare decimals[0]/decimals[-1] guess has no way to know which of 8 columns
        # is actually Qty vs. Total).
        if row.x_qty is not None:
            qty = row.x_qty
        if row.x_amount is not None and row.x_amount != 0:
            amount = row.x_amount
        if len(description) < 2:
            continue
        items.append((
            row.y,
            LineItem(description=description, quantity=qty, amount=amount, confidence=confidence, vat_percent=row.vat_percent),
        ))
        last_item_y = row.y

    # 3. A names-only row with a numbers row just below it that already had its own name
    #    is a wrapped description -- left alone; the user can merge it if needed.
    items.sort(key=lambda p: p[0])
    items = _attach_trailing_total_fragments(items, body, line_h)
    return [it for _, it in _drop_duplicate_readings(items, line_h)][:MAX_LINES]


def _same_reading(a: LineItem, b: LineItem) -> bool:
    if a.amount is not None and b.amount is not None:
        return a.amount == b.amount
    # One side has no amount at all (e.g. a real column it genuinely wasn't read from, not a
    # misread) -- that alone is weak evidence of "same row read twice" and, on a dense table,
    # just as often means two adjacent DIFFERENT items where one's amount cell was lost. Only
    # call it a duplicate when the descriptions themselves are clearly the same text misread.
    if not a.description or not b.description:
        return False
    return difflib.SequenceMatcher(None, a.description.lower(), b.description.lower()).ratio() >= 0.4


def _drop_duplicate_readings(items: list[tuple[float, LineItem]], line_h: float) -> list[tuple[float, LineItem]]:
    """The English and Arabic recognizer passes can both read the same printed row
    ("CKUMEER" / "CKCREER"): same height on the page, same amount. Keep the better-read one."""
    kept: list[tuple[float, LineItem]] = []
    for y, item in items:
        twin = next(
            (k for k in kept if abs(k[0] - y) <= line_h * 0.6 and _same_reading(k[1], item)),
            None,
        )
        if twin is None:
            kept.append((y, item))
        elif item.confidence > twin[1].confidence:
            kept[kept.index(twin)] = (y, item)
    return kept
