# Multi-item bills: per-line project allocation + OCR line-item extraction

Session notes recording what was found and changed while adding per-line project/OP
allocation to multi-item claims, and investigating why OCR wasn't pre-filling line items
on real multi-item bills. Written as a findings record, not a spec — see git history on
`dev-teja` for the actual diffs.

## 1. Per-line project/OP allocation (implemented, committed)

**Problem:** project/OP-code assignment on a claim was claim-level only
(`ErpExpenseTransaction.op_number`, one free-text field). Real multi-item bills often span
more than one client project/OP (e.g. a hardware-store receipt with some items for one site,
some for another) — previously impossible to represent without splitting into multiple claims.

**What changed:**
- `ErpExpenseLineItem.op_number` column added (migration:
  `backend/scripts/add_line_item_op_number_column.py`, run against ERP-Dev).
- `LineItemIn.op_number` added to the create/update claim API; persisted via
  `transaction_service._replace_line_items`; returned per-line on read.
- New shared `OpCodeField` widget (`lib/src/widgets/op_code_field.dart`) — the debounced
  "Project / OP code" search-as-you-type field, extracted so both the claim-level field
  and each line item's field share one implementation.
- `LineItemDraft.opResult` added; `_LineCard` in `line_items_editor.dart` shows a per-line
  `OpCodeField` under the Category dropdown.
- **Smart default:** a newly-added line item defaults to the OP of the line above it, or
  the claim-level OP for the first line — so a bill that's mostly one project with one item
  split off costs one edit, not N (confirmed design choice, since real bills commonly have
  5+ line items).

Commit: `56c5942` on `dev-teja` (bundled with an unrelated Phosphor-icons/nav-drawer change
from earlier in the session).

## 2. OCR line-item extraction was silently broken on real bills

Tested the actual production pipeline (`services.ocr_service.run()`, not a mock) against 3
real sample multi-item bills in `assets/multi_line/` (`image.png` / Fabricast, 2 items;
`img2.jpeg` / Standard Hardware, 3 items; `img3.jpeg` / Bab Al Hayat Pharmacy, 12 items).
**`line_items` came back empty for all three**, even though vendor/total were read correctly.

### Root causes found in `backend/extraction/line_items.py`

1. **2-decimal-digit assumption.** The money-value regexes (`_DECIMAL`, `_SPLIT_DECIMAL`,
   `_TRAILING_ONE_DECIMAL`) only matched exactly 2 decimal digits. `img2.jpeg` prints amounts
   with 3 decimals (`480.000`, `87.600`...) — some Gulf-invoice formats do this — so every
   money value on every row failed to match, and rows were dropped as "no numbers."
2. **Column-splitting breaks table rows.** `group_into_lines()` (shared with the single-field
   pipeline) splits a wide row into several `OcrLine`s whenever the horizontal gap between
   words exceeds a page-wide threshold — correct for unrelated side-by-side page content, wrong
   inside an item table. `image.png`/`img3.jpeg` have columns spread far apart, so one printed
   row (`"1 CABLE CONNECTOR,70"` / `"70-95 2.0 Nos 28.00"` / `"Nos 56.00 5% 2.80 58.80"`) read
   as three unrelated lines, none of which alone had both a description and a usable amount.
3. **Header-fragment false positives for end-of-table.** A wrapped multi-row header's own
   stray "VAT"/"Total" column label (e.g. `"...Incl.VAT(AED) Total"`) was read as the
   end-of-table marker before any item row had been seen.

### Fix (`backend/extraction/line_items.py`)

- Widened the decimal regexes to accept 2 **or** 3 digits.
- Added `_merge_row_fragments()`: reconstructs a true table row from `group_into_lines()`'s
  fragments by chaining lines that are both **close vertically** (within ~1 row-height) AND
  **start to the right of everything already read into the row** — i.e. the left-to-right
  column order a row actually prints in. This was non-obvious to get right:
  - A naive "merge if y-gap is small" chain (first attempt) over-merged: a wrapped
    description continuation (e.g. `"16mnm"`, the second line of an item's product name)
    sits at a small y-gap to *both* the row above and the row below, bridging two unrelated
    complete rows into one garbled mess. The x-rightward constraint fixes this — a
    continuation line restarts near the left margin, so it never passes the check, and is
    left for the existing nearest-y "pair rejoin" step to glue back on instead.
  - Merging across the *whole page* (tried before bounding to the table) catastrophically
    merged unrelated address/invoice-metadata blocks above the header, which also have
    naturally tight line spacing. Scoped the merge to only run on the body already bounded
    between the detected header and end-of-table marker.
- Added a `seen_item` guard: an end-of-table match doesn't end the table until at least one
  real item row (one with parsed numbers) has already been captured.
- Added `"vat"` as a literal end-of-table trigger word — the label-concept matcher missed a
  percentage-suffixed reading like `"VAT 5%"` (vs. a standalone `"VAT"` line, which it caught).

### Verified results (CPU/RapidOCR path — see §3 for why this caveat matters)

| Bill | Real items | Before | After |
|---|---|---|---|
| `image.png` (Fabricast) | 2 | 0 | 3 (2 correct + a 3rd leftover fragment split off item 2) |
| `img2.jpeg` (Standard Hardware) | 3 | 0 | 3/3, all correct |
| `img3.jpeg` (Bab Al Hayat Pharmacy) | 12 | 0 | 7/12, all real values, no garbage |

No regressions: `test_line_items.py` (10/10), `test_pipeline_general.py`,
`test_pipeline_enoc_regression.py` all pass. The only failing tests anywhere
(`test_claim_line_items.py`, 8 cases) are a **pre-existing, unrelated** fixture bug — missing
`bill_number` kwarg — confirmed present before this session's changes too (`git stash` + rerun).

**Not done:** new unit-test fixtures exercising the merge logic directly (only real-bill
end-to-end verification was done, which is a strong but not exhaustive signal). `img3.jpeg`'s
remaining 5/12 missed items likely need the same kind of column-fragmentation fix carried
further — diminishing returns hit for this session's effort budget.

## 3. The fix above didn't run in production at all — now fixed too

`services/ocr_service.py` tries **RunPod GPU OCR first**, falling back to the CPU/RapidOCR
pipeline above only on RunPod failure/timeout. Tested via the actual Flutter app
(Android emulator) against `img2.jpeg`: **line items still came back empty**, Bill number was
blank, and currency went undetected — none of which matched the CPU-path test results above.

Initial root cause read: `_run_runpod_ocr()` builds `OcrLine`s via `words_from_text()`, which
treats each full printed line as one atomic "word" with `bounding_box=None` — no per-word
geometry to reconstruct a table from. `extract_line_items()` was briefly wired up to that
geometry-less path during this investigation and produced garbage (header labels paired with
random nearby numbers via list-order-proximity pairing); that attempt was reverted.

### Corrected finding: the worker already returns boxes — we just weren't reading them

Got the RunPod worker's actual handler source (deployed as `teja060803/paddle-onnx-runpod:v1.5.1`,
endpoint `arbaic` / `ze0kdoq723wbrh`, confirmed matching `.env`'s `RUNPOD_ENDPOINT_ID`) directly
from the person who built it. It runs `rapidocr_onnxruntime.RapidOCR` and **already returns a
`boxes` array** alongside the plain `text`:
```python
boxes.append({"text": text, "x": ..., "y": ..., "w": ..., "h": ...})
return {"text": "\n".join(lines), "boxes": boxes, "line_count": ..., "engine": ..., "status": "success"}
```
`_run_runpod_ocr()` was only ever reading `output["text"]` and silently discarding `output["boxes"]`
— no worker change needed at all, just reading data that was already there.

**Fix (`backend/services/ocr_service.py`):** when `boxes` is present, build real `OcrWord`s from
it (`bounding_box=(x, y, x+w, y+h)`, confidence defaulted to `1.0` since the worker doesn't return
per-box confidence) and run them through the *same* `group_into_lines`/`dedupe_lines`/
`extract_line_items` pipeline the CPU path uses — so every fix from §2 (3-decimal regex,
column-aware row merge, seen_item guard, vat end-word) applies automatically on this path too.
Falls back to the old geometry-less `words_from_text(text)` only if a response ever comes back
without `boxes` (e.g. an older worker version).

**Verified against the live endpoint** (not simulated — actually called `_run_runpod_ocr()`
against the real RunPod API for all 3 sample bills):

| Bill | Real items | Before this fix | After (RunPod, live) |
|---|---|---|---|
| `image.png` | 2 | 0 | 2/2, both correct |
| `img2.jpeg` | 3 | 0 | 3/3 item count, but see §4 — one remaining known issue |
| `img3.jpeg` | 12 | 0 | 10/12, real values |

Full test suite (`test_line_items.py`, `test_pipeline_general.py`,
`test_pipeline_enoc_regression.py`, `test_ocr_service_modes.py` — 46 tests) passes, no
regressions.

## 4. Row-merge robustness: one remaining known issue, investigated and bounded

`img2.jpeg` on the RunPod path initially extracted **4** items instead of 3: the wrapped
continuation fragment `"16mnm"` (the second line of item 1's product name) sits almost exactly
between item 1 and item 2's own fragments, and `_merge_row_fragments`'s left-to-right
x-rightward merge rule — needed to prevent a continuation from bridging two unrelated complete
rows together on densely-packed bills — can't reunite a row whose right-side (amount) columns
happen to sort at a *smaller* y than its own left-side (description) columns, which is exactly
what RunPod's finer per-word boxes exposed on this bill (confirmed via the raw box dump: item
2's amount cluster at y=909 sorts before its own description cluster at y=911, a 2px real
print/scan jitter reversal).

**Tried:** letting two fragments merge purely on an extremely small y-gap (≤2-2.5px),
regardless of x, specifically to catch that jitter reversal. This worked for `img2.jpeg`, but
broke two already-passing real-bill unit tests
(`tests/fixtures/line_item_bills.py`'s `SUPERMARKET` and `PHARMACY` fixtures,
`test_supermarket_rejoins_numbers_with_the_item_name_below_them` and
`test_pharmacy_reads_every_item_row`): both have a genuine "numbers line, item name a few px
below" print layout with real gaps as small as **1px** — the same magnitude as the jitter case
being targeted. There is no y-gap-only threshold that reliably separates "two fragments of one
physical row, printed slightly out of order" from "two deliberately separate rows, printed
close together" — they look identical by vertical gap alone.

**Reverted** to the x-rightward-only merge (the version that passes all 46 tests) rather than
ship a fix for one bill that silently breaks two other real, previously-verified ones.
`img2.jpeg` on RunPod still extracts 4 items (1 false split) as a result — a known, bounded
limitation, not a regression from before this session (which extracted 0).

**What would actually fix this properly:** real column/x-band detection — clustering a page's
money-value tokens by x-position first to infer the table's actual column boundaries, then
assigning every fragment (including out-of-y-order ones) to a row by which column band it falls
in, rather than inferring row membership from y-order and reading-direction alone. Scoped out of
this session; the current merge heuristic is a reasonable approximation that measurably helps
(0 → correct/mostly-correct across all 3 bills on both OCR paths) without that bigger rewrite.

### Separately relevant: prior accuracy finding (still open)

`OCR_ENGINE_EVALUATION.md`'s existing RunPod-vs-CPU comparison (2026-09-18, 9 real KSA images)
found RunPod **worse** overall on *field* extraction accuracy — "RunPod frequently drops digits,"
"dates... RunPod nailed effectively 0/7 cleanly," vendor roughly a wash — independent of the
line-items gap just closed above. Whether RunPod should stay first in the try-order is still an
open question worth revisiting with real data now that line items work on both paths.

## 5. Single-item-bill regression check, then a real single-value-field accuracy audit

### Regression check: did any of §2's changes affect bills that aren't multi-item at all?

Ran the real CPU pipeline on 7 true single-value bills (taxi/ride receipts — `ksa1/3/4/5/8/9.png`,
`enoc_test.jpg`), both before and after this session's `line_items.py` changes, comparing
`line_items` output directly. **6 of 7 unaffected** — byte-identical `[]` before and after.

**1 of 7 regressed:** `enoc_test.jpg` (one real item, "ICE BAG"). Before: `line_items: []`. After:
a false item (`"Shift"` / amount `1.04`, read from the footer timestamp `"Shift:1 04:52:23"`).
Root cause: this receipt happens to print a `"Description UnitPrc Qty\nAmount V"` column header
even though it only has one line — triggering table-detection to start scanning at all (the other
6 bills never trigger it, since nothing on a plain taxi receipt looks like a table header). Once
scanning, the `seen_item` guard added in §2 never flips true (this bill's own amount is glued
directly to its currency code — `AED6.00`, no space — so it never matches the decimal regex), so
the guard suppresses every legitimate early end-of-table match and scanning runs unchecked into
the footer. **Known, not yet fixed** — narrow (one receipt shape, not single-item bills broadly)
but real; flagged for a follow-up fix to `extract_line_items`'s `seen_item` guard (likely: cap how
far past the header unchecked scanning is allowed, rather than suppressing every end-match
indefinitely until a real item is found).

**Second, independently-confirmed instance, different mechanism: `assets/dubai/image (4).png`.**
Tested the production pipeline against a few more real itemized bills found during the accuracy
audit below and found footer/payment rows leaking in as fake items again — but traced it directly
against the live RunPod OCR output and confirmed `seen_item` is *not* the cause here (it correctly
flips `True` early, since this bill's real items do have real decimal amounts). The actual cause:
`_is_end()`'s keyword/concept matching requires the OCR text to still resemble the real word, and
OCR garbled "Rounding"→"RoMcing", "Amount"→"Anount", "CASH"→"CAS" — none of which match any known
end-of-table keyword anymore, so `_is_end()` legitimately (and correctly, given its inputs) returns
`False` for each, and 4 fake items leak in (`RoMcing`/0.0, `Anount`/47.5, `CAS`/47.5,
`sraunt ta rerrn`/6.0) alongside the real ones.

Tried a fix: when two *consecutive* body rows report the identical amount, treat it as a
footer/payment echo (`"Anount 47.50"` → `"CAS 47.50"`) rather than two coincidentally same-priced
items, and stop there. Checked this against `tests/fixtures/line_item_bills.py`'s `PHARMACY`
fixture first — it genuinely has two *different* items both priced `23.94`, confirming a naive
"any duplicate value = stop" rule would be unsafe — so the fix only fired on *consecutive*
duplicates, which PHARMACY's don't have (several other rows separate its two 23.94 items).

**Measured, then reverted.** On the targeted bill it worked as designed: `image (4).png`'s items
dropped from 6 to 3 (`Anount`/`CAS`/`sraunt ta rerrn` correctly removed; `RoMcing` remained as a
known residual). But the full test suite caught a real regression this targeted check didn't
anticipate: `test_same_row_read_by_both_ocr_passes_is_kept_once` lost its items entirely (5/10
`test_line_items.py` tests failed). Root cause: when the bilingual pipeline's English and Arabic
recognizer passes both read the *same physical row* (a deliberate, handled scenario — meant to be
deduplicated by the later, more careful `_drop_duplicate_readings` step), they produce two
consecutive candidate rows with the identical amount — exactly the pattern the new check was
designed to catch, but here it's legitimately one real row read twice, not a footer echo. The
fix fired before dedup ever ran and deleted the real item. Reverted cleanly (confirmed via
`git diff` — only this paragraph's investigation notes remain, no code change). Full suite back to
155 passed / 5 skipped, same 8 pre-existing unrelated failures.

**Status: still an open, real bug**, now confirmed on two real bills via two *different* root
causes, both attempts at a fix found and reverted for measurable regressions on already-working
cases. A durable fix likely needs a structural signal that doesn't rely on literal keyword
matching (fragile against OCR noise) or naive value-repetition (collides with the deliberate
bilingual-dedup design) — e.g. distinguishing "this row has its own real multi-word description"
(genuine items) from "this row is a short label fragment" (footer echoes) more robustly than
string length alone (tried and found too unreliable to even implement — see the per-case text in
the git history of this file's earlier revision for why). Scoped out of this session.

### Real accuracy audit: ground-truth-verified, actual production pipeline

The existing historical numbers in `OCR_ENGINE_EVALUATION.md`/`scripts/ocr_accuracy.md` come from
a separate, naive test script (`scripts/test_runpod_ocr.py`'s own regex), not the real backend —
that doc's own "Suggested next step" flags this and was apparently never followed up. Used
`scripts/ocr_results.csv`'s hand-verified `actual_*` columns as ground truth and ran the actual
`ocr_service.run()` pipeline (RunPod-then-CPU, exactly as production calls it) against the same
13 bills:

| Field | Before | After this session |
|---|---|---|
| Vendor | 4/13 (31%) | 4/13 (31%) — unchanged |
| Total amount | 7/13 (54%) | 7/13 (54%) — unchanged, see §2 below |
| Currency | 5/13 (38%) | **12/13 (92%)** — fixed |

Three gaps found, in order of how actionable they are:

1. **Currency — fixed this session.** Confirmed via raw OCR text: for every failing case, "AED"/
   "SAR" literally never appears anywhere in the OCR'd text — some receipts just never print a
   currency code, assuming local currency is obvious. There was no fallback anywhere in the
   pipeline; `currency` just stayed `None`. **Fix:** `default_currency_for_region()` (new, in
   `extraction/reference_data.py`, reading a new `default_currency` key per region in
   `extraction/config/tax_rules.yaml` — UAE→AED, KSA→SAR, OMAN→OMR, IN→INR) is applied in
   `OcrService.run()` only when `currency` comes back empty. Required threading a new
   `region_code` parameter through `OcrService.run()` → `TransactionService.run_ocr()` /
   `analyze_receipt()` → the `/ocr` and `/receipts/{id}/ocr` routes (`CurrentUser.region_code`,
   already available from the JWT, was just never passed through). Verified: all 6 previously-`None`
   cases now resolve correctly (AED/SAR), the 2 that already worked are unaffected, and omitting/
   not-recognizing a region still correctly leaves `currency: None` (no false guessing for unknown
   regions). Full test suite: 155 passed, 5 skipped, same 8 pre-existing unrelated failures.

2. **Total amount — real bug found, attempted fix, reverted (doesn't actually solve it).**
   `image (4).png`: got `total_amount = 4.56`, actual `47.49`. Traced the mechanism: `amount` and
   `vat_amount` both resolved to the *same* number (`2.28`, the real VAT) instead of `amount`
   correctly reading `45.21`. The bill's VAT-breakdown row reads as `"45.21\n2.28 47.49"` under a
   garbled column-header line (`"VATK iaxable Amount VAT\n5."`) — three numbers meant to align with
   three columns (Amount / VAT / Total), but `extraction/candidates.py`'s `_money_field_candidates`
   deliberately pairs every label on a line/row with every nearby number (cross-product, not
   positional — its own comment explains order-based pairing was tried before and reverted as
   net-negative on garbled receipts generally), so all three numbers became candidates for *both*
   `amount` and `vat_amount`.

   Tried a narrow fix in `extraction/select.py`: when `amount`/`vat_amount` resolve to the exact
   same value, re-pick the weaker-confidence one from its own ranked candidate list for the next
   distinct value. **Checked the actual scores first and they're a problem**: all three candidates
   score *exactly* identically for both fields (`0.830671` to 6 decimal places — not just close,
   tied) — `scoring.py` has no column-position signal anywhere to break the tie. The "fix" just
   swapped which arbitrary tied value got picked; verified it does **not** fix `image (4).png`
   (now gets `amount=47.49`, the real *total*, giving `total_amount=49.77` — still wrong, just
   differently wrong) and makes **zero net difference** on the 13-bill ground-truth set
   (`total_amount` stayed at 7/13 before and after, same 7 bills passing both times). Reverted —
   confirmed `git diff` is empty, no trace left. Unit tests were clean throughout (34/34, then full
   suite 155 passed/5 skipped after revert), so this was a correctness/effectiveness problem, not a
   stability one.

   This is the same bug *class* as the `img2.jpeg` "2,665 pcs picked instead of 769.230" mixup in
   §1. **A real fix needs genuine position-aware column assignment** (N labels → N numbers by
   column order) for this specific "VAT-breakdown row" pattern — similar in spirit to how
   `line_items.py` already does `decimals[0]`/`decimals[-1]` positional assignment for table rows,
   but scoped narrowly to this exact-tie case rather than the general candidate-pairing logic that
   was already found harmful when done broadly. Genuinely out of scope for a quick follow-up;
   needs its own properly-planned investigation.

3. **Vendor on garbled/handwritten headers — not an extraction-logic bug.** Confirmed the raw OCR
   text itself doesn't contain a clean vendor name in these failures (the garbled text is genuinely
   all OCR produced) — this is an OCR-engine read-quality limitation, matches the historical doc's
   finding, and isn't fixable by changing extraction/selection logic.

## 6. New sample batch (`assets/multi_line/img{21-27}*.png`): 2 more root causes found and fixed

User added 9 new real multi-item bills (invoices and delivery notes from 2 vendors: Jannat Al
Naeem Building Materials, Rainbow Led & Display, Blue Rhine General Trading, plus a second Bab Al
Hayat Pharmacy bill). Ran the real production pipeline (`OcrService.run()`) against all of them.
Most under-extracted severely (1 item found on bills with 7-13 real items). Traced root causes by
dumping actual OCR geometry/line data and replaying `extract_line_items`'s table-detection logic
against it (not guessing from final output alone).

### Root cause: bare label-vocabulary words end the table mid-item

`_is_end()` (`line_items.py`) treats a row as end-of-table if it matches any `LabelConcept` in
`_END_CONCEPTS` (`CARD`, `CASH`, `VAT_TAX_AMOUNT`, `DISCOUNT`, ...), matched via
`label_vocabulary.yaml` with **plain substring search, no word boundary** (`labels.py`'s
`match_label_concepts`). Several of those concepts' synonyms are bare, short words: `vat`
(`vat_tax_amount`), `card` (`card`). Any item whose own text happens to contain one of those words
ends the table right there:
- `img 27.png` (13-item pharmacy bill): item 2 is `"ADV MED GUIDANCE CARD..."` → matches `CARD` →
  table ends after item 1. Only 1/13 extracted.
- `img23.png`: item 2 is `"Receiving Card FS-LCE"` → same `CARD` match → ends after item 1.
- `img 25.png`: every row's own Tax Code column literally prints `"VAT_AE:S"` → bare `vat`
  substring match on every item row → table truncates after item 2 of 4.

**Fix:** `_is_end()` now only lets an `_END_CONCEPTS` match end the table when no real word
appears before the match on that line (`_is_end_concept_match`) — a genuine summary/footer row
leads with its own label (`"CASH 49.25"`, `"VAT@ 5%"`, optionally after a leading SI number); a
concept word first appearing after real product text is the word occurring inside real item data,
not a table-end marker. The literal-keyword branch (`_END_WORDS`/`_SUMMARY_ROW`) is untouched.

### Root cause: integer-only quantities are invisible to the row parser

`_DECIMAL` only matches numbers **with a decimal point**. Many invoices print quantity as a bare
integer with a unit suffix (`"50 Pcs"`, `"1,000 Pc"`) while Rate/Amount have decimals. Since
`_amount_and_qty` takes `decimals[0]` as quantity when 2+ numbers are found, and the true quantity
never enters `decimals`, **the Rate column gets mistaken for the quantity** instead (`img 21.png`:
real qty 50, extracted qty 4.73 — that's the Rate). It's also why pure quantity-only delivery
notes extract near-garbage: with no decimal numbers present at all, `has_numbers` is false for
every real row.

**Fix:** new `_QTY_UNIT` regex + `_leading_qty_match()` captures a leading bare-integer quantity
with a known unit suffix (`pcs/nos/mtr/kg/ctn/box/unit/ea/ltr/...`), separately from the
decimals list, only when it's the first real content on the row (not buried after other words —
see below). `_Row.int_qty` carries it through; `extract_line_items` prefers it over
`decimals[0]` when present. `_Row.has_numbers` now also considers `int_qty`, so pure
quantity-only rows are recognized as items at all. A row whose only "description" turns out to be
the bare unit word itself (`"Pcs"`) now has its description cleared so it can rejoin with the real
product name sitting on an adjacent OCR line instead of keeping the unit word as the final name.

### Verified result (CPU path, ground-truth ratio): `img23.png` 1/7 → 7/7 items, `img 27.png`
(13-item pharmacy) 1/13 → 12/13 items. Field-level accuracy on items that do extract: amounts
right ~70-80% of the time, quantities ~40-55% (still the weaker field — see §7).

### Two new false-positive side effects found and fixed (bounded)

The `int_qty` capture above, while a net strong win, introduced 2 new phantom line items:
1. `img 21.png`/`img 22.png`: a wrapped packing-note footnote (`"1 PKT PER 400 PCS"`, `"75 PKT X
   400 PCS = 30000 PCS"`) matched `_QTY_UNIT` on its own `"400 PCS"` and surfaced as 2 fake items.
   **Fixed**: `_leading_qty_match()` only accepts a match with no real words ahead of it on the
   line — the footnote's quantity is buried after `"PKT PER"`/`"PKT X"`, so it's skipped.
2. `img26.png`: a delivery note with **no totals/VAT row at all** never trips `_is_end`, so
   `body_lines` scanned to the bottom of the page and picked up a date glued into one decimal by
   OCR (`"2026 12:56"` → `"2026.12"` via `_SPLIT_DECIMAL`) in the signature block, surfacing as a
   fake trailing item. **Fixed**: a geometric (not keyword-based) safety net — once a huge
   vertical gap (5x the median row height, floor 80px) opens up after the last real item, the rest
   of the body is treated as footer, not more items. Chosen over a keyword-based fix specifically
   to avoid the failure mode the two reverted attempts in §5 ran into (fragile against OCR noise,
   or colliding with legitimate same-bill patterns) — a large vertical gap is a purely structural
   signal, unrelated to either of those.

Both confirmed fixed via direct re-test against the specific bills that produced them, zero new
regressions in the full test suite (155 passed / 5 skipped, same 8 pre-existing unrelated
failures throughout all of this session's changes).

## 7. Still open after this session

- **Row-shift on dense multi-column invoices** (`img23.png`, `img24.png`, `img 25.png`'s 9-column
  table): values from one item occasionally land under the adjacent item's description. Same
  underlying gap as §4's `img2.jpeg` issue and §5.2's VAT-breakdown-row issue — `_merge_row_fragments`
  has no real concept of table columns, only y-proximity + left-to-right reading order. A proper
  fix needs column/x-band detection: cluster the table's money-value x-positions (from the header
  row's cell boundaries, or the decimal tokens themselves) to learn where each column actually
  sits, then assign fragments to rows by x-band membership, not just reading order. Scoped out of
  this session — real rewrite risk to the simple 3-column bills that already work well
  (`img27.png` at 83% fully-correct), needs the full fixture suite plus all sample bills re-checked
  before trusting it.
- **Quantity is the weakest extracted field** (~40-55% correct vs ~70-80% for amount) — mostly a
  downstream symptom of the row-shift issue above on complex layouts.
