"""Test script for the PaddleOCR RunPod GPU endpoint.

Usage:
    python scripts/test_runpod_ocr.py [path/to/image]

Reads RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY from environment variables
(load them via a local .env file, e.g. with `python-dotenv`, or export
them in your shell). Never hardcode the API key in this file.

Each run appends a row to scripts/ocr_results.csv with the fields the
Flutter app actually tracks (vendor, amount, vat_amount, total_amount,
currency, date) so OCR output can be compared against the real bill
values by filling in the actual_* columns by hand.
"""
import base64
import csv
import json
import os
import re
import sys
import time
from datetime import datetime

import requests

DEFAULT_IMAGE_PATH = "assets/dubai/image (6).png"
RESULTS_CSV = os.path.join(os.path.dirname(__file__), "ocr_results.csv")

CSV_FIELDS = [
    "timestamp",
    "image",
    "ocr_vendor",
    "ocr_amount",
    "ocr_vat_amount",
    "ocr_total_amount",
    "ocr_currency",
    "ocr_date",
    "actual_vendor",
    "actual_amount",
    "actual_vat_amount",
    "actual_total_amount",
    "actual_currency",
    "actual_date",
    "notes",
]

NUMBER_RE = r"([\d,]+\.\d{2})"


def extract_fields(text: str) -> dict:
    """Best-effort extraction of the fields the app tracks. OCR text is noisy,
    so this looks for the last/strongest match of each label rather than
    assuming a fixed layout. Values should still be checked against the
    actual bill."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    def value_after_label(label_pattern, occurrence="last"):
        matches = []
        for i, line in enumerate(lines):
            if re.search(label_pattern, line, re.IGNORECASE):
                # number can be on the same line or one of the next few lines
                same_line = re.search(NUMBER_RE, line)
                if same_line:
                    matches.append(same_line.group(1))
                    continue
                for j in range(i + 1, min(i + 3, len(lines))):
                    m = re.search(NUMBER_RE, lines[j])
                    if m:
                        matches.append(m.group(1))
                        break
        if not matches:
            return ""
        return matches[-1] if occurrence == "last" else matches[0]

    total_amount = value_after_label(r"total\s*amount")
    vat_amount = value_after_label(r"^vat$|vat\s*amount|^vat%")
    amount = value_after_label(r"excl\.?\s*vat")

    date_match = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", text)
    date = date_match[-1] if date_match else ""

    currency = "AED" if "AED" in text.upper() or "DUBAI" in text.upper() else ""

    vendor = lines[0] if lines else ""

    return {
        "ocr_vendor": vendor,
        "ocr_amount": amount,
        "ocr_vat_amount": vat_amount,
        "ocr_total_amount": total_amount,
        "ocr_currency": currency,
        "ocr_date": date,
    }


def log_result(image_path: str, output: dict):
    is_new = not os.path.exists(RESULTS_CSV)
    text = output.get("text", "") if isinstance(output, dict) else ""
    fields = extract_fields(text)

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "image": image_path,
        **fields,
        "actual_vendor": "",
        "actual_amount": "",
        "actual_vat_amount": "",
        "actual_total_amount": "",
        "actual_currency": "",
        "actual_date": "",
        "notes": "",
    }

    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)

    print(f"\nLogged extracted fields to {RESULTS_CSV}:")
    for k in ["ocr_vendor", "ocr_amount", "ocr_vat_amount", "ocr_total_amount", "ocr_currency", "ocr_date"]:
        print(f"  {k}: {row[k]!r}")
    print("Fill in the actual_* columns in the CSV by hand to compare accuracy.")


def main():
    endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID")
    api_key = os.environ.get("RUNPOD_API_KEY")
    if not endpoint_id or not api_key:
        print("Error: set RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY environment variables.")
        sys.exit(1)

    image_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE_PATH

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"input": {"image_base64": encoded_string}}

    print(f"Sending {image_path} to RunPod GPU...")
    run_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    response = requests.post(run_url, headers=headers, json=payload)
    result = response.json()

    if "id" not in result:
        print("Error sending job:", result)
        sys.exit(1)

    job_id = result["id"]
    print(f"Job ID: {job_id}. Waiting for GPU to process...")

    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    while True:
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        status = status_data.get("status")

        if status == "COMPLETED":
            output = status_data.get("output")
            print("\nSUCCESS! Here is the OCR result:")
            print(json.dumps(output, indent=2))
            log_result(image_path, output)
            break
        elif status == "FAILED":
            print("\nFAILED:")
            print(json.dumps(status_data, indent=2))
            break
        else:
            print(f"Status: {status}... waiting 5 seconds")
            time.sleep(5)


if __name__ == "__main__":
    main()
