"""PaddleOCR — the only OCR engine this project uses.

First call downloads model weights (cached under ~/.paddlex/official_models/) —
expect the first run per language to be slow, subsequent runs fast.

PaddleOCR 3.x note: MKLDNN/oneDNN CPU inference crashes on this Windows setup with
`NotImplementedError: ConvertPirAttribute2RuntimeAttribute ...` — enable_mkldnn=False
works around it. If you're on a different machine and don't hit that crash, this
still works fine with mkldnn enabled.
"""
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("FLAGS_use_mkldnn", "0")

_engines: dict[str, Any] = {}  # cached per-language PaddleOCR instances


def _get_engine(lang: str):
    if lang not in _engines:
        from paddleocr import PaddleOCR  # imported lazily — heavy dependency

        _engines[lang] = PaddleOCR(lang=lang, enable_mkldnn=False)
    return _engines[lang]


def _poly_to_bbox(poly: Any):
    try:
        xs = [float(p[0]) for p in poly]
        ys = [float(p[1]) for p in poly]
        return (min(xs), min(ys), max(xs), max(ys))
    except (TypeError, IndexError, ValueError):
        return None


def extract_text_paddle(image_path: str, lang: str = "en") -> dict[str, Any]:
    """lang: 'en' for Latin-script bills, 'ar' for Arabic-script bills.
    Returns {engine, raw_text, words: [{text, confidence, bounding_box}], error?}.
    Mirrors services/ocr_service.py's production wrapper (including bounding-box
    capture) so this comparison harness exercises the same geometry-aware
    candidate generation real uploads get, not a text-only degraded path."""
    try:
        engine = _get_engine(lang)
        results = engine.predict(image_path)
    except Exception as exc:  # PaddleOCR/paddlepaddle not installed or failed to init
        return {"engine": f"paddleocr[{lang}]", "raw_text": "", "words": [], "error": str(exc)}

    words: list[dict[str, Any]] = []
    for r in results:
        texts = r.get("rec_texts", [])
        scores = r.get("rec_scores", [])
        polys = r.get("rec_polys") or r.get("dt_polys") or []
        for idx, (text, score) in enumerate(zip(texts, scores)):
            if text.strip():
                bbox = _poly_to_bbox(polys[idx]) if idx < len(polys) else None
                words.append({"text": text, "confidence": float(score), "bounding_box": bbox})

    raw_text = "\n".join(w["text"] for w in words)
    return {"engine": f"paddleocr[{lang}]", "raw_text": raw_text, "words": words, "error": None}
