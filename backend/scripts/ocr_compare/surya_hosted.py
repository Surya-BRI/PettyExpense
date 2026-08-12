"""Surya (Datalab) hosted OCR API — no local llama.cpp/vllm server needed.
Sign up at https://www.datalab.to/ ($5 free credit), get an API key from the dashboard.

Same interface shape as google_vision.py / azure_vision.py / paddle_ocr.py so
run_compare.py can report all engines side by side.

API reference (current, non-deprecated): https://documentation.datalab.to/api-reference/convert-document
  POST https://www.datalab.to/api/v1/convert   (multipart, header X-API-Key)
    -> {success, request_id, request_check_url, ...}
  GET  {request_check_url}                     (header X-API-Key) -- poll until status == "complete"
    -> {status, success, pages / result_url, ...}

The exact JSON shape of the completed result isn't fully documented (block objects with
"html"/"text"/"confidence" fields, per Surya's own model docs) — _walk() below recursively
collects any text-like and confidence-like fields it finds, so this keeps working even if
the schema differs slightly from what the docs describe.
"""
import time
from typing import Any

import httpx

BASE_URL = "https://www.datalab.to/api/v1"


def _walk_collect(node: Any, words: list[dict[str, Any]]) -> None:
    """Recursively pull out anything that looks like recognized text (+ confidence)."""
    if isinstance(node, dict):
        text = node.get("text") or node.get("html")
        if isinstance(text, str) and text.strip():
            words.append({"text": text.strip(), "confidence": node.get("confidence")})
        for value in node.values():
            _walk_collect(value, words)
    elif isinstance(node, list):
        for item in node:
            _walk_collect(item, words)


def extract_text_surya_hosted(
    image_bytes: bytes,
    api_key: str,
    filename: str = "bill.png",
    timeout: float = 60.0,
    poll_interval: float = 2.0,
    max_polls: int = 60,
) -> dict[str, Any]:
    """Returns {engine, raw_text, words: [{text, confidence}], error?}."""
    headers = {"X-API-Key": api_key}

    submit = httpx.post(
        f"{BASE_URL}/convert",
        headers=headers,
        files={"file": (filename, image_bytes, "image/png")},
        data={"output_format": "json", "mode": "accurate"},
        timeout=timeout,
    )
    if submit.status_code >= 400:
        return {"engine": "surya_hosted", "raw_text": "", "words": [], "error": f"{submit.status_code}: {submit.text[:500]}"}

    submitted = submit.json()
    check_url = submitted.get("request_check_url")
    if not check_url:
        return {"engine": "surya_hosted", "raw_text": "", "words": [], "error": f"No request_check_url in response: {submitted}"}

    for _ in range(max_polls):
        time.sleep(poll_interval)
        poll = httpx.get(check_url, headers=headers, timeout=timeout)
        if poll.status_code >= 400:
            return {"engine": "surya_hosted", "raw_text": "", "words": [], "error": f"{poll.status_code}: {poll.text[:500]}"}
        result = poll.json()
        status = result.get("status")
        if status == "complete":
            if not result.get("success", True):
                return {"engine": "surya_hosted", "raw_text": "", "words": [], "error": result.get("error") or "Surya reported failure"}

            payload = result
            result_url = result.get("result_url")
            if result_url:
                dl = httpx.get(result_url, timeout=timeout)
                if dl.status_code < 400:
                    payload = dl.json()

            words: list[dict[str, Any]] = []
            _walk_collect(payload, words)
            raw_text = "\n".join(w["text"] for w in words)
            return {"engine": "surya_hosted", "raw_text": raw_text, "words": words, "error": None}
        if status == "failed":
            return {"engine": "surya_hosted", "raw_text": "", "words": [], "error": result.get("error") or "Surya job failed"}
        # status likely "processing" / "pending" -> keep polling

    return {"engine": "surya_hosted", "raw_text": "", "words": [], "error": "Timed out waiting for Surya result"}
