"""Google Cloud Vision OCR — DOCUMENT_TEXT_DETECTION, tuned for printed + handwritten
text, supports Arabic + Latin script in the same image.

Auth: a simple API key (Cloud Console -> APIs & Services -> Credentials -> API key,
with the Vision API enabled on the project). No service-account JSON needed for this
REST call style.

Usage:
    from google_vision import extract_text_google_vision
    result = extract_text_google_vision(image_bytes, api_key="...")
"""
import base64
from typing import Any

import httpx

GOOGLE_VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def extract_text_google_vision(image_bytes: bytes, api_key: str, timeout: float = 30.0) -> dict[str, Any]:
    """Returns {engine, raw_text, words: [{text, confidence}], error?}."""
    body = {
        "requests": [
            {
                "image": {"content": base64.b64encode(image_bytes).decode("ascii")},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                # Hint both scripts — these bills mix Arabic labels with Latin handwriting.
                "imageContext": {"languageHints": ["ar", "en"]},
            }
        ]
    }
    resp = httpx.post(GOOGLE_VISION_URL, params={"key": api_key}, json=body, timeout=timeout)
    if resp.status_code >= 400:
        return {"engine": "google_vision", "raw_text": "", "words": [], "error": f"{resp.status_code}: {resp.text[:500]}"}

    data = resp.json()
    response = (data.get("responses") or [{}])[0]
    if "error" in response:
        return {"engine": "google_vision", "raw_text": "", "words": [], "error": response["error"].get("message")}

    full_text_annotation = response.get("fullTextAnnotation") or {}
    raw_text = full_text_annotation.get("text", "")

    words: list[dict[str, Any]] = []
    for page in full_text_annotation.get("pages", []):
        for block in page.get("blocks", []):
            for paragraph in block.get("paragraphs", []):
                for word in paragraph.get("words", []):
                    text = "".join(s.get("text", "") for s in word.get("symbols", []))
                    confidence = word.get("confidence")
                    words.append({"text": text, "confidence": confidence})

    return {"engine": "google_vision", "raw_text": raw_text, "words": words, "error": None}
