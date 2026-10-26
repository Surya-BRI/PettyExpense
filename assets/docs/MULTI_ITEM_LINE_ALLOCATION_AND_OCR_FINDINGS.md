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

   **Follow-up (later session): tried, found unsafe on the real bill, reverted.** Added
   `_positional_money_candidates()` in `extraction/candidates.py` — same word-geometry-by-x-
   position technique as `line_items.py` §7, scoped to engage only when a row's `tiered_matches`
   come from one source line, map to distinct money concepts, and their count matches the count
   of usable number tokens on the value row (1:1, later relaxed to allow exactly one unlabeled
   leftover number, to tolerate a header missing one garbled label).

   **Synthetic test passed cleanly:** a `Subtotal`/`VAT` header line above a `45.21 2.28` value
   line (mirroring the bug's description) resolved correctly — `amount=45.21`, `vat_amount=2.28`
   — where the old cross-product tied both to `45.21`.

   **Real-bill test (`image (4).png`, live RunPod→CPU fallback) found a worse failure mode.**
   Dumped the actual OCR geometry: this bill's true single logical row (`"45.21 2.28 47.49"`)
   is itself fragmented by the OCR engine into **three separate `OcrLine`s** — `"5."`, `"45.21"`,
   and `"2.28 47.49"` (the last a case of two numbers sharing one detected word box, which also
   needed a separate proportional-interpolation fix to even get distinguishable x-positions
   within it). `_money_field_candidates` evaluates tokens per-line, so on the `"2.28 47.49"`
   fragment alone the function saw exactly 2 labels (`Subtotal`, `VAT`, from the header above)
   and exactly 2 tokens — a clean-looking 1:1 match — and confidently paired
   `Subtotal↔2.28, VAT↔47.49`. Both wrong: the real `amount` (`45.21`) was never in view, since
   it lives on a sibling fragment this per-line function has no visibility into. Confirmed this
   isn't specific to this session's "allow one extra token" relaxation — the original strict
   1:1-only version would fire identically wrongly here too, since 2 labels/2 tokens satisfies
   strict equality just as well. Net real-bill result: `amount=2.28, vat_amount=47.49,
   total_amount=49.77` — a new, *confidently* wrong answer (not an improvement on the pre-fix
   arbitrary tie).

   **Root cause, for a real future fix:** operating line-by-line is fundamentally insufficient
   once OCR fragments one physical row into multiple `OcrLine`s (apparently common on this bill,
   independent of the original "missing Total label" problem this session set out to fix). A
   correct fix needs to reconstruct the full row first — gather tokens from every line that's
   part of the same visual row (via the existing `_same_row`/`_nearest_aligned_line_above`
   geometry, already computed here for labels but not for tokens) before doing positional
   assignment — i.e., genuine row reconstruction similar in spirit to `line_items.py`'s
   `_merge_row_fragments`, not a per-line patch. **Reverted** (`extraction/candidates.py` back to
   its pre-session state, confirmed via `git diff`) rather than ship a fix that trades a known,
   bounded-wrong tie for a new, confidently-wrong failure mode on the one real bill available to
   test against. Scoped out of this session; §5.2's bug is still open.

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
- `mage.png` (13-item pharmacy bill): item 2 is `"ADV MED GUIDANCE CARD..."` → matches `CARD` →
  table ends after item 1. Only 1/13 extracted.
- `img23.png`: item 2 is `"Receiving Card FS-LCE"` → same `CARD` match → ends after item 1.
- `amer.png`: every row's own Tax Code column literally prints `"VAT_AE:S"` → bare `vat`
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

### Verified result (CPU path, ground-truth ratio): `img23.png` 1/7 → 7/7 items, `mage.png`
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

## 7. Column/x-band number selection for dense multi-column invoices (implemented, bounded win)

Real word-level geometry on `amer.png`'s 9-column table (dumped and inspected directly) turned
out very clean: each column's x-position clusters within ~15px across all 4 rows. That makes
column-band detection viable without a full table-layout rewrite -- implemented a bounded version
scoped to just the two fields the API actually needs (`quantity`, `amount`), not a general column
parser:

- `_header_column_x()` scans the header row's own word geometry for the Qty cell (leftmost match)
  and the row's real Total cell (rightmost "total"/"amount" match -- a wrapped header like this
  one has several "...Amount" columns; the grand total is reliably the rightmost). Scans the full
  header-to-first-item span, not just the recognized header cluster, since a stray column label
  with no qty/rate word of its own (a lone "AMOUNT"/"TOTAL" fragment) doesn't match `_is_header`
  by itself and would otherwise be missed.
- `_nearest_column_number()` then picks, per body row, whichever of that row's own words sits
  closest (within `3x` the median line height) to each learned column x -- read directly off
  geometry instead of guessed from decimals[0]/decimals[-1] reading order.
- Only engages when real word bounding boxes exist (same guard the existing merge logic already
  uses); geometry-less sources (plain-text fixtures) are unaffected -- confirmed via the full test
  suite, unchanged at 155 passed / 5 skipped / same 8 pre-existing failures.

**Result: net positive, not a clean sweep.** Four confirmed fixes against real bills: `img23.png`
item 1 amount `3.75` -> `3750.60` (was reading the VAT% column); `amer.png` item 1 amount
`1.449` -> `1449.00` (a factor-of-1000 decimal bug); `img26.png` quantity on all 4 items
`None` -> correct (previously the real value only appeared, mislabeled, in `amount`); `mage.png`
item 3 quantity `None` -> `5.0` (now fully correct, was amount-only before). Two new wrong-pairings
appeared alongside these (`img23.png` item 5's amount pulled in a neighboring row's value;
`mage.png`'s item 6/7 merged row kept a wrong description against a now-different, also-wrong
number) -- both are the *same already-broken row* as before, just wrong in a different way, not a
new failure mode; no item count regressed anywhere. Kept rather than tightening the x-tolerance to
suppress them, since that would trade back genuine wins to patch cases that stay wrong either way.

## 8. Still open after this session

- **Row description/number pairing on dense multi-column invoices** is the real remaining gap
  behind both of §7's new mismatches and the original row-shift problem (`img23.png`, `img24.png`):
  `_merge_row_fragments` still has no real concept of table columns for deciding which OCR
  fragments belong to the *same row* -- only y-proximity + left-to-right reading order. §7's fix
  only chooses the right number once a row's boundary is already (possibly wrongly) decided; it
  doesn't fix the boundary decision itself. A proper fix needs column-aware row reconstruction:
  assign every fragment to a row by both its y-band and which x-band its pieces fall in, not just
  reading order. Bigger rewrite than §7, real regression risk to the simple 3-column bills that
  already work well (`img27.png` at 83% fully-correct) -- needs the full fixture suite plus all
  sample bills re-checked before trusting it. Scoped out of this session.
- **Quantity is still the weaker extracted field relative to amount** overall, though §7 narrowed
  the gap on the specific dense-table case it targeted.

## 10. VAT/amount/total: arithmetic-identity detector (implemented, measured on all sample bills)

§5.2's tie bug was finally solved by dropping label/geometry reasoning for tax-summary rows
entirely (the row-fragmentation finding in §5.2 showed geometry is the wrong tool) and using the
accounting invariant instead: on a tax-summary row, `amount + vat == total` and `vat ~= rate *
amount` for a plausible nonzero rate (`ReferenceData.plausible_vat_rates`).

**Implementation (`extraction/candidates.py::_vat_breakdown_candidates`, wired into
`generate_candidates`):**
- Row = a line plus its `_same_row` neighbours, so OCR fragmenting one row across several
  `OcrLine`s no longer matters. Collects decimal tokens (2-6 distinct values).
- Requires a **rate cue** (a printed `5%`, or a VAT-concept label on the row / the aligned line
  above / the previous text line when there is no geometry) so unrelated number pairs can't match.
- Tries every pair (x < y) as (vat, total) or (amount, total) with the third value derived from the
  difference, and accepts it only if `|vat - rate*amount| <= max(0.03, 0.0012*amount)`. Needs only
  **2 of the 3 numbers to read cleanly**: `image (3).png`'s amount cell read as `4u.84`, but
  `49.18 - 2.34 = 46.84` and `2.34/46.84 = 4.996%`, so it is recovered.
- Several different readings -> prefer one whose three numbers were all printed; still ambiguous ->
  emit nothing (falls back to the pre-existing behaviour).
- Emits `amount`/`vat_amount`/`total_amount` candidates tagged `vat_breakdown_arithmetic` (and
  `derived_from_breakdown` for a recovered value). `scoring.py` gives the tag +0.42;
  `select.py` ranks a verified candidate above unverified ones, and breaks ties *between* verified
  triples (stacked receipts, e.g. `image (6).png`) by "lower on the page" -- the same prior scoring
  already uses -- because arithmetic reconciliation saturates both at the 1.0 confidence cap.

**Results** (cached CPU-RapidOCR words, so old/new differ only in extraction):

| Metric | Before | After |
|---|---|---|
| Ground truth `amount` (11 bills with truth) | 5/11 | **8/11** |
| Ground truth `vat_amount` | 3/7 | **6/7** |
| Ground truth `total_amount` | 6/11 | **8/11** |
| Arithmetic-coherent output (amount+vat=total, 2-20% rate), all 38 sample bills | 14 | **28** |
| Bills that went coherent -> incoherent | | **0** |

All 7 printed bills with ground truth are now fully correct (`image (2)`-`(6)`, `enoc_test`). The
remaining ground-truth misses are the handwritten KSA slips, where the digits never reach the OCR
text at all -- not fixable in extraction. `enoc_test.jpg` `amount` (6.00 -> 5.71) was fixed as a
side effect. Tests: `tests/test_vat_breakdown.py` (5 cases from the real rows, incl. a no-cue
negative and a non-reconciling negative); suite 160 passed, same 8 pre-existing failures.

**Bugs the all-bills sweep caught in my own first versions (worth remembering):** a 0.3%-of-amount
tolerance let a spurious `(4.17, 83.37)` pair through and the ambiguity guard then suppressed the
real triple; and a global y-position tie-break picked `vat=10.0` over `0.48` on one bill -- fixed by
restricting the tie-break to verified triples. Checking only the 4 target bills would have shipped
both.

**Still open:** `multi_line/amer.png`, `mage.png`, `img27.png` (dense multi-item invoices) still
produce incoherent totals before and after; their summary rows don't follow the single-rate
5% pattern this detector targets.

## 11. Case study: hand-filled AL MANAR invoice (single and multi-item both wrong) -- 5 root causes

Reproduced from the emulator: the app showed `amount 5.71 / vat 0.29` and the multi-item screen a
one-line item. The captured image was pulled from the debug app's cache
(`adb exec-out run-as com.expense.expense_app cat ...`; use `exec-out`, plain `shell` corrupts
binary via CRLF) and run through the real `OcrService.run()` (RunPod first). True figures:
330.00 / VAT 5% 16.50 / Grand Total 346.50, bill no 22860, date 06.07.2026.

| # | Root cause | Evidence | Fix |
|---|---|---|---|
| 1 | Hand-filled totals lose decimals / garble digits: `Total 330`, `VAT 5%` + `16 so`, `Grand Total bE 6`. The lone `6` won as the total; the existing inclusive-VAT rule then split 6.00 at 5% into 5.71 / 0.29 (coincidentally identical to the ENOC receipt, which is also 6.00). | RunPod text | `_stacked_totals_candidates`: subtotal line + printed `VAT r%` line => `vat = subtotal*r`, `total = subtotal+vat`. Accepted only when the garbled VAT reading (or grand total) agrees within 1 -- so an unrelated pair can't invent numbers. |
| 2 | Fields are selected independently, so impossible triples survive (VAT >= total, total < amount, `amount = -10.0` from `total - vat`). | 10 of 38 sample bills incoherent | `select._enforce_arithmetic_consistency`: when picks don't reconcile, take the best reconciling triple *already among the candidates* with a plausible tax rate (or zero VAT), flagged `resolved_by_arithmetic_consistency` for review. Derived `amount` must be > 0. |
| 3 | `normalize_text` rewrote `No. 22860` as `N0.22860` (rule meant for `AEDO.29`), destroying the `invoice no` label, so the bill number was blank. | `inv2.py` trace | O->0 repair now only for an uppercase O after 2+ uppercase letters. |
| 4 | The TRN (`TRN100362941500003`) on the same line tied with / beat the real number. On the sweep, **5 bills were reporting a 15-digit TRN as the bill number**. | sweep diff | Tokens belonging to a TRN label are never invoice-number candidates. |
| 5 | Year misread `06.07.1016`; no year plausibility check existed anywhere. | RunPod text | `_check_year`: year outside [this-6, this+1] is penalised, and repaired to this/last year only if exactly one is within 2 digit positions of the OCR text. |

Also found and removed: I had defined `_nearest_aligned_line_below` a second time, silently
overriding the original (which only scans later lines) and changing ID-candidate behaviour.

**Measured on the 38-bill sweep (cached CPU OCR), original code vs now:**
amount+vat=total coherent **14 -> 33**; five TRN-as-bill-number errors fixed; ground truth unchanged
(amount 8/11, vat 6/7, total 8/11 -- already at the printed-bill ceiling); 0 coherent->incoherent
regressions. AL MANAR bill: RunPod and CPU OCR both now give 330.00 / 16.50 / 346.50, bill no 22860,
date 06.07.2026. Tests: 170 passed, same 8 pre-existing unrelated failures.

**Considered and rejected:** gating totals on the sum of extracted line items. Item sums are not a
reliable reference (e.g. image (3): items sum 12.18 vs real total 49.18; image (4): 96.49 vs 47.49).

**Still not fixable in extraction:** the handwritten item description (`wifh ap 1nreR.`) -- OCR noise
from handwriting; the user must retype it. Quantity 30 and amount 330.00 do come through.

### 11.1 Bill-number hardening (found by auditing every bill's chosen bill number against its source line)

After the TRN fix, a sweep of what the bill-number field actually returned on all 38 sample bills
showed ~8 clearly wrong values. Root cause: `_id_candidates` lends an "invoice no" label from a
neighbouring line to *any* number-like token, so addresses, phone/fax lines, ISO numbers, bank
accounts, delivery notes, IBANs, e-mail names and date fragments all won. Fix (`candidates.py`,
`scoring.py`):
- Reject by shape: phone numbers (`05xxxxxxxx`, `+971 ...`, tokens after Tel/Mob/Fax), `SAR72`-style
  currency+amount, IBANs, e-mail local parts, >=14-digit TRN/barcode runs, words with one stray digit
  (`Invo1ce`, `Telbole6`).
- Reject by context: preceded by tel/phone/fax/bank/a-c/iso/PO box/delivery note/date, followed by
  street/road/near/building, or prefixed `CUST-`/`LPO-`.
- **Prefer the number printed beside its own label** (`adjacent_to_label`, +0.12 in scoring). A number
  borrowed from a neighbouring line's label must also have a strong invoice shape (separators,
  letter+digit mix, or 7+ digits), so a bare `3810`/`7905` is dropped.

Result on the 38 sample bills: wrong values removed (phone numbers, `SAR72`, `Telbole6`, `Invoice`
misreads, `9001` from "ISO 9001", bank account `1015789510401`, `Tel:+971 547578173`, IBAN, e-mail name),
and labelled numbers that were hidden behind them now surface: `INV-DIP-112954`, `ECR0045786`,
`PEN91473`, `000POSDIP2000039678`; `Bill No` bills went from ambiguous to confident (0.62 -> 0.85).
12 bills now return a value (was 23, but ~11 of those 23 were wrong), 11 of the 12 verified plausible by
source line; `BR-TZ231` (a product code near a borrowed label) is still wrong. Amounts, VAT, totals and
dates are byte-identical before/after this step. Known loss: `ksa1` `92375` (an Arabic-labelled
number next to a misspelled label) is no longer returned.

### 11.2 Arabic coverage check of this session's changes

Tested on Arabic-label / Arabic-Indic-digit / Hijri inputs (the repo has no real Arabic multi-item
sample, so these are synthetic): single-item totals, stacked-block derivation (incl. dropped decimals),
bill number and the `٫`/`٪` separators all work with Arabic labels (48 Arabic label synonyms already
existed; the new detectors reuse them). Two things were found and fixed: (1) my year-plausibility check
penalised Hijri years (1447 AH), dropping a Hijri-only date's confidence 0.67 -> 0.37 -- years 1300-1500
are now exempt; (2) Arabic unit words (`قطعة`, `كجم`, `علبة`...) and Arabic Qty/Amount header words were
missing from `line_items.py`, so a row like `2 قطعة قلم 5.00 10.00` took the rate as the quantity -- added
(line items identical on all 38 sample bills, so English behaviour is untouched).

**Still open (needs a real sample to do safely):** a fully right-to-left item table, where the amount
column is physically leftmost (`10.00 5.00 2 قلم`), yields **no items** -- the row parser assumes
description-first / quantity-before-amount. Also, with geometry-less input quantity is read as the rate
when the description precedes the quantity (English too); real bills use column geometry which mitigates it.

## 9. Editor UI: paginated item cards + quantity sanity nudge (in progress, uncommitted)

With real multi-item bills now extracting correctly (up to 12-13 items, §6-7), the claim editor's
`LineItemsEditor` (`lib/src/features/claims/line_items_editor.dart`) needed to actually handle that
many lines well -- stacking a dozen+ full item cards in one scroll was unreasonable, especially on
the pharmacy/hardware bills this session's OCR fixes specifically targeted.

**What changed (not yet committed):**
- `LineItemsEditor` converted `StatelessWidget` -> `StatefulWidget`, now shows **one item card at a
  time** with Previous/Next (`PhosphorIcons.caretLeft/caretRight`) and an "Item N of M" counter,
  instead of a stacked list.
- Add/remove now re-navigate to the sensible slot: adding jumps to the new last item, removing
  lands on whatever slid into the removed index (or steps back if the last item was removed) --
  both rely on `lines` being the same `List` instance the parent mutates in place, so
  `lines.length` already reflects the change by the time `onAdd`/`onRemove` return.
- New `LineItemDraft.quantityLooksOff` getter: flags a line (orange border + inline warning text)
  when its parsed quantity is non-integer. Rationale: a real counted quantity (pieces, boxes,
  units) is almost always whole; a fractional one is the same OCR failure mode chased all through
  §2-§7 above (Rate or VAT% column misread into the Qty field) now surfaced as a user-facing nudge
  rather than a silent wrong value. Non-blocking -- genuinely fractional quantities (metres, kilos)
  exist, so it's a double-check prompt, not a validation error.

**Status:** implemented, not yet tested against the app running end-to-end on an emulator or
committed. Natural next step once verified: confirm add/remove navigation against a real 12+ item
bill (e.g. `mage.png`'s pharmacy case) and commit.

## 12. Real Arabic bills (`assets/ksa/*.png`): crash fix, vendor/money bugs, OCR-engine dead end

Follow-up session specifically auditing the 6 real KSA bills (`ksa1/3/4/5/8/9.png` -- `ksa2/6/7`
referenced in the old `scripts/ocr_results.csv` no longer exist in the repo). All work below is
**uncommitted** (`candidates.py`, `scoring.py`, `label_vocabulary.yaml`).

### Crash: Arabic text after a number broke extraction outright

`extraction/candidates.py::_looks_like_non_money` checked `after[:1].isalpha()` (Unicode-aware --
true for Arabic letters too) then matched the tail with `re.match(r"[A-Za-z]+", after)` (ASCII-only)
and called `.group(0)` unconditionally. A number glued directly to Arabic text with no space (e.g.
a number immediately followed by `ريال`) made the regex return `None`, crashing with
`AttributeError`. Hit on `ksa4.png`. **Fixed**: tail regex changed to `r"[^\W\d_]+"` (any Unicode
letter), with a `None`-safe fallback. This bug was introduced by this session's own earlier
uncommitted changes, not present in committed history.

### Vendor: generic document titles and screenshot UI chrome mistaken for the business name

`"Ride details"` (Uber app screen title), `"Tax Invoice"`, `"Delivery Note"`, `"Credit Note"`,
`"Customer Invoice"` and its real OCR misread `"Customer Invoise"` (c/s confusion, seen verbatim on
`ksa1.png`) were all winning as the vendor candidate over the real business name. **Fixed**: new
`_DOCUMENT_TITLE_RE` in `candidates.py` (short, <=3-word lines ending in
details/summary/receipt/invoice/invoise/history/note/slip/voucher/statement) excludes these from
vendor eligibility -- generic document/screen chrome, not vendor-specific.

**Known-vendor substring matching added** (`_vendor_known_match_bonus` in `candidates.py`,
`scoring.py`'s `_reference_match_weight`): previously a vendor candidate only scored a bonus on a
>=0.85 whole-line similarity match against `reference_data.known_vendors`. Real app-receipt
screenshots embed the brand mid-sentence ("UberX Saver reserve", not "Uber" alone), so added a
narrow second candidate-generation pass scanning past the normal header window specifically for a
known-vendor name as a substring/word match. Verified on `ksa8.png`/`ksa9.png` with a synthetic
`known_vendors=("Uber",...)` -- correctly picks `"UberX Saver reserve"` /
`"UberX Saver ride with"` over `"Ride details"`.

**Important caveat, confirmed by direct DB query:** this fix is currently dormant in practice.
`ERP-Dev`'s live `ErpExpenseVendor` table has only 19 active vendors (several with data-quality
issues -- a phone+email glued into one name field, a bare `"TRADING L.L.C"` fragment, a test record
`"Zylo Test Vendor Alpha 9931"`), none of them Uber/Careem/Talabat or any app-based vendor. Checked
the real production server too (`ERP-Live`, 65.2.162.104) -- it has 792 tables but **zero**
containing "Expense" or "Vendor" in the name anywhere; this app's entire schema
(`ErpExpenseVendor`, `ErpExpenseTransaction`, etc.) was created by this codebase's own
`init_db()`/`Base.metadata.create_all()` against `ERP-Dev` only and has never been migrated to the
real production ERP. So right now `ERP-Dev` isn't a test copy of production data -- it's the only
place this app's data exists at all.

### Money: a handwritten location/zone code misread as the amount

All three handwritten taxi receipts (`ksa1/3/5.png`) share the same rider's habit of writing a
Riyadh business-district code (`"KAFD 2.08"`, `"KAFD208"`) on the notes/from-location line. That
decimal number was winning as the extracted `amount` -- e.g. `ksa1.png` returned `208.0` (from
"KAFD **2.08**"), wildly wrong vs. the real ~45 SAR fare. **Fixed**: `_looks_like_non_money` now
also rejects a decimal number immediately preceded by a short (2-6 letter) all-caps code word
(`_ZONE_CODE_PREFIX_RE`), *unless* that word is a currency code ("SAR 45.00") or a recognised money
label on the same line ("VAT 5.00", "CASH 45.00") -- both legitimate. Took two iterations: the
first version had no label-context exception and broke `test_tax_exclusive_total` (`"VAT 5.00"`
looks identical in shape to `"KAFD 2.08"` -- short caps word + space + decimal). Fixed by threading
`label_matches_by_line[i]` into the check and only suppressing when the prefix word isn't itself a
recognised label span.

Net effect on the 3 bills: `ksa1` 208.0 -> 51.0, `ksa5` 2.09 -> 1.0 -- the false zone-code pick is
gone, but the *real* handwritten amount (45 / 40 / 50) still isn't recovered, because those digits
never form a clean parseable decimal anywhere in the OCR'd text (`"45+"`, `"40f"`, `"50/1"` are all
malformed as numbers). This is a genuine bug fix (stops a wrong-but-specific-looking number from
being reported with false confidence) but not a full recovery -- consistent with this doc's
existing conclusion (§5) that handwriting is an OCR-engine read-quality ceiling, not an
extraction-logic gap.

### Money: "Amount"/"Fare" were never recognised as English money labels

Real, generalisable vocabulary gap found while chasing `ksa3.png`'s amount: `label_vocabulary.yaml`'s
`subtotal` concept had `"المبلغ"` (Amount) and `"الأجرة"` (Fare) in Arabic, but no plain English
`"amount"` or `"fare"` synonym at all -- despite these being extremely common English column
headers. **Fixed**: added `amount` and `fare` to `subtotal`'s synonym list. Safe because
`match_label_concepts`'s `_suppress_shorter_overlapping_matches` already prefers longer/more-specific
matches on overlap, so this doesn't disturb `"VAT Amount"`/`"Paid Amount"` (already separate,
longer, multi-word entries under their own concepts).

Confirmed via direct candidate-generation trace on `ksa3.png`: before the fix, the real "Amount"
column cell (`"40f"`, OCR misreading a handwritten `/` as `f`) generated **zero** candidates since
its header literally wasn't recognised as a label. After the fix it generates a real `40.0`
candidate at confidence 0.835 -- but a near-duplicate bilingual-OCR-pass reading of the same
physical row (`"409 KAFD208 29-6-26"`, the Arabic pass's garbled full-row merge) scores 0.838 and
edges it out by ~0.003, a noise-level margin. **Not fixed** -- this is the same class of bug this
doc's §5.2 already flagged as open and twice attempted/reverted for regressions (collapsing
duplicate bilingual-OCR-pass row readings is subtle; a naive dedup-by-overlapping-box rule breaks
the legitimate case where the same row is deliberately read twice and needs real dedup, not blind
suppression). Deliberately not reattempted this session given that history.

### Dead end investigated and explicitly rejected: swapping the OCR detector model

Hypothesis: the shared text-detection model (hardcoded `PP-OCRv6 + SMALL` in
`services/ocr_service.py::_REC_ENGINE_CONFIG`/`_get_rapid_engine`) might be missing/merging faint
handwritten strokes that a larger model would catch. Confirmed Arabic *recognition* has no larger
variant to upgrade to (RapidOCR only ships `arabic_*_rec_mobile` for both PP-OCRv4 and PP-OCRv5 --
no `_server` recognition model exists for Arabic). But detection does have a larger `PP-OCRv5_det_server`
option available as a drop-in config swap.

**Tested directly** (controlled A/B, same recognition/retry logic, only the detector config
varied) against all 4 bills with ground-truth-ish values: mixed result, including a real
regression --

| Bill | Field | Current (v6 small det) | v5 server det |
|---|---|---|---|
| ksa1 | amount | 51.0 | 4.51 (closer to real ~45, plausible win) |
| ksa1 | vendor | `شركة الشارقة` (clean) | `عامة أجرة الشارقة شركة` (word order scrambled) |
| ksa3 | amount | 0.01 | 1.0 (still wrong either way) |
| ksa4 | amount | **55.0 (correct)** | **1.0 -- regressed a previously-correct value** |
| ksa5 | vendor | clean | gained stray garbage text ("asle") |

Also ~1.8x slower per bill (2.1s -> 3.8s). **Rejected** -- the larger detector finds text in a
different reading order that the geometry-dependent logic (vendor multi-line merge, same-row
alignment, `_nearest_aligned_line_above`) isn't tuned for; one plausible win is outweighed by one
clear regression and broad quality loss on vendor text. Detection changes have page-wide blast
radius (shared by English and Arabic both, affects every bill not just Arabic ones) -- not a safe
drop-in upgrade on this evidence. Conclusion: there is no available OCR-engine-level lever left to
pull for Arabic specifically (recognition has one model size, the alternative detector trades bugs
rather than strictly improving) -- further gains have to come from extraction-logic fixes
downstream of OCR, same as everything else in this document, not from swapping engines/models.

**Full regression status throughout this section's changes:** 203 passed, same 8 pre-existing
unrelated failures (`test_claim_line_items.py`'s missing-`bill_number`-kwarg fixture bug, see §2),
0 new regressions.
