import json
import os
import random
from datetime import date
from typing import Any, Optional

from sqlalchemy.orm import Session

from config import get_settings
from extraction import (
    CategoryRef,
    OcrWord,
    ReferenceData,
    default_tax_rules_for_region,
    dedupe_lines,
    extract,
    extract_from_text_input,
    group_into_lines,
    to_legacy_dict,
    words_from_text,
)

# PaddleOCR 3.x's oneDNN CPU backend crashes on some Windows setups with
# `NotImplementedError: ConvertPirAttribute2RuntimeAttribute ...` before any real
# OCR runs. Must be set before paddleocr/paddlepaddle is imported.
os.environ.setdefault("FLAGS_use_mkldnn", "0")

_paddle_engines: dict[str, Any] = {}

SAMPLE_VENDORS = [
    "Indian Oil Petrol Pump",
    "HP Fuel Station",
    "Bharat Petroleum",
    "Cafe Coffee Day",
    "Hotel Saravana Bhavan",
    "Local Dhaba",
]

# Reference data (known vendors, categories, currency/VAT-rate priors) is
# injected from the DB/config rather than hard-coded — see refresh_reference_data().
# A safe, fully-functional default is used until the first refresh (e.g. in tests
# or before any request has run one), so this module never hard-fails on import.
_reference_data: ReferenceData = ReferenceData()


def refresh_reference_data(db: Session, region_code: Optional[str] = None) -> None:
    """Rebuilds the cached ReferenceData from the DB (vendors/categories) and
    the shipped tax-rules config (currency/VAT-rate priors). Called once per
    OCR request by transaction_service — adding a vendor or category via the
    existing admin UI flows into extraction with zero engine code changes."""
    global _reference_data
    from database.models import ErpExpenseCategory, ErpExpenseVendor

    vendors = tuple(
        row[0]
        for row in db.query(ErpExpenseVendor.vendor_name).filter(ErpExpenseVendor.is_active == 1).all()
        if row[0]
    )
    categories = tuple(
        CategoryRef(name=c.category_name, name_ar=c.category_name_ar)
        for c in db.query(ErpExpenseCategory).filter(ErpExpenseCategory.is_active == 1).all()
    )
    currencies, rates = default_tax_rules_for_region(region_code)
    _reference_data = ReferenceData(
        known_vendors=vendors,
        categories=categories,
        valid_currency_codes=currencies,
        plausible_vat_rates=rates,
    )


def _get_paddle_engine(lang: str):
    if lang not in _paddle_engines:
        from paddleocr import PaddleOCR  # type: ignore  # imported lazily — heavy dependency

        _paddle_engines[lang] = PaddleOCR(lang=lang, enable_mkldnn=False)
    return _paddle_engines[lang]


def _poly_to_bbox(poly: Any) -> Optional[tuple[float, float, float, float]]:
    try:
        xs = [float(p[0]) for p in poly]
        ys = [float(p[1]) for p in poly]
        return (min(xs), min(ys), max(xs), max(ys))
    except (TypeError, IndexError, ValueError):
        return None


def _paddle_ocr_pass(image_path: str, lang: str) -> list[OcrWord]:
    """Paddle has no mixed-script model, so bilingual bills need both 'en' and 'ar' passes."""
    engine = _get_paddle_engine(lang)
    results = engine.predict(image_path)
    words: list[OcrWord] = []
    order = 0
    for r in results:
        texts = r.get("rec_texts", [])
        scores = r.get("rec_scores", [])
        polys = r.get("rec_polys") or r.get("dt_polys") or []
        for idx, (text, score) in enumerate(zip(texts, scores)):
            if not text.strip():
                continue
            bbox = _poly_to_bbox(polys[idx]) if idx < len(polys) else None
            words.append(
                OcrWord(text=text, confidence=float(score), lang=lang, bounding_box=bbox, page=1, reading_order=order, source_pass="paddle")
            )
            order += 1
    return words


def _paddle_ocr(image_bytes: bytes) -> dict[str, Any] | None:
    try:
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            en_words = _paddle_ocr_pass(tmp_path, "en")
            ar_words = _paddle_ocr_pass(tmp_path, "ar")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except Exception:
        return None

    words = en_words + ar_words
    result = extract(dedupe_lines(group_into_lines(words)), _reference_data)
    parsed = to_legacy_dict(result)
    parsed["raw_text"] = result.raw_text
    parsed["raw_json"] = {
        "engine": "paddle",
        "words": [{"text": w.text, "confidence": w.confidence, "lang": w.lang, "bounding_box": w.bounding_box} for w in words],
        "field_confidence": parsed["field_confidence"],
        "low_confidence_fields": parsed["low_confidence_fields"],
        "expense_type": parsed["expense_type"],
    }
    return parsed


def _stub_ocr(filename_hint: str = "") -> dict[str, Any]:
    vendor = random.choice(SAMPLE_VENDORS)
    amount = round(random.uniform(120, 2500), 2)
    vat_amount = round(amount * 0.05, 2)
    total_amount = round(amount + vat_amount, 2)
    text = (
        f"{vendor}\nTAX INVOICE\nBill Amount: {total_amount}\nVAT 5%: {vat_amount}\n"
        f"Amount (Excl.Vat): {amount}\nDate: {date.today().isoformat()}\n{filename_hint}"
    )
    result = extract_from_text_input(text, _reference_data)
    parsed = to_legacy_dict(result)
    parsed["raw_text"] = f"{vendor}\nBill Amount: {total_amount}\nVAT: {vat_amount}\nDate: {date.today().isoformat()}\n{filename_hint}"
    parsed["raw_json"] = {"engine": "stub", "vendor": vendor, "amount": amount, "field_confidence": parsed["field_confidence"]}
    return parsed


class OcrService:
    def run(self, image_bytes: bytes, filename: str = "receipt.jpg") -> dict[str, Any]:
        settings = get_settings()
        if settings.ocr_backend == "paddle":
            paddle = _paddle_ocr(image_bytes)
            if paddle:
                return paddle

        stub = _stub_ocr(filename)
        stub["raw_json"] = json.dumps(stub["raw_json"])
        return stub

    def extract_from_text(self, text: str, words: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
        ocr_words = (
            [
                OcrWord(
                    text=w.get("text", ""), confidence=float(w.get("confidence", 1.0)), lang=w.get("lang", "en"),
                    bounding_box=w.get("bounding_box"), reading_order=i,
                )
                for i, w in enumerate(words)
                if (w.get("text") or "").strip()
            ]
            if words
            else words_from_text(text)
        )
        lines = dedupe_lines(group_into_lines(ocr_words))
        return to_legacy_dict(extract(lines, _reference_data))

    def merge_bilingual(
        self,
        en_text: str,
        ar_text: str,
        en_words: Optional[list[dict[str, Any]]] = None,
        ar_words: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Combines the English- and Arabic-pass OCR output into one word
        list and extracts once — dedup (stage 3) and per-candidate scoring
        (stage 6) let the better-recognized language win per field, rather
        than parsing each language separately and merging afterward."""
        en_ocr_words = (
            [
                OcrWord(
                    text=w.get("text", ""), confidence=float(w.get("confidence", 1.0)), lang="en",
                    bounding_box=w.get("bounding_box"), reading_order=i, source_pass="en_pass",
                )
                for i, w in enumerate(en_words)
                if (w.get("text") or "").strip()
            ]
            if en_words
            else [OcrWord(text=w.text, confidence=w.confidence, lang=w.lang, reading_order=w.reading_order, source_pass="en_pass") for w in words_from_text(en_text or "")]
        )
        ar_ocr_words = (
            [
                OcrWord(
                    text=w.get("text", ""), confidence=float(w.get("confidence", 1.0)), lang="ar",
                    bounding_box=w.get("bounding_box"), reading_order=i, source_pass="ar_pass",
                )
                for i, w in enumerate(ar_words)
                if (w.get("text") or "").strip()
            ]
            if ar_words
            else [OcrWord(text=w.text, confidence=w.confidence, lang="ar", reading_order=w.reading_order, source_pass="ar_pass") for w in words_from_text(ar_text or "")]
        )
        lines = dedupe_lines(group_into_lines(en_ocr_words + ar_ocr_words))
        return to_legacy_dict(extract(lines, _reference_data))


ocr_service = OcrService()
