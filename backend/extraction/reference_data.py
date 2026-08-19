"""Injected reference data: known vendors, categories, currencies, VAT-rate
priors, and the label-synonym vocabulary. Nothing in this module hard-codes a
vendor name, brand, or country — callers (an admin-config/DB adapter, or a
test) build a ReferenceData instance and pass it in.
"""
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

_CONFIG_DIR = Path(__file__).parent / "config"

LabelVocabulary = dict[str, tuple[str, ...]]


@lru_cache
def _load_label_vocabulary() -> LabelVocabulary:
    path = _CONFIG_DIR / "label_vocabulary.yaml"
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return {concept: tuple(synonyms) for concept, synonyms in raw.items()}


@lru_cache
def _load_label_exclusions() -> LabelVocabulary:
    path = _CONFIG_DIR / "label_exclusions.yaml"
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return {concept: tuple(words) for concept, words in raw.items()}


@lru_cache
def _load_tax_rules() -> dict:
    path = _CONFIG_DIR / "tax_rules.yaml"
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def default_tax_rules_for_region(region_code: Optional[str] = None) -> tuple[tuple[str, ...], tuple[float, ...]]:
    """Returns (valid_currency_codes, plausible_vat_rates) for a region code,
    falling back to the shipped 'default' entry for unknown/missing codes."""
    rules = _load_tax_rules()
    base = rules.get("default", {})
    currencies = tuple(base.get("valid_currency_codes", ()))
    rates = tuple(float(r) for r in base.get("plausible_vat_rates", ()))
    if region_code:
        override = rules.get("regions", {}).get(region_code, {})
        if "valid_currency_codes" in override:
            currencies = tuple(override["valid_currency_codes"])
        if "plausible_vat_rates" in override:
            rates = tuple(float(r) for r in override["plausible_vat_rates"])
    return currencies, rates


DEFAULT_CURRENCIES, DEFAULT_VAT_RATES = default_tax_rules_for_region(None)


@dataclass(frozen=True)
class CategoryRef:
    name: str
    keywords: tuple[str, ...] = ()
    name_ar: Optional[str] = None


@dataclass(frozen=True)
class ReferenceData:
    known_vendors: tuple[str, ...] = ()
    categories: tuple[CategoryRef, ...] = ()
    valid_currency_codes: tuple[str, ...] = DEFAULT_CURRENCIES
    plausible_vat_rates: tuple[float, ...] = DEFAULT_VAT_RATES
    date_format_hints: tuple[str, ...] = ()
    label_vocabulary: LabelVocabulary = field(default_factory=_load_label_vocabulary)
    label_exclusions: LabelVocabulary = field(default_factory=_load_label_exclusions)
