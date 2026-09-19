"""Helpers for building synthetic mocked-OCR input in tests — no real images,
no vendor-specific matching, just plain OcrWord/OcrLine construction."""
from extraction.types import BoundingBox, OcrLine, OcrWord
from typing import Optional


def word(
    text: str,
    confidence: float = 0.95,
    bbox: Optional[BoundingBox] = None,
    lang: str = "en",
    order: int = 0,
    source_pass: str = "paddle",
) -> OcrWord:
    return OcrWord(text=text, confidence=confidence, lang=lang, bounding_box=bbox, page=1, reading_order=order, source_pass=source_pass)


def line(
    text: str,
    bbox: Optional[BoundingBox] = None,
    order: int = 0,
    confidence: float = 0.95,
    lang: str = "en",
) -> OcrLine:
    w = word(text, confidence=confidence, bbox=bbox, lang=lang, order=order)
    return OcrLine(text=text, words=(w,), confidence=confidence, bounding_box=bbox, page=1, reading_order=order)


def receipt(*lines: OcrLine) -> list[OcrLine]:
    return list(lines)
