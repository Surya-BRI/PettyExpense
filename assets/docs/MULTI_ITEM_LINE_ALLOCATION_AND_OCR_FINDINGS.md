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

## 3. Bigger finding: the fix above may not run in production at all

`services/ocr_service.py` tries **RunPod GPU OCR first**, falling back to the CPU/RapidOCR
pipeline above only on RunPod failure/timeout. Tested via the actual Flutter app
(Android emulator) against `img2.jpeg`: **line items still came back empty**, Bill number was
blank, and currency went undetected — none of which matches the CPU-path test results above.

Root cause: **RunPod's response is plain text only, with no bounding boxes at all.**
`_run_runpod_ocr()` builds `OcrLine`s via `words_from_text()`, which treats each full printed
line as one atomic "word" with `bounding_box=None` — there is no per-word geometry to
reconstruct a table from. `extract_line_items()` was briefly wired up to the RunPod path during
this investigation and produced garbage (header labels paired with random nearby numbers via
list-order-proximity pairing); this was reverted — `parsed["line_items"] = []` is left explicit
on that path, with a comment explaining why, rather than emitting wrong suggestions.

**This means today's fix only helps when the CPU fallback actually runs** — which, per
`.env`'s `RUNPOD_ENDPOINT_ID` being configured and RunPod evidently succeeding in this dev
environment, is apparently not the common case.

### RunPod worker investigation

- Endpoint: RunPod Serverless, name `arbaic`, ID `ze0kdoq723wbrh` (confirmed matches
  `.env`'s `RUNPOD_ENDPOINT_ID`).
- Docker image: `teja060803/paddle-onnx-runpod:v1.5.1` — a custom-built image (not a
  stock/third-party one), per `console.runpod.io`.
- **The worker's handler source is not in this repository.** Searched the whole repo
  (excluding `.venv`/build dirs) for any `Dockerfile`, `handler.py`, or RunPod SDK usage —
  found only `scripts/test_runpod_ocr.py` (a client that *calls* the endpoint, not the
  worker) and `backend/scripts/ocr_compare/paddle_vl_local.py` (an unrelated local benchmark
  referencing a different machine's path, `C:\Users\Tej\ocrs\paddle-vl-venv`). The actual
  handler code that builds the Docker image is apparently not checked into this repo at all.

### Separately relevant: prior accuracy finding

`OCR_ENGINE_EVALUATION.md`'s existing RunPod-vs-CPU comparison (2026-09-18, 9 real KSA images)
already found RunPod **worse** overall — "RunPod frequently drops digits," "dates... RunPod
nailed effectively 0/7 cleanly," vendor roughly a wash — and explicitly left open
*"whether RunPod should stay first in the try-order... since success ≠ better data."*
That question is still open.

### Open decision (not yet acted on)

Two live options, not yet chosen between:
1. **Demote/skip RunPod** in `ocr_service.run()` so scans (at least multi-item ones, maybe
   all) go to CPU OCR directly — small, contained change here, immediately unblocks both
   this session's line-item fix and (per §3's prior-accuracy note) may improve other fields
   too. Loses RunPod's speed advantage.
2. **Add bounding boxes to the RunPod worker's output** — would let line items work on the
   faster GPU path too, but requires locating/recovering the handler source (not in this
   repo) and rebuilding/redeploying the Docker image — materially bigger, currently blocked
   on finding that source.
