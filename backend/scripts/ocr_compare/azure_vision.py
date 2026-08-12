"""Azure AI Vision Read API (v3.2) — async OCR, tuned for printed + handwritten text,
supports Arabic + Latin script in the same image, per-word confidence.

Auth: an Azure AI Vision (Computer Vision) resource's endpoint + subscription key
(Azure Portal -> your Vision resource -> Keys and Endpoint).

Usage:
    from azure_vision import extract_text_azure_vision
    result = extract_text_azure_vision(image_bytes, endpoint="https://<resource>.cognitiveservices.azure.com", key="...")
"""
import time
from typing import Any

import httpx


def extract_text_azure_vision(
    image_bytes: bytes,
    endpoint: str,
    key: str,
    timeout: float = 30.0,
    poll_interval: float = 1.0,
    max_polls: int = 20,
) -> dict[str, Any]:
    """Returns {engine, raw_text, words: [{text, confidence}], error?}."""
    endpoint = endpoint.rstrip("/")
    submit_url = f"{endpoint}/vision/v3.2/read/analyze"
    headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/octet-stream"}

    submit_resp = httpx.post(submit_url, headers=headers, content=image_bytes, timeout=timeout)
    if submit_resp.status_code != 202:
        return {"engine": "azure_vision", "raw_text": "", "words": [], "error": f"{submit_resp.status_code}: {submit_resp.text[:500]}"}

    operation_location = submit_resp.headers.get("Operation-Location")
    if not operation_location:
        return {"engine": "azure_vision", "raw_text": "", "words": [], "error": "No Operation-Location header returned"}

    poll_headers = {"Ocp-Apim-Subscription-Key": key}
    for _ in range(max_polls):
        time.sleep(poll_interval)
        poll_resp = httpx.get(operation_location, headers=poll_headers, timeout=timeout)
        if poll_resp.status_code >= 400:
            return {"engine": "azure_vision", "raw_text": "", "words": [], "error": f"{poll_resp.status_code}: {poll_resp.text[:500]}"}
        result = poll_resp.json()
        status = result.get("status")
        if status == "succeeded":
            lines_text: list[str] = []
            words: list[dict[str, Any]] = []
            for page in result.get("analyzeResult", {}).get("readResults", []):
                for line in page.get("lines", []):
                    lines_text.append(line.get("text", ""))
                    for word in line.get("words", []):
                        words.append({"text": word.get("text", ""), "confidence": word.get("confidence")})
            return {"engine": "azure_vision", "raw_text": "\n".join(lines_text), "words": words, "error": None}
        if status == "failed":
            return {"engine": "azure_vision", "raw_text": "", "words": [], "error": "Azure Read job failed"}
        # status in ("notStarted", "running") -> keep polling

    return {"engine": "azure_vision", "raw_text": "", "words": [], "error": "Timed out waiting for Azure Read result"}
