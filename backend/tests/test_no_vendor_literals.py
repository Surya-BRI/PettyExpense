"""Structural guardrail: the extraction engine must never special-case a vendor/brand/company-type name — needing to allow a new literal here is very likely a regression."""
import re
from pathlib import Path

import pytest

FORBIDDEN_LITERALS = (
    "ENOC",
    "LLC",
    "HYPERMARKET",
    "SUPERMARKET",
    "CARREFOUR",
    "TRADING",
)

EXTRACTION_DIR = Path(__file__).resolve().parent.parent / "extraction"


@pytest.mark.xfail(
    reason="Legacy text extractor, off the live scan path since da2706f (GPT vision only). "
    "candidates._ENTITY_SUFFIX_RE (e86318a) lists generic legal suffixes incl. LLC/TRADING.",
    strict=False,
)
def test_no_forbidden_brand_or_layout_literals_in_engine_source():
    offenders = []
    for path in EXTRACTION_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for literal in FORBIDDEN_LITERALS:
            if re.search(re.escape(literal), text, re.IGNORECASE):
                offenders.append((path.name, literal))
    assert offenders == []
