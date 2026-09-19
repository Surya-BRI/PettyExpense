"""Run the real shared-detection RapidOCR pipeline against sample bill photos. Usage: python scripts/ocr_compare/run_compare.py [subfolder] [--mode auto|en|ar] — subfolder is an assets/ folder, e.g. `dubai` or `ksa`."""
import sys
from pathlib import Path

# Windows terminals default stdout to cp1252, which can't encode Arabic text — force UTF-8 so print() doesn't crash.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))  # for services.ocr_service
load_dotenv(BACKEND_ROOT / ".env")

from services.ocr_service import ocr_service  # noqa: E402  (production entrypoint, reused as-is)

from paddle_ocr import extract_words_shared

SAMPLES_DIR = BACKEND_ROOT.parent / "assets"


def _production_fields(image_path: Path, mode: str) -> dict:
    # The actual production path: OcrService.run() on the raw file bytes — exactly what a real upload executes.
    image_bytes = image_path.read_bytes()
    return ocr_service.run(image_bytes, image_path.name, mode=mode)


def _low_confidence(words: list) -> list:
    return [w for w in words if w.get("confidence") is not None and w["confidence"] < 0.5]


def run_one(image_path: Path, mode: str) -> dict:
    print(f"\n{'=' * 70}\n{image_path.name}\n{'=' * 70}")
    shared = extract_words_shared(str(image_path), mode=mode)
    fields = _production_fields(image_path, mode)
    print(f"\n-- Production (mode={mode}) --\n  parsed fields: {fields}")
    _report("English recognizer", shared.get("en") or {})
    _report("Arabic recognizer", shared.get("ar") or {})
    return {"name": image_path.name, "fields": fields, "shared": shared}


def _report(label: str, result: dict) -> None:
    print(f"\n-- {label} --")
    raw_text = result.get("raw_text") or ""
    print("  raw text:")
    for line in raw_text.splitlines():
        print(f"    {line}")
    low_confidence = _low_confidence(result.get("words") or [])
    if low_confidence:
        print(f"  low-confidence words (<0.5): {low_confidence}")


def _md_escape(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("```", "'''")
    # Raw OCR lines carry trailing spaces — strip per-line so the report never triggers trailing-whitespace diff-check warnings.
    return "\n".join(line.rstrip() for line in text.split("\n"))


def _md_pass(label: str, result: dict) -> str:
    low = _low_confidence(result.get("words") or [])
    raw = _md_escape(result.get("raw_text") or "")
    low_line = ", ".join(f"{w.get('text')} ({w.get('confidence'):.2f})" for w in low) if low else "(none)"
    return f"### {label}\n\n**Low-confidence words (<0.5):** {low_line}\n\n**Raw text:**\n\n```\n{raw}\n```\n"


def write_markdown(out_path: Path, folder: str, mode: str, rows: list[dict]) -> None:
    lines = [
        f"# OCR results — {folder}",
        "",
        f"Engine: single shared-detection RapidOCR pipeline (mode=`{mode}`) — one detection pass,",
        "sequential English + Arabic recognition against the same detected regions.",
        "Summary reflects the actual production result (`OcrService.run`). The per-image",
        "sections below also show each recognizer's raw reading for debugging.",
        f"Images: `{len(rows)}`.",
        "",
        "## Summary",
        "",
        "| Image | Vendor | Amount | VAT | Total | Date | Currency | Mismatch |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        f = row["fields"]
        lines.append(
            "| {name} | {vendor} | {amount} | {vat} | {total} | {date} | {currency} | {mismatch} |".format(
                name=row["name"].strip(),
                vendor=(f.get("vendor") or "").strip(),
                amount=f.get("amount") if f.get("amount") is not None else "",
                vat=f.get("vat_amount") if f.get("vat_amount") is not None else "",
                total=f.get("total_amount") if f.get("total_amount") is not None else "",
                date=(f.get("date") or "").strip(),
                currency=(f.get("currency") or "").strip(),
                mismatch=f.get("reconciliation_mismatch"),
            )
        )
    lines.append("")
    for row in rows:
        lines.append(f"## {row['name']}")
        lines.append("")
        lines.append(f"### Production (mode={mode})\n\n**Parsed fields:** `{row['fields']}`\n")
        lines.append(_md_pass("English recognizer", row["shared"].get("en") or {}))
        lines.append(_md_pass("Arabic recognizer", row["shared"].get("ar") or {}))
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_path}")


REGIONS = ("ksa", "dubai")


def main() -> None:
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mode = "auto"
    for flag in flags:
        if flag.startswith("--mode="):
            mode = flag.split("=", 1)[1]
    folder = args[0] if args else "all"
    # assets/ also holds unrelated Flutter build/branding images — only sweep the known sample-region folders, never the whole tree.
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
        row = run_one(image_path, mode)
        rows.append(row)
        write_markdown(out_path, folder, mode, rows)


if __name__ == "__main__":
    main()
