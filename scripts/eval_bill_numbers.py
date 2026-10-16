"""Score bill/invoice-number extraction against scripts/bill_number_truth.json (numbers read by eye off the sample bills).

Run from the backend virtualenv, e.g.
    backend\\.venv\\Scripts\\python.exe scripts\\eval_bill_numbers.py [--cache DIR]

Runs the CPU OCR pipeline on every sample image (a few minutes the first time). --cache keeps the OCR words on disk so
re-running after an extraction change takes seconds. Reports accuracy on bills that print a number, and any value shown
for a bill that prints none.
"""
import json
import os
import pickle
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT / "backend")  # the app's settings read backend/.env relative to the working directory

from extraction.dedupe import dedupe_lines  # noqa: E402
from extraction.normalize import group_into_lines  # noqa: E402
from extraction.pipeline import extract  # noqa: E402
from services.ocr_service import _OCR_MAX_SIDE_PX, _reference_data, _resize_for_ocr, _run_shared_detection_ocr  # noqa: E402

truth = json.loads((ROOT / "scripts" / "bill_number_truth.json").read_text(encoding="utf-8"))
cache_dir = Path(sys.argv[sys.argv.index("--cache") + 1]) if "--cache" in sys.argv else None
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())


def lines_for(image_rel: str):
    cache = cache_dir / (re.sub(r"[^A-Za-z0-9]+", "_", image_rel) + ".pkl") if cache_dir else None
    if cache and cache.exists():
        en, ar = pickle.loads(cache.read_bytes())
    else:
        en, ar = _run_shared_detection_ocr(_resize_for_ocr((ROOT / image_rel).read_bytes(), _OCR_MAX_SIDE_PX), "auto")
        if cache:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(pickle.dumps((en, ar)))
    return dedupe_lines(group_into_lines(en) + group_into_lines(ar))


correct = wrong = missing = false_value = blank_ok = 0
problems = []
for image, expected in truth.items():
    if image.startswith("_") or expected == "skip":
        continue
    fields = extract(lines_for(image), _reference_data).fields
    got = fields["invoice_number"].value or fields["transaction_number"].value
    if expected is None:
        if got:
            false_value += 1
            problems.append(f"  false value  {image}: printed none, got {got!r}")
        else:
            blank_ok += 1
    elif not got:
        missing += 1
        problems.append(f"  missing      {image}: expected {expected!r}")
    elif norm(got) == norm(expected):
        correct += 1
    else:
        wrong += 1
        problems.append(f"  WRONG        {image}: expected {expected!r}, got {got!r}")

with_number = correct + wrong + missing
print(f"bills that print a number: {with_number}  correct {correct}  wrong {wrong}  missing {missing}"
      f"   ({100 * correct / with_number:.0f}% correct)")
print(f"bills that print none:     {blank_ok + false_value}  correctly blank {blank_ok}  false value {false_value}")
print("\n".join(problems))
