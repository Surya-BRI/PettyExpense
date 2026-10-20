"""
Run Indra OCR folder-wise: dubai, ksa, multi_line, today.
Usage (from project root):
    python scripts/test_indra_ocr.py [--no-preprocess]
"""
import json, os, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import importlib.util as _ilu, types as _types

def _load_preprocess():
    spec = _ilu.spec_from_file_location(
        "image_preprocess",
        Path(__file__).resolve().parent.parent / "backend" / "services" / "image_preprocess.py",
    )
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_pp = _load_preprocess()
assess_quality      = _pp.assess_quality
preprocess_if_needed = _pp.preprocess_if_needed

from extraction import ReferenceData, dedupe_lines, extract, group_into_lines, to_legacy_dict
from extraction.line_items import extract_line_items
from extraction.types import OcrWord

FOLDERS = {
    "dubai":      Path("assets/dubai"),
    "ksa":        Path("assets/ksa"),
    "multi_line": Path("assets/multi_line"),
    "today":      Path("assets/today"),
    "new_bills":  Path("assets/new_bills"),
}
EXTS = {".png", ".jpg", ".jpeg", ".JPEG"}

_conv = None
def get_conv():
    global _conv
    if _conv is None:
        import indra_ocr
        _conv = indra_ocr.load(threads=4)
    return _conv


def run_indra(image_path: Path, ref: ReferenceData, use_preprocess: bool = True) -> dict:
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    quality_summary = "off"
    if use_preprocess:
        image_bytes, quality = preprocess_if_needed(image_bytes)
        quality_summary = quality.summary()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    t0 = time.perf_counter()
    try:
        pages = list(get_conv().convert(tmp_path))
    finally:
        os.unlink(tmp_path)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    if not pages:
        return {"error": "no pages", "elapsed_ms": elapsed_ms}

    _, page = pages[0]
    words: list[OcrWord] = []
    for i, line in enumerate(page.lines or []):
        text = getattr(line, "text", None) or ""
        if not text.strip():
            continue
        conf = float(getattr(line, "conf", 1.0) or 1.0)
        box_raw = getattr(line, "box", None)
        bbox = None
        if box_raw:
            try:
                bbox = (float(box_raw[0]), float(box_raw[1]), float(box_raw[2]), float(box_raw[3]))
            except Exception:
                pass
        words.append(OcrWord(text=text, confidence=conf, lang="en", bounding_box=bbox, page=1, reading_order=i, source_pass="indra"))

    lines = dedupe_lines(group_into_lines(words))
    result = extract(lines, ref)
    parsed = to_legacy_dict(result)
    line_items = extract_line_items(lines, ref)

    return {
        "elapsed_ms":    elapsed_ms,
        "vendor":        parsed.get("vendor"),
        "date":          parsed.get("date"),
        "invoice_no":    (parsed.get("fields") or {}).get("invoice_number", {}).get("value"),
        "amount":        parsed.get("amount"),
        "vat":           parsed.get("vat_amount"),
        "total":         parsed.get("total_amount"),
        "currency":      parsed.get("currency"),
        "conf":          parsed.get("confidence"),
        "low_conf":      parsed.get("low_confidence_fields", []),
        "line_items":    [li.to_dict() for li in line_items],
        "preprocess":    quality_summary,
    }


def print_result(img: Path, r: dict):
    if "error" in r:
        print(f"  {img.name:<35} ERROR: {r['error']}")
        return
    li_count = len(r["line_items"])
    low = ",".join(r["low_conf"]) if r["low_conf"] else "-"
    pre = r.get("preprocess", "off")
    print(f"  {img.name:<35} {r['elapsed_ms']:>6} ms | "
          f"vendor={str(r['vendor']):<28} invoice={str(r['invoice_no']):<16} "
          f"date={str(r['date']):<12} "
          f"amt={str(r['amount']):<8} total={str(r['total']):<8} "
          f"conf={r['conf']} | preprocess=[{pre}]")
    if li_count:
        for li in r["line_items"]:
            print(f"    -> {li.get('description',''):<30} qty={li.get('quantity')}  amt={li.get('amount')}  vat%={li.get('vat_percent')}  conf={li.get('confidence')}")


def main():
    use_preprocess = "--no-preprocess" not in sys.argv
    from extraction.reference_data import default_tax_rules_for_region
    currencies, rates = default_tax_rules_for_region()
    ref = ReferenceData(valid_currency_codes=currencies, plausible_vat_rates=rates)
    print(f"  Preprocessing: {'ON (CLAHE + sharpen + denoise + deskew + 2x upscale)' if use_preprocess else 'OFF'}")
    for folder_name, folder_path in FOLDERS.items():
        images = sorted(p for p in folder_path.iterdir() if p.suffix.lower() in EXTS) if folder_path.exists() else []
        print(f"\n{'='*120}")
        print(f"  FOLDER: {folder_name}  ({len(images)} images)")
        print(f"{'='*120}")
        if not images:
            print("  (no images found)")
            continue
        for img in images:
            print_result(img, run_indra(img, ref, use_preprocess=use_preprocess))

if __name__ == "__main__":
    main()
