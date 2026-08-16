import json
import os
import random
import re
from datetime import date
from typing import Any, Optional

from config import get_settings

# PaddleOCR 3.x's oneDNN CPU backend crashes on some Windows setups with
# `NotImplementedError: ConvertPirAttribute2RuntimeAttribute ...` before any real
# OCR runs. Must be set before paddleocr/paddlepaddle is imported.
os.environ.setdefault("FLAGS_use_mkldnn", "0")

_ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_HAS_ARABIC = re.compile(r"[\u0600-\u06FF]")
_paddle_engines: dict[str, Any] = {}

LOW_CONFIDENCE = 0.5
RECONCILE_TOLERANCE = 0.02

SAMPLE_VENDORS = [
    "Indian Oil Petrol Pump",
    "HP Fuel Station",
    "Bharat Petroleum",
    "Cafe Coffee Day",
    "Hotel Saravana Bhavan",
    "Local Dhaba",
]

# Real bill amounts here are well under six figures. Digit-boundary lookarounds stop
# barcodes / TRNs / phone numbers being taken as money.
_NUMBER = r"(?<!\d)(\d{1,6}(?:[.,]\d{1,2})?)(?!\d)"

_CURRENCY_RE = re.compile(r"\b(SAR|AED)(?![A-Za-z])", re.IGNORECASE)
_CURRENCY_AMOUNT_RE = re.compile(r"\b(?:SAR|AED)\s*" + _NUMBER, re.IGNORECASE)

_TOTAL_RE = re.compile(
    r"(?:amount\s*\(?\s*incl\.?\s*vat\)?|total\s*amount|bill\s*amount|paid\s*amount|"
    r"total\s*(?:aed|sar)|grand\s*total|total\s*incl)"
    r"[^\d]{0,24}" + _NUMBER,
    re.IGNORECASE,
)
_SUBTOTAL_RE = re.compile(
    r"(?:amount\s*\(?\s*excl\.?\s*vat\)?|sub\s*-?\s*total)[^\d]{0,24}" + _NUMBER,
    re.IGNORECASE,
)
_LEGACY_AMOUNT_RE = re.compile(
    r"(?:total|amount|grand\s*total)\s*[:\-]?\s*" + _NUMBER,
    re.IGNORECASE,
)
# Common UAE POS "Tax Inclusive" summary row: VAT% | Excl.VAT | Incl.VAT | VAT.
# A plain "nearest number after the word VAT" search can't tell the rate column
# (VAT%) from the amount column (VAT) apart, so this reads the header labels in
# the order they actually appear and pairs the money-formatted numbers that
# follow positionally, rather than guessing which number belongs where.
_VAT_TABLE_HEADER_RE = re.compile(
    r"vat\s*%[\s\S]{0,60}?"
    r"exc\w{0,2}\.?\s*vat[\s\S]{0,60}?"
    r"inc\w{0,2}\.?\s*vat[\s\S]{0,20}?"
    r"\bvat\b",
    re.IGNORECASE,
)
_MONEY_RE = re.compile(r"(?<!\d)\d{1,6}\.\d{2}(?!\d)")
# Fallback for VAT summary rows whose column headers are too OCR-garbled to match
# by label (e.g. "VATX" / "VAI" / "T:ta" instead of "VAT%" / "VAT" / "Total").
# A standalone 1-2 digit number near the word "va..." is almost always the VAT
# rate (5%, 15%, ...); the tolerance below is looser than RECONCILE_TOLERANCE
# because real POS rounding-adjustment lines can leave excl+vat a few cents off
# total even on a correctly-read row — this only needs to pick the better of two
# candidate column orders, not certify the row is internally exact.
_ARITH_PCT_ANCHOR_RE = re.compile(r"(?<!\d)(\d{1,2})\s*%?(?!\d)")
_ARITH_TOLERANCE = 0.15
# Last-resort fallback for bills with no VAT breakdown at all — e.g. a single
# handwritten taxi fare with no table structure to disambiguate at all. Never
# trusted outright: any value found this way is always forced to a "guess"
# tier (low confidence), so it's offered as a starting point for the employee
# to confirm/correct rather than silently accepted like a "label"-tier read.
# "الأجرة" (Arabic for "fare") is deliberately excluded: it's baked into how taxi
# companies describe themselves on their own letterhead ("... لأجرة العامة" = "...
# for General Transport/Hire"), so it reliably matches that tagline before ever
# reaching the real fare-column header — unlike "fare"/"amount"/"total"/"المبلغ"/
# "المجموع", which only showed up as genuine field labels in the samples checked.
_AMOUNT_KEYWORD_RE = re.compile(r"fare|amount|total|المبلغ|المجموع", re.IGNORECASE)
_AMOUNT_GUESS_WINDOW = 400
# "Amount"/"Total" are also generic column headers on itemized invoices (e.g.
# Dubai's "Description | Qty | Amount" table) — there the first number after the
# header is just a line-item price, not the bill total. The guess fallback is only
# safe on bills with no such item table (e.g. a single-line taxi fare slip).
_ITEMIZED_TABLE_RE = re.compile(r"\bqty\b|\bdescri?pt", re.IGNORECASE)
# OCR commonly drops/swaps one letter in "amount"/"total" on a blurry POS printout
# (seen for real: "Amount" -> "Aaount", "Bill" -> "B111") — a literal match on those
# words would miss the very labels this last-resort fallback exists to use. The `.`
# tolerates exactly one substituted character; still specific enough not to match
# unrelated words.
_FUZZY_TOTAL_RE = re.compile(r"a.ount|t.tal|grand.{0,4}t.tal", re.IGNORECASE)
# Stricter than _NUMBER: also rejects digits glued to letters (e.g. the "11" inside
# a garbled OCR token like "a11", or the "208" inside a route code like "KA8D208"),
# since the guess fallback has no keyword-adjacency to lean on and would otherwise
# happily "extract" noise instead of the real handwritten figure.
_STANDALONE_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])(\d{1,6}(?:[.,]\d{1,2})?)(?![A-Za-z0-9])")
# On Saudi taxi-slip templates the VAT-rate line ("ضريبة القيمة المضافة 5" / "VAT 5%")
# often sits inside the same keyword-guess window as the real fare, and — unlike the
# real fare — it's always a bare 5 or 15. Skip a candidate number that's immediately
# preceded by a VAT/tax-rate word and also happens to be 5 or 15, rather than trusting
# whichever language's OCR pass happened to wander past the rate line first.
_RATE_CONTEXT_RE = re.compile(r"ضريب|مضاف|vat|tax", re.IGNORECASE)
_DATE_RE = re.compile(
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    r"|(\d{4}[/-]\d{1,2}[/-]\d{1,2})"
    r"|(\d{1,2}[\s.\-]*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s.\-]*\d{2,4})",
    re.IGNORECASE,
)
_SKIP_VENDOR_LINE = re.compile(
    r"^(tax\s*invoice|فاتورة|date\b|bill\s*no|tel\b|mob\b|trn\b|pos\b|user\s*id|"
    r"thank|qty\b|amount\b|description|keep bill|no cash|total\b|vat\b|invoice|"
    r"hold invoice|sl\.?\s*no|barcode|cash\b|rounding)",
    re.IGNORECASE,
)
_COMPANY_HINT = re.compile(
    r"LLC|L\.L\.C|HYPERMARKET|SUPERMARKET|TRADING|MARKET|STORE|شركة|ذ\.?\s*م\.?\s*م",
    re.IGNORECASE,
)

_EXPENSE_TYPE_KEYWORDS = {
    "Food": (
        "food", "supermarket", "hypermarket", "grocery", "restaurant", "cafe", "mart",
        "yoghurt", "yogurt", "vegetable", "cucumber", "carrot", "banana", "onion",
    ),
    "Fuel": ("petrol", "fuel", "diesel", "gasoline", "pump", "station"),
    "IT Equipment": ("computer", "laptop", "electronic", "software", "relay", "hardware", "it equipment"),
}


def _to_float(raw: str) -> float:
    return float(raw.replace(",", ""))


def _looks_like_phone_or_id(value: float) -> bool:
    as_int = int(value) if value == int(value) else None
    if as_int is None:
        return False
    digits = str(as_int)
    return len(digits) >= 5 and value >= 10000


def _word_score(words: list[dict[str, Any]], value: Any) -> Optional[float]:
    if value is None:
        return None
    needle = str(value).strip().lower().replace(",", "")
    if not needle:
        return None
    scores = [
        float(w["confidence"])
        for w in words
        if needle in w.get("text", "").lower().replace(",", "")
    ]
    return max(scores) if scores else None


def _field(value: Any, tier: str, words: list[dict[str, Any]]) -> dict[str, Any]:
    base = {
        "label": 0.75, "table": 0.8, "heuristic": 0.45, "bare": 0.28,
        "missing": 0.0, "mismatch": 0.2, "guess": 0.3,
    }.get(tier, 0.2)
    word = _word_score(words, value)
    confidence = round(((base + word) / 2) if word is not None else base, 2)
    if value is None or value == "":
        confidence = 0.0
        tier = "missing"
    low = confidence < LOW_CONFIDENCE
    if tier in ("mismatch", "guess"):
        low = True
    return {
        "value": value,
        "confidence": confidence,
        "low": low,
        "tier": tier,
    }


def _extract_vat_table(text: str) -> Optional[tuple[float, float, float]]:
    """Positionally reads a 'VAT% | Excl.VAT | Incl.VAT | VAT' summary row.

    Returns (amount, vat_amount, total_amount) or None if the header isn't found or
    isn't followed by enough money-formatted numbers to fill it in with confidence.
    """
    header = _VAT_TABLE_HEADER_RE.search(text)
    if not header:
        return None
    window = text[header.end() : header.end() + 200]
    money = _MONEY_RE.findall(window)
    if len(money) < 3:
        return None
    excl, incl, vat = (_to_float(m) for m in money[:3])
    return excl, vat, incl


def _extract_vat_table_arithmetic(text: str) -> Optional[tuple[float, float, float]]:
    """Label-blind fallback: find a VAT-rate-like anchor followed by three money
    numbers, then pick whichever of the two plausible column orders —
    [excl, total, vat] or [excl, vat, total] — actually reconciles, instead of
    trusting OCR-garbled header text to say which number means what.
    """
    best: Optional[tuple[float, float, float, float]] = None  # (amount, vat, total, diff)
    for anchor in _ARITH_PCT_ANCHOR_RE.finditer(text):
        prefix = text[max(0, anchor.start() - 60) : anchor.start()]
        if "va" not in prefix.lower():
            continue
        window = text[anchor.end() : anchor.end() + 150]
        money = _MONEY_RE.findall(window)
        if len(money) < 3:
            continue
        n1, n2, n3 = (_to_float(m) for m in money[:3])
        candidates = [
            (n1, n3, n2, abs(n1 + n3 - n2)),  # [excl, total, vat]
            (n1, n2, n3, abs(n1 + n2 - n3)),  # [excl, vat, total]
        ]
        for amount, vat, total, diff in candidates:
            if diff <= _ARITH_TOLERANCE and (best is None or diff < best[3]):
                best = (amount, vat, total, diff)
    if best is None:
        return None
    return best[0], best[1], best[2]


def _extract_amount_guess(text: str) -> Optional[float]:
    if _ITEMIZED_TABLE_RE.search(text):
        return None
    keyword = _AMOUNT_KEYWORD_RE.search(text)
    if not keyword:
        return None
    window = text[keyword.end() : keyword.end() + _AMOUNT_GUESS_WINDOW]
    for match in re.finditer(_STANDALONE_NUMBER_RE, window):
        value = _to_float(match.group(1))
        if value <= 0 or _looks_like_phone_or_id(value):
            continue
        if value in (5, 5.0, 15, 15.0):
            prefix = window[max(0, match.start() - 24) : match.start()]
            if _RATE_CONTEXT_RE.search(prefix):
                continue
        return value

    # Some taxi-slip layouts print the keyword (e.g. "S.R. Total") directly under the
    # handwritten figure instead of above it, so the forward scan above finds nothing.
    # A short backward look is safe here specifically because it's the immediate
    # run-up to the keyword, not a general scan of the page — wide enough for the
    # figure plus a currency abbreviation, too narrow to reach the date/phone/invoice
    # numbers that tend to sit a full line or more earlier.
    behind = text[max(0, keyword.start() - 40) : keyword.start()]
    behind_matches = list(re.finditer(_STANDALONE_NUMBER_RE, behind))
    if behind_matches:
        value = _to_float(behind_matches[-1].group(1))
        if value > 0 and not _looks_like_phone_or_id(value):
            return value
    return None


def _extract_vat(text: str) -> tuple[Optional[float], str]:
    for match in re.finditer(r"vat(?:\s*amount)?", text, re.IGNORECASE):
        prefix = text[max(0, match.start() - 12) : match.start()].lower()
        if "excl" in prefix or "incl" in prefix:
            continue
        rest = text[match.end() : match.end() + 90]
        rest = re.sub(r"^\s*\d{1,2}\s*%", "", rest)
        if re.match(r"\s*taxable", rest, re.IGNORECASE):
            continue
        number = re.search(_NUMBER, rest)
        if not number:
            continue
        value = _to_float(number.group(1))
        window = text[match.start() : match.end() + 24]
        if value in (5, 5.0, 15, 15.0) and re.search(r"\b(5|15)\s*%", window):
            further = re.search(_NUMBER, rest[number.end() :])
            if further:
                value = _to_float(further.group(1))
        if not _looks_like_phone_or_id(value):
            return value, "label"
    return None, "missing"


def _extract_vendor(lines: list[str]) -> tuple[Optional[str], str]:
    usable = []
    for line in lines:
        compact = re.sub(r"\s+", " ", line).strip()
        if len(compact) < 3 or _SKIP_VENDOR_LINE.search(compact):
            continue
        if re.fullmatch(r"[\d.\-/:]+", compact):
            continue
        usable.append(compact[:160])
    if not usable:
        return None, "missing"
    company = [ln for ln in usable if _COMPANY_HINT.search(ln)]
    arabic = [ln for ln in usable if _HAS_ARABIC.search(ln)]
    picked = company[:2] or arabic[:1] or usable[:1]
    # Prefer bilingual vendor when both scripts exist.
    latin = next((ln for ln in picked if not _HAS_ARABIC.search(ln)), None)
    ar = next((ln for ln in (arabic or picked) if _HAS_ARABIC.search(ln)), None)
    if latin and ar and latin != ar:
        return f"{ar} / {latin}", "heuristic"
    return picked[0], "heuristic" if not company else "label"


def _extract_expense_type(text: str) -> tuple[str, str]:
    lowered = text.lower()
    for name, keywords in _EXPENSE_TYPE_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return name, "heuristic"
    return "Other", "bare"


def _extract_with_regex(text: str, words: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    words = words or []
    normalized = text.translate(_ARABIC_INDIC_DIGITS)
    lines = [ln.strip() for ln in normalized.splitlines() if ln.strip()]

    currency_match = _CURRENCY_RE.search(normalized)
    currency = currency_match.group(1).upper() if currency_match else None

    vat_amount, vat_tier = _extract_vat(normalized)

    total_match = _TOTAL_RE.search(normalized)
    total_amount = _to_float(total_match.group(1)) if total_match else None
    total_tier = "label" if total_match else "missing"

    amount = None
    amount_tier = "missing"
    subtotal_match = _SUBTOTAL_RE.search(normalized)
    if subtotal_match:
        amount = _to_float(subtotal_match.group(1))
        amount_tier = "label"
    else:
        currency_amount_match = _CURRENCY_AMOUNT_RE.search(normalized)
        if currency_amount_match:
            amount = _to_float(currency_amount_match.group(1))
            amount_tier = "label"
        else:
            legacy_match = _LEGACY_AMOUNT_RE.search(normalized)
            if legacy_match:
                amount = _to_float(legacy_match.group(1))
                amount_tier = "label"

    if amount is not None and _looks_like_phone_or_id(amount):
        amount, amount_tier = None, "missing"

    # A recognized "VAT% | Excl.VAT | Incl.VAT | VAT" summary row is a stronger,
    # self-consistent read than the independent per-field regexes above (which
    # can't distinguish the VAT% rate column from the actual VAT amount column) —
    # prefer it outright when found.
    table_result = _extract_vat_table(normalized) or _extract_vat_table_arithmetic(normalized)
    if table_result:
        amount, vat_amount, total_amount = table_result
        amount_tier = vat_tier = total_tier = "table"

    amount_was_read = amount is not None
    vat_was_read = vat_amount is not None
    total_was_read = total_amount is not None

    if amount is None and total_amount is not None:
        amount = round(total_amount - vat_amount, 2) if vat_amount is not None else total_amount
        amount_tier = "heuristic"

    if total_amount is None and amount is not None and vat_amount is not None:
        total_amount = round(amount + vat_amount, 2)
        total_tier = "heuristic"

    # Table reads already picked the best-reconciling column order themselves (with a
    # tolerance that knowingly accounts for real POS rounding-adjustment lines) — re-running
    # the stricter generic check against them would just undo that and flag good reads.
    reconciliation_mismatch = False
    if not table_result and amount_was_read and vat_was_read and total_was_read:
        expected_total = round(amount + vat_amount, 2)
        if abs(expected_total - total_amount) > RECONCILE_TOLERANCE:
            reconciliation_mismatch = True
            amount_tier = "mismatch"
            vat_tier = "mismatch"
            total_tier = "mismatch"
    elif vat_amount is None and amount is not None and total_amount is not None:
        implied_vat = round(total_amount - amount, 2)
        if implied_vat > 0:
            vat_amount, vat_tier = implied_vat, "heuristic"

    if amount is None:
        guess = _extract_amount_guess(normalized)
        if guess is not None:
            amount, amount_tier = guess, "guess"

    # Absolute last resort, deliberately tried even on itemized-table bills that the
    # keyword-guess above refuses to touch (it can't tell a line-item price from the
    # bill total there). A blank field forces the employee to type the number from
    # scratch off the photo; a wrong-but-plausible starting point is strictly less
    # work for them to fix — and it's always "guess" tier, so it stays low-confidence
    # and editable rather than silently trusted.
    if amount is None and total_amount is None:
        last_resort = None
        # Prefer a money value sitting right after a (possibly OCR-garbled) total/amount
        # label over blindly taking the last number in the bill — an itemized receipt's
        # last 2-decimal number is often a quantity/weight subtotal ("Total Qty: 6.05"),
        # not money, and would otherwise silently out-rank the real total ("Aaount: 29.00")
        # printed earlier in the text.
        for keyword in _FUZZY_TOTAL_RE.finditer(normalized):
            # "Total Qty"/"Qty Total" is itself a distractor — a piece count or weight
            # subtotal, not currency (the real bug that motivated this exclusion:
            # "Total Qty: 6.05" out-ranking the actual "Aaount: 29.00" a few lines up).
            span = normalized[max(0, keyword.start() - 8) : keyword.end() + 8].lower()
            if "qty" in span:
                continue
            window = normalized[keyword.end() : keyword.end() + 24]
            money_match = _MONEY_RE.search(window)
            if money_match:
                value = _to_float(money_match.group(0))
                if not _looks_like_phone_or_id(value):
                    last_resort = value
        if last_resort is None:
            money = [m for m in _MONEY_RE.findall(normalized) if not _looks_like_phone_or_id(_to_float(m))]
            if money:
                last_resort = _to_float(money[-1])
        if last_resort is not None:
            # The label this is usually found under ("Total"/"Bill Amount") is the
            # incl.-VAT figure, not the excl.-VAT one — if VAT was independently
            # resolved already, derive amount from it instead of setting amount ==
            # total and silently ignoring a VAT value we're otherwise confident in.
            total_amount = last_resort
            amount = round(total_amount - vat_amount, 2) if vat_amount is not None else last_resort
            amount_tier = total_tier = "guess"

    date_match = _DATE_RE.search(normalized)
    bill_date = date_match.group(0) if date_match else None

    vendor, vendor_tier = _extract_vendor(lines)
    expense_type, expense_tier = _extract_expense_type(normalized)

    fields = {
        "vendor": _field(vendor, vendor_tier, words),
        "expense_type": _field(expense_type, expense_tier, words),
        "amount": _field(amount, amount_tier, words),
        "vat_amount": _field(vat_amount, vat_tier, words),
        "total_amount": _field(total_amount, total_tier, words),
        "date": _field(bill_date, "label" if bill_date else "missing", words),
    }
    confidences = [item["confidence"] for item in fields.values()]
    overall = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    return {
        "vendor": vendor or "",
        "expense_type": expense_type,
        "amount": amount,
        "vat_amount": vat_amount,
        "total_amount": total_amount,
        "currency": currency,
        "date": bill_date or "",
        "confidence": overall,
        "field_confidence": {name: item["confidence"] for name, item in fields.items()},
        "low_confidence_fields": [name for name, item in fields.items() if item["low"]],
        "reconciliation_mismatch": reconciliation_mismatch,
        "fields": fields,
    }


def _pick_better_field(en_field: dict[str, Any], ar_field: dict[str, Any]) -> dict[str, Any]:
    if en_field["tier"] == "missing" and ar_field["tier"] != "missing":
        return ar_field
    if ar_field["tier"] == "missing" and en_field["tier"] != "missing":
        return en_field
    return en_field if en_field["confidence"] >= ar_field["confidence"] else ar_field


def _money_group_score(parsed: dict[str, Any]) -> float:
    confs = [parsed["fields"][k]["confidence"] for k in ("amount", "vat_amount", "total_amount")]
    score = sum(confs) / 3
    if parsed["reconciliation_mismatch"]:
        score -= 1.0  # a mismatched trio should essentially never beat a clean one
    return score


def _merge_parsed_results(en: dict[str, Any], ar: dict[str, Any]) -> dict[str, Any]:
    """Combine the English-pass and Arabic-pass parses field-by-field, instead of
    concatenating their raw text and parsing once. Concatenation makes whichever
    language happens to come first in the string win any false-positive match,
    regardless of which language actually got the field right — this compares the
    two languages' already-parsed results directly so the better answer wins.

    amount/vat_amount/total_amount are merged as one atomic group, not per-field:
    they're computed together (VAT-table detection, reconciliation check) and only
    make sense as a self-consistent trio — cherry-picking across languages would
    reintroduce the inconsistency the reconciliation check exists to catch.
    """
    fields: dict[str, Any] = {}
    for name in ("vendor", "expense_type", "date"):
        fields[name] = _pick_better_field(en["fields"][name], ar["fields"][name])

    money_source = en if _money_group_score(en) >= _money_group_score(ar) else ar
    for name in ("amount", "vat_amount", "total_amount"):
        fields[name] = money_source["fields"][name]
    reconciliation_mismatch = money_source["reconciliation_mismatch"]

    confidences = [item["confidence"] for item in fields.values()]
    overall = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    return {
        "vendor": fields["vendor"]["value"] or "",
        "expense_type": fields["expense_type"]["value"],
        "amount": fields["amount"]["value"],
        "vat_amount": fields["vat_amount"]["value"],
        "total_amount": fields["total_amount"]["value"],
        "currency": en["currency"] or ar["currency"],
        "date": fields["date"]["value"] or "",
        "confidence": overall,
        "field_confidence": {name: item["confidence"] for name, item in fields.items()},
        "low_confidence_fields": [name for name, item in fields.items() if item["low"]],
        "reconciliation_mismatch": reconciliation_mismatch,
        "fields": fields,
    }


def _stub_ocr(filename_hint: str = "") -> dict[str, Any]:
    vendor = random.choice(SAMPLE_VENDORS)
    amount = round(random.uniform(120, 2500), 2)
    vat_amount = round(amount * 0.05, 2)
    total_amount = round(amount + vat_amount, 2)
    parsed = _extract_with_regex(
        f"{vendor}\nTAX INVOICE\nBill Amount: {total_amount}\nVAT 5%: {vat_amount}\nAmount (Excl.Vat): {amount}\nDate: {date.today().isoformat()}\n{filename_hint}"
    )
    parsed["raw_text"] = parsed.get("raw_text", "")
    parsed["raw_json"] = {"engine": "stub", "vendor": vendor, "amount": amount, "field_confidence": parsed["field_confidence"]}
    parsed["raw_text"] = f"{vendor}\nBill Amount: {total_amount}\nVAT: {vat_amount}\nDate: {date.today().isoformat()}\n{filename_hint}"
    return parsed


def _get_paddle_engine(lang: str):
    if lang not in _paddle_engines:
        from paddleocr import PaddleOCR  # type: ignore  # imported lazily — heavy dependency

        _paddle_engines[lang] = PaddleOCR(lang=lang, enable_mkldnn=False)
    return _paddle_engines[lang]


def _paddle_ocr_pass(image_path: str, lang: str) -> list[dict[str, Any]]:
    """Paddle has no mixed-script model, so bilingual bills need both 'en' and 'ar' passes."""
    engine = _get_paddle_engine(lang)
    results = engine.predict(image_path)
    words: list[dict[str, Any]] = []
    for r in results:
        texts = r.get("rec_texts", [])
        scores = r.get("rec_scores", [])
        for text, score in zip(texts, scores):
            if text.strip():
                words.append({"text": text, "confidence": float(score), "lang": lang})
    return words


def _paddle_ocr(image_bytes: bytes) -> dict[str, Any] | None:
    try:
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            en_words = _paddle_ocr_pass(tmp_path, "en")
            ar_words = _paddle_ocr_pass(tmp_path, "ar")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except Exception:
        return None

    # Automatic script coverage: always run both Latin and Arabic recognizers. Each is
    # parsed independently and merged at the field level (not by concatenating raw text
    # first) so a false-positive match in one language's text can't shadow the other
    # language's correct answer just by coming first in the string.
    en_text = "\n".join(w["text"] for w in en_words)
    ar_text = "\n".join(w["text"] for w in ar_words)
    en_parsed = _extract_with_regex(en_text, en_words)
    ar_parsed = _extract_with_regex(ar_text, ar_words)
    parsed = _merge_parsed_results(en_parsed, ar_parsed)

    words = en_words + ar_words
    raw_text = en_text + "\n" + ar_text
    parsed["raw_text"] = raw_text
    parsed["raw_json"] = {
        "engine": "paddle",
        "words": words,
        "field_confidence": parsed["field_confidence"],
        "low_confidence_fields": parsed["low_confidence_fields"],
        "expense_type": parsed["expense_type"],
    }
    return parsed


class OcrService:
    def run(self, image_bytes: bytes, filename: str = "receipt.jpg") -> dict[str, Any]:
        settings = get_settings()
        if settings.ocr_backend == "paddle":
            paddle = _paddle_ocr(image_bytes)
            if paddle:
                return paddle

        stub = _stub_ocr(filename)
        stub["raw_json"] = json.dumps(stub["raw_json"])
        return stub

    def extract_from_text(self, text: str, words: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
        return _extract_with_regex(text, words)

    def merge_bilingual(
        self,
        en_text: str,
        ar_text: str,
        en_words: Optional[list[dict[str, Any]]] = None,
        ar_words: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Parse the English and Arabic OCR text separately and merge field-by-field —
        the same logic `_paddle_ocr` uses in production. Exposed so tooling (e.g. the
        comparison scripts) can reproduce real merge behavior without duplicating it."""
        en_parsed = _extract_with_regex(en_text, en_words)
        ar_parsed = _extract_with_regex(ar_text, ar_words)
        return _merge_parsed_results(en_parsed, ar_parsed)


ocr_service = OcrService()
