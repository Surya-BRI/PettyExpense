"""Core data structures for the extraction pipeline.

Zero third-party/framework imports — this module (and the rest of the
`extraction` package) must be importable and testable without FastAPI,
SQLAlchemy, or a database connection.
"""
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

BoundingBox = tuple[float, float, float, float]  # (x_min, y_min, x_max, y_max), y increasing downward

FIELD_NAMES = (
    "vendor",
    "date",
    "currency",
    "amount",
    "vat_rate",
    "vat_amount",
    "discount",
    "service_charge",
    "tip",
    "cash_tendered",
    "card_amount",
    "change",
    "total_amount",
    "invoice_number",
    "transaction_number",
    "expense_category",
)


@dataclass(frozen=True)
class OcrWord:
    text: str
    confidence: float = 1.0
    lang: Literal["en", "ar"] = "en"
    bounding_box: Optional[BoundingBox] = None
    page: int = 1
    reading_order: int = 0
    source_pass: str = "paddle"


@dataclass(frozen=True)
class OcrLine:
    """One line of a receipt — one or more OcrWords grouped by normalize.group_into_lines()."""

    text: str
    words: tuple[OcrWord, ...]
    confidence: float
    bounding_box: Optional[BoundingBox]
    page: int
    reading_order: int


@dataclass
class FieldCandidate:
    field_name: str
    value: Any
    source_text: str
    confidence: float
    page: int = 1
    bounding_box: Optional[BoundingBox] = None
    signals: list[str] = field(default_factory=list)
    raw_score_breakdown: dict[str, float] = field(default_factory=dict)
    reading_order: int = 0


@dataclass
class SelectedField:
    value: Any
    confidence: float
    evidence: str
    signals: list[str]
    low_confidence: bool
    warning: Optional[str] = None


@dataclass
class ExtractionResult:
    fields: dict[str, SelectedField]
    overall_confidence: float
    reconciliation_mismatch: bool
    raw_text: str
    all_candidates: dict[str, list[FieldCandidate]] = field(default_factory=dict)
