"""Per-field OCR baseline for one image, one fresh process per invocation.
Records everything Step 1 of the crop-preprocessing investigation needs before
any crop code is written: extracted fields, per-field confidence, input image
dimensions, the OCR-input dimensions after services.ocr_service's 1600px cap,
timing, and peak RAM. No code in services/ is modified by this script -- it
only imports the existing _resize_for_ocr helper to report the real cap
dimensions without duplicating that logic.
Usage: python baseline_field_benchmark.py <image_path>
"""
import json
import sys
import threading
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    image_path = Path(sys.argv[1])
    image_bytes = image_path.read_bytes()

    watcher = threading.Thread(target=_poll_rss, daemon=True)
    watcher.start()

    t0 = time.time()
    from PIL import Image

    from services.ocr_service import _OCR_MAX_SIDE_PX, _resize_for_ocr, ocr_service

    with Image.open(image_path) as img:
        input_dims = img.size  # (width, height)

    ocr_input_bytes = _resize_for_ocr(image_bytes, _OCR_MAX_SIDE_PX)
    with Image.open(__import__("io").BytesIO(ocr_input_bytes)) as resized:
        ocr_dims = resized.size

    cold_start_s = time.time() - t0

    t1 = time.time()
    parsed = ocr_service.run(image_bytes, image_path.name, mode="auto")
    inference_s = time.time() - t1

    _STOP = True
    watcher.join(timeout=1)

    fields = parsed.get("fields", {})
    field_report = {
        name: {"value": info.get("value"), "confidence": info.get("confidence"), "low": info.get("low"), "warning": info.get("warning")}
        for name, info in fields.items()
    }

    print(
        json.dumps(
            {
                "image": image_path.name,
                "input_dims": input_dims,
                "ocr_dims": ocr_dims,
                "overall_confidence": parsed.get("confidence"),
                "fields": field_report,
                "low_confidence_fields": parsed.get("low_confidence_fields"),
                "reconciliation_mismatch": parsed.get("reconciliation_mismatch"),
                "cold_start_s": round(cold_start_s, 3),
                "inference_s": round(inference_s, 3),
                "total_s": round(time.time() - t0, 3),
                "peak_rss_mb": round(PEAK_RSS_MB, 1),
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()
