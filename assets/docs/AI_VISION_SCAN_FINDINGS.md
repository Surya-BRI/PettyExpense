# AI vision scan (ChatGPT) — findings, design and open items

> **Status: GPT is the only live scan pipeline (2026-10-26).** gpt-5.4-mini won the benchmark
> against Indra/RapidOCR and against self-hosted Qwen3-VL (§3, §9, §10). Camera and gallery
> both call GPT. The app shows "Scanning…" only — no ChatGPT / OpenAI wording. Self-hosted
> Qwen stays in code (`AI_VISION_PROVIDER=runpod`) but is not the production path.

Session record, 2026-10-22 → 2026-10-26. Covers why a vision LLM was evaluated, how it was
benchmarked against the existing OCR pipeline and Qwen, the full `assets/multi_line` re-run,
and the switch to GPT-only. Related history:
[OCR_ENGINE_EVALUATION.md](OCR_ENGINE_EVALUATION.md),
[MULTI_ITEM_LINE_ALLOCATION_AND_OCR_FINDINGS.md](MULTI_ITEM_LINE_ALLOCATION_AND_OCR_FINDINGS.md).
Raw per-bill caches: `backend/scripts/ocr_compare/llm_results/`.

## 1. Why

Both earlier findings docs reach the same ceiling: on **handwritten** bills (KSA taxi slips) the
digits never reach the OCR text in usable form (`45+`, `40f`, `50/1`, `451`), so no extraction rule
can recover them. A larger detector model was tried and rejected (§12 of the multi-item doc), and
many heuristic fixes were reverted for regressions. The remaining lever was a model that reads the
**image itself**, not OCR text.

Current production engine for reference (verified in code, `services/ocr_service.py`): **Indra OCR
first, then RapidOCR**, CPU only. RunPod is no longer called — the "RunPod first" statements in
the older docs are out of date.

## 2. Model choice

- Open-source vision models (Qwen3-VL, Gemma 3, …) need a GPU; the prod server (m5.xlarge,
  ~4 GB free, no GPU) cannot host them. Deferred — RunPod serverless is the path if self-hosting
  is wanted later (keeps bills in-house).
- Tested with the existing **OpenAI API key**. 141 models were available on the key; picked
  **`gpt-5.4-mini`** (reasoning model, cheap) with `reasoning_effort=low`.
- Pricing (OpenAI, standard tier, per 1M tokens): input $0.75, output $4.50.

## 3. Benchmark

Tool: `backend/scripts/ocr_compare/llm_vision_compare.py`.
- Plan mode by default (lists bills, **no API call**); `--yes` to send; `--pick` for exact files;
  `--baseline-only` for the free local pipeline only.
- Every API answer cached in `llm_results/<model>/`, so a bill is never paid for twice; the cached
  raw answer is re-mapped on each run, so mapping fixes cost nothing to re-check.
- Scores against `scripts/ocr_results.csv` (hand-verified values) and checks the mapped output
  against the backend / Flutter contract (`_receipt_payload`, `OcrResult.fromJson`,
  `OcrLineItem.fromJson`, `LineItemIn`).
- Report: `llm_results/report_gpt-5.4-mini.md`.

Note: `indra_ocr` is not installed on the dev PC, so "current pipeline" below = RapidOCR only.

### 3.1 Single-value fields (7 KSA bills with ground truth)

| Field | Current pipeline | gpt-5.4-mini |
|---|---|---|
| Vendor | 2/6 | **6/6** |
| Amount | 4/7 | **7/7** |
| VAT | 7/7 | 7/7 |
| Total | 4/7 | **7/7** |
| Currency | 7/7 | 6/7 → fixed (see §6.4) |
| Date | 3/5 | **5/5** |

Handwritten fares read correctly by AI: 45, 45, 40, 55, 50 (current pipeline: 51, 0.01, 1 on three
of them). Uber screenshots: vendor "Uber" (current: "Al Jubaytas", "Riyadh").

### 3.2 Multi-item bills

| Bill | Real items | Current | AI | AI Σ lines = bill total |
|---|---|---|---|---|
| `multi_line/image.png` (Fabricast) | 2 | 0 | **2** | 90.30 ✅ |
| `multi_line/img2.jpeg` (Standard Hardware) | 3 | 0 (total read as 77) | **3** | 769.23 ✅ |
| `multi_line/img23.png` (Rainbow Led) | 7 | 7 (vendor "Emirate : Dubai") | **7** | 4,939.41 ✅ |
| `multi_line/img3.jpeg` (Bab Al Hayat 50A79618) | 12 | 9 (8 in the app, shifted) | **12** | 224.99 ✅ |
| `multi_line/mage.png` (Bab Al Hayat 50A86803) | 13 | 12, **VAT missed** (total 438.91) | **13**, VAT 1.09 | 440.00 ✅ |
| `new_bills/bill_3.png` (Jannat tax invoice) | 11 | 20 (washer lines split off) | **11**, all qty right | 7,787.19 ✅ |
| `new_bills/bill_1.png` (Jannat delivery note) | 11 | 19 | **11** | no prices on a DN |
| `new_bills/bill_2.png` (Jannat delivery note) | 5 | 5 | **5** | no prices on a DN |

Every AI row on `img3.jpeg` and `mage.png` was checked by eye against the image: descriptions,
quantities, row amounts and the per-row **VAT (%)** column (0.00 everywhere except one 5.00 row on
`mage.png`) all correct; bottom labels read correctly (`Net Total Before VAT 438.91`,
`VAT Inclusive 1.09`, `Round Net Total 440.00`).

### 3.3 Cost and speed

15 bills: 24,681 input + 8,008 output tokens → avg **1,645 / 533 per bill**, ≈ **$0.0036/bill**,
avg **5.7 s** (max 8.3 s). Total spent this session ≈ $0.06.

Where the tokens go (avg per bill): prompt + schema ~870 (fixed), image ~780, model reasoning ~226,
JSON answer ~307. Output is two-thirds of the cost. Prompt caching does not kick in (needs a ≥1,024
token prefix; ours is ~870 → 0 cached tokens on every call).

## 4. What was built — "Scan with AI (ChatGPT)"

Employee opts in per bill; the standard Camera / Gallery buttons are unchanged and never send
anything to OpenAI.

```
Add receipt sheet → choose Single / Multiple → "Scan with AI (ChatGPT)" → pick photo
  POST /api/claims/ocr/upload                         (unchanged: S3 + receipt row)
  Confirm screen, engine='ai', "Reading with AI (ChatGPT)…"
  POST /api/claims/receipts/{id}/ocr?engine=ai
    routes_claims.analyze_receipt  (400 if engine not standard|ai; LlmVisionError → 502)
    → transaction_service.analyze_receipt(engine)
    → ocr_service.run(engine="ai") → llm_vision_service.run_llm_vision   (no fallback)
    → OpenAI chat completions (prompt + image + strict JSON schema)
    → to_ocr_service_shape()  — checks/fixes, same dict shape as the normal scan
    → ocr_* columns + raw answer saved in ocr_raw_json (engine "openai_vision"), duplicate check
  Confirm screen fills the form; failure → "Couldn't read this bill" + reason + Retry
```

| File | Change |
|---|---|
| `backend/services/llm_vision_service.py` (new) | prompt, schema, OpenAI call, mapping, `LlmVisionError` |
| `backend/config.py`, `.env.example` | `OPENAI_API_KEY`, `OPENAI_VISION_MODEL=gpt-5.4-mini`, `OPENAI_REASONING_EFFORT=low`, `OPENAI_TIMEOUT_SECONDS=60` |
| `services/ocr_service.py`, `services/transaction_service.py`, `api/routes_claims.py` | `engine` parameter threaded through |
| `lib/src/features/claims/capture_receipt_sheet.dart` | third button, passes `engine: 'ai'` |
| `lib/src/routing/app_router.dart` | forwards `engine` to the confirm screen |
| `lib/src/features/claims/confirm_claim_screen.dart` | passes engine; AI label; hides Auto/English/Arabic selector; 1 attempt (paid call); shows the server's reason |
| `lib/src/api/api_client.dart` | `analyzeReceipt(..., engine)` |
| `backend/tests/test_llm_vision_service.py` (new) | 13 tests, OpenAI mocked |

Decisions made with the user: separate button (not a toggle); on AI failure **show an error**, do
not fall back to the normal scan; no automatic retry.

Deploy note: add `OPENAI_API_KEY` to the prod server's `backend/.env` and restart via pm2;
without it the button returns "AI scan is not set up on the server".

## 5. The prompt (what the model receives)

1. **System prompt** (`PROMPT` in `llm_vision_service.py`): reads UAE/KSA bills in English/Arabic,
   possibly handwritten; rules for vendor (not "Tax Invoice", not a phone clock, app brand for
   screenshots), date as YYYY-MM-DD day-first + Hijri conversion, amount/VAT/total with
   `amount + vat = total`, "45/" = 45, currency from money words (ريال/هللة/Riyal/S.R. = SAR,
   درهم/Dirham/Dhs = AED, city names don't decide), bill number never a TRN/phone/P.O. Box/IBAN,
   every item row with rightmost money column + qty + VAT %, first receipt only, per-field
   confidence, null instead of guessing.
2. **User message**: `"Today is <date>. Extract this bill."` + the image (base64, `detail: high`).
3. **Strict JSON schema** (`response_format: json_schema, strict: true`): `vendor, date, amount,
   vat_amount, vat_percent, total_amount, currency, bill_number, line_items[{description, quantity,
   amount, vat_percent}], line_items_include_vat, confidence{…}, notes`.

Worked example (`mage.png`, 8.3 s, 1,572 / 969 tokens): model returned 438.91 / VAT 1.09 / 440.00,
13 rows, bill 50A86803, date 2026-09-11, confidences 0.90–0.99, note
"totals reconcile to 438.91 + 1.09 = 440.00".

## 6. Bugs and issues found

### 6.1 AI mapping: line items vs the app's total rule — fixed
`_replace_line_items` (transaction_service) always sets **total = Σ line amounts** for multi-item
claims, so line amounts must be the bill's final, VAT-inclusive figures.
- `bill_3.png`: model returned pre-VAT rows (697.00) → would have saved 7,416.36 instead of 7,787.19.
- `mage.png`: model flagged rows "excl. VAT" although the "Net Total" column already includes VAT
  and discount → naive conversion would have saved 441.13 instead of 440.00.
- **Fix** (`_make_lines_vat_inclusive`): decide from arithmetic, not the model's flag — rows that
  already sum to the total are kept; rows summing to the pre-VAT amount get each row's VAT added;
  rounding drift (≤ max(0.05, 0.01×rows)) absorbed into the last line. All 9 priced bills now
  sum exactly to the bill total.

### 6.2 Normal scan: row shift on angled photos — open
Claim #88 (`img3.jpeg`, photo at an angle): RapidOCR paired each description with the numbers of
the row above, dropped 4 rows, and put qty/item-code digits into "VAT %" (2–7% on a 0% bill). Same
open issue as §8 of the multi-item doc.

### 6.3 App overwrites a correct scanned total with a wrong item sum — open
Claim #88: the scan read the total correctly (224.99) but the 8 shifted lines summed to 186.71, and
`_replace_line_items` silently replaced the total. Proposed: a confirm-screen warning when
Σ lines ≠ scanned total ("Items add up to X but the bill total is Y").

### 6.4 Currency guessed from a place name — fixed
`ksa1.png`: company "Sharjah" → model said AED on a riyal slip. Fixed twice over: prompt rule
(money words decide) and mapping fallback (currency confidence < 0.5 → employee's region currency).

### 6.5 Normal-scan VAT errors seen in the database (last 25 receipts) — open
- #269 / #270 (safety Consultancy): VAT saved as 450.00 (should be 22.50; 450 + 22.50 = 472.50).
- #277: VAT 55.00 with no amount.
- #289 (`img27.png`, 50A88862): VAT 0 and total 297.75 — missed "VAT Inclusive 2.85", real total 300.60.
- `mage.png` in the benchmark: VAT missed, total 438.91 instead of 440.00.
None of these were AI scans — no AI scan has been made through the app yet.

### 6.6 Date format differs between engines — open
AI returns ISO (`2026-09-11`), the normal scan returns the printed form (`11/09/2026`). Display is
fine (`_fmtDate` parses both), but `_find_duplicate` compares dates as text, so the same bill
scanned once each way is not flagged as a duplicate. Fix: normalise to one format or compare parsed
dates.

### 6.7 Delivery notes have no prices
`bill_1.png` / `bill_2.png` are delivery notes (quantities only). AI reads the items correctly, but
`LineItemIn.amount` is required, so they cannot be submitted as line items. The matching tax invoice
(`bill_3.png` for DN 18812) is the claimable document.

## 7. Data fixes made during the session

- `scripts/ocr_results.csv`: ksa1 / ksa4 rows had unquoted commas inside values, shifting every
  later column (quoted, no values changed); ksa9 date corrected from "Oct 1" to **Oct 12** (as
  printed on the screenshot).
- `backend/uploads/`: 9 files were only 4 images. Kept and renamed
  `ksa2_qema_taxi_45sar.png`, `enoc_fuel_150aed.jpeg`, `enoc_icebag_6aed.jpg`; deleted 5 duplicates;
  restored the missing `assets/ksa/ksa2.png`.
- **Removed a photo of an Emirates ID card** from `backend/uploads/`. It is still in git history on
  `main`, `dev-teja` and `indra` (pushed) — purging needs a history rewrite + force-push; not done.
- Renamed confusable sample files: `multi_line/img 27.png` → **`mage.png`** (13 items, 50A86803),
  `multi_line/img 25.png` → **`amer.png`** (Blue Rhine INV-DIP-112954). `img27.png` (6 items,
  50A88862) is a different bill. References updated in `scripts/bill_number_truth.json`, the
  benchmark script and the multi-item findings doc.

## 8. Open items

1. Confirm-screen warning when Σ lines ≠ scanned total (§6.3). Still useful for `amer.png` (§10.2).
2. Normalise bill dates for the duplicate check (§6.6).
3. ~~AI-scan `img27.png` and `amer.png`.~~ Done 2026-10-26 — see §10.2. `img27` correct; `amer`
   line items correct, header total invented (page 1 of 2 has no grand total).
4. Prompt rule: if the page says "page 1 of 2" and has no payable total, leave amount/total null
   instead of guessing (`amer.png`).
5. Skip line items in the schema when the employee chose "Single item" (shorter, faster answer).
6. Try `reasoning_effort=minimal` on the 7 handwritten KSA bills (≈ $0.02); switch only if all
   amounts stay correct.
7. End-to-end test on the emulator (backend local; app at `http://10.0.2.2:8000`). Not yet run
   through the Flutter app.
8. Decide on purging the Emirates ID photo from git history.
9. Pre-existing test failures (not caused by this work): 8 × `test_claim_line_items.py` fixture
   bug, `test_no_vendor_literals` (`TRADING` in `extraction/candidates.py`),
   `test_arabic_receipts::test_multiline_vendor_header_merges_top_to_bottom`, and the
   date-sensitive `test_notification_service::test_delegation_redirects_to_backup`.

## 9. Self-hosted option: RunPod vision endpoint (in progress, 2026-10-23)

Goal: run the same "Scan with AI" flow on an open-source vision model on our own RunPod account,
so bill images never leave our infrastructure, and compare its accuracy with gpt-5.4-mini on the
same 15 bills.

### 9.1 How it works

No code is deployed to RunPod. RunPod's **official vLLM worker** hosts the model and exposes the
same OpenAI-compatible chat API that `llm_vision_service.py` already calls, so only the URL, key and
model change; prompt, schema, VAT/line-item checks and the Flutter app are identical.

| | ChatGPT (`AI_VISION_PROVIDER=openai`) | RunPod (`AI_VISION_PROVIDER=runpod`) |
|---|---|---|
| URL | `https://api.openai.com/v1` | `https://api.runpod.ai/v2/<RUNPOD_VISION_ENDPOINT_ID>/openai/v1` |
| Key | `OPENAI_API_KEY` | `RUNPOD_API_KEY` (existing) |
| Model | `gpt-5.4-mini` (`reasoning_effort=low`) | `Qwen/Qwen3-VL-8B-Instruct` (no reasoning param) |
| Timeout | 60 s | 300 s (`RUNPOD_VISION_TIMEOUT_SECONDS`, covers a cold start) |

The setting selects exactly one provider; there is **no automatic fallback** between providers or
to the normal scan (same rule as §4: an AI failure shows an error with Retry).

Benchmark: `python scripts/ocr_compare/llm_vision_compare.py --provider runpod --yes --limit 1`
(results cached under `llm_results/runpod-Qwen3-VL-8B-Instruct/`; stops sending after the first
error so a broken endpoint costs one call).

### 9.2 Endpoint settings (as configured in the console — testing profile)

Created in the console because the `RUNPOD_API_KEY` in `backend/.env` is a **restricted, run-only
key**: it can call endpoints but the management API (`rest.runpod.io/v1/templates|endpoints`)
returns 401. That is a good setup for a key stored on the server; it was not replaced.

**Page 1 — image**

| Setting | Value |
|---|---|
| Container image | `runpod/worker-v1-vllm:v2.30.1` (vLLM v0.32.0, released 2026-10-22) |
| Container start command | empty |
| Registry authentication | none (public image) |
| Container disk | 40–60 GB *(to confirm which was saved)* — not billed separately on Serverless; must fit the ~17 GB model, too small = billed crash loops |
| Endpoint type | **Queue** (not Load balancer — the code uses the queue endpoint's `/openai/v1` route) |

**Environment variables**

| Key | Value | Why |
|---|---|---|
| `MODEL_NAME` | `Qwen/Qwen3-VL-8B-Instruct` | Apache-2.0 vision model, fits a 24 GB GPU |
| `MAX_MODEL_LEN` | `8192` | bill image + prompt + answer ≈ 2–3k tokens; smaller = less GPU memory |
| `GPU_MEMORY_UTILIZATION` | `0.92` | headroom for the vision encoder on 24 GB |
| `MAX_NUM_SEQS` | `4` | few parallel requests at test volume; less KV-cache memory |
| `LIMIT_MM_PER_PROMPT` | `{"image": 1}` | one bill image per request |

**Page 2 — configure and deploy**

| Setting | Value | Note |
|---|---|---|
| Endpoint name | `expense-qwen3vl-8b` | |
| Compute type | GPU | |
| GPUs | **24 GB — Latest generation** ($0.69/hr) and **24 GB — Previous generation** ($0.69/hr) | Both = more chances of a free GPU; only one GPU ever runs (max workers 1), same price either way. All sizes showed "Out of capacity" at setup time. Optional: Previous-gen 48 GB ($1.22/hr) as an extra fallback — **not ticked**. 16 GB is too small for this model. |
| Worker priority | Availability | |
| Max workers | **1** | caps spend; one bill at a time |
| Active workers | **0** | nothing billed while idle (but cold starts) |
| GPU count | 1 | |
| Idle timeout | **5 s** | GPU stops 5 s after the last bill |
| FlashBoot | **On** (Standard) | faster restarts, no extra cost |
| Execution timeout | 600 s | |
| Cached model | `https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct` *(recommended — to confirm it was entered)* | model pre-cached on hosts, so cold starts don't spend billed minutes downloading 17 GB |
| Security & compliance | Any | |
| Data centers | all (34) | |
| Network / global volume | none | volumes are billed monthly; not needed |
| Allowed CUDA versions | **13.0** only | the image is built on CUDA 13; other hosts would crash-loop (billed) |
| Auto scaling | Queue delay, 4 s | |

**Deployed 2026-10-23: endpoint `expense-qwen3vl-8b`, ID `7mcor3e6kjpfnx`** (queue based, GPU type
24 GB, $0 spent at creation).

Backend `.env`: `RUNPOD_VISION_ENDPOINT_ID=7mcor3e6kjpfnx` (added; separate from the old OCR
`RUNPOD_ENDPOINT_ID`) and `RUNPOD_VISION_API_KEY=<key scoped to this endpoint>`. The existing
`RUNPOD_API_KEY` returns **403 Forbidden** on the new endpoint — restricted RunPod keys are scoped
per endpoint — so the vision endpoint gets its own key (falls back to `RUNPOD_API_KEY` if blank).
Switch the app to it with `AI_VISION_PROVIDER=runpod`.

### 9.3 Testing vs production profile

What is billed on Serverless: only the seconds a worker runs (per GPU type price). Ticking several
GPU types, a large container disk or FlashBoot does not add cost; active workers, max workers and
GPU count do.

| Setting | Testing (current) | Production (if adopted) |
|---|---|---|
| Active workers | 0 | 1 (no cold start) |
| Idle timeout | 5 s | 60–300 s |
| Max workers | 1 | 2–3 (concurrent scans) |
| GPU types | 24 GB ×2 | + more types / regions against "out of capacity" |

Cost comparison: ChatGPT ≈ $3.60 per 1,000 bills with ~6 s answers and no cold start; RunPod with one
always-on 24 GB worker ≈ $500/month list ($0.69/hr × 720 h, before RunPod's always-on discount)
regardless of volume; RunPod with 0 active workers ≈ cents but the first scan after idle waits for a
GPU + model load (minutes). RunPod is worth it in production only if keeping bills in-house is a
requirement or volume is very high. Changing profile is a console edit — no code change.

### 9.4 Plan and status

1. ✅ Backend provider switch + benchmark `--provider runpod` (tests: 15/15 AI tests, suite 230
   passed, same pre-existing failures).
2. ✅ Endpoint deployed (`7mcor3e6kjpfnx`), ID + scoped key in `backend/.env`.
3. ✅ One test bill (`ksa/ksa3.png`) — worked, cold start 148 s.
4. ✅ All 15 bills, two prompt variants — see §9.5. Prompt reverted to the original.

Also found: the **old PaddleOCR endpoint** (`RUNPOD_ENDPOINT_ID`) showed **2 idle/ready workers**
on 2026-10-23 although production no longer calls RunPod (Indra → RapidOCR). Idle/ready workers
are not billed when active workers = 0 — only check that its active workers is 0.

### 9.5 Results — Qwen3-VL-8B on RunPod (same 15 bills, same scoring)

**Run 1 — original prompt** (cache `llm_results/runpod-Qwen3-VL-8B-Instruct/`):

| | Normal scan | Qwen3-VL-8B | gpt-5.4-mini |
|---|---|---|---|
| KSA amount / total | 4/7 / 4/7 | **7/7 / 7/7** | 7/7 / 7/7 |
| KSA vendor / date | 2/6 / 3/5 | 6/6 / 5/5 | 6/6 / 5/5 |
| KSA currency | 7/7 | 5/7 (AED on ksa1, ksa3) | 7/7 |

Multi-item / invoices: image.png, img23, img3 (12 items), mage (13 items) correct; mistakes GPT did
not make — img2 total 845.83 (real 769.23), bill_3 total = pre-VAT 7,416.36 (real 7,787.19),
**invented amounts on both delivery notes** (bill_1 used the "Total 5,516 Pcs" quantity as money),
mage date read month-first (2026-11-09), ksa4 vendor = the route ("Kingdom Centre"), ksa3 bill number =
the "KAFD 208" zone code. Speed: cold start 127–148 s, warm 8–32 s (GPT 5–8 s).

**Run 2 — tightened prompt** (cache `…-v2/`): one rule per mistake above (null money on documents
without prices, total = printed payable line, day-first examples, never guess currency, no route /
zone code as vendor / bill number). Result: fixed 5 (ksa3 currency + bill no, ksa4 vendor, mage date,
bill_2 no invented prices), **regressed 2 that were right** (image.png 90.30/4.30/94.30, img23 VAT
236.21), left 3 money errors (bill_1 still invents 5,516, bill_3 total, img2 amount) and AED on ksa1/2.
Warm latency improved to 6–20 s (compact JSON). The app's amount + VAT ≠ total flag would highlight
4 of the 5 money errors; the delivery-note invention is not flagged.

**Decision: prompt reverted to the original** (2,059 chars, the version validated 15/15 on GPT) —
the 8B model is inconsistent on invoice totals and wording changes move the errors around rather
than removing them. Next candidate if in-house is required: Qwen3-VL-32B (48 GB GPU).

**Operational issues found on the way:**
- **JSON whitespace loop**: on `ksa5` Qwen emitted ~2,600 blank lines inside the forced JSON until the
  length limit → unreadable answer. Mitigation kept in code: RunPod answers capped at 2,500 tokens
  (`provider_config`, longest real answer ≈ 970) so a loop fails fast instead of burning GPU time.
- vLLM's `STRUCTURED_OUTPUTS_CONFIG={"disable_any_whitespace": true}` prevents the loop but **vLLM
  v0.32.0 refuses to start** with it unless the backend is explicit (`{"backend": "xgrammar",
  "disable_any_whitespace": true}`; `structured_outputs.py` validator) — the bare form made every
  job fail ("vLLM rejected its command line … StructuredOutputsConfig"). Removed again with the revert.
- Editing the endpoint makes the console demand a Hugging Face token ("gated model") although
  Qwen3-VL-8B is public; a free **read** token satisfies it (console only, not in our `.env`).
- A request sent during a config rollout can land on a restarting worker → gateway 502; health
  `/health` (free) shows worker states. The benchmark stops after the first error.
- Spend for all RunPod tests (≈ 35 calls incl. cold starts): ≈ $0.30, credit $7.04 → ~$6.7.

Nothing from this session is committed yet.

## 10. Decision and full `multi_line` re-run (2026-10-26)

ChatGPT (`gpt-5.4-mini`) was chosen as the only live scan engine. Qwen was evaluated and rejected
(§9.5). Camera and gallery both call GPT; the old Indra → RapidOCR path is no longer used for
employee scans. The app shows **Scanning…** only — no ChatGPT / OpenAI / AI wording.

### 10.1 Model comparison (same 15-bill set, 2026-10-23)

| | Current OCR (Indra → RapidOCR) | Qwen3-VL-8B (RunPod) | **gpt-5.4-mini** |
|---|---|---|---|
| KSA vendor | 2/6 | 6/6 | **6/6** |
| KSA amount / total | 4/7 | 7/7 | **7/7** |
| KSA date | 3/5 | 5/5 | **5/5** |
| KSA currency | 7/7 | 5/7 (AED on riyal slips) | **7/7** (after §6.4 fix) |
| Multi-item counts | often 0, or rows shifted | mixed; invents money on DNs | **correct counts; Σ = printed total** |
| Invoice totals | misses VAT Inclusive on pharmacy | img2 845.83 (real 769.23); bill_3 7,416.36 (real 7,787.19) | **correct** |
| Delivery notes | garbage items / invented money | invents amounts (5,516 pcs as money) | **null money, items + qty only** |
| Latency | ~2–4 s local | cold 127–148 s, warm 8–32 s | **avg 5.7–8.9 s** |
| Cost | free (CPU) | always-on 24 GB ≈ $500/month | **≈ $0.0036 / bill** ($3.60 / 1,000) |

Qwen3-VL-32B was only partly run (4 bills, avg 108 s, one timeout, line sums off). Not adopted.

### 10.2 All 12 bills in `assets/multi_line` (GPT, 2026-10-26)

Command (from `backend/`): `python scripts/ocr_compare/llm_vision_compare.py --only multi_line --no-baseline --yes`

5 already cached from 23 Oct; 7 new sent. Report: `llm_results/report_gpt-5.4-mini.md`.
Usage this folder: 12 bills, 23,112 prompt + 5,108 completion tokens, avg **8.9 s** (max 13.8 s).

Checked by eye against the photos (not only the auto-scorer — `ocr_results.csv` has no truth rows for this folder).

**Priced invoices — working**

| Bill | Vendor | Amount / VAT / Total | Items | Notes |
|---|---|---|---|---|
| `image.png` | Fabricast FZC | 86.00 / 4.30 / **90.30** | 2/2, Σ = total | |
| `img2.jpeg` | Standard Hardware | 732.60 / 36.63 / **769.23** | 3/3, Σ = total | bill no `CASHHT/1205` vs printed `CASH/SHT/1205` |
| `img23.png` | Rainbow Led | 4,704.20 / 235.21 / **4,939.41** | 7/7, Σ = total | |
| `img3.jpeg` | Bab Al Hayat | 224.99 / 0 / **224.99** | 12/12, Σ = total | |
| `mage.png` | Bab Al Hayat | 438.91 / 1.09 / **440.00** | 13/13, Σ = total | |
| `img 21.png` | Jannat Al Naeem | 3,820 / 191 / **4,011** | 5/5 qtys + amounts | new; invoice **19779** |
| `img27.png` | Bab Al Hayat | **297.75 / 2.85 / 300.60** | 6/6; only eye-wash at 5% | new; the open "VAT Inclusive 2.85" case |
| `img25.png` | Blue Rhine p.2 | **2,628 / 131.40 / 2,759.40** | totals page, no items | no invoice no on this page (expected) |

**Delivery notes — read correctly, cannot submit as claims** (`LineItemIn.amount` is required)

| Bill | Vendor | Doc no | Items | Money |
|---|---|---|---|---|
| `img 22.png` | Jannat | **19065** | 5, qtys right | null (matching invoice is `img 21.png` / 19779) |
| `img26.png` | Blue Rhine | **SO-DN-DIP-110042** | 4, qtys right | null |
| `img24.png` | Rainbow | **2514** | 7 | null; power-supply qty 13 ↔ magnet 432 swapped |

GPT did **not** invent money on delivery notes (Qwen did).

**One miss: `amer.png` (Blue Rhine tax invoice, page 1 of 2)**

| | GPT | Printed |
|---|---|---|
| Invoice | INV-DIP-112954 | correct |
| Date | 2026-10-06 | correct |
| 4 line amounts | 1449 / 170.10 / 216.30 / 924 | correct (Σ **2,759.40**) |
| Header total | **2,942.00** (invented) | **not on this page** |

Page 2 (`img25.png`) has the real payable: 2,628 + 131.40 = **2,759.40**, which matches the line sum.
In multi-item mode `_replace_line_items` overwrites the header with Σ lines → 2,759.40 (right number).
In single-item mode the employee would see 2,942 unless they correct it.

### 10.3 What shipped in the live path (2026-10-26)

```
Add receipt → Single / Multiple → camera or gallery
  POST /api/claims/ocr/upload
  Confirm screen: "Scanning…"
  POST /api/claims/receipts/{id}/ocr     (engine ignored; always GPT)
    ocr_service.run() → llm_vision_service.run_llm_vision
    no Indra / RapidOCR / stub fallback
  Confirm form fills; failure → "Couldn't read this bill" + Retry
```

| Change | Where |
|---|---|
| `OcrService.run()` always calls GPT | `backend/services/ocr_service.py` |
| Routes ignore `engine=standard` | `backend/api/routes_claims.py` |
| Camera / gallery both GPT; "Scan with AI" button removed | `capture_receipt_sheet.dart` |
| Progress label "Scanning…"; no AI / OpenAI in errors | `confirm_claim_screen.dart`, `llm_vision_service.py` |
| `.env` | `AI_VISION_PROVIDER=openai`, `OPENAI_VISION_MODEL=gpt-5.4-mini` |

Indra / RapidOCR helpers stay in the repo for compare scripts and extraction unit tests. They are
not called from a live scan.

GPT unit tests: 15/15 passed. End-to-end emulator scan still open (§8.7).

### 10.4 `assets/uploads` (GPT, 2026-10-26)

Three receipts that used to live in `backend/uploads/` (renamed). Same command with `--pick`.
Caches: `llm_results/gpt-5.4-mini/uploads__*.json`. Avg **4.6 s**.

| Bill | Printed | GPT | Verdict |
|---|---|---|---|
| `enoc_fuel_150aed.jpeg` | ENOC, 20/08/2026, SPECIAL 42.98 L, 142.86 + VAT 7.14 = **150.00 AED**, receipt **886117** | same | **OK** |
| `enoc_icebag_6aed.jpg` | ENOC, 18/08/2026, ICE BAG, printed total **6.00**, VAT **0.29** (excl. = 5.71), TRAN **584439** | vendor / date / bill / VAT / total right; **amount kept as 6.00** (printed sale), so 6.00 + 0.29 ≠ 6.00 — `reconciliation_mismatch` | **mostly OK** — total payable is right; excl. VAT should be 5.71 |
| `ksa2_qema_taxi_45sar.png` | Qema Al-Khaleej, **25/06/26**, handwritten **45/**, invoice **0386**, ريال | vendor / 45 / 0386 right; date **2025-06-25** (should be 2026-06-25); currency **null** (ريال is on the slip; a KSA login would fill SAR via the low-confidence fallback) | **amount OK**; year and currency need the employee to confirm |

The ice-bag slip prints both "Sale Amt AED6.00" and "VAT Amt AED0.29" with "TOTAL AED6.00" — the 6.00 already includes VAT. GPT followed the printed sale/total and did not derive 5.71. The old OCR pipeline had the same receipt as `assets/dubai/enoc_test.jpg` (truth 5.71 / 0.29 / 6.00).
