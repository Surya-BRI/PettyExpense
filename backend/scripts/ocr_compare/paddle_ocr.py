"""OCR engine wrapper for the comparison harness — reuses services/ocr_service.py's exact shared-detection pipeline so results never drift from production."""
import sys
from pathlib import Path
from typing import Any, Optional

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Reuses production's exact model config/resize/engine logic (this `from` import isn't affected by services/__init__.py's `ocr_service` name shadowing).
from services.ocr_service import (  # noqa: E402
    _OCR_MAX_SIDE_PX,
    _resize_for_ocr,
    _run_shared_detection_ocr,
)


def extract_words_shared(image_path: str, mode: str = "auto", max_side: Optional[int] = _OCR_MAX_SIDE_PX) -> dict[str, Any]:
    # Runs the real shared-detection pipeline and returns both recognizer readings for debugging: {engine, mode, en: {...}, ar: {...}, error?}.
    try:
        with open(image_path, "rb") as f:
            original_bytes = f.read()
        image_bytes = _resize_for_ocr(original_bytes, max_side) if max_side is not None else original_bytes
        en_words, ar_words = _run_shared_detection_ocr(image_bytes, mode)
    except Exception as exc:  # rapidocr/onnxruntime not installed or failed to init
        return {"engine": "rapidocr", "mode": mode, "en": {"raw_text": "", "words": []}, "ar": {"raw_text": "", "words": []}, "error": str(exc)}

    def _pack(words):
        packed = [{"text": w.text, "confidence": w.confidence, "bounding_box": w.bounding_box} for w in words]
        return {"raw_text": "\n".join(w["text"] for w in packed), "words": packed}

    return {"engine": "rapidocr", "mode": mode, "en": _pack(en_words), "ar": _pack(ar_words), "error": None}
