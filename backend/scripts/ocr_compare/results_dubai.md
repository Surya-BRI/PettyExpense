# PaddleOCR results — dubai

Engine: PaddleOCR only (`lang=en` then `lang=ar`).
Summary reflects the merged (production) result — see `ocr_service.merge_bilingual`:
each language pass is parsed separately and merged field-by-field, matching what
`ocr_service._paddle_ocr` actually does for real uploads. The per-image sections below
still show each language pass on its own for debugging, plus the merged result.
Images: `7`.

## Summary

| Image | Vendor (merged) | Amount (merged) | VAT (merged) | Total (merged) | Date (merged) | Currency (merged) |
|---|---|---|---|---|---|---|
| enoc_test.jpg | ENOC RETAIL | 6.0 | 0.29 | 6.0 | 8/18/2026 | AED |
| image (1).png | BlueR in |  |  |  | 03-Aug-2026 |  |
| image (2).png | TUFFCO BUILDING MATERIALS TRADING L.L.G TRADING L.L.C | 20.0 | 1383.0 | 21.0 |  |  |
| image (3).png | OAMAR AL MADINA | 46.84 | 2.34 | 49.18 |  |  |
| image (4).png | M.S | 0.0 | 45.21 | 45.21 | 05-Aug-202 |  |
| image (5).png | amar Alhuda حارة العامةذمم | 45.0 | 2.25 | 47.25 |  |  |
| image (6).png | Slue Rhme | 1.0 | 2.48 | 52.0 | 04/08/2026 |  |

## enoc_test.jpg

### Merged (production)

**Parsed fields:** `{'vendor': 'ENOC RETAIL', 'expense_type': None, 'amount': 6.0, 'vat_amount': 0.29, 'total_amount': 6.0, 'currency': 'AED', 'date': '8/18/2026', 'confidence': 0.38, 'field_confidence': {'vendor': 0.24002333481155302, 'date': 0.2980496676041813, 'currency': 0.34114483732974665, 'amount': 0.67856630020137, 'vat_rate': 0.6456169843673706, 'vat_amount': 0.6745000050010368, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.9709393477117693, 'card_amount': 0.0, 'change': 0.9762751848886372, 'total_amount': 0.8385976517885118, 'invoice_number': 0.0, 'transaction_number': 0.3858145367109638, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'discount', 'service_charge', 'tip', 'card_amount', 'invoice_number', 'expense_category'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'ENOC RETAIL', 'confidence': 0.24002333481155302, 'evidence': 'ENOC RETAIL', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '8/18/2026', 'confidence': 0.2980496676041813, 'evidence': '8/18/2026 Shift:1', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'AED', 'confidence': 0.34114483732974665, 'evidence': 'AED6.00 L AED6.00 S', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'amount': {'value': 6.0, 'confidence': 0.67856630020137, 'evidence': 'AED6.00', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.6456169843673706, 'evidence': 'S 5', 'signals': ['vat_tax_rate_label', 'known_vat_rate', 'format_known_vat_rate'], 'low': False}, 'vat_amount': {'value': 0.29, 'confidence': 0.6745000050010368, 'evidence': 'AED0.29', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 10.0, 'confidence': 0.9709393477117693, 'evidence': 'AED10.00', 'signals': ['cash_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'tendered_change_total_arithmetic'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': 4.0, 'confidence': 0.9762751848886372, 'evidence': 'AED4.00', 'signals': ['change_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'tendered_change_total_arithmetic'], 'low': False}, 'total_amount': {'value': 6.0, 'confidence': 0.8385976517885118, 'evidence': 'AED6.00', 'signals': ['total_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch', 'tendered_change_total_arithmetic'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': '584439', 'confidence': 0.3858145367109638, 'evidence': 'POS: 2 2 CSR:Babbry, Wahid TRAN Wahid TRAN 584439', 'signals': ['transaction_number_label', 'fuzzy_label_match', 'position_prior_upper'], 'low': False}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'NOC RETAIL', 'expense_type': None, 'amount': 6.0, 'vat_amount': 0.29, 'total_amount': 6.0, 'currency': 'AED', 'date': '8/18/2026', 'confidence': 0.38, 'field_confidence': {'vendor': 0.2635080797423727, 'date': 0.2980496676041813, 'currency': 0.3504688925724692, 'amount': 0.6796563769736574, 'vat_rate': 0.6456169843673706, 'vat_amount': 0.6796811556152165, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.9709393477117693, 'card_amount': 0.0, 'change': 0.9762751848886372, 'total_amount': 0.8385976517885118, 'invoice_number': 0.0, 'transaction_number': 0.3858145367109638, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'discount', 'service_charge', 'tip', 'card_amount', 'invoice_number', 'expense_category'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'NOC RETAIL', 'confidence': 0.2635080797423727, 'evidence': 'NOC RETAIL', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '8/18/2026', 'confidence': 0.2980496676041813, 'evidence': '8/18/2026 Shift:1', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'AED', 'confidence': 0.3504688925724692, 'evidence': 'AED6.00', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'amount': {'value': 6.0, 'confidence': 0.6796563769736574, 'evidence': 'AED6.00', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.6456169843673706, 'evidence': 'S 5', 'signals': ['vat_tax_rate_label', 'known_vat_rate', 'format_known_vat_rate'], 'low': False}, 'vat_amount': {'value': 0.29, 'confidence': 0.6796811556152165, 'evidence': 'AED0.29', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 10.0, 'confidence': 0.9709393477117693, 'evidence': 'AED10.00', 'signals': ['cash_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'tendered_change_total_arithmetic'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': 4.0, 'confidence': 0.9762751848886372, 'evidence': 'AED4.00', 'signals': ['change_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'tendered_change_total_arithmetic'], 'low': False}, 'total_amount': {'value': 6.0, 'confidence': 0.8385976517885118, 'evidence': 'AED6.00', 'signals': ['total_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch', 'tendered_change_total_arithmetic'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': '584439', 'confidence': 0.3858145367109638, 'evidence': 'POS: 2 CSR:Babbry, Wahid TRAN 584439', 'signals': ['transaction_number_label', 'fuzzy_label_match', 'position_prior_upper'], 'low': False}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
MTO
öJ
NOC
RETAIL
P.0. Box -5589
Dubai, U.A.E
Site number:1635
Welcome to ZOOM
Description
UnitPrc
Qty
Amount V
ICE BAG
AED6.00
AED6.00 S
TOTAL AED
AED6.00
Total savings:
AED0.00
Cash AED:
AED10.00
AED10.00
Change AED
AED4.00
VAT %
Sale Amt
VAT Amt
S 5
AED6.00
AEDO.29
VAT Reg Number: 100221692500003
8/18/2026
Shift:1
04:52:23
POS: 2
CSR:Babbry, Wahid TRAN:
584439
VAT Description
S:Standard
Z:Zero
E:Tax Exempt
Keep Bill for exchange within 7 Days
Vaild only at Issued Store. T&C Apply
THANK YOU
HAVE A NICE DAY
Customer care: 800-ENOC (3662)
Customer care: 8U0-ENUC (3662)
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'ENOC RETAIL', 'expense_type': None, 'amount': 6.0, 'vat_amount': 0.29, 'total_amount': 6.29, 'currency': 'AED', 'date': '8/18/2026', 'confidence': 0.34, 'field_confidence': {'vendor': 0.23937090973734393, 'date': 0.29791137424214925, 'currency': 0.3266329676948459, 'amount': 0.7983132943545529, 'vat_rate': 0.6240165024995803, 'vat_amount': 0.7935294176482786, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8184283344902127, 'card_amount': 0.0, 'change': 0.8259970845172764, 'total_amount': 0.4, 'invoice_number': 0.0, 'transaction_number': 0.37824120266096933, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'discount', 'service_charge', 'tip', 'card_amount', 'total_amount', 'invoice_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'ENOC RETAIL', 'confidence': 0.23937090973734393, 'evidence': 'ENOC RETAIL', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '8/18/2026', 'confidence': 0.29791137424214925, 'evidence': '8/18/2026 Shift:1', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'AED', 'confidence': 0.3266329676948459, 'evidence': 'AED10.00', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'amount': {'value': 6.0, 'confidence': 0.7983132943545529, 'evidence': 'AED6.00', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.6240165024995803, 'evidence': 'S 5', 'signals': ['vat_tax_rate_label', 'known_vat_rate', 'format_known_vat_rate'], 'low': False}, 'vat_amount': {'value': 0.29, 'confidence': 0.7935294176482786, 'evidence': 'AED0.29', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 10.0, 'confidence': 0.8184283344902127, 'evidence': 'AED10.00', 'signals': ['cash_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': 4.0, 'confidence': 0.8259970845172764, 'evidence': 'AED4.00', 'signals': ['change_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'total_amount': {'value': 6.29, 'confidence': 0.4, 'evidence': 'derived: AED6.00', 'signals': ['derived_arithmetic'], 'low': True, 'warning': 'derived_value'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': '584439', 'confidence': 0.37824120266096933, 'evidence': 'POS 2 CSR: Babbry, Wahid TRAN 584439', 'signals': ['transaction_number_label', 'fuzzy_label_match', 'position_prior_upper'], 'low': False}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** S O09OES (0.46), كيردـ (0.41), HAIOL (0.35), AEA (0.31), 00 'NCEN (0.45)

**Raw text:**

```
فريبية
فاتورة
TBK
Inyo
ENOC
RETAIL
P.0.
Box - 5589
Dubai,
, U.A.E
Site number: 1635
Welcome to Zoom
Description
UnitPrc
Qty
Amount v
ICE BAG
AED6. 00
L
S O09OES
كيردـ
HAIOL
AEA
00 'NCEN
Total savings:
AEDO. 00
Cash AED:
AED10. 00
AED10. 00
Change AED
AED4.00
VAT %
Sale Amt
VAT Amt
S 5
AED6. 00
AEDO. 29
VAT Reg Number :
100221692500003
8/18/2026
Shift:1
04:52:23
POS:
2
CSR: Babbry,
Wahid TRAN:
584439
VAT Description
S:Standard
Z:Zero
E:Tax
Exempt
Keep Bill
for
exchange within 7 Days
Vaild only
at
Issued Store.
T&C Apply
THANK
YOU
HAVE
A
NICE DAY
Customer
care:
800-EN0C (3662)
Customer care: 8U0-ENUc (3662)
```

## image (1).png

### Merged (production)

**Parsed fields:** `{'vendor': 'BlueR in', 'expense_type': None, 'amount': None, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '03-Aug-2026', 'confidence': 0.08, 'field_confidence': {'vendor': 0.27222532767408036, 'date': 0.2946634314901688, 'currency': 0.0, 'amount': 0.0, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.7854301416453193, 'total_amount': 0.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'BlueR in', 'confidence': 0.27222532767408036, 'evidence': 'BlueR in', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '03-Aug-2026', 'confidence': 0.2946634314901688, 'evidence': 'ate :03-Aug-2026 17:40 Bi11 No :236191 User ID :ARSHIN', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': 11.0, 'confidence': 0.7854301416453193, 'evidence': 'pnp bi11for exchange. 29', 'signals': ['change_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'total_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'BlueR in', 'expense_type': None, 'amount': None, 'vat_amount': 412.0, 'total_amount': None, 'currency': None, 'date': '03-Aug-2026', 'confidence': 0.13, 'field_confidence': {'vendor': 0.27222532767408036, 'date': 0.30824828558108386, 'currency': 0.0, 'amount': 0.0, 'vat_rate': 0.0, 'vat_amount': 0.7187708450555801, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.790006651836283, 'total_amount': 0.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'BlueR in', 'confidence': 0.27222532767408036, 'evidence': 'BlueR in', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '03-Aug-2026', 'confidence': 0.30824828558108386, 'evidence': 'ate :03-Aug-2026 17:40 Bi11 No :236191', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 412.0, 'confidence': 0.7187708450555801, 'evidence': '0: 412', 'signals': ['vat_tax_amount_label', 'same_row', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': 11.0, 'confidence': 0.790006651836283, 'evidence': 'p bi11 for exchange. 29', 'signals': ['change_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'total_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
BlueR in
050759.4165
FIDAALMADINA
HYPERMARKET LLC
DIP Phase 2 - Dubal, UAE
Tel:04-8851961
t :0-fu9-202% 17:40
111 Nc:236191
Tax Lcanee Namber : 1051005
FIS Haw: P058
 0: 412
180000
ate
:03-Aug-2026 17:40
Bi11 No :236191
OS Name: POS8
User ID : ARSHINA
1.No DesorIption
Qty
Amount
CHCUMER
9N18780003 1 a 4.49
2.17
9.13
COPROT CHIRA
2.10
11.99
29801543008010
6.00
BIRNMH PHILIPINE 163
0.00
6.99
95062470000019
7.55
SHIPPING BAG
1.00
0.25
1000000
18 1.25
B111 Aaount: 29.00
Total Qty: 6.05
mank you visit again
29
p bi11 for exchange.
Cash Refund
chenge of Undergareent: not al lowed due to hyg
nic reasons
Hold Ivmined 236191
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'FIDAALMADINA', 'expense_type': None, 'amount': None, 'vat_amount': None, 'total_amount': None, 'currency': 'SAR', 'date': '', 'confidence': 0.08, 'field_confidence': {'vendor': 0.22415970018330744, 'date': 0.0, 'currency': 0.2811333854899687, 'amount': 0.0, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.7856066122335545, 'total_amount': 0.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'FIDAALMADINA', 'confidence': 0.22415970018330744, 'evidence': 'FIDAALMADINA', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': 'SAR', 'confidence': 0.2811333854899687, 'evidence': 'sar :412', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': 11.0, 'confidence': 0.7856066122335545, 'evidence': 'pnp bi11for exchange. 29', 'signals': ['change_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'total_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** n1 (0.40)

**Raw text:**

```
5075
1.t665
FIDAALMADINA
HYPERMARKET LLC
DIP Phase 2 - Dubal, UAE
Tl: 048851961
n1
611 ١c:26191
;00-4e2-22X 17:40
F9S TN: POIS8
sar :412
Eax L Scoesee Ealer : 18051085
1 80809
ute
:03-Aeg-202617:40
User ID :ARSHIN
BI11 No :236191
0S Name: POER
1 .No Descript ion
Qty
Amcunt
CKCEREER
2.17
9.1
FO8O1TR 1 8
CAPBOT CHEA
4.29
2.0
11.99
VARNDD PHELIFINE 163
18015400800 1 9
6.00
0.60
9590247000 1 9
E.99
SHIPIHG BAe
7.55
1.00
0.25
HICBIOO
11
4.25
Total Qty: 6.05
wank yau vislt again
B111
Aaount: 29.00
pnp bi11for exchange.
29
Cash Refuand.
schange of Undergareents not al Iceed dae to hye
nic reasons
Hald Jnnices 236191
```

## image (2).png

### Merged (production)

**Parsed fields:** `{'vendor': 'TUFFCO BUILDING MATERIALS TRADING L.L.G TRADING L.L.C', 'expense_type': None, 'amount': 20.0, 'vat_amount': 1383.0, 'total_amount': 21.0, 'currency': None, 'date': '', 'confidence': 0.18, 'field_confidence': {'vendor': 0.27067635027443193, 'date': 0.0, 'currency': 0.1641695196564133, 'amount': 0.4542658520519818, 'vat_rate': 0.6499797314405441, 'vat_amount': 0.5829839285333583, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.6826320544377837, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'TUFFCO BUILDING MATERIALS TRADING L.L.G TRADING L.L.C', 'confidence': 0.27067635027443193, 'evidence': 'TUFFCO BUILDING MATERIALS TRADING L.L.G TRADING L.L.C', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.1641695196564133, 'evidence': 'AED', 'signals': ['currency_code_match', 'position_prior_upper'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'amount': {'value': 20.0, 'confidence': 0.4542658520519818, 'evidence': 'Shuttaff 20 20 1 21', 'signals': ['subtotal_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': 5.0, 'confidence': 0.6499797314405441, 'evidence': 'VAT 5%', 'signals': ['vat_tax_rate_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_amount': {'value': 1383.0, 'confidence': 0.5829839285333583, 'evidence': 'N0. 1383 TAXINVOICE Date YAuy26', 'signals': ['vat_tax_amount_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'ambiguous_candidates'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 21.0, 'confidence': 0.6826320544377837, 'evidence': 'Amount Total 21', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'reconciliation_mismatch'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'TUFFCO BUILDING MATERIALS TRADING L.L.C', 'expense_type': None, 'amount': 20.0, 'vat_amount': 1383.0, 'total_amount': 21.0, 'currency': None, 'date': '', 'confidence': 0.18, 'field_confidence': {'vendor': 0.29170123326640596, 'date': 0.0, 'currency': 0.16618751482122895, 'amount': 0.4551581339939481, 'vat_rate': 0.6499797314405441, 'vat_amount': 0.5835086306769379, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.6844310332157708, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'TUFFCO BUILDING MATERIALS TRADING L.L.C', 'confidence': 0.29170123326640596, 'evidence': 'TUFFCO BUILDING MATERIALS TRADING L.L.C', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.16618751482122895, 'evidence': 'Total AED', 'signals': ['currency_code_match', 'position_prior_upper'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'amount': {'value': 20.0, 'confidence': 0.4551581339939481, 'evidence': 'Shuttaff 20 20 1 21', 'signals': ['subtotal_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': 5.0, 'confidence': 0.6499797314405441, 'evidence': 'VAT 5%', 'signals': ['vat_tax_rate_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_amount': {'value': 1383.0, 'confidence': 0.5835086306769379, 'evidence': 'N0. 1383 TAXINVOICE Date YAuy26', 'signals': ['vat_tax_amount_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'ambiguous_candidates'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 21.0, 'confidence': 0.6844310332157708, 'evidence': 'Amount Total 21', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'reconciliation_mismatch'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
TUFFCO BUILDING MATERIALS
TRADING L.L.C
DEALERS IN BUILDING MATERIALS
Mob: +971 55 889 9852,Shop no-7, Farhad Building,
Umm Al Thuoob, Umm AI Quwain
E-mail : buildmtr@gmail.com
TR:10525230500
No. 1383 TAXINVOICE
Date YAuy26
Mr.Ms Blue Rbybe
Cust. TRN
Description
21051
Amount
VAT 5%
Amount
Qty.
Rate
(Excl.Vat)
Shuttaff
(Incl.Vat)
20
20
1
21
Amount
20
VAT 5%
Total AED
Total
Amount
21
AED
Signature
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'TUFFCO BUILDING MATERIALS TRADING L.L.G', 'expense_type': None, 'amount': 1.0, 'vat_amount': 20.0, 'total_amount': 21.0, 'currency': None, 'date': '', 'confidence': 0.18, 'field_confidence': {'vendor': 0.27067635027443193, 'date': 0.0, 'currency': 0.1628026914800044, 'amount': 0.4, 'vat_rate': 0.6494691371917725, 'vat_amount': 0.5737478596601598, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.7696110489705887, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'TUFFCO BUILDING MATERIALS TRADING L.L.G', 'confidence': 0.27067635027443193, 'evidence': 'TUFFCO BUILDING MATERIALS TRADING L.L.G', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.1628026914800044, 'evidence': 'Total AED.', 'signals': ['currency_code_match', 'position_prior_upper'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'amount': {'value': 1.0, 'confidence': 0.4, 'evidence': 'derived: Amount Total 21', 'signals': ['derived_arithmetic'], 'low': True, 'warning': 'derived_value'}, 'vat_rate': {'value': 5.0, 'confidence': 0.6494691371917725, 'evidence': 'VAT 5%', 'signals': ['vat_tax_rate_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_amount': {'value': 20.0, 'confidence': 0.5737478596601598, 'evidence': 'Shuttayy 20 20 2/', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': True, 'warning': 'ambiguous_candidates'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 21.0, 'confidence': 0.7696110489705887, 'evidence': 'Amount Total 21', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** سجازف 90اد (0.49), | (0.18)

**Raw text:**

```
سجازف 90اد
توفك9
TUFFCO BUILDING MATERIALS TRADING L.L.G
DEALERS IN BUILDING MATERIALS
Mob: +971 55 889 9852,Shop no-7, Farhad Building,
Umm AI Thuoob, Umm AI Quwain
E-mail : buildmtr@gmail.com
فاتورة الضرييية
TRN:10525230S5060
o. 1 38 3 TANICE
Date.Auyالتاريط
wr.ms.BlueRbyhe
السيدالسادة
Cust. TRN
التفاصيل اpن
الكمية
Qty.
السعر
Amounالمبلغ ا
VAT 5%
Amount المبلغ
Rate
Exl.Vat)
ll.Va)
Shuttayy
20
20
|
2/
Amount
20
VAT 5%
Total AED.
Total
Amount
21
AED
Signature
النو فيع
```

## image (3).png

### Merged (production)

**Parsed fields:** `{'vendor': 'OAMAR AL MADINA', 'expense_type': None, 'amount': 46.84, 'vat_amount': 2.34, 'total_amount': 49.18, 'currency': None, 'date': '', 'confidence': 0.31, 'field_confidence': {'vendor': 0.284427407654849, 'date': 0.0, 'currency': 0.0, 'amount': 1.0, 'vat_rate': 0.7818251550197601, 'vat_amount': 1.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8607880633587788, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'OAMAR AL MADINA', 'confidence': 0.284427407654849, 'evidence': 'OAMAR AL MADINA', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 46.84, 'confidence': 1.0, 'evidence': '5% 46.84 2.34 49.18', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'near_percent_marker', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.7818251550197601, 'evidence': '5% 46.84 2.34 49.18', 'signals': ['vat_tax_amount_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 2.34, 'confidence': 1.0, 'evidence': '5% 46.84 2.34 49.18', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 49.25, 'confidence': 0.8607880633587788, 'evidence': 'CASH 49.25', 'signals': ['cash_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 49.18, 'confidence': 1.0, 'evidence': '5% 46.84 2.34 49.18', 'signals': ['total_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'OAMAR AL MADINA', 'expense_type': None, 'amount': 46.84, 'vat_amount': 2.24, 'total_amount': 49.18, 'currency': None, 'date': '', 'confidence': 0.31, 'field_confidence': {'vendor': 0.2878962081189107, 'date': 0.0, 'currency': 0.0, 'amount': 0.9756663399152081, 'vat_rate': 0.7991089075803757, 'vat_amount': 0.9894453041120009, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8649621617312382, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.9894453041120009, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'OAMAR AL MADINA', 'confidence': 0.2878962081189107, 'evidence': 'OAMAR AL MADINA', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 46.84, 'confidence': 0.9756663399152081, 'evidence': '46.84', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.7991089075803757, 'evidence': '5%', 'signals': ['vat_tax_amount_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 2.24, 'confidence': 0.9894453041120009, 'evidence': '2.24 49.18', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_inclusive'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 49.25, 'confidence': 0.8649621617312382, 'evidence': 'CASH 49.25', 'signals': ['cash_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 49.18, 'confidence': 0.9894453041120009, 'evidence': '2.24 49.18', 'signals': ['total_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_inclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** hea zu for shopving an pts core aanto (0.46)

**Raw text:**

```
OAMAR AL MADINA
SUPERMARKETL.L.C
Nw ( yu Uma Al (Ju
0585405699
TAX INVDICE
RN: 104645729500013
21:29 3a1-2026 09.4
3:11 No:104
Pús Neve:
PI57
Uter 10: 99
Dascription
Qty
Amount
9963950000000
CURIANDER LEAF
2.00
1.98
9988002000000
ONION (INDTA)
1.06
3.70
6291044111119
SAFA YOGHURT 10KG
1.00
38.00
9968016000000
GINGER (PRC)
0.53
4.50
9989948000000
CURRY LEAF
1.00
1.00
DAQ-5000-BLUE RINE
Qly: 5.59
Rouncing:
0.07
B111
Amount:
49.25
49.2
CASH:
49.25
Ampunt tu return :
0.00
VATX
Taxable Amount
VAI
Total
5%
46.84
2.24 49.18
Fuap bill fur c(hange.
hea zu for shopving an pts core aanto
ino Lasn hafund
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'OAMAR AL MADINA', 'expense_type': None, 'amount': 2.34, 'vat_amount': None, 'total_amount': 2.34, 'currency': None, 'date': '', 'confidence': 0.18, 'field_confidence': {'vendor': 0.284427407654849, 'date': 0.0, 'currency': 0.0, 'amount': 0.7902979156224414, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8607880633587788, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.9402979156224415, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'OAMAR AL MADINA', 'confidence': 0.284427407654849, 'evidence': 'OAMAR AL MADINA', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 2.34, 'confidence': 0.7902979156224414, 'evidence': '5X 4t.84 2.34 49.18', 'signals': ['subtotal_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 49.25, 'confidence': 0.8607880633587788, 'evidence': 'CASH 49.25', 'signals': ['cash_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 2.34, 'confidence': 0.9402979156224415, 'evidence': '5X 4t.84 2.34 49.18', 'signals': ['total_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
OAMAR AL MADINA
GUPERMARKETL.L.C
Nrw Hy  A
( 0585405699
TaX InVdICE
RN: 104645729500013
s0le :29 41-2026 69.4t
31٦1 N0:104
PU'S Neve: PHa
Uter i0: 99
Description
Qty
Amount
3363950060000
CURJANDER LEAF
2.00
1.98
9e83002000000
ONION (INDTA)
1.06
3.70
6291044111119
SAFA YOGHURT 10KG
1.00
38.00
9958016000000
GINGER (PRC)
0.53
4.50
9989943000006
CURRY LEAF
1.00
1.00
LAQ- 5000-BLUE RINE
Qly: 5.59
Rouncing:
0.07
B1l1 Amount:
49.25
49.2
CASH :
49.25
Aedunt to reten :
0.00
JATX
Taxabie Amcunt
yaI
Total
5X
4t.84
2.34 49.18
renp bill tar c>change
hnd nid for shooity on pls cure dante
ing Lasn hefund
```

## image (4).png

### Merged (production)

**Parsed fields:** `{'vendor': 'M.S', 'expense_type': None, 'amount': 0.0, 'vat_amount': 45.21, 'total_amount': 45.21, 'currency': None, 'date': '05-Aug-202', 'confidence': 0.22, 'field_confidence': {'vendor': 0.29549382047228406, 'date': 0.34334922861995515, 'currency': 0.0, 'amount': 0.4, 'vat_rate': 0.0, 'vat_amount': 0.8338705804700071, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8580885103579317, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.8338705804700071, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'M.S', 'confidence': 0.29549382047228406, 'evidence': 'M.S', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '05-Aug-202', 'confidence': 0.34334922861995515, 'evidence': 'Dete :05-Aug-202% 10:59', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 0.0, 'confidence': 0.4, 'evidence': 'derived: 45.21 2.28 47.49', 'signals': ['derived_arithmetic'], 'low': True, 'warning': 'derived_value'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 45.21, 'confidence': 0.8338705804700071, 'evidence': '45.21 2.28 47.49', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 6.0, 'confidence': 0.8580885103579317, 'evidence': 'Amount to return 6.00 47.5', 'signals': ['cash_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 45.21, 'confidence': 0.8338705804700071, 'evidence': '45.21 2.28 47.49', 'signals': ['total_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'M.S', 'expense_type': None, 'amount': 45.21, 'vat_amount': 2.28, 'total_amount': 47.49, 'currency': None, 'date': '05-Aug-202', 'confidence': 0.35, 'field_confidence': {'vendor': 0.29549382047228406, 'date': 0.69148897486552, 'currency': 0.0, 'amount': 1.0, 'vat_rate': 0.7989461243152618, 'vat_amount': 1.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8580885103579317, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'M.S', 'confidence': 0.29549382047228406, 'evidence': 'M.S', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '05-Aug-202', 'confidence': 0.69148897486552, 'evidence': 'Date :05-Aug-202% 10:59', 'signals': ['date_format_match', 'date_label', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 45.21, 'confidence': 1.0, 'evidence': '45.21 2.28 47.49', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.7989461243152618, 'evidence': '5', 'signals': ['vat_tax_amount_label', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 2.28, 'confidence': 1.0, 'evidence': '45.21 2.28 47.49', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 47.5, 'confidence': 0.8580885103579317, 'evidence': 'Amount to return 0.00 47.5', 'signals': ['cash_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 47.49, 'confidence': 1.0, 'evidence': '45.21 2.28 47.49', 'signals': ['total_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
M.S
OAMAR AL MADINA
SUPERMARKETLL.
New Banuyya Uzmo AI Quwuin-1A
0585405699
TAX INVOICE
RN: 104645729500003
Date
0111 No: 152
:05-Aug-202% 10:59
U1e1 T0: 99
POS Nene: P052
Description
Qty
Anount
9988948000000
CURRY LEAF
1.00
1.00
9988949000000
MINT LEAF
2.00
2.00
9968002000000
ONION (INDIA)
1.00
3.49
9988893000000
CHILLY SMALL
0.16
2.0
9988950000000
CORTANDER LEA
1.00
0.99
6291044111:19
SAFA VOGHURI 10KG
1.00
38.00
UAQ-500D-BLUE RINE
Qty: 6.16
Rouncing:
0.01
B111
Anount:
47.50
CASH;
47.50
47.5
Amount to return :
0.00
VAT
Taxable Amount
VAT
Total
5
45.21
2.28 47.49
NEer DiTi r eange
henk ylu for crarutus and sis core égeir
No Lasn r cnd
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'M.S', 'expense_type': None, 'amount': None, 'vat_amount': 45.21, 'total_amount': None, 'currency': None, 'date': '', 'confidence': 0.07, 'field_confidence': {'vendor': 0.27882716464519497, 'date': 0.0, 'currency': 0.0, 'amount': 0.0, 'vat_rate': 0.0, 'vat_amount': 0.8334371936321259, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'M.S', 'confidence': 0.27882716464519497, 'evidence': 'M.S', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 45.21, 'confidence': 0.8334371936321259, 'evidence': '45.21 2.28 47.49', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
M.S
OAMAR AL MADINA
SUPERMARKETLL.C
New Hanyya Uguo Al Quwin-UAE
L
0585405699
TAX TNVOICE
RN: 104645729500003
Dete
fil1 Mo:1%2
:05-f0n-202% 10:59
User 10: 9
POS Hene: PUS2
Bascript lon
Qty
Anont
9998943000000
CIHRRY L EAF
1.0)
1.00
9988949090000
MINT LEAF
2.0)
2.00
9965002000D60
ONJON (INDLA)
1.00
3.49
998889 3000000
CHILLY SMAL
0.16
2.111
996950000000
COREANDER IEAI
1.00
0.99)
0291044111:19
SAFA VOGKURT TUKG
1.0)
38.00
UA0 - 5000-BLUE RINE
Qty: 6.16
Rouncing:
0.01
B111 Anount:
47.50
CAS1
4/.50
47.5
Anount to return :
6.00
VATN
TaxableAmcun't
VAT
T:ta
51
45.21
2.28 47.49
*EET D T1 "Or NLsaNge
Thenk you for grutoy ao2 pis core Rga1
No Leun -ctod
```

## image (5).png

### Merged (production)

**Parsed fields:** `{'vendor': 'amar Alhuda حارة العامةذمم', 'expense_type': None, 'amount': 45.0, 'vat_amount': 2.25, 'total_amount': 47.25, 'currency': None, 'date': '', 'confidence': 0.26, 'field_confidence': {'vendor': 0.2749283127101934, 'date': 0.0, 'currency': 0.0, 'amount': 1.0, 'vat_rate': 0.9333542823791504, 'vat_amount': 1.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'amar Alhuda حارة العامةذمم', 'confidence': 0.2749283127101934, 'evidence': 'amar Alhuda حارة العامةذمم', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 45.0, 'confidence': 1.0, 'evidence': '1.00 PCS 45.00 45.00 5% 2.25 47.25', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.9333542823791504, 'evidence': '1.00 PCS 45.00 45.00 5% 2.25 47.25', 'signals': ['vat_tax_amount_label', 'vat_tax_rate_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 2.25, 'confidence': 1.0, 'evidence': '1.00 PCS 45.00 45.00 5% 2.25 47.25', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'near_percent_marker', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 47.25, 'confidence': 1.0, 'evidence': '1.00 PCS 45.00 45.00 5% 2.25 47.25', 'signals': ['total_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'amar Alhuda', 'expense_type': None, 'amount': 45.0, 'vat_amount': 2.25, 'total_amount': 47.25, 'currency': None, 'date': '', 'confidence': 0.26, 'field_confidence': {'vendor': 0.29332553069916134, 'date': 0.0, 'currency': 0.0, 'amount': 1.0, 'vat_rate': 0.9333542823791504, 'vat_amount': 1.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'amar Alhuda', 'confidence': 0.29332553069916134, 'evidence': 'amar Alhuda', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 45.0, 'confidence': 1.0, 'evidence': '1.00 PCS 45.00 45.00 5% 2.25 47.25', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.9333542823791504, 'evidence': '1.00 PCS 45.00 45.00 5% 2.25 47.25', 'signals': ['vat_tax_amount_label', 'vat_tax_rate_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 2.25, 'confidence': 1.0, 'evidence': '1.00 PCS 45.00 45.00 5% 2.25 47.25', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'near_percent_marker', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 47.25, 'confidence': 1.0, 'evidence': '1.00 PCS 45.00 45.00 5% 2.25 47.25', 'signals': ['total_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** 1 (0.14), dangi (0.44), d l   (0.49), Apa (0.42), A uat  (0.42), d uil da g (0.48), das uchll o ilas (0.47)

**Raw text:**

```
amar Alhuda
QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.U
: 0528194512
(JOTUN MULTI COLOUR CENTRE)
0528194629
We are DealingSanitary Wares, Plumbing.Electricals, Paints,Hardware, Plywood
qomoouda.k@gmoil.com
Worehouse No. 75,76, 77, Opp. AIKO Hypermarket, Dubai Inves
all kinds of Building Materials
100340280500003
ent Pork 1, Tel.: + 971 4 884 8200, + 971 4 889 5541
TAXINVOICE
Invoice No.
Date
LUE RHINE INDUSTRIES LLC
Delivery Note
Delivery Note Date
LOT NO 597673
BOX114001
Supplier's Ref.
Mode/Terma of Payment
e TN
Pv-SER-BR1/65
UBAL UAE
Buyer'a Order No.
Dated
100011246
1
dangi
1
d l
Apa
A uat
Amount Incl. VAT
Description
Quantity
Unit
Rate
Amount Excl VAT
VAT%
VAT Amount
UV RELAY US-UVR-3PHASC
1.00
PCS
45.00
45.00
5%
2.25
47.25
USPRO
e l
TOTAL EXCL VAT
UAE Dirhams Forty Seven and Twenty Five fis Only
d uil da g
TOTAL VAT
das uchll o ilas
225
TOTAL INCL VAT
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'amar Alhuda حارة العامةذمم', 'expense_type': None, 'amount': 0.0, 'vat_amount': 1.0, 'total_amount': 1.0, 'currency': 'USD', 'date': '', 'confidence': 0.14, 'field_confidence': {'vendor': 0.2749283127101934, 'date': 0.0, 'currency': 0.30434381441331243, 'amount': 0.4, 'vat_rate': 0.0, 'vat_amount': 0.7448842702980891, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.5948842702980892, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'amar Alhuda حارة العامةذمم', 'confidence': 0.2749283127101934, 'evidence': 'amar Alhuda حارة العامةذمم', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': 'USD', 'confidence': 0.30434381441331243, 'evidence': "BOX 114001 Pv- USD ER-BR1/65 Suppler's Ref.", 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 0.0, 'confidence': 0.4, 'evidence': 'derived: 1.00 PCS 45.00 45.00 54 2.25 47.25', 'signals': ['derived_arithmetic'], 'low': True, 'warning': 'derived_value'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 1.0, 'confidence': 0.7448842702980891, 'evidence': '1.00 PCS 45.00 45.00 54 2.25 47.25', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': True, 'warning': 'ambiguous_candidates'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 1.0, 'confidence': 0.5948842702980892, 'evidence': '1.00 PCS 45.00 45.00 54 2.25 47.25', 'signals': ['total_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** s (0.15)

**Raw text:**

```
amar Alhuda
حارة العامةذمم
QAMAR ALHUDA ALJADEED GENERAL TRADING LL.L
 0528194512
(JOTUN MULTI COLOUR CENTRE)
0528194629
iqomorahude.lc@gmoil.com
Werghoute No. 75,76, 77, Opp. AlKO Hyp
all kinds of Building Materials
100340280500003
rket, Duba
TEالفاتورة الضريبية
Invoice No.
Date
LUE RHINE INDUSTRIES LLC
Delivery Note
Delivery Nots Sate
BOX 114001
Suppler's Ref.
Mode/Terms of Payment
TRN
Pv-$ER-BR1/65
JBAL UAB
Buyer's Dnder Ne
Dated
الاي10001
Quantity
الكمية
الوحدة
السعر
مبلغسون الضرية
الضريية
مبلغ الضريية
Amount incl. VAT
مجل مع الضريية
Description
Unit
Rate
Amoust ExL. VIT
VAT%
VAT Amount
UV RELAY US-UVR-3PHASC
1.00
PCS
45.00
45.00
54
2.25
47.25
USPRO
s
AIW
TOTAL EXCL VAT
مبلغ دون الضرية
UAE Dirhams Forty Seven and Twenty Five fils Only
مجموعة الضريية
TOTAL VAT
TOTAL INCL VAT
مبلغمع الضريية
```

## image (6).png

### Merged (production)

**Parsed fields:** `{'vendor': 'Slue Rhme', 'expense_type': None, 'amount': 1.0, 'vat_amount': 2.48, 'total_amount': 52.0, 'currency': None, 'date': '04/08/2026', 'confidence': 0.29, 'field_confidence': {'vendor': 0.24191052004299332, 'date': 0.29496763217765676, 'currency': 0.0, 'amount': 0.9503392124017783, 'vat_rate': 0.9451915413141251, 'vat_amount': 0.4, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.817909536889169, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_amount', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Slue Rhme', 'confidence': 0.24191052004299332, 'evidence': 'Slue Rhme', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '04/08/2026', 'confidence': 0.29496763217765676, 'evidence': '04/08/2026 09:19 09', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': True, 'warning': 'ambiguous_candidates'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 1.0, 'confidence': 0.9503392124017783, 'evidence': 'الذوح الرغر الكبية 1 السجع', 'signals': ['subtotal_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.9451915413141251, 'evidence': '5 83.37 87.54 4.17', 'signals': ['vat_tax_rate_label', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 2.48, 'confidence': 0.4, 'evidence': 'derived: TOTAL AMOUNT 52.00 at 5.0%', 'signals': ['derived_arithmetic', 'derived_inclusive'], 'low': True, 'warning': 'derived_value'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 52.0, 'confidence': 0.817909536889169, 'evidence': 'Paid Amounl(MAS) 52 52.00', 'signals': ['tendered_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 52.0, 'confidence': 1.0, 'evidence': 'TOTAL AMOUNT 52.00', 'signals': ['total_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_inclusive', 'arithmetic_reconciled_exclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'BlueRhme', 'expense_type': None, 'amount': 49.52, 'vat_amount': 10.1, 'total_amount': 87.54, 'currency': None, 'date': '04/08/2026', 'confidence': 0.22, 'field_confidence': {'vendor': 0.255195600480105, 'date': 0.2957321511538683, 'currency': 0.0, 'amount': 0.6768432315134368, 'vat_rate': 0.0, 'vat_amount': 0.7066488301210698, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.826209099044842, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.7243133113967105, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'BlueRhme', 'confidence': 0.255195600480105, 'evidence': 'BlueRhme', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '04/08/2026', 'confidence': 0.2957321511538683, 'evidence': '04/08/2026 09:19 09', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': True, 'warning': 'ambiguous_candidates'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 49.52, 'confidence': 0.6768432315134368, 'evidence': '49.52 52.00 2.48', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 10.1, 'confidence': 0.7066488301210698, 'evidence': '9901129005055 0.505 KGS 10.10', 'signals': ['vat_tax_amount_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'ambiguous_candidates'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 52.0, 'confidence': 0.826209099044842, 'evidence': 'Paid Amounl(MAS) 52.00', 'signals': ['tendered_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 87.54, 'confidence': 0.7243133113967105, 'evidence': 'Paid Amount(MAS) 87.54', 'signals': ['total_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** 6 (0.19), GLE (0.48), y  & j g (0.40), AEN (0.45), 2 (0.31), 2s2 (0.32)

**Raw text:**

```
BlueRhme
BlueRhi
6
65-t8
PASONS
305
PASONS
Pasons S/M&Dept.Store
Dubai Investment Park-2, Dubai, U AE
GLE
Tel: 04-8640966 . Mob:0557692020
Pasons S/M&DepI Store
www.pasonsme.com
Dubal Investment Park-2, Dubai, U AE
TRN 100453349100003
Tel 04-0840968, Mob:0557692020
Tax Invoice
y  & j g
www.pasonsme.com
Srl. ltem
TRN 100453349100003
AEN
Qty
Unit
Amount
Tax Invoice
2  3  g
≤
1
2
Srl. Rem
8.000 PCS
Oty
Unil
Amount
6291031020837
Marmum Yoghurt 1Kg Full Cresm
52.00
A21 e213
2s2
1
t
2 9901125020304
6291031020837
8.600 PCS
52.00
2.030 KGS
13.20
Marmum Yoghiart 1Kg Full Cream
Carrot
TOTAL AMOUNT
52.00
3
87158069
1.000
PCS
4.00
Item Count 8
52
Nezo Salt 1Kg Pkt Blue
Paid Amounl(MAS)
52.00
9901129005055
0.505
KGS
10.10
Chili India
Tax Inclusive
9901140020855
8.24
VAT%
Excl VAT
Incl VAT
VAT
5
2.085
KGS
Cucumber
49.52
52.00
2.48
Served by:
SAFWAN CHANGOTH
TOTAL AMOUNT
87.54
Ilem Count 12
87-50
Date
Time
Stare
POS
Bill
87.54
04/08/2026
09:19
09
137
Paid Amount(MAS)
Tax Inclusive
Keep Recaipt For Exchange, T&C Apply
VAT%
Excd.VAT
Incl VAT
VAT
No Exchange On Under Garments
83.37
87.54
4.17
No Cash Refund,Thank You. Visit Again
Served by
SAFWAN CHANGOTH
Date
Time
05/08/2026
Store
POS
Bil
090120260804137
09:12
09
115
Keep Receipt For Exchange, T&C Apply
No Exchenge On Under Garments
No Cash Refund, Thank You, Visit Again
090120260805115
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'Slue Rhme', 'expense_type': None, 'amount': 1.0, 'vat_amount': 0.05, 'total_amount': 1.0, 'currency': None, 'date': '04/08/2026', 'confidence': 0.3, 'field_confidence': {'vendor': 0.2418820414137333, 'date': 0.2947882874214903, 'currency': 0.0, 'amount': 1.0, 'vat_rate': 1.0, 'vat_amount': 0.4, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.816697639100095, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_amount', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Slue Rhme', 'confidence': 0.2418820414137333, 'evidence': 'Slue Rhme', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '04/08/2026', 'confidence': 0.2947882874214903, 'evidence': '04/08/2026 09:19 09', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': True, 'warning': 'ambiguous_candidates'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 1.0, 'confidence': 1.0, 'evidence': 'Mamum Yoghurt 1Kg Full Cresm', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 1.0, 'evidence': '5 83.37 87.54 4.17', 'signals': ['vat_tax_rate_label', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 0.05, 'confidence': 0.4, 'evidence': 'derived: Mamum Yoghurt 1Kg Full Cresm at 5.0%', 'signals': ['derived_arithmetic', 'derived_inclusive'], 'low': True, 'warning': 'derived_value'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 4.0, 'confidence': 0.816697639100095, 'evidence': '3 87158069 1.000 PCS 4.00', 'signals': ['tendered_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 1.0, 'confidence': 1.0, 'evidence': 'Mamum Yoghurt 1Kg Full Cresm', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** T5ن (0.34), CHV (0.41), لسع (0.50), لح (0.42), g (0.41), BO (0.49)

**Raw text:**

```
Slue Rhme
BlueRhom
6sts
SNOSAd
T5ن
PASONS
CHV
Dubai Investment Park-2, Dubai , U AE
Pasons S/M&Dept, Slore
SLENC
Tet(4-0640966Mob:0557692020
PasonsS/M&Depl Slore
www.pesonsme.com
Dubal Imvnsmeat Park-2 OubaiU AE
TRN 100453349100003
Tel 04-8840966Mob 0557692020
Tax Invoice
نتورة ضرية
'anew pasansime.con
Sn.""bem
TRN 100453349100003
الذوح الرغر
Oity
Unit
Amount
Tax Invoice
نقورة ضرببية
1 6291031020837
الكبية
لسع
السجع
Sd." tem
'PCS
Olty
Unsl
Amounl
Mamum Yoghurt 1Kg Full Cresm
8.000
52.00
تنوع الرقم
الخبوة
لح
الجحع
2 9901125020304
6291031029837
a.000
PCS
52.00
2.030 KGS
13.20
Marmun Yoghart 1Kg Full Cream
Carrot
3 87158069
TOTAL AMOUNT
52.00
1.000 PCS
4.00
Nezo Sat 1Kg Pht Blue
Item Counl 8
5a
Paid Amounl(MAS)
52.00
9901129005055
0.505
KGS
10.10
Chilli India
Tax Inclusie
الشرية لديزة
2.085 KGS
8.24
VAT% Exdl VAT
IncIVAT
VAT
59901140020855
Cucumber
g
49.52
52.00
2.48
87.54
Served by
SAFWAN CHANGOTH
TOTAL AMOUNT
Ilem Count 12
Dete
Time
Slore
POS
BO
87.54
04/08/2026
09:19
09
137
Tax Inclusive
الضرية المئة
Keep Receipt For Exchange, T&C Apply
VAT% ExLVAT
IncIl VAT
VAT
No Exchenge On Under Garments
5
83.37
87.54
4.17
No Cash Refund Thank You, Visit Again
Served by
SAPWAN CHANGOTH
Date
Time
05/08/2026
Slore
POS
09:12
0
Bil
090120260804137
-
115
Keep Receipt For Exchange, T&C Apply
No Exchenge On Under Garments
No Cash Refund, Thank You, Visit Again
090120260805115
```
