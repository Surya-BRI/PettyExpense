"""Company base currency — the one place that decides it.

ErpExpenseRegionConfig.baseCurrency is the source of truth. The map below only seeds that
column (and covers rows it hasn't been backfilled on yet); tax_rules.yaml default_currency is
for the OCR fallback only and is not used for conversion.
"""
from typing import Optional

DEFAULT_BASE_CURRENCY = {
    "DUBAI": "AED",
    "UAE": "AED",
    "KSA": "SAR",
    "OMAN": "OMR",
    "IN": "INR",
}


def default_base_currency(region_code: Optional[str]) -> str:
    return DEFAULT_BASE_CURRENCY.get((region_code or "").strip().upper(), "AED")


def region_base_currency(region) -> str:
    """Base currency of an ErpExpenseRegionConfig row (AED when there's no region)."""
    if region is None:
        return "AED"
    stored = (getattr(region, "base_currency", None) or "").strip().upper()
    return stored or default_base_currency(region.region_code)


def format_money(currency: Optional[str], amount: Optional[float]) -> str:
    return f"{(currency or '').strip()} {float(amount or 0):,.2f}".strip()


def bill_and_base_text(txn) -> str:
    """'SAR 1,000.00 (≈ AED 978.20)' — bill total, plus the converted total when they differ."""
    total = txn.total_amount if txn.total_amount is not None else (txn.amount or 0) + (txn.vat_amount or 0)
    bill = format_money(txn.currency, total)
    base = (txn.base_currency or "").strip().upper()
    if base and base != (txn.currency or "").strip().upper() and txn.total_amount_base is not None:
        return f"{bill} (≈ {format_money(base, txn.total_amount_base)})"
    return bill
