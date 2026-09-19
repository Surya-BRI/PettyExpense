from extraction.dedupe import dedupe_lines
from tests.fixtures.ocr_lines import line


def test_dedupe_text_only_no_bbox_merges_noisy_duplicate():
    lines = [
        line("Total AED45.00", order=0, confidence=0.9),
        line("Totai AED45,00", order=1, confidence=0.6),  # same value, OCR-garbled duplicate
    ]
    result = dedupe_lines(lines)
    assert len(result) == 1
    assert result[0].confidence == 0.9  # higher-confidence member survives


def test_dedupe_keeps_genuinely_different_lines():
    lines = [
        line("Total AED45.00", order=0),
        line("VAT Amt AED0.29", order=1),
    ]
    result = dedupe_lines(lines)
    assert len(result) == 2


def test_dedupe_bbox_overlap_merges_even_with_different_text():
    lines = [
        line("Total AED45.00", bbox=(0, 0, 100, 20), order=0, confidence=0.5),
        line("Total AED45.00", bbox=(2, 1, 98, 19), order=5, confidence=0.9),  # same region, far reading order
    ]
    result = dedupe_lines(lines)
    assert len(result) == 1
    assert result[0].confidence == 0.9


def test_dedupe_far_apart_reading_order_not_merged_without_bbox():
    lines = [line(f"Item {i}", order=i) for i in range(10)]
    lines.append(line("Item 0", order=9))  # textually identical to lines[0] but far away in reading order
    result = dedupe_lines(lines)
    assert len(result) == 11  # not merged: "Item 0" vs "Item 9" text differs enough, and vs itself far apart
