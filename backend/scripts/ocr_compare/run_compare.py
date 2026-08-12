"""Side-by-side OCR comparison: Google Cloud Vision vs Azure AI Vision Read API,
against real sample bill images (drop them into scripts/ocr_compare/samples/).

Run from backend/:
    set GOOGLE_VISION_API_KEY=...
    set AZURE_VISION_ENDPOINT=https://<resource>.cognitiveservices.azure.com
    set AZURE_VISION_KEY=...
    python scripts/ocr_compare/run_compare.py

Either engine can be skipped by leaving its env vars unset — the script just
reports "skipped (no key)" for that engine and still runs the other.
"""
import os
import re
import sys
from pathlib import Path

# Windows terminals default stdout to cp1252, which can't encode Arabic text —
# force UTF-8 so Arabic OCR output doesn't crash the print statements below.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))  # for services.ocr_service
load_dotenv(BACKEND_ROOT / ".env")

from services.ocr_service import ocr_service  # noqa: E402  (regex field parser, reused as-is)

from azure_vision import extract_text_azure_vision
from google_vision import extract_text_google_vision
from paddle_ocr import extract_text_paddle
from surya_hosted import extract_text_surya_hosted

SAMPLES_DIR = Path(__file__).parent / "samples"

# Arabic-Indic digits -> ASCII, so the regex field parser works regardless of which
# numeral style a bill (or an engine's transcription of it) uses.
_ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def normalize_digits(text: str) -> str:
    return text.translate(_ARABIC_INDIC_DIGITS)


def run_one(
    image_path: Path,
    google_key: str | None,
    azure_endpoint: str | None,
    azure_key: str | None,
    surya_key: str | None,
    run_paddle: bool,
) -> None:
    print(f"\n{'=' * 70}\n{image_path.name}\n{'=' * 70}")
    image_bytes = image_path.read_bytes()

    if google_key:
        g = extract_text_google_vision(image_bytes, google_key)
        _report("Google Cloud Vision", g)
    else:
        print("\n-- Google Cloud Vision: skipped (no GOOGLE_VISION_API_KEY) --")

    if azure_endpoint and azure_key:
        a = extract_text_azure_vision(image_bytes, azure_endpoint, azure_key)
        _report("Azure AI Vision (Read)", a)
    else:
        print("\n-- Azure AI Vision: skipped (no AZURE_VISION_ENDPOINT/AZURE_VISION_KEY) --")

    if surya_key:
        s = extract_text_surya_hosted(image_bytes, surya_key, filename=image_path.name)
        _report("Surya (hosted API)", s)
    else:
        print("\n-- Surya hosted API: skipped (no SURYA_API_KEY) --")

    if run_paddle:
        p_en = extract_text_paddle(str(image_path), lang="en")
        _report("PaddleOCR (lang=en)", p_en)
        p_ar = extract_text_paddle(str(image_path), lang="ar")
        _report("PaddleOCR (lang=ar)", p_ar)


def _report(label: str, result: dict) -> None:
    print(f"\n-- {label} --")
    if result.get("error"):
        print(f"  ERROR: {result['error']}")
        return
    raw_text = result["raw_text"]
    print("  raw text:")
    for line in raw_text.splitlines():
        print(f"    {line}")

    normalized = normalize_digits(raw_text)
    fields = ocr_service.extract_from_text(normalized)
    print(f"  parsed fields (regex, reused from ocr_service.py): {fields}")

    low_confidence = [w for w in result["words"] if w.get("confidence") is not None and w["confidence"] < 0.5]
    if low_confidence:
        print(f"  low-confidence words (<0.5): {low_confidence}")


def main() -> None:
    google_key = os.environ.get("GOOGLE_VISION_API_KEY")
    azure_endpoint = os.environ.get("AZURE_VISION_ENDPOINT")
    azure_key = os.environ.get("AZURE_VISION_KEY")
    surya_key = os.environ.get("SURYA_API_KEY")

    # Optional CLI args: a subfolder name under samples/ (e.g. "ksa"), and/or "--no-paddle"
    # to skip the free self-hosted engine (it's slow on first run — downloads model weights).
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run_paddle = "--no-paddle" not in sys.argv[1:]
    root = SAMPLES_DIR / args[0] if args else SAMPLES_DIR
    images = sorted(
        p for p in root.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )
    if not images:
        print(f"No sample images found under {root} — drop your test bill photos there (.jpg/.png) and re-run.")
        return

    for image_path in images:
        run_one(image_path, google_key, azure_endpoint, azure_key, surya_key, run_paddle)


if __name__ == "__main__":
    main()
