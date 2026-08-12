import json
import random
import re
from datetime import date
from typing import Any

from config import get_settings


SAMPLE_VENDORS = [
    "Indian Oil Petrol Pump",
    "HP Fuel Station",
    "Bharat Petroleum",
    "Cafe Coffee Day",
    "Hotel Saravana Bhavan",
    "Local Dhaba",
]


def _extract_with_regex(text: str) -> dict[str, Any]:
    amount = None
    amount_match = re.search(
        r"(?:(?:rs\.?|inr|₹)\s*)(\d+(?:[.,]\d{1,2})?)|"
        r"(?:total|amount|grand\s*total)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:[.,]\d{1,2})?)",
        text,
        re.IGNORECASE,
    )
    if amount_match:
        raw = amount_match.group(1) or amount_match.group(2)
        amount = float(raw.replace(",", ""))

    bill_date = None
    date_match = re.search(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        text,
    )
    if date_match:
        bill_date = date_match.group(0)

    vendor = None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines:
        vendor = lines[0][:120]

    return {
        "vendor": vendor or "Unknown Vendor",
        "amount": amount if amount is not None else 0.0,
        "date": bill_date or date.today().isoformat(),
        "confidence": 0.55 if amount is not None else 0.25,
    }


def _stub_ocr(filename_hint: str = "") -> dict[str, Any]:
    vendor = random.choice(SAMPLE_VENDORS)
    amount = round(random.uniform(120, 2500), 2)
    return {
        "vendor": vendor,
        "amount": amount,
        "date": date.today().isoformat(),
        "confidence": 0.82,
        "raw_text": f"{vendor}\nTotal: Rs {amount}\nDate: {date.today().isoformat()}\n{filename_hint}",
        "raw_json": {"engine": "stub", "vendor": vendor, "amount": amount},
    }


def _paddle_ocr(image_bytes: bytes) -> dict[str, Any] | None:
    try:
        import tempfile
        from pathlib import Path

        from paddleocr import PaddleOCR  # type: ignore
    except Exception:
        return None

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        result = ocr.ocr(tmp_path, cls=True)
        Path(tmp_path).unlink(missing_ok=True)

        lines: list[str] = []
        if result:
            for block in result:
                if not block:
                    continue
                for line in block:
                    if line and len(line) >= 2 and line[1]:
                        lines.append(str(line[1][0]))
        raw_text = "\n".join(lines)
        parsed = _extract_with_regex(raw_text)
        return {
            **parsed,
            "raw_text": raw_text,
            "raw_json": {"engine": "paddle", "lines": lines},
        }
    except Exception:
        return None


class OcrService:
    def run(self, image_bytes: bytes, filename: str = "receipt.jpg") -> dict[str, Any]:
        settings = get_settings()
        if settings.ocr_backend == "paddle":
            paddle = _paddle_ocr(image_bytes)
            if paddle:
                return paddle

        # Try light regex on empty / stub path: still return stub values
        stub = _stub_ocr(filename)
        # If caller later wires real text, regex helper remains available
        return {
            "vendor": stub["vendor"],
            "amount": stub["amount"],
            "date": stub["date"],
            "confidence": stub["confidence"],
            "raw_text": stub["raw_text"],
            "raw_json": json.dumps(stub["raw_json"]),
        }

    def extract_from_text(self, text: str) -> dict[str, Any]:
        return _extract_with_regex(text)


ocr_service = OcrService()
