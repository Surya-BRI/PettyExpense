# OCR comparison — PaddleOCR only

Standalone PaddleOCR test harness against real bill photos. Not a second OCR stack —
the running app also uses PaddleOCR (`OCR_BACKEND=paddle` in `backend/.env`).

## Setup

1. Drop sample bill photos (`.jpg`/`.png`) into `samples/<region>/` (e.g. `samples/dubai/`).
   **Note:** the current KSA/Dubai sample images have been moved to `assets/ksa/` and
   `assets/dubai/` at the repo root; `run_compare.py` still reads from `samples/<region>/`
   next to this script, so copy (or re-point `SAMPLES_DIR` in `run_compare.py` to) the
   `assets/` images before re-running the harness.
2. Install PaddleOCR if needed: `pip install paddlepaddle paddleocr`.
3. From `backend/`: `python scripts/ocr_compare/run_compare.py [subfolder]`
   - `subfolder` (optional): a folder under `samples/`, e.g. `ksa` or `dubai`.

Each image is run twice — `lang="en"` and `lang="ar"` — because PaddleOCR has no single
mixed-script model. Results are written to `results_<subfolder>.md` (e.g. `results_dubai.md`)
after every image so a long run is not lost.

## What it prints, per image
- Raw extracted text from each language pass.
- Fields parsed out of that text by `ocr_service.extract_from_text` (after normalizing
  Arabic-Indic digits to ASCII).
- Words with confidence below 0.5.

## Files
- `paddle_ocr.py` — `extract_text_paddle(image_path, lang)`
- `run_compare.py` — runs PaddleOCR against every image in a `samples/<region>/` folder
