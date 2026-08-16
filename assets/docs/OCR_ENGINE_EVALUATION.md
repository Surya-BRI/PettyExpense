# OCR Engine Evaluation — Process & Results

**Decision (2026-08-15): PaddleOCR only.** Google Vision, Azure Vision, and Surya have been
removed from the repo and from `backend/.env`. The running app and `scripts/ocr_compare`
use PaddleOCR (`OCR_BACKEND=paddle`). Historical results below are kept for the record.

Investigation for Phase 4 (Bill Capture & OCR Enhancements) of the Petty Cash module, see
[PETTY_CASH_PHASED_PLAN.md](PETTY_CASH_PHASED_PLAN.md).

## Candidate engines considered

| Engine | Type | Arabic support | Notes |
|---|---|---|---|
| PaddleOCR | Free, self-hosted | Yes (separate `lang="ar"` model) | Apache-2.0 |
| EasyOCR | Free, self-hosted | Yes | Not yet tested |
| Tesseract | Free, self-hosted | Yes (language pack) | Not yet tested; weakest on phone photos historically |
| Surya | Free, self-hosted | Yes, strong on benchmarks | **License confirmed clean**: Apache-2.0 as of the current release (`datalab-to/surya`, checked via GitHub API on 2026-08-12) — it moved off its older GPL-3.0/commercial dual-license model. No adoption blocker remaining on the licensing front. |
| AWS Textract | Paid, cloud | No real Arabic support | Ruled out — GCC bills need Arabic |
| Google Cloud Vision (`DOCUMENT_TEXT_DETECTION`) | Paid, cloud | Yes | Strong on handwriting per public benchmarks; blocked on billing activation during this evaluation, not yet tested |
| Azure AI Vision (Read API v3.2) | Paid, cloud | Yes | Comparable to Google on handwriting; GCC (UAE) datacenter presence; not yet tested — credentials were never provided |

## Real bill samples used

9 real KSA taxi/transport bills, plus 6 UAE tax invoices — now at `assets/ksa/` and
`assets/dubai/` at the repo root (moved from `backend/scripts/ocr_compare/samples/`):
- 7 physical printed-form bills with **handwritten** fields (date, route, amount) — bilingual
  Arabic/English templates, typical of GCC taxi receipts
- 2 digital Uber app "Ride details" screenshots (fully rendered text, no handwriting)

## Process followed

1. **Built comparison tooling**, not production code — three standalone functions with the
   same return shape (`{engine, raw_text, words: [{text, confidence}], error}`) so results are
   directly comparable:
   - `google_vision.py` — `extract_text_google_vision(image_bytes, api_key)`, calls
     `vision.googleapis.com/v1/images:annotate` with `DOCUMENT_TEXT_DETECTION`,
     `languageHints: ["ar","en"]`.
   - `azure_vision.py` — `extract_text_azure_vision(image_bytes, endpoint, key)`, calls the
     async Read v3.2 API (submit → poll `Operation-Location` → fetch result).
   - `paddle_ocr.py` — `extract_text_paddle(image_path, lang)`, wraps `PaddleOCR(lang=...)`,
     one instance cached per language.
   - `run_compare.py` — runs all three against every image in a `samples/<region>/` folder,
     prints raw text, flags words with confidence < 0.5, and re-runs the raw text through the
     existing `ocr_service.extract_from_text` regex parser (after normalizing Arabic-Indic
     digits to ASCII) so the report shows what the *rest of the pipeline* would actually
     receive, not just raw OCR dump.

2. **Google Cloud Vision setup attempt** — enabled the "Cloud Vision API" (not "Vision AI API"
   or "Cloud Document AI API", which are different products), created an API key. Blocked:
   the GCP project needs billing enabled before the API will serve requests (`403
   PERMISSION_DENIED`, "This API method requires billing to be enabled"). **Not yet
   resolved** — billing was never enabled during this session, so Google Cloud Vision has no
   real test results yet, only a confirmed integration (the code correctly calls the API and
   correctly reports the billing error).

3. **Azure AI Vision setup** — walked through creating a "Computer Vision" resource in the
   Azure Portal (Marketplace search "Computer Vision", not "azure ai vision" which returns
   unrelated marketplace products). **Not yet completed** — endpoint/key were never provided,
   so Azure has no test results yet either.

4. **PaddleOCR setup** — installed `paddlepaddle` + `paddleocr` (pulled in `paddleocr==3.7.0`,
   a major-version jump from what the existing `ocr_service.py` stub code assumed). Hit two
   real problems, both fixed:
   - **API breaking change**: PaddleOCR 3.x removed `use_angle_cls`/`show_log` constructor
     args and changed `.ocr()`'s result shape entirely. Fixed by switching to `.predict()`,
     which returns objects with `rec_texts`/`rec_scores` arrays (index-aligned).
   - **Windows CPU inference crash**: `NotImplementedError: ConvertPirAttribute2RuntimeAttribute
     ... [pir::ArrayAttribute<pir::DoubleAttribute>]` inside PaddlePaddle's oneDNN/PIR
     executor, on every image, before any real OCR ran. Fixed with `enable_mkldnn=False`
     (disables the oneDNN CPU backend) — a workaround specific to this Windows setup, not a
     code bug on our side.
   - **Console encoding crash**: Windows terminal defaulted stdout to cp1252, which can't
     encode Arabic characters, crashing mid-run. Fixed with
     `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` in `run_compare.py`.

5. **Ran all 9 KSA samples** through PaddleOCR twice each — once with `lang="en"`
   (loads `PP-OCRv6_medium_det` + `PP-OCRv6_medium_rec`) and once with `lang="ar"`
   (loads `PP-OCRv5_server_det` + `arabic_PP-OCRv5_mobile_rec`) — confirming PaddleOCR has
   **no single mixed-script model**; each language is a fully separate detection+recognition
   pipeline, run independently. The Arabic pass is noticeably slower (heavier "server"-scale
   detection model on CPU).

6. **Surya license re-verified live** (not from memory) via `gh api repos/datalab-to/surya` —
   confirmed **Apache-2.0** as of the current release, having moved off an older GPL-3.0 +
   commercial-tier model. No licensing blocker.

7. **Surya architecture investigation** — checked the actual repo docs rather than assume:
   self-hosting Surya's real OCR pipeline (not just text-line detection) requires a running
   inference server (`vllm` for GPU, `llama.cpp` for CPU) — quoted CPU throughput is
   ~0.108 pages/sec even on Apple Silicon Metal, and Windows CPU-only self-hosting has no
   documented simple path at all. This is a materially bigger lift than PaddleOCR's single
   `pip install`. Per user decision, tested Surya's **hosted API** instead
   (`https://www.datalab.to/`, $5 free credit) rather than self-hosting — no llama.cpp/vllm
   setup needed.

8. **Surya hosted API integration** (`backend/scripts/ocr_compare/surya_hosted.py`) — the
   public docs at documentation.datalab.to only fully document a *deprecated* OCR endpoint;
   the current one is `POST /api/v1/convert` (multipart, `X-API-Key` header, `output_format`/
   `mode` params), async: submit → poll `request_check_url` → fetch a signed `result_url`.
   The completed-result JSON schema isn't fully documented, so the parser
   (`_walk_collect()`) recursively collects any `text`/`html` + `confidence` fields rather
   than assuming an exact shape — this worked correctly against the real API on the first try.
   Ran with `mode="accurate"` (highest quality tier) against all 9 KSA images.

## Results — PaddleOCR, all 9 images

| # | Bill type | Vendor name | Date | Amount | Route/notes |
|---|---|---|---|---|---|
| ksa1 | Sharja taxi (handwritten) | ✅ SHARJA | ❌ garbled | ⚠️ "45" readable but buried in noise | ❌ "to Dalay" (actual: "to Malaz") |
| ksa2 | Qema Al-Khaleej (handwritten) | ✅ full name, English **and** Arabic | ❌ merged digits | ❌ "451" for actual "45/" | ⚠️ partial |
| ksa3 | Shahad Tawik (handwritten) | ✅ perfect | ✅ "29-6-26" correct | ❌ regex grabbed wrong number | ✅ "KAFD 208 to malzz" — close |
| ksa4 | Unnamed taxi invoice (handwritten) | ❌ invoice # merged into vendor | ❌ garbled | ✅ "55" readable | ⚠️ partial |
| ksa5 | Taxi Al-Ajme (handwritten) | ✅ correct | ✅ "03/07/26" correct | ❌ missed entirely | ✅ "To: Malaz / KAFD 2.08" — perfect |
| ksa6 | Shaml Al-Doha (mostly printed) | ✅ perfect, English **and** Arabic | ✅ "05/07/26" correct | ❌ "351" for actual "35/" | n/a |
| ksa7 | Unnamed taxi (handwritten, noisy photo) | ❌ garbled | ✅ "14/07/26" correct | ⚠️ "45" buried in noise | ❌ mostly unreadable |
| ksa8 | Uber app screenshot (digital) | ✅ perfect | ✅ perfect | ✅ perfect ("SAR72.90") | ✅ perfect |
| ksa9 | Uber app screenshot (digital) | ✅ perfect | ✅ perfect | ✅ perfect ("SAR42.00") | ✅ perfect |

**Full raw output** (per image, per language, with per-word confidence) is preserved in the
session log; re-running `python scripts/ocr_compare/run_compare.py ksa` reproduces it exactly
(deterministic given the same images/model versions).

## Results — Surya (hosted API, `mode="accurate"`), all 9 images

Surya returns structured **HTML with real `<table>` markup** (headers + cells), not a flat
text dump — a materially different (and more parseable) output shape than PaddleOCR's line
list. The existing `ocr_service.extract_from_text` regex parser can't use this at all (it
returned garbage on every image, e.g. treating `<p>90375</p>` as the vendor name) — a proper
integration needs an HTML/table-aware parser (e.g. BeautifulSoup, mapping header cell text
like "Fare"/"Amount"/"المبلغ" to the value in the same column), not the current regex.
Judging accuracy below from the raw HTML content, not the (currently unusable) regex output:

| # | Bill type | Vendor name | Date | Amount | Route/notes |
|---|---|---|---|---|---|
| ksa1 | Sharja taxi (handwritten) | ✅ perfect, full bilingual + footer text | ⚠️ garbled ("22/66/26") | ✅ "45" correctly isolated in its table cell | ❌ "KAFD 208 / to Dalay" (actual: "KAFD 2.08 / to Malaz") |
| ksa2 | Qema Al-Khaleej (handwritten) | ✅ perfect, English **and** Arabic | ✅ "25/06/26" correct | ✅ **"45/" preserved literally — no slash-misread bug** | ✅ "to Malaz" correct |
| ksa3 | Shahad Tawik (handwritten) | ✅ perfect, English **and** Arabic | ✅ "29-6-26" correct | ❌ "409" (table columns partly mislabeled) | ✅ "KAFD 208 / to Malaz" — close |
| ksa4 | Unnamed taxi invoice (handwritten) | ⚠️ invoice # correct, no separate vendor name on this bill | ⚠️ two dates shown (Hijri + "26/06/2020") | ❌ "551" (rowspan cell merge issue) | ⚠️ "Kingdom / center to / Malay" — partial |
| ksa5 | Taxi Al-Ajme (handwritten) | ✅ perfect, full bilingual | ✅ both Hijri and Gregorian captured | ✅ **"50 /" preserved literally — no slash-misread bug** | ✅ "Malaz / KAFD 2.08" — **perfect** |
| ksa6 | Shaml Al-Doha (mostly printed) | ✅ perfect, English **and** Arabic, incl. VAT/license/phone | ✅ "05/07/26" correct | ✅ **"35/" preserved literally — no slash-misread bug** | ✅ "Malay to kingdom" reasonable |
| ksa7 | Unnamed taxi (handwritten, noisy photo) | ✅ perfect, full bilingual + license/tax number | ⚠️ unusual order ("26/07/14") | ❌ "451" (same digit-merge pattern as Paddle) | ⚠️ "kingdom tower to Dahab" — partial |
| ksa8 | Uber app screenshot (digital) | ✅ perfect (+ generated alt-text for icons/map, unrequested but harmless) | ✅ perfect | ✅ perfect ("SAR72.90") | ✅ perfect |
| ksa9 | Uber app screenshot (digital) | ✅ perfect | ✅ perfect | ✅ perfect ("SAR42.00") | ✅ perfect |

## Findings

1. **Digital receipts: 100% accurate** (2/9) — expected, no handwriting involved, confirms the
   pipeline works end-to-end when text is machine-rendered.
2. **Printed vendor/company info is strong, including Arabic script** — 7/9 correct vendor
   names, including two cases where the *Arabic* company name was read correctly
   ("شركة قمة الخليج المحدودة", "شركة شمل الدوحة"). Better than expected for a free model.
3. **Handwritten dates: ~half correct** (4/7 physical bills) — not reliable enough to trust
   without employee confirmation.
4. **Handwritten amount is the weak point, with a specific recurring bug**: these bills use
   regional shorthand "45/" (45 riyals, no halalas), and PaddleOCR repeatedly misreads the
   trailing "/" as digit "1" — "45/" → "451", "35/" → "351". Consistent enough across images
   to be a known, fixable failure mode rather than random noise.
5. **A separate bug, unrelated to OCR accuracy**: the existing regex parser
   (`ocr_service.extract_from_text`) failed to isolate "amount" in 7/9 cases, even when the
   raw OCR text clearly contained the right number. It only matches currency-prefixed or
   "Total:"-labeled numbers, not a bare number sitting in a table cell — a parsing-logic gap
   on our side, independent of which OCR engine is chosen.
6. **No single mixed-script pass (PaddleOCR)**: PaddleOCR needs two separate runs (`en` + `ar`)
   per image for bilingual bills, and neither pass alone is sufficient — the `en` pass garbles
   Arabic text into gibberish, the `ar` pass was sometimes *worse* than the `en` pass at reading
   handwritten Latin numbers on the same bill.
7. **Surya (hosted, `mode="accurate"`) is the strongest result of the three engines tested so
   far** — it does mixed-script Arabic+English in a single pass (no two-pass problem), got
   9/9 vendor names essentially perfect including full bilingual company info (license
   numbers, phone, VAT), got more dates right than PaddleOCR, and **directly solved 3 of the
   9 "slash → digit" amount-misreads** that plagued PaddleOCR (ksa2 "45/", ksa5 "50/", ksa6
   "35/" all preserved literally, not corrupted into "451"/"501"/"351"). It still got the
   amount wrong on 3 other images (ksa3 "409", ksa4 "551", ksa7 "451") via a different
   failure mode (table column mislabeling / rowspan cell merging), so it is not a full fix —
   but it's a clear step up from PaddleOCR's near-universal amount-field failure.
8. **Surya's output shape is fundamentally different and needs different parsing**: it returns
   real HTML with `<table>` markup (headers + cells preserved), not a flat text/line list.
   The existing regex parser is completely unusable against this (it returned nonsense like
   treating `<p>90375</p>` as the vendor on every single image) — a real integration needs an
   HTML/table-aware parser (e.g. BeautifulSoup mapping header text like "Fare"/"المبلغ" to the
   value in the same table column), which is a different and arguably more reliable approach
   than PaddleOCR's plain-text regex, since the table structure is already segmented for us.

9. **CORRECTED — the Surya hosted-API results above are confirmed genuine, not provisional.**
   Initially flagged the `runtime: 0.087` seconds / `cost_breakdown.final_cost_cents: 0`
   response as suspiciously fast/free for real inference, and the user's "mock key" phrasing
   as a further red flag. **User confirmed the key is a real, non-mock production key.** The
   "suspiciously fast" reasoning was also a flawed comparison in the first place: it measured
   against the *self-hosted CPU/Apple-Silicon* benchmark (0.108 pages/sec), but Datalab's
   actual hosted infrastructure almost certainly runs on dedicated GPU servers — sub-100ms for
   a 650M-parameter model on real GPU hardware is unremarkable, not suspicious. **Surya is the
   confirmed front-runner of the three engines tested so far**, not a provisional one.
10. **The API never confirms which model actually ran.** `versions` came back `None`, and no
    `model` field exists in the response. Datalab's own materials say their hosted platform
    runs "both Surya and variants of their highest-accuracy model, Chandra" — meaning
    `mode="accurate"` may have been served by **Chandra** (`datalab-to/chandra-ocr-2`), a
    different and reportedly stronger model than the "Surya-2" model you'd get from local
    self-hosting (`datalab-to/surya-ocr-2-gguf`). Self-hosting locally could plausibly score
    **lower** than what's documented above, not equivalent — this needs testing, not assuming.

## Self-hosting feasibility — target server

User's existing PM2-hosted server (already running other LLM workloads) was evaluated as a
candidate for local Surya-2 self-hosting, in case cloud/hosted-API results don't pan out.

**Hardware** (from `free -h` / `nproc` / `lscpu`, provided by user):
- Likely AWS `m5.xlarge` — Intel Xeon Platinum 8259CL @ 2.50GHz, 4 vCPU (2 physical cores,
  hyperthreaded), KVM-virtualized.
- **AVX-512 supported** (`avx512f`, `avx512dq`, `avx512bw`, `avx512vl`, `avx512cd`) — material
  advantage, `llama.cpp` has optimized AVX-512 kernels.
- RAM: 15Gi total, **only ~4.3Gi "available"** at the time checked (11Gi already in use by
  the user's other hosted models). No swap configured.
- No GPU — CPU-only inference path (`llama.cpp`, not `vllm`).

**Assessment:**
- Surya-2 is small for this class of model (650M params) — plausible fit for available RAM
  headroom (~1-2GB expected footprint at 4-bit quantization, weights + KV cache + detection
  model), but not generous if the existing hosted models spike memory concurrently.
- AVX-512 meaningfully helps CPU throughput vs. a non-AVX-512 box, but the only real
  benchmark available (0.108 pages/sec) is from Apple Silicon **with Metal GPU acceleration**
  — not comparable to this plain-CPU setup. Real throughput here is unmeasured.
- CPU contention risk: only 4 threads total, shared with whatever the user's existing hosted
  models are already serving — not an isolated benchmark environment.

**Recommended setup, if pursued:**
```bash
# Pull quantized weights + start server, threads capped to leave room for existing workloads
./llama-server -hf datalab-to/surya-ocr-2-gguf --threads 2 --port 8090
```
```
SURYA_INFERENCE_BACKEND=llamacpp
SURYA_INFERENCE_URL=http://localhost:8090/v1
SURYA_INFERENCE_PARALLEL=1
```
- Prefer a **Q4_K_M** GGUF quantization if offered (best speed/memory tradeoff for CPU) over
  Q8/F16 — exact quant variants published weren't confirmed (HF file listing wasn't fetched in
  full; check `huggingface.co/datalab-to/surya-ocr-2-gguf/tree/main` directly).
- `--threads 2` / `SURYA_INFERENCE_PARALLEL=1` deliberately conservative, to avoid starving
  the user's already-running hosted models.

**Not yet done** (requires running commands on that server, outside this session's reach):
- Actually pulling the model and starting `llama-server` there.
- Measuring real per-image latency and peak RAM usage against the same 9 KSA samples.
- Comparing local Surya-2 accuracy against the hosted-API numbers above, given finding 10's
  Surya-vs-Chandra ambiguity — local self-hosting may not reproduce the hosted results.

## Open items / next steps

- [x] Engine choice: **PaddleOCR only** — Google / Azure / Surya tooling and keys removed.
- [x] Dubai samples populated and run through PaddleOCR (`en` + `ar`).
      Full dump: [`backend/scripts/ocr_compare/results_dubai.md`](../../backend/scripts/ocr_compare/results_dubai.md).
- [ ] Improve the regex amount parser so it prefers "Bill Amount" / labeled totals over
      phone numbers and OCR typos (`B111 Aaount` on Dubai image 1 left amount empty) — a
      fuzzy `a.ount`/`t.tal` fallback (tolerating one OCR-garbled character) plus a
      Total-minus-VAT derivation were added to `ocr_service.py`, but **re-running
      `run_compare.py dubai` still shows image 1 with `amount`/`vat_amount`/`total_amount`
      all `None`** despite the raw text containing `B111 Aaount: 29.00` — see
      [`results_dubai.md`](../../backend/scripts/ocr_compare/results_dubai.md#image-1png).
      Not actually fixed for this case; needs debugging (the fuzzy match or its
      quantity-context exclusion is likely still rejecting this exact line), not marking done.
- [x] Per-field confidence in the Flutter confirm form (vendor / amount / VAT / total / date) —
      done, via `OcrResult.isLow()`/`confidenceFor()` consumed in `confirm_claim_screen.dart`.
- [ ] **Image preprocessing was tried and reverted** — grayscale + autocontrast + upscale +
      sharpen (Pillow only, no new dependency) was added to `ocr_service.py` to improve
      handwritten-amount reads, then tested against the real `ksa1.png` sample. Result: it made
      accuracy *worse* — the sharpening step caused PaddleOCR to merge two adjacent handwritten
      digits into one glued token (`45` + trailing `1` → `451`), corrupting a previously-correct
      read (`45.0` → wrong `1.0`). Reverted in full (both `ocr_service.py` and the
      `run_compare.py` tooling). Lesson: blanket sharpen/contrast is too blunt an instrument for
      cursive handwriting on this dataset — any future attempt needs a much larger before/after
      sample to validate, not a single-image spot check.

## Compare tooling (current)
- `backend/scripts/ocr_compare/paddle_ocr.py`
- `backend/scripts/ocr_compare/run_compare.py` — PaddleOCR only; writes `results_<folder>.md`
- `backend/scripts/ocr_compare/results_dubai.md` — last Dubai run (6 images, en + ar)
- `backend/scripts/ocr_compare/README.md`
- `assets/ksa/` and `assets/dubai/` — sample bill photos (moved out of `backend/scripts/ocr_compare/samples/`; re-point `run_compare.py`'s `SAMPLES_DIR` or copy them back before re-running the harness)
