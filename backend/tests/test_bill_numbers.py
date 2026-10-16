"""Bill / invoice number extraction: the value beside or under its label, garbled labels, and the shapes that must never win."""
from extraction.normalize import group_into_lines, normalize_text
from extraction.pipeline import extract, extract_from_text_input
from extraction.reference_data import ReferenceData
from extraction.types import OcrWord


def _text(text: str):
    return extract_from_text_input(text, ReferenceData())


def _bill_no(text: str):
    f = _text(text).fields
    return f["invoice_number"].value or f["transaction_number"].value


def _boxed(*entries):
    """entries: (text, x0, y0, x1, y1) -> extraction result, as the real RunPod/CPU paths build it."""
    words = [
        OcrWord(text=t, confidence=1.0, bounding_box=(x0, y0, x1, y1), reading_order=i)
        for i, (t, x0, y0, x1, y1) in enumerate(entries)
    ]
    return extract(group_into_lines(words), ReferenceData())


def _boxed_no(*entries):
    return _boxed(*entries).fields["invoice_number"].value


# --- label wording -------------------------------------------------------------------------------

def test_label_variants_beyond_invoice_no():
    assert _bill_no("DN NUMBER: SO-DN-DIP-110042") == "SO-DN-DIP-110042"
    assert _bill_no("Inv : SID-SHJ-2026-10580") == "SID-SHJ-2026-10580"
    assert _bill_no("Credit No : CN-2026-0262") == "CN-2026-0262"
    assert _bill_no("TRAN: 584439") == "584439"
    assert _bill_no("INVOICENO: PEN91473") == "PEN91473"


def test_bare_no_label_at_the_start_of_a_line():
    assert _bill_no("No. 1383 TAX INVOICE Date 4 Aug 26") == "1383"
    assert _bill_no("B/NO.20367 103107126") == "20367"


def test_a_garbled_label_with_digits_for_letters_still_matches():
    assert _bill_no("date :03-Aug-2026 17:40 Bi11 No :236191") == "236191"
    assert _bill_no("B11 No :236191") == "236191"


def test_no_followed_by_a_word_is_not_a_label():
    assert _bill_no("No Exchange On Under Garments") is None
    assert _bill_no("No Cash Refund, Thank You") is None


def test_investment_is_not_an_invoice_label():
    assert normalize_text("Investment Park 2026") == "Investment Park 2026"
    assert _bill_no("Dubai Investment Park-2 Jabel Ali") is None


# --- value placement -----------------------------------------------------------------------------

def test_value_directly_below_its_label_in_the_same_column():
    got = _boxed_no(
        ("Invoice No.", 1016, 181, 1145, 213),
        ("Dated", 1341, 189, 1418, 219),
        ("SHT P.O.Box : 35141, Sharjah", 184, 214, 706, 287),
        ("CASH/SHT/1205 29-Jul-26", 1016, 215, 1470, 253),
    )
    assert got == "CASH/SHT/1205"


def test_a_slightly_tilted_page_still_pairs_label_and_value_below():
    got = _boxed_no(("Invoice No.", 498, 213, 582, 244), ("T-INV/26/1854 Dated", 496, 232, 747, 270))
    assert got == "T-INV/26/1854"


def test_invoice_number_beats_the_delivery_note_number_on_the_same_page():
    got = _boxed_no(
        ("Invoice No.", 498, 213, 582, 244),
        ("T-INV/26/1854 Dated", 496, 232, 747, 270),
        ("Delivery Note 9-Jul-2026", 495, 250, 787, 285),
        ("T-DO/26/1907 Supplier's Ref. Cash", 496, 271, 749, 324),
    )
    assert got == "T-INV/26/1854"


def test_a_delivery_note_number_is_used_when_there_is_no_invoice_number():
    assert _bill_no("DELIVERY NOTE\nDN NUMBER: SO-DN-DIP-110042") == "SO-DN-DIP-110042"


def test_alpha_prefix_and_number_are_kept_together():
    assert _bill_no("Invoice No.\nRB 26/01008 18-Sep-26") == "RB 26/01008"


def test_a_header_word_bill_labels_the_value_beneath_it():
    got = _boxed_no(
        ("Date Time Store POS Bill", 202, 1703, 780, 1753),
        ("05/08/2026 09:12 00 1 115", 198, 1742, 787, 1791),
    )
    assert got == "115"


# --- shapes that must never win ------------------------------------------------------------------

def test_numbers_cut_out_of_a_decimal_are_not_bill_numbers():
    assert _bill_no("Credit No\n210.0000") is None
    assert _bill_no("Invoice No\n24.007024.00") is None


def test_license_and_phone_context_do_not_block_a_labelled_number_on_the_same_line():
    assert _bill_no("Tel 04-8831644 Bill No: 236191") == "236191"
    assert _bill_no("Fax License Number : 19051005") is None


def test_the_zero_inside_a_mostly_alphabetic_code_is_read_as_the_letter_o():
    assert _bill_no("Invoice No.: 000P0SDIP2000039678") == "000POSDIP2000039678"


def test_a_product_code_inside_a_description_is_not_the_bill_number():
    got = _boxed_no(("Invoice#", 1449, 1082, 1700, 1130), ("NTRL BR-TZ231 Label Cassette", 1781, 295, 1840, 732))
    assert got != "NTRL BR-TZ231" and got != "BR-TZ231"


def test_a_dotted_code_is_kept_whole_but_never_cut_in_half():
    assert _bill_no("Invoice No.: XK-T-2026.08.15-02324") == "XK-T-2026.08.15-02324"


# --- currency: an explicit "Currency: AED" beats a code read out of a garbled table header ---------------

def test_labelled_currency_beats_a_code_misread_from_a_table_header():
    f = _text("CURRENCY: AED\nSAR PRODUCT UNIT XA 1 QTY UNIT UNIT").fields
    assert f["currency"].value == "AED"
