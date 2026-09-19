"""Structural guardrail: the extraction engine must never special-case a vendor/brand/company-type name — needing to allow a new literal here is very likely a regression."""
import re
from pathlib import Path

FORBIDDEN_LITERALS = (
    "ENOC",
    "LLC",
    "HYPERMARKET",
    "SUPERMARKET",
    "CARREFOUR",
    "TRADING",
)

EXTRACTION_DIR = Path(__file__).resolve().parent.parent / "extraction"


def test_no_forbidden_brand_or_layout_literals_in_engine_source():
    offenders = []
    for path in EXTRACTION_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for literal in FORBIDDEN_LITERALS:
            if re.search(re.escape(literal), text, re.IGNORECASE):
                offenders.append((path.name, literal))
    assert offenders == []
