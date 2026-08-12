# OCR comparison — Google Cloud Vision vs Azure AI Vision vs Surya (hosted) vs PaddleOCR

Standalone comparison tooling, **not wired into the app**. Purpose: measure real
accuracy on real bill samples before picking an engine for `services/ocr_service.py`.

## Setup

1. Drop sample bill photos (`.jpg`/`.png`) into `samples/<region>/` (e.g. `samples/ksa/`).
2. Get credentials for whichever engine(s) you want to test:
   - **Google Cloud Vision**: GCP Console → APIs & Services → Credentials → create an API key,
     with the Vision API enabled on that project (billing must be enabled on the project).
   - **Azure AI Vision**: Azure Portal → create a "Computer Vision" resource →
     Keys and Endpoint blade.
   - **Surya (hosted API)**: sign up at https://www.datalab.to/ ($5 free credit, no local
     llama.cpp/vllm setup needed), get an API key from the dashboard.
   - **PaddleOCR**: free, self-hosted, no key needed — `pip install paddlepaddle paddleocr`.
     Runs automatically unless `--no-paddle` is passed (see below).
3. Set env vars (any subset — the script skips whichever isn't set):
   ```
   set GOOGLE_VISION_API_KEY=...
   set AZURE_VISION_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com
   set AZURE_VISION_KEY=...
   set SURYA_API_KEY=...
   ```
   (Or add them to `backend/.env` — `run_compare.py` loads it automatically.)
4. From `backend/`: `python scripts/ocr_compare/run_compare.py [subfolder] [--no-paddle]`
   - `subfolder` (optional): a folder name under `samples/`, e.g. `ksa`, to test one region's
     bills instead of everything under `samples/`.
   - `--no-paddle`: skip the free self-hosted pass (it's slow — runs both an English and an
     Arabic model per image).

## What it prints, per image
- Raw extracted text from each engine.
- Fields parsed out of that text by the existing regex parser (`ocr_service.extract_from_text`),
  after normalizing Arabic-Indic digits to ASCII — so you see what the *rest of the pipeline*
  would actually receive, not just raw OCR text.
- Any word with confidence below 0.5, flagged separately (a proxy for what would trigger the
  "low confidence — review this field" UI behavior in Phase 4).

## Files
- `google_vision.py` — `extract_text_google_vision(image_bytes, api_key)`
- `azure_vision.py` — `extract_text_azure_vision(image_bytes, endpoint, key)`
- `surya_hosted.py` — `extract_text_surya_hosted(image_bytes, api_key)` — uses Datalab's
  `/api/v1/convert` endpoint (submit → poll → fetch result); no local model/server needed.
  Self-hosting Surya locally would instead need a running `llama.cpp`/`vllm` inference server
  (see `docs/OCR_ENGINE_EVALUATION.md` for why that's a bigger lift than PaddleOCR).
- `paddle_ocr.py` — `extract_text_paddle(image_path, lang)` — free, self-hosted, runs both
  `en` and `ar` passes per image (PaddleOCR has no single mixed-script model).
- `run_compare.py` — runs all engines with credentials set against every image in a
  `samples/<region>/` folder, prints a side-by-side report.

Nothing here is imported by `main.py` / the running app — this is pre-decision testing only.
Once you've picked an engine based on real results, we wire the winner into `ocr_service.py`.

## Known API documentation gaps (Surya hosted)
Datalab's public docs don't fully specify the completed-result JSON schema for `/convert`
(block objects with `text`/`html`/`confidence` fields, per Surya's own model docs, but not
confirmed against docs.datalab.to). `surya_hosted.py`'s `_walk_collect()` recursively pulls
out anything that looks like text/confidence rather than assuming an exact shape, so it
should keep working even if the real schema differs slightly — but treat the first real run's
output as a sanity check on that assumption, not a given.
