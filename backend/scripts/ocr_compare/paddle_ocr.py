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


def extract_text_paddle(image_path: str, lang: str = "en") -> dict[str, Any]:
    """lang: 'en' for Latin-script bills, 'ar' for Arabic-script bills.
    Returns {engine, raw_text, words: [{text, confidence}], error?}."""
    try:
        engine = _get_engine(lang)
        results = engine.predict(image_path)
    except Exception as exc:  # PaddleOCR/paddlepaddle not installed or failed to init
        return {"engine": f"paddleocr[{lang}]", "raw_text": "", "words": [], "error": str(exc)}

    words: list[dict[str, Any]] = []
    for r in results:
        texts = r.get("rec_texts", [])
        scores = r.get("rec_scores", [])
        for text, score in zip(texts, scores):
            if text.strip():
                words.append({"text": text, "confidence": float(score)})

    raw_text = "\n".join(w["text"] for w in words)
    return {"engine": f"paddleocr[{lang}]", "raw_text": raw_text, "words": words, "error": None}
