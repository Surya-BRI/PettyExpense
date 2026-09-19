import pytest

from extraction.normalize import normalize_text, parse_amount, repair_numeric_ocr_errors


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("١٢٣", "123"),  # Arabic-Indic digits
        ("۱۲۳", "123"),  # Persian digits
        ("Total:", "Total"),
        ("....", "."),
        ("  a   b  ", "a b"),
        ("VAT ٪", "VAT %"),
        ("5°", "5%"),
    ],
)
def test_normalize_text(raw, expected):
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("45.00", 45.00),
        ("45,00", 45.00),
        ("1,234.56", 1234.56),
        ("1.234,56", 1234.56),
        ("6", 6.0),
        ("0.29", 0.29),
        ("1,234", 1234.0),
    ],
)
def test_parse_amount_decimal_formats(raw, expected):
    assert parse_amount(raw) == pytest.approx(expected)


def test_parse_amount_rejects_garbage():
    assert parse_amount("abc") is None
    assert parse_amount("") is None
    assert parse_amount(None) is None


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("l5.00", "15.00"),
        ("4S.00", "45.00"),
        ("45.00", "45.00"),
        ("4SB.00", None),  # more than one substitution — not repaired
    ],
)
def test_repair_numeric_ocr_errors(raw, expected):
    assert repair_numeric_ocr_errors(raw) == expected
