"""Standalone RapidOCR (production OCR_BACKEND=paddle) single-image benchmark.
Runs under backend/.venv, invoked as a fresh subprocess per image so cold-start
time and peak RAM are real, not skewed by process-level model caching in
services.ocr_service. Usage: python rapidocr_single.py <image_path>
Prints one JSON object to stdout. Calls the real production entrypoint
(ocr_service.run) — never a stub. On real OCR failure the underlying exception
(with traceback) is surfaced, not swallowed.
"""
import json
import sys
import threading
import time
import traceback
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_ROOT / ".env")

PEAK_RSS_MB = 0.0
_STOP = False


def _poll_rss() -> None:
    global PEAK_RSS_MB
    import psutil

    proc = psutil.Process()
    while not _STOP:
        rss_mb = proc.memory_info().rss / (1024 * 1024)
        if rss_mb > PEAK_RSS_MB:
            PEAK_RSS_MB = rss_mb
        time.sleep(0.05)


def main() -> None:
    global _STOP
    image_path = sys.argv[1]

    watcher = threading.Thread(target=_poll_rss, daemon=True)
    watcher.start()

    t0 = time.time()
    try:
        from services.ocr_service import ocr_service  # cold import — engine construction happens on first .run() call

        cold_start_s = time.time() - t0
        image_bytes = Path(image_path).read_bytes()

        t1 = time.time()
        parsed = ocr_service.run(image_bytes, Path(image_path).name, mode="auto")
        inference_s = time.time() - t1

        _STOP = True
        watcher.join(timeout=1)

        raw_json = parsed.get("raw_json")
        words = raw_json.get("words") if isinstance(raw_json, dict) else None

        print(
            json.dumps(
                {
                    "engine": "rapidocr",
                    "image": image_path,
                    "raw_text": parsed.get("raw_text"),
                    "words": words,
                    "bbox_granularity": "word (per detected text region)",
                    "fields": {k: v for k, v in parsed.items() if k not in ("raw_json",)},
                    "cold_start_s": round(cold_start_s, 3),
                    "inference_s": round(inference_s, 3),
                    "total_s": round(time.time() - t0, 3),
                    "peak_rss_mb": round(PEAK_RSS_MB, 1),
                    "error": None,
                },
                default=str,
            )
        )
    except Exception as exc:
        _STOP = True
        print(
            json.dumps(
                {
                    "engine": "rapidocr",
                    "image": image_path,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                    "peak_rss_mb": round(PEAK_RSS_MB, 1),
                }
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
