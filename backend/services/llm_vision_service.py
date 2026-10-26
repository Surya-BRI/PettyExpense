"""Bill reading with an OpenAI vision model -- the only scan pipeline.

The model reads the image itself (not OCR text), which is what fixes handwritten amounts/dates that
never reach the OCR text in usable form. Its answer is mapped into the exact dict shape
OcrService.run() returns, so transaction_service._receipt_payload and the Flutter OcrResult need no
changes. Benchmarked against the rule pipeline in scripts/ocr_compare/llm_vision_compare.py.
"""
import base64
import io
import json
import logging
import time
from datetime import date
from typing import Any, Optional

import httpx
from PIL import Image

from config import get_settings
from extraction import default_currency_for_region

logger = logging.getLogger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"
RUNPOD_BASE_URL = "https://api.runpod.ai/v2/{endpoint_id}/openai/v1"  # official vLLM worker

PROMPT = """You read one photo of a receipt / bill / tax invoice from the UAE or Saudi Arabia.
Text may be English, Arabic or both; some fields may be handwritten. Read the IMAGE carefully.

Return JSON only, following the schema. Rules:
- vendor: the business that issued the bill (the company name printed in the header or logo),
  not a document title like "Tax Invoice" / "Customer Invoice", not a phone clock. For app
  screenshots (Uber, Careem...) use the app brand. Prefer the English name if both are printed.
- date: the bill date as YYYY-MM-DD. GCC bills write day first (05/07/26 = 5 July 2026). If the
  year is missing, assume the most recent past date. Convert Hijri to Gregorian if only Hijri is shown.
- amount: total EXCLUDING VAT. vat_amount: VAT charged (0 if none printed). total_amount: final
  amount payable INCLUDING VAT. They must satisfy amount + vat_amount = total_amount.
- A handwritten "45/" or "45/-" means 45 (the slash is not a digit "1").
- currency: ISO code (AED, SAR, OMR, USD...) or null if nothing on the bill shows it. Decide from
  money words, not place names: ريال / هللة / Riyal / S.R. = SAR; درهم / Dirham / Dhs / AED = AED.
  A city in the company name (e.g. "Sharjah") does not decide the currency.
- bill_number: the invoice / bill / receipt number. Never a TRN / VAT registration number,
  phone number, P.O. Box or IBAN.
- line_items: every purchased item row (empty list if the bill has no item table). For each row
  amount = that row's line total as printed (rightmost money column); quantity as printed;
  vat_percent if the row shows one. Do not include subtotal / VAT / total / payment / change rows.
- line_items_include_vat: true if the row totals already include VAT (sum of rows = total_amount),
  false if VAT is added only at the bottom (sum of rows = amount).
- If the image holds more than one receipt, read the first / top one only.
- For each field give confidence 0..1 for how sure you are of what you read. Use null for a field
  you cannot read rather than guessing; use a low confidence for a guess.
"""

_NUM = {"type": ["number", "null"]}
_STR = {"type": ["string", "null"]}
_CONFIDENCE_KEYS = ["vendor", "date", "amount", "vat_amount", "total_amount", "currency", "bill_number"]
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "vendor", "date", "amount", "vat_amount", "vat_percent", "total_amount", "currency",
        "bill_number", "line_items", "line_items_include_vat", "confidence", "notes",
    ],
    "properties": {
        "vendor": _STR,
        "date": _STR,
        "amount": _NUM,
        "vat_amount": _NUM,
        "vat_percent": _NUM,
        "total_amount": _NUM,
        "currency": _STR,
        "bill_number": _STR,
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["description", "quantity", "amount", "vat_percent"],
                "properties": {"description": {"type": "string"}, "quantity": _NUM, "amount": _NUM, "vat_percent": _NUM},
            },
        },
        "line_items_include_vat": {"type": ["boolean", "null"]},
        "confidence": {
            "type": "object",
            "additionalProperties": False,
            "required": _CONFIDENCE_KEYS,
            "properties": {k: {"type": "number"} for k in _CONFIDENCE_KEYS},
        },
        "notes": _STR,
    },
}

# Fields the confirm screen colours by confidence (confirm_claim_screen.dart isLow()/confidenceFor()).
LOW_CONFIDENCE_THRESHOLD = 0.6
_LLM_TO_APP_FIELD = {
    "vendor": "vendor", "date": "date", "amount": "amount", "vat_amount": "vat_amount",
    "total_amount": "total_amount", "currency": "currency", "bill_number": "invoice_number",
}


class LlmVisionError(RuntimeError):
    """The AI scan failed; the message is safe to show the employee."""


def _image_mime(image_bytes: bytes) -> str:
    try:
        fmt = (Image.open(io.BytesIO(image_bytes)).format or "").lower()
    except Exception as exc:
        raise LlmVisionError("The receipt image could not be opened.") from exc
    return {"png": "image/png", "webp": "image/webp", "gif": "image/gif"}.get(fmt, "image/jpeg")


def call_openai(
    image_bytes: bytes, model: str, api_key: str, reasoning: Optional[str], timeout: float = 60,
    base_url: str = OPENAI_BASE_URL, service: str = "OpenAI", max_tokens: int = 4000,
) -> dict[str, Any]:
    """One chat-completions call with a strict JSON schema against any OpenAI-compatible server
    (OpenAI itself, or the RunPod vLLM worker). Raises LlmVisionError on any failure."""
    if not api_key:
        raise LlmVisionError("Scan is not set up on the server.")
    data_url = f"data:{_image_mime(image_bytes)};base64,{base64.b64encode(image_bytes).decode()}"
    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": f"Today is {date.today().isoformat()}. Extract this bill."},
                {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
            ]},
        ],
        "response_format": {"type": "json_schema", "json_schema": {"name": "bill", "strict": True, "schema": SCHEMA}},
        "max_completion_tokens": max_tokens,
    }
    if reasoning:  # gpt-5* / o-series only
        body["reasoning_effort"] = reasoning
    started = time.monotonic()
    try:
        resp = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions", json=body,
            headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout,
        )
    except httpx.TimeoutException as exc:
        raise LlmVisionError("Scan timed out. Try again.") from exc
    except httpx.HTTPError as exc:
        raise LlmVisionError("Could not reach the scan service. Try again later.") from exc
    elapsed = time.monotonic() - started
    if resp.status_code != 200:
        # Body can echo request details; log a short slice server-side only.
        logger.error("%s vision HTTP %s: %s", service, resp.status_code, resp.text[:300])
        if resp.status_code in (401, 403):
            raise LlmVisionError("Scan is not authorised on the server.")
        if resp.status_code == 429:
            raise LlmVisionError("Scan is busy right now. Try again later.")
        raise LlmVisionError("Scan failed. Try again.")
    try:
        payload = resp.json()
        content = payload["choices"][0]["message"].get("content") or ""
        parsed = json.loads(content)
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.exception("%s vision returned an unreadable answer", service)
        raise LlmVisionError("Couldn't read this bill. Try again.") from exc
    usage = payload.get("usage") or {}
    logger.info(
        "%s vision model=%s prompt_tokens=%s completion_tokens=%s seconds=%.1f",
        service, payload.get("model"), usage.get("prompt_tokens"), usage.get("completion_tokens"), elapsed,
    )
    return {"parsed": parsed, "usage": usage, "seconds": round(elapsed, 2), "model": payload.get("model")}


def _round(v: Any) -> Optional[float]:
    return round(float(v), 2) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _make_lines_vat_inclusive(lines: list[dict[str, Any]], include_vat: Optional[bool], amount: Optional[float],
                              vat: Optional[float], total: Optional[float]) -> None:
    """_replace_line_items treats line amounts as the bill's final, VAT-inclusive figures (total = sum
    of lines). Decide from the arithmetic, not the model's include_vat flag -- on Bab Al Hayat bills the
    model said "excl. VAT" for a "Net Total" column that already includes VAT and discount. Rows that
    add up to the pre-VAT amount get each row's VAT share added; then small rounding drift is absorbed
    into the last line so the lines sum to the bill total exactly."""
    priced = [li for li in lines if li["amount"] is not None]
    if not priced or total is None:
        return
    row_sum = sum(li["amount"] for li in priced)
    tolerance = max(0.05, 0.01 * len(priced))
    already_inclusive = abs(row_sum - total) <= tolerance
    pre_vat_rows = vat and amount is not None and abs(row_sum - amount) <= tolerance
    if not already_inclusive and (pre_vat_rows or (include_vat is False and vat)):
        for li in priced:
            rate = li["vat_percent"]
            share = li["amount"] * rate / 100 if isinstance(rate, (int, float)) else (vat * li["amount"] / row_sum if row_sum else 0)
            li["amount"] = round(li["amount"] + share, 2)
    drift = round(total - sum(li["amount"] for li in priced), 2)
    if drift and abs(drift) <= tolerance:
        priced[-1]["amount"] = round(priced[-1]["amount"] + drift, 2)


def to_ocr_service_shape(llm: dict[str, Any], region_code: Optional[str]) -> dict[str, Any]:
    """Same keys/types OcrService.run() returns, so _receipt_payload and Flutter need no change."""
    amount, vat, total = _round(llm.get("amount")), _round(llm.get("vat_amount")), _round(llm.get("total_amount"))
    # Fill one missing money field from the other two -- same invariant the rule pipeline enforces.
    if total is None and amount is not None:
        total = round(amount + (vat or 0.0), 2)
    if amount is None and total is not None:
        amount = round(total - (vat or 0.0), 2)
    if vat is None and amount is not None and total is not None:
        vat = round(total - amount, 2)
    mismatch = None not in (amount, vat, total) and abs(amount + vat - total) > 0.05

    conf = llm.get("confidence") or {}
    field_confidence = {_LLM_TO_APP_FIELD[k]: float(v) for k, v in conf.items() if k in _LLM_TO_APP_FIELD}
    low = [app for llm_key, app in _LLM_TO_APP_FIELD.items()
           if llm.get(llm_key) in (None, "") or field_confidence.get(app, 0.0) < LOW_CONFIDENCE_THRESHOLD]
    if mismatch:
        low += [f for f in ("amount", "vat_amount", "total_amount") if f not in low]

    # The employee's region beats an unsure guess (e.g. "AED" on a Saudi "ريال" slip) -- same fallback OcrService uses.
    currency = (llm.get("currency") or "").upper()
    if not currency or field_confidence.get("currency", 0.0) < 0.5:
        currency = default_currency_for_region(region_code) or currency
    bill_no = llm.get("bill_number") or None
    overall = round(sum(field_confidence.values()) / len(field_confidence), 2) if field_confidence else 0.0
    line_items = [
        {
            "description": (li.get("description") or "").strip(),
            "quantity": li.get("quantity"),
            "amount": _round(li.get("amount")),
            "confidence": overall,
            "vat_percent": li.get("vat_percent"),
        }
        for li in llm.get("line_items") or []
        if (li.get("description") or "").strip()
    ]
    _make_lines_vat_inclusive(line_items, llm.get("line_items_include_vat"), amount, vat, total)
    return {
        "vendor": llm.get("vendor") or "",
        "expense_type": None,
        "amount": amount,
        "vat_amount": vat,
        "total_amount": total,
        "currency": currency or None,
        "date": llm.get("date") or "",
        "confidence": overall,
        "field_confidence": field_confidence,
        "low_confidence_fields": low,
        "reconciliation_mismatch": mismatch,
        "fields": {"invoice_number": {"value": bill_no, "confidence": field_confidence.get("invoice_number", 0.0)}},
        "line_items": line_items,
        "raw_text": llm.get("notes") or "",
        "raw_json": {"engine": "openai_vision", "llm": llm},
    }


def provider_config(provider: str, settings: Any = None) -> dict[str, Any]:
    """call_openai kwargs for `openai` (hosted GPT) or `runpod` (self-hosted Qwen-VL on our RunPod)."""
    settings = settings or get_settings()
    if provider == "runpod":
        endpoint_id = settings.runpod_vision_endpoint_id.strip()
        if not endpoint_id:
            raise LlmVisionError("Scan is not set up on the server.")
        return {
            "base_url": RUNPOD_BASE_URL.format(endpoint_id=endpoint_id),
            "api_key": settings.runpod_vision_api_key or settings.runpod_api_key,
            "model": settings.runpod_vision_model,
            "reasoning": None,  # reasoning_effort is an OpenAI-only parameter
            "timeout": settings.runpod_vision_timeout_seconds,  # covers a cold start (model load)
            "service": "RunPod",
            # Longest real answer so far ~970 tokens; an open model stuck in a JSON whitespace loop
            # (seen on ksa5 with Qwen3-VL-8B) then fails fast instead of burning billed GPU time.
            "max_tokens": 2500,
        }
    return {
        "base_url": OPENAI_BASE_URL,
        "api_key": settings.openai_api_key,
        "model": settings.openai_vision_model,
        "reasoning": settings.openai_reasoning_effort or None,
        "timeout": settings.openai_timeout_seconds,
        "service": "OpenAI",
        "max_tokens": 4000,  # reasoning tokens count here too
    }


def run_llm_vision(image_bytes: bytes, region_code: Optional[str] = None) -> dict[str, Any]:
    settings = get_settings()
    cfg = provider_config(settings.ai_vision_provider, settings)
    raw = call_openai(
        image_bytes, cfg["model"], cfg["api_key"], cfg["reasoning"],
        timeout=cfg["timeout"], base_url=cfg["base_url"], service=cfg["service"], max_tokens=cfg["max_tokens"],
    )
    result = to_ocr_service_shape(raw["parsed"], region_code)
    result["raw_json"].update(
        provider=settings.ai_vision_provider, model=raw["model"], usage=raw["usage"], seconds=raw["seconds"],
    )
    return result
