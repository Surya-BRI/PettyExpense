# OCR comparison — RapidOCR (shared production pipeline)

Standalone harness against real bill photos, built on `services/ocr_service.py`'s exact
shared-detection RapidOCR pipeline — not a second OCR stack. The running app uses the same
code (`OCR_BACKEND=rapidocr` in `backend/.env`, default). PaddleOCR/PaddlePaddle are no longer
used anywhere in this repo; `paddle_ocr.py` keeps its old filename but wraps RapidOCR now.

## Setup

1. Drop sample bill photos (`.jpg`/`.png`) into `samples/<region>/` (e.g. `samples/dubai/`).
   **Note:** the current KSA/Dubai sample images have been moved to `assets/ksa/` and
   `assets/dubai/` at the repo root; `run_compare.py` still reads from `samples/<region>/`
   next to this script, so copy (or re-point `SAMPLES_DIR` in `run_compare.py` to) the
   `assets/` images before re-running the harness.
2. Install the OCR deps if needed: `pip install -r ../../requirements.txt` (pulls in
   `rapidocr`, `onnxruntime`).
3. From `backend/`: `python scripts/ocr_compare/run_compare.py [subfolder]`
   - `subfolder` (optional): a folder under `samples/`, e.g. `ksa` or `dubai`.

Each image goes through one shared PP-OCRv6 text-detection pass, then two sequential
recognizer passes (English, then Arabic) reusing the same detected regions — mirroring exactly
what `services/ocr_service.py` does for a real submitted receipt. Results are written to
`results_<subfolder>.md` (e.g. `results_dubai.md`) after every image so a long run is not lost.

## What it prints, per image
- Raw extracted text from each recognizer pass (English, Arabic).
- Fields parsed out of that text by the `extraction/` pipeline (after normalizing
  Arabic-Indic digits to ASCII).
- Words with confidence below 0.5.

## Files
- `paddle_ocr.py` — `extract_words_shared(image_path, mode)`, thin wrapper around
  `services.ocr_service._run_shared_detection_ocr` (kept its old name; no longer PaddleOCR)
- `run_compare.py` — runs the shared RapidOCR pipeline against every image in a
  `samples/<region>/` folder
