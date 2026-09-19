"""Feeds PaddleOCR-VL's recognized raw_text through the production extraction
pipeline (services.ocr_service.extract_from_text), for a fair comparison of
structured-field output against RapidOCR. Runs under backend/.venv.
Usage: python paddle_vl_extract.py <paddle_vl_output.json>
PaddleOCR-VL gives no bounding boxes finer than block-level and no per-word
confidence, so this necessarily goes through the geometry-less text fallback
(extraction.normalize.words_from_text), which hardcodes confidence=1.0 for
every word. That is reported explicitly, not silently accepted.
"""
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_ROOT / ".env")

from services.ocr_service import ocr_service  # noqa: E402


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw_text = payload.get("raw_text") or ""
    fields = ocr_service.extract_from_text(raw_text)
    print(
        json.dumps(
            {
                "engine": "paddle_vl",
                "image": payload.get("image"),
                "structured_fields": fields,
                "disabled_pipeline_features": [
                    "same_row / same_line / column-alignment candidate scoring — no per-word or per-line bounding boxes exist, only block-level boxes, so geometry-based label-value pairing cannot run",
                    "low_ocr_confidence_possible_handwriting — words_from_text() hardcodes confidence=1.0 for every word, so this flag can never fire regardless of actual recognition quality",
                    "per-word position_prior / reading_order signals collapse to one-line-per-source-line ordering, not real spatial layout",
                ],
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()
