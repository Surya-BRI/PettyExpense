"""Line-item extraction on real OCR output of itemised bills (see fixtures/line_item_bills.py)."""
from extraction.line_items import extract_line_items
from extraction.reference_data import ReferenceData
from extraction.types import OcrLine, OcrWord
from tests.fixtures.line_item_bills import PHARMACY, SUPERMARKET


def _lines(rows: list[tuple[int, str]]) -> list[OcrLine]:
    out = []
    for i, (y, text) in enumerate(rows):
        bbox = (0.0, float(y), 600.0, float(y) + 12.0)
        w = OcrWord(text=text, confidence=0.95, lang="en", bounding_box=bbox, page=1, reading_order=i)
        out.append(OcrLine(text=text, words=(w,), confidence=0.95, bounding_box=bbox, page=1, reading_order=i))
    return out


def _items(rows):
    return [(i.description, i.quantity, i.amount) for i in extract_line_items(_lines(rows), ReferenceData())]


def test_supermarket_rejoins_numbers_with_the_item_name_below_them():
    assert _items(SUPERMARKET) == [
        ("CURIANDER LEAF", 2.0, 1.98),
        ("ONION (INDTA)", 1.06, 3.70),
        ("SAFA YOGHURT 10KG", 1.0, 38.0),
        ("GINGER (PRC)", 0.53, 4.50),
        ("CURRY LEAF", 1.0, 1.0),
    ]


def test_supermarket_stops_at_the_table_summary_and_totals():
    descriptions = [d for d, _, _ in _items(SUPERMARKET)]
    # "Qly: 5.59" (item count), "Bill Amount", "CASH", the VAT table: none are items.
    assert not any(word in " ".join(descriptions).lower() for word in ("qly", "amount", "cash", "rounding", "taxable"))


def test_pharmacy_reads_every_item_row():
    items = _items(PHARMACY)
    assert len(items) == 12
    by_name = {d: (q, a) for d, q, a in items}
    assert by_name["ADV MED GAUZE SWAB NON S ERILE 5X5CM 8PLY 10"] == (5.0, 23.94)
    # Name on its own line just below its numbers.
    assert by_name["MEDI COTTON WOOL 50G"] == (5.0, 23.94)
    assert by_name["MED ADVANCE WOUND ADHES VE 100S"] == (2.0, 28.72)
    assert by_name["MED ADVANCE NORMAL SCISSOR"] == (1.0, 7.66)
    assert by_name["ADV MED AM0FS-102BX CPR MASK"] == (1.0, 19.1)


def test_pharmacy_ignores_item_codes_and_product_sizes():
    by_name = {d: (q, a) for d, q, a in _items(PHARMACY)}
    # "1.25CMX5M" is a size, not the quantity; the 8-digit item code is dropped from the name.
    assert by_name["ADV MED ZINC OXIDE PLASTER 1.25CMX5M TRANS"] == (1.0, 2.87)
    assert by_name["MED ADVANCE ZINC OXIDE ADH ESIVE PLASTER 2.5*5"] == (4.0, 19.15)
    assert all("55541782" not in d and "9999" not in d for d in by_name)


def test_pharmacy_row_whose_amount_is_cut_off_keeps_the_item_but_no_amount():
    by_name = {d: (q, a) for d, q, a in _items(PHARMACY)}
    # The photo cut this row's net amount off: "2.00 0 00" is qty + VAT%, not a 0.00 total.
    assert by_name["COTTON TIP APPLICATOR WO DEN 6 INCH 100S"] == (2.0, None)


def test_pharmacy_last_amount_with_one_decimal_is_still_read():
    by_name = {d: (q, a) for d, q, a in _items(PHARMACY)}
    assert by_name["ADV MED CONFORMING BANDACE 5CMX4.5M"] == (5.0, 14.3)


def test_no_item_table_header_means_no_line_items():
    rows = [(10, "ENOC"), (30, "Super 98 40.00 L"), (50, "Total AED 106.40")]
    assert _items(rows) == []


def test_empty_input():
    assert extract_line_items([], ReferenceData()) == []


def test_same_row_read_by_both_ocr_passes_is_kept_once():
    rows = [(100, "Description Qty Amount"), (120, "CUCUMBER 2.17 9.13"), (121, "CKCREER 2.17 9.13"), (140, "TOMATO 1.00 4.49")]
    assert _items(rows) == [("CUCUMBER", 2.17, 9.13), ("TOMATO", 1.0, 4.49)]


def test_total_qty_and_garbled_bill_amount_end_the_table():
    rows = [(100, "Description Qty Amount"), (120, "BREAD 1.00 6.00"), (140, "Total Qty 6.05"), (160, "B111 Amount 29.00")]
    assert _items(rows) == [("BREAD", 1.0, 6.0)]


# --- quantity: description-before-qty rows, and the OCR artifacts that destroy that quantity -----

def test_a_bare_quantity_after_the_description_is_read_not_the_rate():
    # Real layout: "Bolt 20X100 | 50 Pcs | 4.73 | 4.50 Pcs | 225.00 | 5% | 225.00 | 11.25 | 236.25".
    # Before the fix, _leading_qty_match only accepted "50 Pcs" when nothing preceded it on the row,
    # so a row starting with a product name first (the common case) fell back to decimals[0] -- the Rate.
    rows = [
        (100, "Description of Goods Quantity Rate"),
        (120, "Bolt 20X100 50 Pcs 4.73 4.50 Pcs 225.00 5% 225.00 11.25 236.25"),
    ]
    assert _items(rows) == [("Bolt 20X100 50 Pcs", 50.0, 236.25)]


def test_packing_note_footnotes_are_not_read_as_items():
    # "1 PKT PER 400 PCS" / "75 PKT X 400 PCS = 30000 PCS" are a wrapped note below the real row, not a
    # second item -- neither has a Rate/Amount decimal of its own, unlike a genuine Qty cell's row.
    rows = [
        (100, "Description of Goods Quantity Rate"),
        (120, "Drywall Screw 8x2 60 Pcs 16.01 15.25 Pcs 915.00 5% 915.00 45.75 960.75"),
        (140, "1 PKT PER 400 PCS"),
        (160, "75 PKT X 400 PCS = 30000 PCS"),
        (180, "Total 960.75"),
    ]
    assert _items(rows) == [("Drywall Screw 8x2 60 Pcs", 60.0, 960.75)]


def test_an_item_codes_trailing_digits_are_not_merged_into_the_adjacent_quantity():
    # _SPLIT_DECIMAL exists to rejoin OCR's "38.00" misread as "38 00"; it must not also rejoin
    # an item code's own trailing digits ("20X100") with a following bare quantity cell ("50 Pcs")
    # into a fake decimal ("20X100.50") that destroys the one place the real quantity was readable.
    rows = [(100, "Description Quantity Rate"), (120, "Bolt 20X100 50 Pcs 4.73 225.00")]
    items = _items(rows)
    assert items == [("Bolt 20X100 50 Pcs", 50.0, 225.0)]
    assert "100.50" not in items[0][0]


def test_a_quantity_cell_merged_with_its_unit_into_one_ocr_word_still_resolves_by_column():
    # On the real bill this comes from, the OCR engine returned "50 Pcs" as ONE word box (no
    # space inside its own geometry) sitting under the "Quantity" header -- _nearest_column_number's
    # clean-number check used to skip that word entirely and silently grab the next-nearest
    # number (the Rate column) instead, overriding the correct int_qty with the wrong value.
    header = OcrLine(
        text="Description Quantity Rate",
        words=(
            OcrWord(text="Description", confidence=0.95, bounding_box=(50.0, 10.0, 140.0, 24.0), reading_order=0),
            OcrWord(text="Quantity", confidence=0.95, bounding_box=(326.0, 10.0, 368.0, 24.0), reading_order=1),
            OcrWord(text="Rate", confidence=0.95, bounding_box=(380.0, 10.0, 410.0, 24.0), reading_order=2),
        ),
        confidence=0.95, bounding_box=(50.0, 10.0, 410.0, 24.0), page=1, reading_order=0,
    )
    body = OcrLine(
        text="Bolt 20X100 50 Pcs 4.73 225.00",
        words=(
            OcrWord(text="Bolt 20X100", confidence=0.95, bounding_box=(67.0, 40.0, 140.0, 54.0), reading_order=3),
            OcrWord(text="50 Pcs", confidence=0.95, bounding_box=(325.0, 40.0, 367.0, 57.0), reading_order=4),
            OcrWord(text="4.73", confidence=0.95, bounding_box=(381.0, 40.0, 407.0, 56.0), reading_order=5),
            OcrWord(text="225.00", confidence=0.95, bounding_box=(486.0, 40.0, 529.0, 57.0), reading_order=6),
        ),
        confidence=0.95, bounding_box=(67.0, 40.0, 529.0, 57.0), page=1, reading_order=1,
    )
    items = extract_line_items([header, body], ReferenceData())
    assert [(i.description, i.quantity, i.amount) for i in items] == [("Bolt 20X100 50 Pcs", 50.0, 225.0)]
