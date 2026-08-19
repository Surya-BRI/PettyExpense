"""Run PaddleOCR (en + ar) against sample bill photos.

Run from backend/:
    python scripts/ocr_compare/run_compare.py [subfolder]

`subfolder` is optional — a folder under assets/ (repo root), e.g. `dubai` or `ksa`.
"""
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

from paddle_ocr import extract_text_paddle

SAMPLES_DIR = BACKEND_ROOT.parent / "assets"

# Arabic-Indic digits -> ASCII, so the regex field parser works regardless of which
# numeral style a bill (or an engine's transcription of it) uses.
_ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def normalize_digits(text: str) -> str:
    return text.translate(_ARABIC_INDIC_DIGITS)


def _fields_of(result: dict) -> dict:
    if result.get("error"):
        return {"error": result["error"]}
    return ocr_service.extract_from_text(normalize_digits(result.get("raw_text") or ""), result.get("words"))


def _merged_fields_of(en_result: dict, ar_result: dict) -> dict:
    """Mirrors production (`ocr_service._paddle_ocr`): parse each language pass
    separately and merge field-by-field, rather than showing only the `en` pass."""
    if en_result.get("error") and ar_result.get("error"):
        return {"error": en_result["error"]}
    return ocr_service.merge_bilingual(
        normalize_digits(en_result.get("raw_text") or ""),
        normalize_digits(ar_result.get("raw_text") or ""),
        en_result.get("words"),
        ar_result.get("words"),
    )


def _low_confidence(result: dict) -> list:
    return [
        w for w in result.get("words") or []
        if w.get("confidence") is not None and w["confidence"] < 0.5
    ]


def run_one(image_path: Path) -> dict:
    print(f"\n{'=' * 70}\n{image_path.name}\n{'=' * 70}")
    p_en = extract_text_paddle(str(image_path), lang="en")
    _report("PaddleOCR (lang=en)", p_en)
    p_ar = extract_text_paddle(str(image_path), lang="ar")
    _report("PaddleOCR (lang=ar)", p_ar)
    merged = _merged_fields_of(p_en, p_ar)
    print(f"\n-- Merged (production) --\n  parsed fields: {merged}")
    return {"name": image_path.name, "en": p_en, "ar": p_ar}


def _report(label: str, result: dict) -> None:
    print(f"\n-- {label} --")
    if result.get("error"):
        print(f"  ERROR: {result['error']}")
        return
    raw_text = result["raw_text"]
    print("  raw text:")
    for line in raw_text.splitlines():
        print(f"    {line}")

    fields = _fields_of(result)
    print(f"  parsed fields (regex, reused from ocr_service.py): {fields}")

    low_confidence = _low_confidence(result)
    if low_confidence:
        print(f"  low-confidence words (<0.5): {low_confidence}")


def _md_escape(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("```", "'''")
    # Raw OCR lines routinely carry trailing spaces (garbled recognition,
    # stray whitespace tokens) — strip per-line so the generated report never
    # introduces trailing-whitespace diff-check warnings.
    return "\n".join(line.rstrip() for line in text.split("\n"))


def _md_pass(label: str, result: dict) -> str:
    if result.get("error"):
        return f"### {label}\n\nERROR: {result['error']}\n"
    fields = _fields_of(result)
    low = _low_confidence(result)
    raw = _md_escape(result.get("raw_text") or "")
    low_line = ", ".join(f"{w.get('text')} ({w.get('confidence'):.2f})" for w in low) if low else "(none)"
    return (
        f"### {label}\n\n"
        f"**Parsed fields:** `{fields}`\n\n"
        f"**Low-confidence words (<0.5):** {low_line}\n\n"
        f"**Raw text:**\n\n```\n{raw}\n```\n"
    )


def _md_merged(en_result: dict, ar_result: dict) -> str:
    fields = _merged_fields_of(en_result, ar_result)
    return f"### Merged (production)\n\n**Parsed fields:** `{fields}`\n"


def write_markdown(out_path: Path, folder: str, rows: list[dict]) -> None:
    lines = [
        f"# PaddleOCR results — {folder}",
        "",
        "Engine: PaddleOCR only (`lang=en` then `lang=ar`).",
        "Summary reflects the merged (production) result — see `ocr_service.merge_bilingual`:",
        "each language pass is parsed separately and merged field-by-field, matching what",
        "`ocr_service._paddle_ocr` actually does for real uploads. The per-image sections below",
        "still show each language pass on its own for debugging, plus the merged result.",
        f"Images: `{len(rows)}`.",
        "",
        "## Summary",
        "",
        "| Image | Vendor (merged) | Amount (merged) | VAT (merged) | Total (merged) | Date (merged) | Currency (merged) |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        f = _merged_fields_of(row["en"], row["ar"])
        lines.append(
            "| {name} | {vendor} | {amount} | {vat} | {total} | {date} | {currency} |".format(
                name=row["name"].strip(),
                vendor=(f.get("vendor") or f.get("error") or "").strip(),
                amount=f.get("amount") if f.get("amount") is not None else "",
                vat=f.get("vat_amount") if f.get("vat_amount") is not None else "",
                total=f.get("total_amount") if f.get("total_amount") is not None else "",
                date=(f.get("date") or "").strip(),
                currency=(f.get("currency") or "").strip(),
            )
        )
    lines.append("")
    for row in rows:
        lines.append(f"## {row['name']}")
        lines.append("")
        lines.append(_md_merged(row["en"], row["ar"]))
        lines.append(_md_pass("PaddleOCR (lang=en)", row["en"]))
        lines.append(_md_pass("PaddleOCR (lang=ar)", row["ar"]))
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_path}")


REGIONS = ("ksa", "dubai")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    folder = args[0] if args else "all"
    # SAMPLES_DIR (assets/) also holds unrelated Flutter build/branding images —
    # only sweep the known sample-region folders, never the whole tree.
    roots = [SAMPLES_DIR / args[0]] if args else [SAMPLES_DIR / r for r in REGIONS]
    images = sorted(
        p
        for root in roots
        for p in root.rglob("*")
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )
    if not images:
        print(f"No sample images found under {roots} — drop your test bill photos there (.jpg/.png) and re-run.")
        return

    out_path = Path(__file__).parent / f"results_{folder}.md"
    rows: list[dict] = []
    for image_path in images:
        row = run_one(image_path)
        rows.append(row)
        write_markdown(out_path, folder, rows)


if __name__ == "__main__":
    main()
