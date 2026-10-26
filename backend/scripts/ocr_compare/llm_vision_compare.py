"""Benchmark an OpenAI vision model against the current OCR pipeline on the sample bills.

Usage (from backend/):
    python scripts/ocr_compare/llm_vision_compare.py                 # plan only: lists bills, makes NO API call
    python scripts/ocr_compare/llm_vision_compare.py --yes           # call the API for bills not cached yet
    python scripts/ocr_compare/llm_vision_compare.py --yes --limit 3 --only ksa
    python scripts/ocr_compare/llm_vision_compare.py --model gpt-5-mini --yes
    python scripts/ocr_compare/llm_vision_compare.py --baseline-only          # free: local pipeline only
    python scripts/ocr_compare/llm_vision_compare.py --provider runpod --yes --limit 1   # self-hosted Qwen-VL

Needs OPENAI_API_KEY (or RUNPOD_API_KEY + RUNPOD_VISION_ENDPOINT_ID for --provider runpod) in backend/.env. Every API answer and every baseline run is cached under
llm_results/<model>/ and llm_results/baseline/, so re-running never pays for the same image twice.

The LLM answer is mapped into the exact dict shape OcrService.run() returns (vendor, amount,
vat_amount, total_amount, currency, date, field_confidence, low_confidence_fields, fields.invoice_number,
line_items[...]) and checked against what transaction_service._receipt_payload and Flutter's
OcrResult / OcrLineItem read -- so a passing run means it could be dropped in without app changes.
"""
import argparse
import csv
import difflib
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any, Optional

# Windows terminals default stdout to cp1252, which can't encode Arabic text — force UTF-8 so print() doesn't crash.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

# Prompt, schema and the OcrService-shape mapping are the production ones ("Scan with AI").
from services.llm_vision_service import (  # noqa: E402
    OPENAI_BASE_URL, RUNPOD_BASE_URL, call_openai, to_ocr_service_shape,
)

ASSETS = REPO_ROOT / "assets"
FOLDERS = ["ksa", "dubai", "multi_line", "new_bills"]
GROUND_TRUTH_CSV = REPO_ROOT / "scripts" / "ocr_results.csv"
RESULTS_DIR = Path(__file__).resolve().parent / "llm_results"
FOLDER_REGION = {"ksa": "KSA", "dubai": "UAE", "multi_line": "UAE", "new_bills": "UAE"}

# Real item counts recorded in assets/docs/MULTI_ITEM_LINE_ALLOCATION_AND_OCR_FINDINGS.md.
EXPECTED_ITEM_COUNTS = {"image.png": 2, "img2.jpeg": 3, "img3.jpeg": 12, "img23.png": 7, "mage.png": 13, "amer.png": 4,
                        "bill_1.png": 11, "bill_3.png": 11}  # bill_1/3 counted by eye from the images

# Arabic names for vendors the CSV only records in English.
VENDOR_ALIASES = {"ksa/ksa1.png": ["شركة الشارقة"]}

def contract_problems(r: dict[str, Any]) -> list[str]:
    """What _receipt_payload + OcrResult.fromJson / OcrLineItem.fromJson / LineItemIn would reject."""
    p = []
    num_or_null = lambda v: v is None or isinstance(v, (int, float)) and not isinstance(v, bool)  # noqa: E731
    for k in ("amount", "vat_amount", "total_amount", "confidence"):
        if not num_or_null(r.get(k)):
            p.append(f"{k} not num/null")
    for k in ("vendor", "date"):
        if not isinstance(r.get(k), str):
            p.append(f"{k} not a string (Flutter casts `as String`)")
    if r.get("currency") is not None and not isinstance(r["currency"], str):
        p.append("currency not string/null")
    if not all(isinstance(v, (int, float)) for v in (r.get("field_confidence") or {}).values()):
        p.append("field_confidence values not numeric")
    if r.get("date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]):
        p.append(f"date '{r['date']}' not ISO (claim_detail_screen _fmtDate parses ISO or d/m/y)")
    for i, li in enumerate(r.get("line_items") or []):
        if not li["description"]:
            p.append(f"line {i + 1}: empty description (LineItemIn rejects)")
        if li["amount"] is None or li["amount"] < 0:
            p.append(f"line {i + 1}: amount missing/negative (LineItemIn.amount is required)")
        if not num_or_null(li["quantity"]) or not num_or_null(li["vat_percent"]):
            p.append(f"line {i + 1}: quantity/vat_percent not num/null")
    return p


# ------------------------------------------------------------ ground truth

def _first_number(text: str) -> Optional[float]:
    m = re.match(r"\s*(\d+(?:\.\d+)?)", text or "")
    return float(m.group(1)) if m else None


def _date_keys(text: str) -> set[tuple[int, int]]:
    """(month, day) a date string means -- day-first (GCC), m/d only when d/m is impossible; year ignored."""
    text = (text or "").strip()
    keys: set[tuple[int, int]] = set()
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if m:
        return {(int(m.group(2)), int(m.group(3)))}
    m = re.match(r"(\d{1,2})[/\-.](\d{1,2})(?:[/\-.](\d{2,4}))?", text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if 1 <= b <= 12:
            keys.add((b, a))
        elif 1 <= a <= 12:
            keys.add((a, b))
        return keys
    m = re.match(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})", text)
    if m:
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        if m.group(1).lower() in months:
            keys.add((months.index(m.group(1).lower()) + 1, int(m.group(2))))
    return keys


def load_ground_truth() -> dict[str, dict[str, Any]]:
    truth: dict[str, dict[str, Any]] = {}
    with GROUND_TRUTH_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            vendor_raw = row["actual_vendor"]
            vendors = [] if vendor_raw.lower().startswith("n/a") else [vendor_raw.split("(")[0].strip()]
            paren = re.search(r"\(([^)]*[؀-ۿ][^)]*)\)", vendor_raw)
            if paren:
                vendors.append(paren.group(1).strip())
            date_raw = row["actual_date"]
            key = row["image"].replace("assets/", "")
            truth[key] = {  # later rows (re-verifications) win
                "vendor": vendors + VENDOR_ALIASES.get(key, []),
                "amount": _first_number(row["actual_amount"]),
                "vat_amount": _first_number(row["actual_vat_amount"]),
                "total_amount": _first_number(row["actual_total_amount"]),
                "currency": (row["actual_currency"] or "").split()[0] if row["actual_currency"] else None,
                "date": set() if ("hijri" in date_raw.lower() or "illegible" in date_raw.lower()) else _date_keys(date_raw),
            }
    return truth


def _norm(s: str) -> str:
    return re.sub(r"[^0-9a-z؀-ۿ]+", " ", (s or "").lower()).strip()


def vendor_ok(got: str, expected: list[str]) -> Optional[bool]:
    if not expected:
        return None
    g = _norm(got)
    if not g:
        return False
    for e in map(_norm, expected):
        if e in g or g in e or difflib.SequenceMatcher(None, g, e).ratio() >= 0.7:
            return True
    return False


def money_ok(got: Optional[float], expected: Optional[float], treat_missing_as_zero: bool = False) -> Optional[bool]:
    if expected is None:
        if not treat_missing_as_zero:
            return None
        expected = 0.0
    return got is not None and abs(float(got) - expected) <= 0.02


def score(result: dict[str, Any], truth: dict[str, Any]) -> dict[str, Optional[bool]]:
    return {
        "vendor": vendor_ok(result.get("vendor") or "", truth["vendor"]),
        "amount": money_ok(result.get("amount"), truth["amount"] if truth["amount"] is not None else truth["total_amount"]),
        "vat_amount": money_ok(result.get("vat_amount"), truth["vat_amount"], treat_missing_as_zero=True),
        "total_amount": money_ok(result.get("total_amount"), truth["total_amount"]),
        "currency": None if not truth["currency"] else (result.get("currency") or "").upper() == truth["currency"].upper(),
        "date": None if not truth["date"] else bool(_date_keys(result.get("date") or "") & truth["date"]),
    }


# ----------------------------------------------------------------- runners

def _cache_path(kind: str, image: Path) -> Path:
    return RESULTS_DIR / kind / f"{image.parent.name}__{image.name}.json"


def baseline_result(image: Path) -> dict[str, Any]:
    """Current production pipeline (OcrService.run -> Indra, then RapidOCR; CPU only, no paid call)."""
    cache = _cache_path("baseline", image)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    from services.ocr_service import ocr_service

    started = time.monotonic()
    try:
        r = ocr_service.run(image.read_bytes(), image.name, mode="auto", region_code=FOLDER_REGION.get(image.parent.name))
        out = {k: r.get(k) for k in ("vendor", "amount", "vat_amount", "total_amount", "currency", "date",
                                     "low_confidence_fields", "reconciliation_mismatch", "line_items")}
        out["bill_number"] = ((r.get("fields") or {}).get("invoice_number") or {}).get("value")
    except Exception as exc:  # report, don't abort the whole run
        out = {"error": str(exc)}
    out["seconds"] = round(time.monotonic() - started, 2)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return out


def llm_result(image: Path, label: str, cfg: dict[str, Any], allow_call: bool) -> Optional[dict[str, Any]]:
    region = FOLDER_REGION.get(image.parent.name)
    cache = _cache_path(label, image)
    if cache.exists():
        # Re-map the cached raw answer every run, so mapping fixes never need a new (paid) call.
        out = json.loads(cache.read_text(encoding="utf-8"))
        raw_llm = out.get("raw") or out["mapped"]["raw_json"]["llm"]
        out["mapped"] = to_ocr_service_shape(raw_llm, region)
        return out
    if not allow_call:
        return None
    raw = call_openai(image.read_bytes(), **cfg)
    mapped = to_ocr_service_shape(raw["parsed"], region)
    out = {"raw": raw["parsed"], "mapped": mapped, "usage": raw["usage"], "seconds": raw["seconds"], "served_model": raw["model"]}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _mark(v: Optional[bool]) -> str:
    return "–" if v is None else ("✅" if v else "❌")


def _money(v: Any) -> str:
    return "" if v is None else f"{v:g}" if isinstance(v, (int, float)) else str(v)


def write_report(model: str, rows: list[dict[str, Any]]) -> Path:
    fields = ["vendor", "amount", "vat_amount", "total_amount", "currency", "date"]
    lines = [f"# Vision LLM vs current pipeline — `{model}`", "",
             f"Generated {date.today().isoformat()} by `llm_vision_compare.py`. Ground truth: `scripts/ocr_results.csv`.", ""]

    scored = [r for r in rows if r.get("truth")]
    lines += ["## Accuracy on bills with ground truth", "", "| Field | Current pipeline | " + model + " |", "|---|---|---|"]
    for f in fields:
        b = [r["base_score"][f] for r in scored if r["base_score"][f] is not None]
        l = [r["llm_score"][f] for r in scored if r.get("llm_score") and r["llm_score"][f] is not None]
        lines.append(f"| {f} | {sum(b)}/{len(b)} | {sum(l)}/{len(l)} |")
    lines.append("")

    lines += ["## Per bill (single-value fields)", "",
              "| Bill | Engine | Vendor | Amount | VAT | Total | Cur | Date | Bill no |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        for label, res, sc in (("current", r["base"], r.get("base_score")), (model, r.get("llm"), r.get("llm_score"))):
            if res is None:
                continue
            if "error" in res:
                lines.append(f"| {r['name']} | {label} | error: {res['error'][:80]} |||||||")
                continue
            s = sc or {}
            cells = [f"{_mark(s.get(f))} {_money(res.get(f))}".strip() if sc else _money(res.get(f)) for f in fields]
            lines.append(f"| {r['name']} | {label} | " + " | ".join(c.replace("|", "/") for c in cells) + f" | {res.get('bill_number') or ''} |")
    lines.append("")

    lines += ["## Line items (multi-item flow)", "",
              "| Bill | Real items | Current | LLM | LLM Σ lines | LLM total | Σ matches |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        llm = r.get("llm")
        base_n = len(r["base"].get("line_items") or [])
        if llm is None or "error" in llm:
            continue
        items = llm.get("line_items") or []
        if not items and not base_n and r["name"] not in EXPECTED_ITEM_COUNTS:
            continue
        total_sum = round(sum(i["amount"] or 0 for i in items), 2)
        target = llm.get("total_amount")
        if not any(i["amount"] is not None for i in items):
            match = "no prices (delivery note?)"
        else:
            match = "" if target is None else ("✅" if abs(total_sum - target) <= 0.05 else "❌")
        expected = EXPECTED_ITEM_COUNTS.get(r["name"].split("/", 1)[-1], "?")
        lines.append(f"| {r['name']} | {expected} | {base_n} | {len(items)} | "
                     f"{total_sum:g} | {_money(target)} | {match} |")
    lines += ["", "Σ matches checks the app's assumption in `_replace_line_items`: line amounts are VAT-inclusive "
              "and sum to the bill total (pre-VAT rows are converted in `_make_lines_vat_inclusive`).", ""]

    problems = [(r["name"], r["contract"]) for r in rows if r.get("contract")]
    lines += ["## Backend / Flutter contract check", ""]
    lines += [f"- **{n}**: " + "; ".join(p) for n, p in problems] or ["All LLM results map cleanly onto `OcrService.run()` → `_receipt_payload` → `OcrResult.fromJson`."]
    lines.append("")

    usage = [r["llm_meta"] for r in rows if r.get("llm_meta")]
    if usage:
        pt = sum(u["usage"].get("prompt_tokens", 0) for u in usage)
        ct = sum(u["usage"].get("completion_tokens", 0) for u in usage)
        secs = [u["seconds"] for u in usage]
        lines += ["## Usage", "", f"- Bills sent: {len(usage)} · prompt tokens {pt:,} · completion tokens {ct:,} "
                  f"(avg {pt // len(usage):,} / {ct // len(usage):,} per bill)",
                  f"- Latency: avg {sum(secs) / len(secs):.1f}s, max {max(secs):.1f}s", ""]
    out = RESULTS_DIR / f"report_{model}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["openai", "runpod"], default="openai",
                    help="runpod = self-hosted Qwen-VL on RUNPOD_VISION_ENDPOINT_ID (same prompt/schema/scoring)")
    ap.add_argument("--model", help="default: gpt-5.4-mini (openai) / RUNPOD_VISION_MODEL (runpod)")
    ap.add_argument("--tag", help="suffix for the cache/report name, e.g. v2 after a prompt change (old answers stay cached)")
    ap.add_argument("--yes", action="store_true", help="actually call the API (otherwise plan only)")
    ap.add_argument("--only", choices=FOLDERS, help="one assets/ folder")
    ap.add_argument("--pick", nargs="+", metavar="FOLDER/FILE", help="exact bills, e.g. ksa/ksa1.png multi_line/mage.png")
    ap.add_argument("--limit", type=int, help="max bills to send to the API this run")
    ap.add_argument("--reasoning", choices=["minimal", "low", "medium", "high"], help="reasoning_effort for gpt-5*/o-series")
    ap.add_argument("--no-baseline", action="store_true", help="skip the local pipeline comparison")
    ap.add_argument("--baseline-only", action="store_true", help="run only the free local pipeline (+ any cached LLM results)")
    args = ap.parse_args()
    if args.baseline_only:
        args.yes = False
    if args.provider == "runpod":
        endpoint_id = os.getenv("RUNPOD_VISION_ENDPOINT_ID", "").strip()
        model = args.model or os.getenv("RUNPOD_VISION_MODEL") or "Qwen/Qwen3-VL-8B-Instruct"
        api_key = os.getenv("RUNPOD_VISION_API_KEY") or os.getenv("RUNPOD_API_KEY")
        cfg = {"model": model, "api_key": api_key, "reasoning": None, "timeout": 300, "max_tokens": 2500,
               "base_url": RUNPOD_BASE_URL.format(endpoint_id=endpoint_id), "service": "RunPod"}
        label = f"runpod-{model.split('/')[-1]}"
        missing_setting = None if endpoint_id and cfg["api_key"] else "RUNPOD_VISION_ENDPOINT_ID / RUNPOD_API_KEY"
    else:
        model = args.model or "gpt-5.4-mini"
        cfg = {"model": model, "api_key": os.getenv("OPENAI_API_KEY"), "reasoning": args.reasoning, "timeout": 120,
               "base_url": OPENAI_BASE_URL, "service": "OpenAI"}
        label = model
        missing_setting = None if cfg["api_key"] else "OPENAI_API_KEY"
    if args.tag:
        label = f"{label}-{args.tag}"

    images = sorted(p for folder in ([args.only] if args.only else FOLDERS)
                    for p in (ASSETS / folder).glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if args.pick:
        missing = [k for k in args.pick if not (ASSETS / k).is_file()]
        if missing:
            sys.exit(f"Not found under assets/: {missing}")
        images = [ASSETS / k for k in args.pick]
    truth = load_ground_truth()
    uncached = [p for p in images if not _cache_path(label, p).exists()]
    to_send = uncached[: args.limit] if args.limit else uncached

    print(f"{len(images)} bills ({sum(1 for p in images if f'{p.parent.name}/{p.name}' in truth)} with ground truth); "
          f"{len(images) - len(uncached)} already cached for {label}; {len(to_send)} would be sent now.")
    if not args.yes and to_send and not args.baseline_only:
        for p in to_send:
            print(f"  would send: {p.parent.name}/{p.name}")
        print("\nPlan only — no API call made. Re-run with --yes to send.")
        return
    if args.yes and to_send and missing_setting:
        sys.exit(f"{missing_setting} is not set in backend/.env")

    send_set = set(to_send) if args.yes else set()
    rows = []
    for p in images:
        key = f"{p.parent.name}/{p.name}"
        print(f"- {key}", flush=True)
        row: dict[str, Any] = {"name": key}
        row["base"] = {"line_items": []} if args.no_baseline else baseline_result(p)
        try:
            meta = llm_result(p, label, cfg, p in send_set)
        except Exception as exc:
            # Every call is paid (and a broken RunPod endpoint can bill each retry) -- stop sending after one failure.
            print(f"    LLM error: {exc}\n    Stopping further API calls for this run.")
            send_set.clear()
            meta = {"mapped": {"error": str(exc)}}
        if meta:
            row["llm"] = meta["mapped"]
            row["llm_meta"] = meta if "usage" in meta else None
            if "error" not in meta["mapped"]:
                row["llm"]["bill_number"] = meta["mapped"]["fields"]["invoice_number"]["value"]
                row["contract"] = contract_problems(meta["mapped"])
        if key in truth:
            row["truth"] = truth[key]
            if "error" not in row["base"] and not args.no_baseline:
                row["base_score"] = score(row["base"], truth[key])
            else:
                row["base_score"] = {f: None for f in ("vendor", "amount", "vat_amount", "total_amount", "currency", "date")}
            if row.get("llm") and "error" not in row["llm"]:
                row["llm_score"] = score(row["llm"], truth[key])
        rows.append(row)

    report = write_report(label, rows)
    print(f"\nReport: {report}")


if __name__ == "__main__":
    main()
