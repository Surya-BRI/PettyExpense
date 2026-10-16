"""VAT tax-summary rows are recognised by arithmetic (amount + vat == total, vat ~= rate * amount), not labels or geometry."""
from extraction.pipeline import extract_from_text_input
from extraction.reference_data import ReferenceData


def _fields(text: str) -> tuple:
    result = extract_from_text_input(text, ReferenceData())
    return tuple(result.fields[f].value for f in ("amount", "vat_amount", "total_amount"))


def test_clean_breakdown_row_with_garbled_header_labels():
    # image (4).png: header read as "VATN Taxable Amount VAT Ttta" -- no Total label survived.
    assert _fields("VATN Taxable Amount VAT Ttta\n5% 45.21 2.28 47.49") == (45.21, 2.28, 47.49)


def test_garbled_amount_is_derived_from_vat_and_total():
    # image (3).png: the amount cell was read as "4u.84"; total - vat recovers 46.84 (2.34 / 46.84 = 5%).
    assert _fields("ATX Taxable Amount VAI Total\n5% 4u.84 2.34 49.18") == (46.84, 2.34, 49.18)


def test_column_order_does_not_matter():
    # image (6).png prints Excl.VAT, Incl.VAT, VAT in that order.
    assert _fields("VAT% Exd.VAT Incl VAT VAT\n5 83.37 87.54 4.17") == (83.37, 4.17, 87.54)


def test_unrelated_decimals_without_a_rate_cue_are_not_treated_as_a_breakdown():
    # 5% of 40.00 is 2.00 and 42.00 is the sum -- but nothing on the row says this is a tax summary.
    amount, vat, total = _fields("Milk 40.00\nBread 2.00\nSum 42.00")
    assert not (amount == 40.0 and vat == 2.0 and total == 42.0)


def test_a_rate_cue_with_numbers_that_do_not_reconcile_is_ignored():
    # 5% printed, but 10.00 + 0.50 != 12.00 and no pair is a 5% split.
    amount, vat, total = _fields("VAT 5%\n10.00 0.50 12.00")
    assert total != 12.0 or vat != 0.5 or amount != 10.0


# --- stacked totals block ("Total / VAT r% / Grand Total", one figure per line) --------------------

def test_stacked_totals_block_derived_from_subtotal_and_printed_rate():
    # AL MANAR hand-filled invoice, CPU OCR: decimals dropped and digits garbled ("16 SO", "396 50").
    assert _fields("Total 330 0\nVAT 5 % 16 SO\nGrand Total 396 50") == (330.0, 16.5, 346.5)


def test_stacked_totals_block_with_geometry_and_a_garbage_grand_total():
    # Same bill via RunPod: VAT amount on its own box on the VAT row, grand total read as "bE 6".
    from extraction.normalize import group_into_lines
    from extraction.pipeline import extract
    from extraction.types import OcrWord

    def w(text, x0, y0, x1, y1, i):
        return OcrWord(text=text, confidence=1.0, bounding_box=(x0, y0, x1, y1), reading_order=i)

    words = [
        w("Total 330", 957, 1359, 1271, 1403, 0),
        w("VAT 5%", 937, 1416, 1061, 1450, 1),
        w("16 so", 1220, 1410, 1345, 1454, 2),
        w("Grand Total bE 6", 915, 1457, 1289, 1501, 3),
    ]
    result = extract(group_into_lines(words), ReferenceData())
    got = tuple(result.fields[f].value for f in ("amount", "vat_amount", "total_amount"))
    assert got == (330.0, 16.5, 346.5)


def test_stacked_block_without_any_corroborating_reading_is_not_invented():
    # Nothing on the VAT or grand-total line agrees with 330 * 5%, so no values may be fabricated.
    assert 346.5 not in _fields("Total 330\nVAT 5%\nGrand Total 900")


# --- arithmetic consistency across independently selected fields ------------------------------------

def _cand(field, value, conf):
    from extraction.types import FieldCandidate
    return FieldCandidate(field, value, f"{field} {value}", conf, signals=[f"{field}_label"])


def test_inconsistent_picks_are_resolved_to_a_reconciling_triple_already_among_the_candidates():
    from extraction.select import select_fields
    selected = select_fields(
        [
            _cand("amount", 9.52, 0.9), _cand("vat_amount", 0.48, 0.9),
            _cand("total_amount", 9.52, 0.9), _cand("total_amount", 10.0, 0.7),
        ],
        (5.0,),
    )
    assert (selected["amount"].value, selected["vat_amount"].value, selected["total_amount"].value) == (9.52, 0.48, 10.0)
    assert selected["total_amount"].warning == "resolved_by_arithmetic_consistency"


def test_a_discount_that_is_not_a_plausible_vat_rate_is_not_promoted_to_vat():
    from extraction.select import select_fields
    selected = select_fields(
        [_cand("amount", 224.99, 0.9), _cand("vat_amount", 10.01, 0.8), _cand("total_amount", 235.0, 0.8),
         _cand("total_amount", 224.99, 0.85)],
        (5.0,),
    )
    assert selected["vat_amount"].value != 10.01


def test_a_negative_amount_is_never_derived_from_an_impossible_total_and_vat():
    from extraction.select import select_fields
    selected = select_fields([_cand("total_amount", 6.0, 0.9), _cand("vat_amount", 16.0, 0.9)], (5.0,))
    assert selected["amount"].value is None or selected["amount"].value > 0


# --- bill number / date fixes found on the same hand-filled invoice -------------------------------

def _result(text: str):
    return extract_from_text_input(text, ReferenceData())


def test_invoice_number_is_not_the_trn_printed_on_the_same_line():
    result = _result("TRN100362941500003 CASH/CREDIT TAX INVOICE No. 22860")
    assert result.fields["invoice_number"].value == "22860"


def test_the_word_no_before_a_number_is_not_rewritten_to_n0():
    from extraction.normalize import normalize_text
    assert normalize_text("TAX INVOICE No. 22860") == "TAX INVOICE No. 22860"
    assert normalize_text("VAT Amt AEDO.29") == "VAT Amt AED0.29"  # the currency-code glitch is still repaired


def test_a_misread_year_is_repaired_to_the_one_plausible_year_within_two_digits():
    from datetime import date
    year = date.today().year
    misread = str(year).replace("2", "1")  # e.g. 2026 -> 1016
    result = _result(f"Date 06.07.{misread}")
    assert result.fields["date"].value == f"06.07.{year}"


def test_an_implausible_year_with_no_close_plausible_year_is_not_trusted():
    result = _result("Date 06.07.1999")
    assert result.fields["date"].value != "06.07.1999" or result.fields["date"].confidence < 0.6


# --- bill-number false positives found by the 38-bill sweep ----------------------------------------

def _bill_no(text: str):
    return _result(text).fields["invoice_number"].value


def test_a_number_beside_its_own_invoice_label_beats_phone_and_fax_numbers():
    assert _bill_no("PHONE 8857517 FAX 8857507\nTAX INVOICE NUMBER: INV-DIP-112954") == "INV-DIP-112954"


def test_labelled_number_wins_over_a_longer_trailing_number():
    assert _bill_no("TRN:100347691600003 INVOICE NO: PEN91473 65768") == "PEN91473"


def test_phone_numbers_are_never_bill_numbers():
    assert _bill_no("Invoice No\nTel:+971 547578173") is None
    assert _bill_no("Invoice No\n0585405699") is None


def test_a_street_number_is_not_a_bill_number():
    assert _bill_no("Invoice No\n7926 Zayd Ibn Thabit Street Riyadh 12831") is None


def test_an_amount_with_its_currency_code_is_not_a_bill_number():
    assert _bill_no("Invoice No\nSAR72") is None


def test_iban_and_email_names_are_not_bill_numbers():
    assert _bill_no("Invoice No AE420400000024160329061") is None
    assert _bill_no("Invoice No\nDANESHALI45@YAHOO.COM") is None


def test_a_number_printed_just_before_its_invoice_label_is_the_invoice_number():
    # Madina Al Safia bill: the value sits left of its "Invoice No." label in the merged OCR line (checked against the paper bill).
    assert _bill_no("Supplier's Ref. Delivery Note M41702 Invoice No. Tax Invoice") == "M41702"


def test_real_code_shaped_invoice_numbers_still_extract():
    assert _bill_no("Bill No 50A86803") == "50A86803"
    assert _bill_no("Invoice # SI-3-0000033820") == "SI-3-0000033820"
    assert _bill_no("TRN100362941500003 CASH/CREDIT TAX INVOICE No. 22860") == "22860"


# --- Arabic coverage for the logic added in this session --------------------------------------------

def test_arabic_labels_and_arabic_indic_digits_give_the_same_totals_as_english():
    ar = _fields("المجموع قبل الضريبة ٣٣٠٫٠٠\nضريبة القيمة المضافة ٥٪ ١٦٫٥٠\nالاجمالي ٣٤٦٫٥٠")
    assert ar == (330.0, 16.5, 346.5)


def test_arabic_stacked_totals_block_with_dropped_decimals_is_derived():
    assert _fields("المجموع 330\nضريبة القيمة المضافة 5% 16 50\nالاجمالي 396 50") == (330.0, 16.5, 346.5)


def test_a_hijri_year_is_not_treated_as_a_misread_year():
    from datetime import date
    # 1447 AH is a real printed year on Saudi bills; the plausible-year check must leave it alone.
    result = _result("الاجمالي 46.00\nالتاريخ 03/07/1447")
    assert result.fields["date"].value == "03/07/1447"
    assert result.fields["date"].confidence >= 0.6


def test_arabic_unit_words_give_the_real_quantity_not_the_rate():
    from extraction.line_items import extract_line_items
    from extraction.normalize import lines_from_text
    text = "الكمية الوصف السعر الاجمالي\n2 قطعة قلم 5.00 10.00\n3 قطعة دفتر 4.00 12.00\nالمجموع 22.00"
    items = [i.to_dict() for i in extract_line_items(lines_from_text(text), ReferenceData())]
    assert [(i["quantity"], i["amount"]) for i in items] == [(2.0, 10.0), (3.0, 12.0)]
