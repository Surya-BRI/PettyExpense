import json
import logging
import random
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)

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

_OCR_MODES = ("auto", "en", "ar")
_DEFAULT_OCR_MODE = "auto"

SAMPLE_VENDORS = [
    "Indian Oil Petrol Pump",
    "HP Fuel Station",
    "Bharat Petroleum",
    "Cafe Coffee Day",
    "Hotel Saravana Bhavan",
    "Local Dhaba",
]

# Reference data is injected from the DB/config, not hard-coded (see refresh_reference_data()); a safe default is used until the first refresh.
_reference_data: ReferenceData = ReferenceData()


def refresh_reference_data(db: Session, region_code: Optional[str] = None) -> None:
    # Rebuilds the cached ReferenceData from the DB and tax-rules config; called once per request so admin-added vendors/categories flow in automatically.
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


# Single-engine RapidOCR/ONNXRuntime pipeline: ONE shared detection pass, then up to two SEQUENTIAL recognizers (English, then Arabic) reuse the same crops.
_TEXT_DETECTION_LANG = "ch"  # any PP-OCRv6-supported value; detection itself is language-agnostic
_REC_ENGINE_CONFIG = {
    "en": {"lang_type": "EN", "model_type": "SMALL", "ocr_version": "PPOCRV6"},
    "ar": {"lang_type": "ARABIC", "model_type": "MOBILE", "ocr_version": "PPOCRV5"},
}
# Resize the OCR *input* copy only — the caller's original image_bytes is never touched; extraction's geometry reasoning is scale-relative so this is safe.
_OCR_MAX_SIDE_PX = 1600

_rapid_engines: dict[str, Any] = {}


def _get_rapid_engine(rec_lang: str):
    # One RapidOCR instance per recognizer ("en"/"ar"), cached for the process lifetime; only the "en" instance's detector is ever invoked.
    if rec_lang not in _rapid_engines:
        from rapidocr import RapidOCR  # type: ignore  # imported lazily — heavy dependency
        from rapidocr.utils.typings import LangDet, LangRec, ModelType, OCRVersion  # type: ignore

        rec_cfg = _REC_ENGINE_CONFIG[rec_lang]
        _rapid_engines[rec_lang] = RapidOCR(
            params={
                "Det.lang_type": LangDet(_TEXT_DETECTION_LANG),
                "Det.model_type": ModelType.SMALL,
                "Det.ocr_version": OCRVersion.PPOCRV6,
                "Rec.lang_type": LangRec[rec_cfg["lang_type"]],
                "Rec.model_type": ModelType[rec_cfg["model_type"]],
                "Rec.ocr_version": OCRVersion[rec_cfg["ocr_version"]],
                "Global.use_cls": False,
            }
        )
    return _rapid_engines[rec_lang]


def _resize_for_ocr(image_bytes: bytes, max_side: int) -> bytes:
    # Returns a downscaled JPEG copy for OCR input only; never mutates the caller's original bytes, and only downscales, preserving aspect ratio.
    from io import BytesIO

    from PIL import Image

    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        width, height = img.size
        longest = max(width, height)
        if longest <= max_side:
            resized = img
        else:
            scale = max_side / float(longest)
            new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
            resized = img.resize(new_size, Image.LANCZOS)
        buf = BytesIO()
        resized.save(buf, format="JPEG", quality=92)
        return buf.getvalue()


def _poly_to_bbox(poly: Any) -> Optional[tuple[float, float, float, float]]:
    try:
        xs = [float(p[0]) for p in poly]
        ys = [float(p[1]) for p in poly]
        return (min(xs), min(ys), max(xs), max(ys))
    except (TypeError, IndexError, ValueError):
        return None


def _words_from_recognition(
    rec_res: Any, boxes: Any, lang: str, source_pass: str, region_indices: Optional[list[int]] = None
) -> list[OcrWord]:
    # boxes/region_indices are in rec_res's own index space; region_indices maps back to the ORIGINAL region index after filtering (the auto-mode Arabic retry), keeping bbox/reading_order correct without mutating a frozen OcrWord. Omitted => recognition ran on every region, so reading_order == j already.
    words: list[OcrWord] = []
    if rec_res is None or rec_res.txts is None:
        return words
    for j, (text, score) in enumerate(zip(rec_res.txts, rec_res.scores)):
        if not text or not text.strip():
            continue
        bbox = _poly_to_bbox(boxes[j]) if boxes is not None and j < len(boxes) else None
        reading_order = region_indices[j] if region_indices is not None else j
        words.append(
            OcrWord(text=text, confidence=float(score), lang=lang, bounding_box=bbox, page=1, reading_order=reading_order, source_pass=source_pass)
        )
    return words


# Below this English-recognizer confidence, "auto" mode retries the region in Arabic. Calibrated on real receipts: clean printed English scores 0.93+, genuinely-Arabic regions score 0.43-0.47. Retry decision only — never used to compare the two engines' scores to pick a winner.
_ARABIC_RETRY_CONFIDENCE_THRESHOLD = 0.90
# The English model's other failure signature on non-Latin script: its output is dominated by non-ASCII characters even when it emits something.
_ARABIC_RETRY_NON_ASCII_FRACTION = 0.30


def _needs_arabic_retry(text: str, score: float) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True  # the English pass found nothing at all on this region
    if score < _ARABIC_RETRY_CONFIDENCE_THRESHOLD:
        return True
    non_ascii = sum(1 for c in stripped if ord(c) > 127)
    return (non_ascii / len(stripped)) > _ARABIC_RETRY_NON_ASCII_FRACTION


def _normalize_mode(mode: Optional[str]) -> str:
    mode = (mode or _DEFAULT_OCR_MODE).strip().lower()
    return mode if mode in _OCR_MODES else _DEFAULT_OCR_MODE


def _run_shared_detection_ocr(image_bytes: bytes, mode: str) -> tuple[list[OcrWord], list[OcrWord]]:
    # Detection runs once; recognizers run SEQUENTIALLY per `mode` (en-only, ar-primary+en-fallback, or auto-retry — see _needs_arabic_retry), returning (en_words, ar_words) for dedup to arbitrate.
    engine_en = _get_rapid_engine("en")
    ori_img = engine_en.load_img(image_bytes)
    img, op_record = engine_en.preprocess_img(ori_img)
    crops, det_res = engine_en.detect_and_crop(img, op_record)  # detection runs exactly once
    if det_res.boxes is None or not crops:
        return [], []

    ori_h, ori_w = ori_img.shape[:2]
    from rapidocr.utils.process_img import map_boxes_to_original  # type: ignore

    boxes = map_boxes_to_original(det_res.boxes, op_record, ori_h, ori_w)

    # English recognition always runs — primary for "en"/"auto", documented fallback for "ar". Only the Arabic recognizer is mode-conditional.
    en_rec = engine_en.recognize_txt(crops)
    en_words = _words_from_recognition(en_rec, boxes, "en", "rapidocr_en")

    ar_words: list[OcrWord] = []
    if mode == "ar":
        # Arabic is primary in this mode — every region, unconditionally, no retry filter.
        engine_ar = _get_rapid_engine("ar")
        ar_rec = engine_ar.recognize_txt(crops)  # sequential — reuses the SAME crops, no second detection
        ar_words = _words_from_recognition(ar_rec, boxes, "ar", "rapidocr_ar")
    elif mode == "auto":
        retry_indices = [
            i for i, (text, score) in enumerate(zip(en_rec.txts or (), en_rec.scores or ()))
            if _needs_arabic_retry(text, score)
        ]
        logger.info(
            "Arabic retry (auto mode): %d/%d regions selected for a second reading",
            len(retry_indices), len(crops),
        )
        if retry_indices:
            engine_ar = _get_rapid_engine("ar")
            retry_crops = [crops[i] for i in retry_indices]
            retry_boxes = [boxes[i] for i in retry_indices]
            ar_rec = engine_ar.recognize_txt(retry_crops)  # sequential, on the FILTERED subset only
            ar_words = _words_from_recognition(ar_rec, retry_boxes, "ar", "rapidocr_ar", region_indices=retry_indices)
    # mode == "en": ar_words stays empty — the Arabic model is never loaded or invoked.
    return en_words, ar_words


def _run_ocr(image_bytes: bytes, mode: str = _DEFAULT_OCR_MODE) -> dict[str, Any] | None:
    mode = _normalize_mode(mode)
    try:
        ocr_input_bytes = _resize_for_ocr(image_bytes, _OCR_MAX_SIDE_PX)
        en_words, ar_words = _run_shared_detection_ocr(ocr_input_bytes, mode)
    except Exception:
        # Logged loudly (with traceback) — OcrService.run treats a None here as a real failure, not license to hand back fake financial data.
        logger.exception("Real OCR pipeline failed (mode=%s)", mode)
        return None

    # Each language is line-grouped independently, then combined — dedupe_lines only collapses genuinely redundant lines, so two differing readings of one region survive as separate candidates.
    lines = dedupe_lines(group_into_lines(en_words) + group_into_lines(ar_words))
    result = extract(lines, _reference_data)
    parsed = to_legacy_dict(result)
    parsed["raw_text"] = result.raw_text
    parsed["raw_json"] = {
        "engine": "rapidocr",
        "mode": mode,
        "words": [
            {"text": w.text, "confidence": w.confidence, "lang": w.lang, "bounding_box": w.bounding_box}
            for w in en_words + ar_words
        ],
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
    def run(self, image_bytes: bytes, filename: str = "receipt.jpg", mode: str = _DEFAULT_OCR_MODE) -> dict[str, Any]:
        settings = get_settings()
        # "paddle" predates this engine rewrite; it now just means "run the real OCR pipeline" (RapidOCR-only today).
        if settings.ocr_backend == "paddle":
            real = _run_ocr(image_bytes, mode)
            if real:
                return real
            # Real engine failed (already logged) — must NOT fall through to fake stub data; raise so the app's "enter manually" UX takes over.
            raise RuntimeError(
                "OCR pipeline failed to process this receipt — see server logs for the underlying exception."
            )

        # Only reached when ocr_backend is explicitly NOT "paddle" — never as a silent fallback from a real OCR failure.
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
        # Combines the English- and Arabic-pass output into one word list and extracts once — dedup + scoring let the better-recognized language win.
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
