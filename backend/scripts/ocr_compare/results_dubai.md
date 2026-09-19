# OCR results — dubai

Engine: single shared-detection RapidOCR pipeline (mode=`auto`) — one detection pass,
sequential English + Arabic recognition against the same detected regions.
Summary reflects the actual production result (`OcrService.run`). The per-image
sections below also show each recognizer's raw reading for debugging.
Images: `7`.

## Summary

| Image | Vendor | Amount | VAT | Total | Date | Currency | Mismatch |
|---|---|---|---|---|---|---|---|
| enoc_test.jpg | ENOC RETAIL | 6.0 | 0.29 | 6.0 | 8/18/2026 | AED | True |
| image (1).png | BlueR n |  | 0.0 |  | 03-Aug-2026 |  | False |
| image (2).png | TUFFCO BUILDING MATERIALS TRADING L.L.C DEALERS IN BUILDING MATERIALS | 20.0 | 1.0 | 21.0 |  | AED | False |
| image (3).png | OAMAR AL MADINA GUPERMARKETLL.C | 2.34 | 0.0 | 2.34 |  |  | False |
| image (4).png | M.S OAMAR AL MADINA | 45.21 | 45.21 | 90.42 |  |  | False |
| image (5).png | Mob: 0528194512 QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.L E-mail: qomorolhude.Il@gmoil.com | 45.0 | 2.25 | 47.25 |  |  | False |
| image (6).png | mnymg | 49.52 | 2.48 | 52.0 | 04/00/2026 | USD | False |

## enoc_test.jpg

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'ENOC RETAIL', 'expense_type': None, 'amount': 6.0, 'vat_amount': 0.29, 'total_amount': 6.0, 'currency': 'AED', 'date': '8/18/2026', 'confidence': 0.41, 'field_confidence': {'vendor': 0.2434736470234114, 'date': 0.30167890802675584, 'currency': 0.6993127725752508, 'amount': 0.7095395809364548, 'vat_rate': 0.6494179999999999, 'vat_amount': 0.7115219415551839, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.9678784414715719, 'card_amount': 0.0, 'change': 0.9740964933110368, 'total_amount': 0.8373696293478261, 'invoice_number': 0.0, 'transaction_number': 0.39469154180602006, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'vat_amount', 'discount', 'service_charge', 'tip', 'card_amount', 'invoice_number', 'expense_category'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'ENOC RETAIL', 'confidence': 0.2434736470234114, 'evidence': 'ENOC RETAIL', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '8/18/2026', 'confidence': 0.30167890802675584, 'evidence': '8/18/2026 Shift:1 04:52:23', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'AED', 'confidence': 0.6993127725752508, 'evidence': 'AED6.00 S', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'amount': {'value': 6.0, 'confidence': 0.7095395809364548, 'evidence': 'S5 AED6.00 VAT Amt', 'signals': ['subtotal_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.6494179999999999, 'evidence': 'S5 AED6.00 VAT Amt', 'signals': ['vat_tax_amount_label', 'known_vat_rate', 'format_known_vat_rate'], 'low': False}, 'vat_amount': {'value': 0.29, 'confidence': 0.7115219415551839, 'evidence': 'AED0.29', 'signals': ['vat_tax_amount_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'ambiguous_candidates'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 10.0, 'confidence': 0.9678784414715719, 'evidence': 'AED10.00 Cash AED AED10.00', 'signals': ['cash_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'tendered_change_total_arithmetic'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': 4.0, 'confidence': 0.9740964933110368, 'evidence': 'Change AED AED4.00', 'signals': ['change_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'tendered_change_total_arithmetic'], 'low': False}, 'total_amount': {'value': 6.0, 'confidence': 0.8373696293478261, 'evidence': 'TOTAL AED AED6.00', 'signals': ['total_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch', 'tendered_change_total_arithmetic'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': '584439', 'confidence': 0.39469154180602006, 'evidence': 'POS: 2 CSR:Babbry, Wahid TRAN 584439', 'signals': ['transaction_number_label', 'fuzzy_label_match', 'position_prior_upper'], 'low': False}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'فاتورة فريبية\nTax Invoice\nENOC RETAIL\nP.O. Box - 5589 LLC\nDubai, U.A.E\nSite number:1635\nWelcome to ZOOM\nDescription UnitPrc Qty\nAmount V\nICE BAG AED6.00\nで\nكيس ثلج\nAED6.00 S\nTOTAL AED AED6.00\nTotal savings\nAED0.00\nAED10.00 Cash AED AED10.00\nChange AED AED4.00\nVAT % Sale Amt\nS5 AED6.00 VAT Amt\nAED0.29\nVAT Reg Number: 100221692500003\n8/18/2026 Shift:1 04:52:23\nPOS: 2 CSR:Babbry, Wahid TRAN 584439\nVAT Description\nS:Standard Z:Zero E:Tax Exempt\nKeep Bill for exchange within 7 Days\nVaild only at Issued Store. T&C Apply\nTHANK YOU\nHAVE A NICE DAY\nCustomer care: 800-ENOC (3662)', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'Tax Invoice', 'confidence': 0.98213, 'lang': 'en', 'bounding_box': (436.0, 141.0, 698.0, 197.0)}, {'text': 'ENOC RETAIL', 'confidence': 0.99861, 'lang': 'en', 'bounding_box': (369.0, 172.0, 640.0, 234.0)}, {'text': 'P.0. Box - 5589', 'confidence': 0.9335, 'lang': 'en', 'bounding_box': (446.0, 208.0, 638.0, 260.0)}, {'text': 'LLC', 'confidence': 0.99864, 'lang': 'en', 'bounding_box': (649.0, 205.0, 730.0, 243.0)}, {'text': 'Dubai, U.A.E', 'confidence': 0.99211, 'lang': 'en', 'bounding_box': (470.0, 238.0, 624.0, 282.0)}, {'text': 'Site number:1635', 'confidence': 0.99921, 'lang': 'en', 'bounding_box': (296.0, 270.0, 502.0, 318.0)}, {'text': 'Welcome to ZOOM', 'confidence': 0.99402, 'lang': 'en', 'bounding_box': (346.0, 324.0, 732.0, 406.0)}, {'text': 'Description', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (282.0, 395.0, 431.0, 440.0)}, {'text': 'UnitPrc Qty', 'confidence': 0.99648, 'lang': 'en', 'bounding_box': (478.0, 409.0, 638.0, 457.0)}, {'text': 'Amount V', 'confidence': 0.98397, 'lang': 'en', 'bounding_box': (674.0, 426.0, 783.0, 464.0)}, {'text': 'ICE BAG', 'confidence': 0.94431, 'lang': 'en', 'bounding_box': (280.0, 453.0, 382.0, 498.0)}, {'text': 'AED6.00', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (464.0, 468.0, 563.0, 511.0)}, {'text': 'で', 'confidence': 0.42793, 'lang': 'en', 'bounding_box': (279.0, 486.0, 379.0, 527.0)}, {'text': 'AED6.00 S', 'confidence': 0.99854, 'lang': 'en', 'bounding_box': (656.0, 482.0, 777.0, 524.0)}, {'text': 'TOTAL AED', 'confidence': 0.99983, 'lang': 'en', 'bounding_box': (277.0, 542.0, 513.0, 614.0)}, {'text': 'AED6.00', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (587.0, 564.0, 768.0, 628.0)}, {'text': 'Total savings:', 'confidence': 0.99979, 'lang': 'en', 'bounding_box': (278.0, 595.0, 457.0, 642.0)}, {'text': 'AED0.00', 'confidence': 0.99388, 'lang': 'en', 'bounding_box': (670.0, 619.0, 764.0, 660.0)}, {'text': 'Cash AED:', 'confidence': 0.98764, 'lang': 'en', 'bounding_box': (468.0, 667.0, 585.0, 704.0)}, {'text': 'AED10.00', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (655.0, 677.0, 761.0, 715.0)}, {'text': 'AED10.00', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (358.0, 687.0, 467.0, 723.0)}, {'text': 'Change AED', 'confidence': 0.99799, 'lang': 'en', 'bounding_box': (455.0, 720.0, 586.0, 755.0)}, {'text': 'AED4.00', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (668.0, 732.0, 758.0, 763.0)}, {'text': 'VAT %', 'confidence': 0.90522, 'lang': 'en', 'bounding_box': (254.0, 803.0, 336.0, 842.0)}, {'text': 'Sale Amt', 'confidence': 0.94852, 'lang': 'en', 'bounding_box': (412.0, 812.0, 524.0, 851.0)}, {'text': 'VAT Amt', 'confidence': 0.99973, 'lang': 'en', 'bounding_box': (635.0, 824.0, 731.0, 865.0)}, {'text': 'S5', 'confidence': 0.99612, 'lang': 'en', 'bounding_box': (252.0, 834.0, 305.0, 868.0)}, {'text': 'AED6.00', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (411.0, 842.0, 512.0, 877.0)}, {'text': 'AED0.29', 'confidence': 0.99829, 'lang': 'en', 'bounding_box': (611.0, 851.0, 710.0, 890.0)}, {'text': 'VAT Reg Number: 100221692500003', 'confidence': 0.98277, 'lang': 'en', 'bounding_box': (247.0, 893.0, 657.0, 947.0)}, {'text': '8/18/2026', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (269.0, 958.0, 402.0, 998.0)}, {'text': 'Shift:1', 'confidence': 0.99971, 'lang': 'en', 'bounding_box': (428.0, 965.0, 526.0, 996.0)}, {'text': '04:52:23', 'confidence': 0.99994, 'lang': 'en', 'bounding_box': (648.0, 968.0, 752.0, 1001.0)}, {'text': 'POS: 2 CSR:Babbry, Wahid TRAN:', 'confidence': 0.97286, 'lang': 'en', 'bounding_box': (239.0, 988.0, 641.0, 1030.0)}, {'text': '584439', 'confidence': 0.99999, 'lang': 'en', 'bounding_box': (679.0, 995.0, 758.0, 1029.0)}, {'text': 'VAT Description', 'confidence': 0.99779, 'lang': 'en', 'bounding_box': (236.0, 1051.0, 446.0, 1090.0)}, {'text': 'S:Standard', 'confidence': 0.99978, 'lang': 'en', 'bounding_box': (234.0, 1083.0, 382.0, 1119.0)}, {'text': 'Z:Zero', 'confidence': 0.99753, 'lang': 'en', 'bounding_box': (405.0, 1084.0, 494.0, 1119.0)}, {'text': 'E:Tax Exempt', 'confidence': 0.99896, 'lang': 'en', 'bounding_box': (517.0, 1080.0, 672.0, 1116.0)}, {'text': 'Keep Bill for exchange within 7 Days', 'confidence': 0.99249, 'lang': 'en', 'bounding_box': (256.0, 1140.0, 718.0, 1180.0)}, {'text': 'Vaild only at Issued Store. T&C Apply', 'confidence': 0.99595, 'lang': 'en', 'bounding_box': (241.0, 1170.0, 718.0, 1212.0)}, {'text': 'THANK YOU', 'confidence': 0.99956, 'lang': 'en', 'bounding_box': (370.0, 1229.0, 614.0, 1294.0)}, {'text': 'HAVE A NICE DAY', 'confidence': 0.97675, 'lang': 'en', 'bounding_box': (286.0, 1284.0, 682.0, 1351.0)}, {'text': 'Customer care: 800-ENOC (3662)', 'confidence': 0.99281, 'lang': 'en', 'bounding_box': (286.0, 1341.0, 678.0, 1386.0)}, {'text': 'Customer care: 8UU-ENUC (3662)', 'confidence': 0.9666, 'lang': 'en', 'bounding_box': (337.0, 1423.0, 716.0, 1495.0)}, {'text': 'فاتورة فريبية', 'confidence': 0.91692, 'lang': 'ar', 'bounding_box': (472.0, 125.0, 631.0, 166.0)}, {'text': 'Tax Invoice', 'confidence': 0.99459, 'lang': 'ar', 'bounding_box': (436.0, 141.0, 698.0, 197.0)}, {'text': 'ENoc RETaIL', 'confidence': 0.73694, 'lang': 'ar', 'bounding_box': (369.0, 172.0, 640.0, 234.0)}, {'text': 'P.O. Box - 5589', 'confidence': 0.95548, 'lang': 'ar', 'bounding_box': (446.0, 208.0, 638.0, 260.0)}, {'text': 'LLC', 'confidence': 0.96667, 'lang': 'ar', 'bounding_box': (649.0, 205.0, 730.0, 243.0)}, {'text': 'Duba1, U.A.E', 'confidence': 0.92809, 'lang': 'ar', 'bounding_box': (470.0, 238.0, 624.0, 282.0)}, {'text': 'Site number: 1635', 'confidence': 0.97527, 'lang': 'ar', 'bounding_box': (296.0, 270.0, 502.0, 318.0)}, {'text': 'Wel come to ZOOM', 'confidence': 0.9618, 'lang': 'ar', 'bounding_box': (346.0, 324.0, 732.0, 406.0)}, {'text': 'Description', 'confidence': 0.99913, 'lang': 'ar', 'bounding_box': (282.0, 395.0, 431.0, 440.0)}, {'text': 'UnitPrc Qty', 'confidence': 0.99725, 'lang': 'ar', 'bounding_box': (478.0, 409.0, 638.0, 457.0)}, {'text': 'Amount V', 'confidence': 0.91135, 'lang': 'ar', 'bounding_box': (674.0, 426.0, 783.0, 464.0)}, {'text': 'ICE BAG', 'confidence': 0.99398, 'lang': 'ar', 'bounding_box': (280.0, 453.0, 382.0, 498.0)}, {'text': 'AED6. 00', 'confidence': 0.89996, 'lang': 'ar', 'bounding_box': (464.0, 468.0, 563.0, 511.0)}, {'text': 'كيس ثلج', 'confidence': 0.92555, 'lang': 'ar', 'bounding_box': (279.0, 486.0, 379.0, 527.0)}, {'text': 'AED6. 00 S', 'confidence': 0.95768, 'lang': 'ar', 'bounding_box': (656.0, 482.0, 777.0, 524.0)}, {'text': 'TOTAL AED', 'confidence': 0.9973, 'lang': 'ar', 'bounding_box': (277.0, 542.0, 513.0, 614.0)}, {'text': 'AED6. 00', 'confidence': 0.97715, 'lang': 'ar', 'bounding_box': (587.0, 564.0, 768.0, 628.0)}, {'text': 'Total savings:', 'confidence': 0.99927, 'lang': 'ar', 'bounding_box': (278.0, 595.0, 457.0, 642.0)}, {'text': 'AEDO. 00', 'confidence': 0.97199, 'lang': 'ar', 'bounding_box': (670.0, 619.0, 764.0, 660.0)}, {'text': 'Cash AED:', 'confidence': 0.99231, 'lang': 'ar', 'bounding_box': (468.0, 667.0, 585.0, 704.0)}, {'text': 'AED10. 00', 'confidence': 0.92831, 'lang': 'ar', 'bounding_box': (655.0, 677.0, 761.0, 715.0)}, {'text': 'AED10. 00', 'confidence': 0.97714, 'lang': 'ar', 'bounding_box': (358.0, 687.0, 467.0, 723.0)}, {'text': 'Change AED', 'confidence': 0.99737, 'lang': 'ar', 'bounding_box': (455.0, 720.0, 586.0, 755.0)}, {'text': 'AED4. 00', 'confidence': 0.9419, 'lang': 'ar', 'bounding_box': (668.0, 732.0, 758.0, 763.0)}, {'text': 'VAT %', 'confidence': 0.91957, 'lang': 'ar', 'bounding_box': (254.0, 803.0, 336.0, 842.0)}, {'text': 'Sale Amt', 'confidence': 0.95152, 'lang': 'ar', 'bounding_box': (412.0, 812.0, 524.0, 851.0)}, {'text': 'VAT Amt', 'confidence': 0.98841, 'lang': 'ar', 'bounding_box': (635.0, 824.0, 731.0, 865.0)}, {'text': 'S5', 'confidence': 0.9009, 'lang': 'ar', 'bounding_box': (252.0, 834.0, 305.0, 868.0)}, {'text': 'AED6. 00', 'confidence': 0.98042, 'lang': 'ar', 'bounding_box': (411.0, 842.0, 512.0, 877.0)}, {'text': 'AEDO. 29', 'confidence': 0.97101, 'lang': 'ar', 'bounding_box': (611.0, 851.0, 710.0, 890.0)}, {'text': 'VAT Reg Number: 100221692500003', 'confidence': 0.98891, 'lang': 'ar', 'bounding_box': (247.0, 893.0, 657.0, 947.0)}, {'text': '8/18/2026', 'confidence': 0.95444, 'lang': 'ar', 'bounding_box': (269.0, 958.0, 402.0, 998.0)}, {'text': 'Shift:1', 'confidence': 0.9686, 'lang': 'ar', 'bounding_box': (428.0, 965.0, 526.0, 996.0)}, {'text': '04:52:23', 'confidence': 0.99735, 'lang': 'ar', 'bounding_box': (648.0, 968.0, 752.0, 1001.0)}, {'text': 'POS 2 CSR:Babbry, Wahid TRAN:', 'confidence': 0.97046, 'lang': 'ar', 'bounding_box': (239.0, 988.0, 641.0, 1030.0)}, {'text': '584439', 'confidence': 0.99976, 'lang': 'ar', 'bounding_box': (679.0, 995.0, 758.0, 1029.0)}, {'text': 'VAT Description', 'confidence': 0.99364, 'lang': 'ar', 'bounding_box': (236.0, 1051.0, 446.0, 1090.0)}, {'text': 'S:Standard', 'confidence': 0.98181, 'lang': 'ar', 'bounding_box': (234.0, 1083.0, 382.0, 1119.0)}, {'text': 'Z:Zero', 'confidence': 0.95415, 'lang': 'ar', 'bounding_box': (405.0, 1084.0, 494.0, 1119.0)}, {'text': 'E: Tax Exempt', 'confidence': 0.95505, 'lang': 'ar', 'bounding_box': (517.0, 1080.0, 672.0, 1116.0)}, {'text': 'Keep Bill for exchange within 7 Days', 'confidence': 0.98991, 'lang': 'ar', 'bounding_box': (256.0, 1140.0, 718.0, 1180.0)}, {'text': 'Vaild only at Issued Store. T&C Apply', 'confidence': 0.9894, 'lang': 'ar', 'bounding_box': (241.0, 1170.0, 718.0, 1212.0)}, {'text': 'THANK YOU', 'confidence': 0.98792, 'lang': 'ar', 'bounding_box': (370.0, 1229.0, 614.0, 1294.0)}, {'text': 'HAVE A NICE DAY', 'confidence': 0.97231, 'lang': 'ar', 'bounding_box': (286.0, 1284.0, 682.0, 1351.0)}, {'text': 'Customer care: 800-ENoc (3662)', 'confidence': 0.96587, 'lang': 'ar', 'bounding_box': (286.0, 1341.0, 678.0, 1386.0)}, {'text': 'Customer care: BUU-ENuc (36b2)', 'confidence': 0.92201, 'lang': 'ar', 'bounding_box': (337.0, 1423.0, 716.0, 1495.0)}], 'field_confidence': {'vendor': 0.2434736470234114, 'date': 0.30167890802675584, 'currency': 0.6993127725752508, 'amount': 0.7095395809364548, 'vat_rate': 0.6494179999999999, 'vat_amount': 0.7115219415551839, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.9678784414715719, 'card_amount': 0.0, 'change': 0.9740964933110368, 'total_amount': 0.8373696293478261, 'invoice_number': 0.0, 'transaction_number': 0.39469154180602006, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'vat_amount', 'discount', 'service_charge', 'tip', 'card_amount', 'invoice_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** で (0.43)

**Raw text:**

```
Tax Invoice
ENOC RETAIL
P.0. Box - 5589
LLC
Dubai, U.A.E
Site number:1635
Welcome to ZOOM
Description
UnitPrc Qty
Amount V
ICE BAG
AED6.00
で
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
S5
AED6.00
AED0.29
VAT Reg Number: 100221692500003
8/18/2026
Shift:1
04:52:23
POS: 2 CSR:Babbry, Wahid TRAN:
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
Customer care: 8UU-ENUC (3662)
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
فاتورة فريبية
Tax Invoice
ENoc RETaIL
P.O. Box - 5589
LLC
Duba1, U.A.E
Site number: 1635
Wel come to ZOOM
Description
UnitPrc Qty
Amount V
ICE BAG
AED6. 00
كيس ثلج
AED6. 00 S
TOTAL AED
AED6. 00
Total savings:
AEDO. 00
Cash AED:
AED10. 00
AED10. 00
Change AED
AED4. 00
VAT %
Sale Amt
VAT Amt
S5
AED6. 00
AEDO. 29
VAT Reg Number: 100221692500003
8/18/2026
Shift:1
04:52:23
POS 2 CSR:Babbry, Wahid TRAN:
584439
VAT Description
S:Standard
Z:Zero
E: Tax Exempt
Keep Bill for exchange within 7 Days
Vaild only at Issued Store. T&C Apply
THANK YOU
HAVE A NICE DAY
Customer care: 800-ENoc (3662)
Customer care: BUU-ENuc (36b2)
```

## image (1).png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'BlueR n', 'expense_type': None, 'amount': None, 'vat_amount': 0.0, 'total_amount': None, 'currency': None, 'date': '03-Aug-2026', 'confidence': 0.19, 'field_confidence': {'vendor': 0.26683656150341684, 'date': 0.6669298291571754, 'currency': 0.0, 'amount': 0.0, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.785125375854214, 'card_amount': 0.0, 'change': 0.785125375854214, 'total_amount': 0.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'card_amount', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'BlueR n', 'confidence': 0.26683656150341684, 'evidence': 'BlueR n', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '03-Aug-2026', 'confidence': 0.6669298291571754, 'evidence': 'Date :03-Aug-2026 17:40 B11 No :236191', 'signals': ['date_format_match', 'date_label', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 111.0, 'confidence': 0.785125375854214, 'evidence': 'eso b111 for exchange. 29', 'signals': ['cash_label', 'same_row', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': 111.0, 'confidence': 0.785125375854214, 'evidence': 'eso b111 for exchange. 29', 'signals': ['change_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'total_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'BlueR n\nFIDAAL MADINA\nHYPERMARKET LLC\nDIP Phase 2 - Dubel , UAR\nDIP Pbase 2 - Dabal, UAB\nTd: 04-8851961\n0ate :065-dag-2026 17:40\nTate :06-Fe9-20% 17:40\nBi11 Nc:236191\nBunr B: 412\n7180003\nFIS IaN: P0S8\nFS MAN: PISE\nfaa Licemse Rmler : 19051005\nFax L Icense Ruler : 18051085\nDate :03-Aug-2026 17:40 B11 No :236191\nPOS Name: P058\nUser ID :ARSHINA\nS1.No Description\nQty Asount\nCKUMEER\nCKCREER\nCAPROT CHINO\nCIPBOT CHIHI\nBARMN PHILIFINE 163\nBRADN PHILIPINE 163\nSHIPPDG BE\nSHaPP ING B%E\n258075430000 1 0 6.00\n9580754008080 1 0 6.08\n998624700000 1 8 7.59\n998010700000 1 8 4.49\n*00107000000 1 4.46\n1000000 11 1.25\n1008000 1 0.25\n2.17 9.13\n2.0 11.99\n0.6.99\n1.08 0.25\nThark you visit agatn\neso b111 for exchange. 29\no Cash Refund.\nExchenge of Underganwents: not allowed due to hyg\nB111 Amount: 29.00\nTotal Qty: 6.05\nenic reasons\nentc reasans\nHold Jnaing 236191\nHald Jmicet 23181\n100823019120260803', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'BlueR', 'confidence': 0.98267, 'lang': 'en', 'bounding_box': (20.0, 49.0, 102.0, 85.0)}, {'text': 'n', 'confidence': 0.93153, 'lang': 'en', 'bounding_box': (108.0, 56.0, 129.0, 74.0)}, {'text': 'FIDAAL MADINA', 'confidence': 0.97304, 'lang': 'en', 'bounding_box': (32.0, 135.0, 130.0, 148.0)}, {'text': 'HYPERMARKET LLC', 'confidence': 0.98977, 'lang': 'en', 'bounding_box': (36.0, 147.0, 126.0, 158.0)}, {'text': 'DIP Phase 2 - Dubel , UAR', 'confidence': 0.91731, 'lang': 'en', 'bounding_box': (37.0, 156.0, 125.0, 167.0)}, {'text': 'Ted:04-8851961', 'confidence': 0.93184, 'lang': 'en', 'bounding_box': (60.0, 166.0, 113.0, 176.0)}, {'text': '0ate :065-dag-2026 17:40', 'confidence': 0.72095, 'lang': 'en', 'bounding_box': (0.0, 181.0, 67.0, 190.0)}, {'text': 'Bi11 Nc:236191', 'confidence': 0.9129, 'lang': 'en', 'bounding_box': (0.0, 190.0, 37.0, 198.0)}, {'text': 'Bunr (l: 412', 'confidence': 0.68778, 'lang': 'en', 'bounding_box': (0.0, 197.0, 35.0, 207.0)}, {'text': '7180003', 'confidence': 0.91221, 'lang': 'en', 'bounding_box': (0.0, 206.0, 20.0, 215.0)}, {'text': 'FIS IaN: P0S8', 'confidence': 0.66333, 'lang': 'en', 'bounding_box': (83.0, 189.0, 125.0, 199.0)}, {'text': 'faa Licemse Rmler : 19051005', 'confidence': 0.8108, 'lang': 'en', 'bounding_box': (83.0, 198.0, 163.0, 208.0)}, {'text': 'Date', 'confidence': 0.9714, 'lang': 'en', 'bounding_box': (0.0, 223.0, 16.0, 233.0)}, {'text': 'POS Name: P058', 'confidence': 0.95048, 'lang': 'en', 'bounding_box': (0.0, 231.0, 53.0, 242.0)}, {'text': ':03-Aug-2026 17:40', 'confidence': 0.9667, 'lang': 'en', 'bounding_box': (26.0, 223.0, 91.0, 233.0)}, {'text': 'B11 No :236191', 'confidence': 0.98031, 'lang': 'en', 'bounding_box': (100.0, 223.0, 155.0, 234.0)}, {'text': 'User ID :ARSHINA', 'confidence': 0.98448, 'lang': 'en', 'bounding_box': (101.0, 233.0, 158.0, 242.0)}, {'text': 'S1.No Description', 'confidence': 0.97907, 'lang': 'en', 'bounding_box': (0.0, 247.0, 60.0, 258.0)}, {'text': 'Qty', 'confidence': 0.98039, 'lang': 'en', 'bounding_box': (111.0, 249.0, 123.0, 259.0)}, {'text': 'Asount', 'confidence': 0.94255, 'lang': 'en', 'bounding_box': (134.0, 249.0, 158.0, 259.0)}, {'text': 'CKUMEER', 'confidence': 0.77697, 'lang': 'en', 'bounding_box': (10.0, 264.0, 34.0, 273.0)}, {'text': 'CAPROT CHINO', 'confidence': 0.77921, 'lang': 'en', 'bounding_box': (10.0, 281.0, 45.0, 290.0)}, {'text': 'BARMN PHILIFINE 163', 'confidence': 0.89614, 'lang': 'en', 'bounding_box': (10.0, 298.0, 64.0, 306.0)}, {'text': 'SHIPPDG BE', 'confidence': 0.77957, 'lang': 'en', 'bounding_box': (10.0, 315.0, 44.0, 323.0)}, {'text': '258075430000 1 0 6.00', 'confidence': 0.91815, 'lang': 'en', 'bounding_box': (12.0, 289.0, 80.0, 299.0)}, {'text': '998624700000 1 8 7.59', 'confidence': 0.88459, 'lang': 'en', 'bounding_box': (12.0, 306.0, 80.0, 316.0)}, {'text': '998010700000 1 8', 'confidence': 0.80477, 'lang': 'en', 'bounding_box': (13.0, 273.0, 68.0, 281.0)}, {'text': '1000000', 'confidence': 0.90505, 'lang': 'en', 'bounding_box': (13.0, 323.0, 36.0, 331.0)}, {'text': '11', 'confidence': 0.97302, 'lang': 'en', 'bounding_box': (48.0, 323.0, 67.0, 332.0)}, {'text': '1.25', 'confidence': 0.89962, 'lang': 'en', 'bounding_box': (65.0, 323.0, 79.0, 332.0)}, {'text': '4.49', 'confidence': 0.96959, 'lang': 'en', 'bounding_box': (66.0, 274.0, 80.0, 281.0)}, {'text': '2.17', 'confidence': 0.99851, 'lang': 'en', 'bounding_box': (113.0, 265.0, 126.0, 273.0)}, {'text': '2.0', 'confidence': 0.98131, 'lang': 'en', 'bounding_box': (113.0, 282.0, 126.0, 291.0)}, {'text': '0.', 'confidence': 0.99988, 'lang': 'en', 'bounding_box': (113.0, 299.0, 125.0, 307.0)}, {'text': '1.08', 'confidence': 0.91217, 'lang': 'en', 'bounding_box': (113.0, 316.0, 125.0, 324.0)}, {'text': '11.99', 'confidence': 0.99734, 'lang': 'en', 'bounding_box': (136.0, 282.0, 152.0, 291.0)}, {'text': '9.13', 'confidence': 0.82064, 'lang': 'en', 'bounding_box': (138.0, 265.0, 152.0, 274.0)}, {'text': '6.99', 'confidence': 0.98766, 'lang': 'en', 'bounding_box': (138.0, 299.0, 151.0, 307.0)}, {'text': '0.25', 'confidence': 0.9945, 'lang': 'en', 'bounding_box': (138.0, 316.0, 151.0, 324.0)}, {'text': 'Thark you visit aga1n', 'confidence': 0.91453, 'lang': 'en', 'bounding_box': (0.0, 356.0, 72.0, 367.0)}, {'text': 'eso b111 for exchange.', 'confidence': 0.9224, 'lang': 'en', 'bounding_box': (0.0, 364.0, 78.0, 376.0)}, {'text': 'o Cash Refund.', 'confidence': 0.98578, 'lang': 'en', 'bounding_box': (0.0, 373.0, 50.0, 383.0)}, {'text': 'Exchenge of Underganwents: not allowed due to hyg', 'confidence': 0.96233, 'lang': 'en', 'bounding_box': (0.0, 381.0, 164.0, 393.0)}, {'text': 'B111 Amount: 29.00', 'confidence': 0.94179, 'lang': 'en', 'bounding_box': (37.0, 347.0, 132.0, 358.0)}, {'text': 'Total Qty: 6.05', 'confidence': 0.99888, 'lang': 'en', 'bounding_box': (61.0, 340.0, 116.0, 350.0)}, {'text': '29', 'confidence': 0.99574, 'lang': 'en', 'bounding_box': (106.0, 358.0, 141.0, 384.0)}, {'text': 'enic reasons', 'confidence': 0.91507, 'lang': 'en', 'bounding_box': (0.0, 391.0, 44.0, 399.0)}, {'text': 'Hold Jnaing 236191', 'confidence': 0.71973, 'lang': 'en', 'bounding_box': (51.0, 397.0, 107.0, 412.0)}, {'text': '100823019120260803', 'confidence': 0.91929, 'lang': 'en', 'bounding_box': (51.0, 429.0, 109.0, 439.0)}, {'text': 'BlueR', 'confidence': 0.86129, 'lang': 'ar', 'bounding_box': (20.0, 49.0, 102.0, 85.0)}, {'text': 'n', 'confidence': 0.80059, 'lang': 'ar', 'bounding_box': (108.0, 56.0, 129.0, 74.0)}, {'text': 'FIDAAL MADINA', 'confidence': 0.92092, 'lang': 'ar', 'bounding_box': (32.0, 135.0, 130.0, 148.0)}, {'text': 'HYPERMARKET LLC', 'confidence': 0.96932, 'lang': 'ar', 'bounding_box': (36.0, 147.0, 126.0, 158.0)}, {'text': 'DIP Pbase 2 - Dabal, UAB', 'confidence': 0.86909, 'lang': 'ar', 'bounding_box': (37.0, 156.0, 125.0, 167.0)}, {'text': 'Td: 04-8851961', 'confidence': 0.95989, 'lang': 'ar', 'bounding_box': (60.0, 166.0, 113.0, 176.0)}, {'text': 'Tate :06-Fe9-20% 17:40', 'confidence': 0.75866, 'lang': 'ar', 'bounding_box': (0.0, 181.0, 67.0, 190.0)}, {'text': 'Bi11 fc:236191', 'confidence': 0.89121, 'lang': 'ar', 'bounding_box': (0.0, 190.0, 37.0, 198.0)}, {'text': 'Bunr B: 412', 'confidence': 0.78425, 'lang': 'ar', 'bounding_box': (0.0, 197.0, 35.0, 207.0)}, {'text': '7180003', 'confidence': 0.89642, 'lang': 'ar', 'bounding_box': (0.0, 206.0, 20.0, 215.0)}, {'text': 'FS MAN: PISE', 'confidence': 0.66302, 'lang': 'ar', 'bounding_box': (83.0, 189.0, 125.0, 199.0)}, {'text': 'Fax L Icense Ruler : 18051085', 'confidence': 0.82428, 'lang': 'ar', 'bounding_box': (83.0, 198.0, 163.0, 208.0)}, {'text': 'Dute', 'confidence': 0.89731, 'lang': 'ar', 'bounding_box': (0.0, 223.0, 16.0, 233.0)}, {'text': 'POS Name: P068', 'confidence': 0.87245, 'lang': 'ar', 'bounding_box': (0.0, 231.0, 53.0, 242.0)}, {'text': ':03-Aug-2026 17:40', 'confidence': 0.95078, 'lang': 'ar', 'bounding_box': (26.0, 223.0, 91.0, 233.0)}, {'text': 'BI11 No :236191', 'confidence': 0.94328, 'lang': 'ar', 'bounding_box': (100.0, 223.0, 155.0, 234.0)}, {'text': 'User ID :ARSHINA', 'confidence': 0.9664, 'lang': 'ar', 'bounding_box': (101.0, 233.0, 158.0, 242.0)}, {'text': 'S1.No Description', 'confidence': 0.93923, 'lang': 'ar', 'bounding_box': (0.0, 247.0, 60.0, 258.0)}, {'text': 'Qty', 'confidence': 0.99807, 'lang': 'ar', 'bounding_box': (111.0, 249.0, 123.0, 259.0)}, {'text': 'Asount', 'confidence': 0.87056, 'lang': 'ar', 'bounding_box': (134.0, 249.0, 158.0, 259.0)}, {'text': 'CKCREER', 'confidence': 0.72407, 'lang': 'ar', 'bounding_box': (10.0, 264.0, 34.0, 273.0)}, {'text': 'CIPBOT CHIHI', 'confidence': 0.79455, 'lang': 'ar', 'bounding_box': (10.0, 281.0, 45.0, 290.0)}, {'text': 'BRADN PHILIPINE 163', 'confidence': 0.87441, 'lang': 'ar', 'bounding_box': (10.0, 298.0, 64.0, 306.0)}, {'text': 'SHaPP ING B%E', 'confidence': 0.76385, 'lang': 'ar', 'bounding_box': (10.0, 315.0, 44.0, 323.0)}, {'text': '9580754008080 1 0 6.08', 'confidence': 0.82246, 'lang': 'ar', 'bounding_box': (12.0, 289.0, 80.0, 299.0)}, {'text': '95824700000 1 9 7.59', 'confidence': 0.86881, 'lang': 'ar', 'bounding_box': (12.0, 306.0, 80.0, 316.0)}, {'text': '*00107000000 1 ', 'confidence': 0.73645, 'lang': 'ar', 'bounding_box': (13.0, 273.0, 68.0, 281.0)}, {'text': '1008000', 'confidence': 0.81368, 'lang': 'ar', 'bounding_box': (13.0, 323.0, 36.0, 331.0)}, {'text': '1', 'confidence': 0.90125, 'lang': 'ar', 'bounding_box': (48.0, 323.0, 67.0, 332.0)}, {'text': '0.25', 'confidence': 0.89608, 'lang': 'ar', 'bounding_box': (65.0, 323.0, 79.0, 332.0)}, {'text': '4.46', 'confidence': 0.86662, 'lang': 'ar', 'bounding_box': (66.0, 274.0, 80.0, 281.0)}, {'text': '2.17', 'confidence': 0.95363, 'lang': 'ar', 'bounding_box': (113.0, 265.0, 126.0, 273.0)}, {'text': '2.00', 'confidence': 0.87962, 'lang': 'ar', 'bounding_box': (113.0, 282.0, 126.0, 291.0)}, {'text': '0.18', 'confidence': 0.80642, 'lang': 'ar', 'bounding_box': (113.0, 299.0, 125.0, 307.0)}, {'text': '1.00', 'confidence': 0.90482, 'lang': 'ar', 'bounding_box': (113.0, 316.0, 125.0, 324.0)}, {'text': '11.99', 'confidence': 0.99427, 'lang': 'ar', 'bounding_box': (136.0, 282.0, 152.0, 291.0)}, {'text': '9.13', 'confidence': 0.70036, 'lang': 'ar', 'bounding_box': (138.0, 265.0, 152.0, 274.0)}, {'text': '6.99', 'confidence': 0.97968, 'lang': 'ar', 'bounding_box': (138.0, 299.0, 151.0, 307.0)}, {'text': '0.25', 'confidence': 0.996, 'lang': 'ar', 'bounding_box': (138.0, 316.0, 151.0, 324.0)}, {'text': 'Thark you visit agatn', 'confidence': 0.95109, 'lang': 'ar', 'bounding_box': (0.0, 356.0, 72.0, 367.0)}, {'text': 'eso b111 for exchange.', 'confidence': 0.8992, 'lang': 'ar', 'bounding_box': (0.0, 364.0, 78.0, 376.0)}, {'text': 'o Cash Refund.', 'confidence': 0.97337, 'lang': 'ar', 'bounding_box': (0.0, 373.0, 50.0, 383.0)}, {'text': 'Exchenge of Undergareents not al lowed due to hyg', 'confidence': 0.95073, 'lang': 'ar', 'bounding_box': (0.0, 381.0, 164.0, 393.0)}, {'text': 'B111 Anount: 29.00', 'confidence': 0.91641, 'lang': 'ar', 'bounding_box': (37.0, 347.0, 132.0, 358.0)}, {'text': 'Total Qty: 6.05', 'confidence': 0.98881, 'lang': 'ar', 'bounding_box': (61.0, 340.0, 116.0, 350.0)}, {'text': '29', 'confidence': 0.9981, 'lang': 'ar', 'bounding_box': (106.0, 358.0, 141.0, 384.0)}, {'text': 'entc reasans', 'confidence': 0.93183, 'lang': 'ar', 'bounding_box': (0.0, 391.0, 44.0, 399.0)}, {'text': 'Hald Jmicet 23181', 'confidence': 0.60215, 'lang': 'ar', 'bounding_box': (51.0, 397.0, 107.0, 412.0)}, {'text': '10082361915260803', 'confidence': 0.8053, 'lang': 'ar', 'bounding_box': (51.0, 429.0, 109.0, 439.0)}], 'field_confidence': {'vendor': 0.26683656150341684, 'date': 0.6669298291571754, 'currency': 0.0, 'amount': 0.0, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.785125375854214, 'card_amount': 0.0, 'change': 0.785125375854214, 'total_amount': 0.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'card_amount', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
BlueR
n
FIDAAL MADINA
HYPERMARKET LLC
DIP Phase 2 - Dubel , UAR
Ted:04-8851961
0ate :065-dag-2026 17:40
Bi11 Nc:236191
Bunr (l: 412
7180003
FIS IaN: P0S8
faa Licemse Rmler : 19051005
Date
POS Name: P058
:03-Aug-2026 17:40
B11 No :236191
User ID :ARSHINA
S1.No Description
Qty
Asount
CKUMEER
CAPROT CHINO
BARMN PHILIFINE 163
SHIPPDG BE
258075430000 1 0 6.00
998624700000 1 8 7.59
998010700000 1 8
1000000
11
1.25
4.49
2.17
2.0
0.
1.08
11.99
9.13
6.99
0.25
Thark you visit aga1n
eso b111 for exchange.
o Cash Refund.
Exchenge of Underganwents: not allowed due to hyg
B111 Amount: 29.00
Total Qty: 6.05
29
enic reasons
Hold Jnaing 236191
100823019120260803
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
BlueR
n
FIDAAL MADINA
HYPERMARKET LLC
DIP Pbase 2 - Dabal, UAB
Td: 04-8851961
Tate :06-Fe9-20% 17:40
Bi11 fc:236191
Bunr B: 412
7180003
FS MAN: PISE
Fax L Icense Ruler : 18051085
Dute
POS Name: P068
:03-Aug-2026 17:40
BI11 No :236191
User ID :ARSHINA
S1.No Description
Qty
Asount
CKCREER
CIPBOT CHIHI
BRADN PHILIPINE 163
SHaPP ING B%E
9580754008080 1 0 6.08
95824700000 1 9 7.59
*00107000000 1
1008000
1
0.25
4.46
2.17
2.00
0.18
1.00
11.99
9.13
6.99
0.25
Thark you visit agatn
eso b111 for exchange.
o Cash Refund.
Exchenge of Undergareents not al lowed due to hyg
B111 Anount: 29.00
Total Qty: 6.05
29
entc reasans
Hald Jmicet 23181
10082361915260803
```

## image (2).png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'TUFFCO BUILDING MATERIALS TRADING L.L.C DEALERS IN BUILDING MATERIALS', 'expense_type': None, 'amount': 20.0, 'vat_amount': 1.0, 'total_amount': 21.0, 'currency': 'AED', 'date': '', 'confidence': 0.24, 'field_confidence': {'vendor': 0.2614762442553191, 'date': 0.0, 'currency': 0.5223119255319149, 'amount': 0.8418286489361703, 'vat_rate': 0.7999565, 'vat_amount': 0.4, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.9485750212765958, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'TUFFCO BUILDING MATERIALS TRADING L.L.C DEALERS IN BUILDING MATERIALS', 'confidence': 0.2614762442553191, 'evidence': 'TUFFCO BUILDING MATERIALS TRADING L.L.C DEALERS IN BUILDING MATERIALS', 'signals': ['top_of_receipt', 'multiline_header_merge', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': 'AED', 'confidence': 0.5223119255319149, 'evidence': 'Total AED', 'signals': ['currency_code_match', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'amount': {'value': 20.0, 'confidence': 0.8418286489361703, 'evidence': '20 20 2/', 'signals': ['subtotal_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.7999565, 'evidence': 'VAT 5%', 'signals': ['vat_tax_rate_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 1.0, 'confidence': 0.4, 'evidence': 'derived: Total Amount 21 at 5.0%', 'signals': ['derived_arithmetic', 'derived_inclusive'], 'low': True, 'warning': 'derived_value'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 21.0, 'confidence': 0.9485750212765958, 'evidence': 'Total Amount 21', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'arithmetic_reconciled_inclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': '.\nتوفكو لتجارة مواد السبناء ذمم\nTUFFCO BUILDING MATERIALS TRADING L.L.C\nDEALERS IN BUILDING MATERIALS\nMob: +971 55 889 9852,Shop no-7, Farhad Building,\nUmm Al Thuoob, Umm Al Quwain\nE-mail : buildmtr@gmail.com\n1052520\nفاتورةالضريبية\nN0.1383 TAX INVOICE Date.4Auy 26\no 1383TAIICE Dale.Auy.2التاريخ\nMr.Ns Blue Rbyhe\nM.wsBluebyhe\nالسيد السادة\nCust. TRN\nDescription deaSr Qty. Rate Amount (Excl.Vat) VAT 5% Amount (Incl.Vat)\nالتفاصيل الكمية Qty. السعر Rate Amonالمبلغ ا (Excl. Vat) VAT 5% Amont المبلغ (Incl.Vat)\nShuttaff\nShuttayy\n20 20 2/\nAmount 209\nVAT 5%\nTotal AED\nTotal Amount 21\nAED\nSignature\nالنوفيع\nCS CamScanner', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': '.    ', 'confidence': 0.65725, 'lang': 'en', 'bounding_box': (9.0, 25.0, 466.0, 56.0)}, {'text': 'TUFFCO BUILDING MATERIALS', 'confidence': 0.99861, 'lang': 'en', 'bounding_box': (12.0, 52.0, 364.0, 81.0)}, {'text': 'TRADING L.L.C', 'confidence': 0.98906, 'lang': 'en', 'bounding_box': (357.0, 57.0, 464.0, 79.0)}, {'text': 'DEALERS IN BUILDING MATERIALS', 'confidence': 0.9951, 'lang': 'en', 'bounding_box': (62.0, 76.0, 421.0, 101.0)}, {'text': 'Mob: +971 55 889 9852,Shop no-7, Farhad Building,', 'confidence': 0.99863, 'lang': 'en', 'bounding_box': (7.0, 95.0, 468.0, 124.0)}, {'text': 'Umm Al Thuoob, Umm Al Quwain', 'confidence': 0.98163, 'lang': 'en', 'bounding_box': (82.0, 114.0, 387.0, 138.0)}, {'text': 'E-mail : buildmtr@gmail.com', 'confidence': 0.98921, 'lang': 'en', 'bounding_box': (103.0, 134.0, 369.0, 157.0)}, {'text': '1052520', 'confidence': 0.64862, 'lang': 'en', 'bounding_box': (136.0, 152.0, 483.0, 179.0)}, {'text': 'No. 1383 TAX INVOICE', 'confidence': 0.97905, 'lang': 'en', 'bounding_box': (4.0, 167.0, 289.0, 206.0)}, {'text': 'Date.4Auy 26', 'confidence': 0.81466, 'lang': 'en', 'bounding_box': (293.0, 174.0, 469.0, 215.0)}, {'text': 'Mr.Ns Blue Rbyhe', 'confidence': 0.80866, 'lang': 'en', 'bounding_box': (1.0, 197.0, 260.0, 243.0)}, {'text': 'Cust. TRN', 'confidence': 0.97948, 'lang': 'en', 'bounding_box': (10.0, 239.0, 74.0, 254.0)}, {'text': 'Description', 'confidence': 0.98168, 'lang': 'en', 'bounding_box': (26.0, 263.0, 173.0, 285.0)}, {'text': 'deaSr', 'confidence': 0.35086, 'lang': 'en', 'bounding_box': (193.0, 256.0, 224.0, 270.0)}, {'text': 'Qty.', 'confidence': 0.99914, 'lang': 'en', 'bounding_box': (193.0, 266.0, 225.0, 289.0)}, {'text': 'Rate', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (226.0, 269.0, 262.0, 289.0)}, {'text': 'Amount ', 'confidence': 0.95591, 'lang': 'en', 'bounding_box': (261.0, 255.0, 339.0, 275.0)}, {'text': '(Excl.Vat)', 'confidence': 0.99453, 'lang': 'en', 'bounding_box': (274.0, 269.0, 326.0, 289.0)}, {'text': 'VAT 5%', 'confidence': 0.9997, 'lang': 'en', 'bounding_box': (339.0, 260.0, 388.0, 282.0)}, {'text': 'Amount ', 'confidence': 0.93475, 'lang': 'en', 'bounding_box': (383.0, 256.0, 464.0, 277.0)}, {'text': '(Incl.Vat)', 'confidence': 0.97717, 'lang': 'en', 'bounding_box': (399.0, 272.0, 446.0, 291.0)}, {'text': 'Shuttaff', 'confidence': 0.97884, 'lang': 'en', 'bounding_box': (19.0, 287.0, 134.0, 335.0)}, {'text': '20', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (228.0, 293.0, 264.0, 319.0)}, {'text': '20', 'confidence': 0.9998, 'lang': 'en', 'bounding_box': (283.0, 292.0, 329.0, 319.0)}, {'text': '21', 'confidence': 0.96712, 'lang': 'en', 'bounding_box': (391.0, 294.0, 424.0, 322.0)}, {'text': 'Amount', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (280.0, 546.0, 338.0, 566.0)}, {'text': '209', 'confidence': 0.83923, 'lang': 'en', 'bounding_box': (383.0, 539.0, 437.0, 590.0)}, {'text': 'VAT 5%', 'confidence': 0.99971, 'lang': 'en', 'bounding_box': (283.0, 566.0, 337.0, 584.0)}, {'text': 'Total AED', 'confidence': 0.99981, 'lang': 'en', 'bounding_box': (8.0, 592.0, 66.0, 608.0)}, {'text': 'Total', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (289.0, 582.0, 322.0, 598.0)}, {'text': 'Amount', 'confidence': 0.99994, 'lang': 'en', 'bounding_box': (289.0, 596.0, 338.0, 611.0)}, {'text': '21', 'confidence': 0.99972, 'lang': 'en', 'bounding_box': (383.0, 586.0, 426.0, 627.0)}, {'text': 'AED', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (289.0, 609.0, 320.0, 626.0)}, {'text': 'Signature', 'confidence': 0.99917, 'lang': 'en', 'bounding_box': (201.0, 650.0, 264.0, 670.0)}, {'text': 'CS CamScanner', 'confidence': 0.97149, 'lang': 'en', 'bounding_box': (391.0, 686.0, 480.0, 705.0)}, {'text': 'توفكو لتجارة مواد السبناء ذمم', 'confidence': 0.90725, 'lang': 'ar', 'bounding_box': (9.0, 25.0, 466.0, 56.0)}, {'text': 'TUFFCO BUILDING MATERIALS', 'confidence': 0.9953, 'lang': 'ar', 'bounding_box': (12.0, 52.0, 364.0, 81.0)}, {'text': 'TRADING L.L.G', 'confidence': 0.9402, 'lang': 'ar', 'bounding_box': (357.0, 57.0, 464.0, 79.0)}, {'text': 'DEALERS IN BUILDING MATERIALS', 'confidence': 0.98863, 'lang': 'ar', 'bounding_box': (62.0, 76.0, 421.0, 101.0)}, {'text': 'Mob: +971 55 889 9852,Shop no-7, Farhad Building,', 'confidence': 0.98017, 'lang': 'ar', 'bounding_box': (7.0, 95.0, 468.0, 124.0)}, {'text': 'Umm AI Thuoob, Umm AI Quwain', 'confidence': 0.93885, 'lang': 'ar', 'bounding_box': (82.0, 114.0, 387.0, 138.0)}, {'text': 'E-mail : buildmtr@gmail.com', 'confidence': 0.97907, 'lang': 'ar', 'bounding_box': (103.0, 134.0, 369.0, 157.0)}, {'text': 'فاتورةالضريبية', 'confidence': 0.75476, 'lang': 'ar', 'bounding_box': (136.0, 152.0, 483.0, 179.0)}, {'text': 'o 1383TAIICE', 'confidence': 0.59976, 'lang': 'ar', 'bounding_box': (4.0, 167.0, 289.0, 206.0)}, {'text': 'Dale.Auy.2التاريخ', 'confidence': 0.6879, 'lang': 'ar', 'bounding_box': (293.0, 174.0, 469.0, 215.0)}, {'text': 'M.wsBluebyhe', 'confidence': 0.66156, 'lang': 'ar', 'bounding_box': (1.0, 197.0, 260.0, 243.0)}, {'text': 'السيد السادة', 'confidence': 0.9509, 'lang': 'ar', 'bounding_box': (391.0, 215.0, 466.0, 233.0)}, {'text': 'Cust. TRN', 'confidence': 0.99365, 'lang': 'ar', 'bounding_box': (10.0, 239.0, 74.0, 254.0)}, {'text': 'التفاصيل ', 'confidence': 0.82919, 'lang': 'ar', 'bounding_box': (26.0, 263.0, 173.0, 285.0)}, {'text': 'الكمية', 'confidence': 0.99749, 'lang': 'ar', 'bounding_box': (193.0, 256.0, 224.0, 270.0)}, {'text': 'Qty.', 'confidence': 0.9851, 'lang': 'ar', 'bounding_box': (193.0, 266.0, 225.0, 289.0)}, {'text': 'السعر', 'confidence': 0.98953, 'lang': 'ar', 'bounding_box': (226.0, 257.0, 262.0, 273.0)}, {'text': 'Rate', 'confidence': 0.9911, 'lang': 'ar', 'bounding_box': (226.0, 269.0, 262.0, 289.0)}, {'text': 'Amonالمبلغ ا', 'confidence': 0.85776, 'lang': 'ar', 'bounding_box': (261.0, 255.0, 339.0, 275.0)}, {'text': '(Excl. Vat)', 'confidence': 0.72386, 'lang': 'ar', 'bounding_box': (274.0, 269.0, 326.0, 289.0)}, {'text': 'VAT 5%', 'confidence': 0.9379, 'lang': 'ar', 'bounding_box': (339.0, 260.0, 388.0, 282.0)}, {'text': 'Amont المبلغ', 'confidence': 0.75799, 'lang': 'ar', 'bounding_box': (383.0, 256.0, 464.0, 277.0)}, {'text': '(Incl.Vat)', 'confidence': 0.95089, 'lang': 'ar', 'bounding_box': (399.0, 272.0, 446.0, 291.0)}, {'text': 'Shuttayy', 'confidence': 0.81847, 'lang': 'ar', 'bounding_box': (19.0, 287.0, 134.0, 335.0)}, {'text': '20', 'confidence': 0.97673, 'lang': 'ar', 'bounding_box': (228.0, 293.0, 264.0, 319.0)}, {'text': '20', 'confidence': 0.99325, 'lang': 'ar', 'bounding_box': (283.0, 292.0, 329.0, 319.0)}, {'text': '2/', 'confidence': 0.98461, 'lang': 'ar', 'bounding_box': (391.0, 294.0, 424.0, 322.0)}, {'text': 'Amount', 'confidence': 0.99964, 'lang': 'ar', 'bounding_box': (280.0, 546.0, 338.0, 566.0)}, {'text': '20', 'confidence': 0.75988, 'lang': 'ar', 'bounding_box': (383.0, 539.0, 437.0, 590.0)}, {'text': 'VAT 5%', 'confidence': 0.9833, 'lang': 'ar', 'bounding_box': (283.0, 566.0, 337.0, 584.0)}, {'text': 'Total AED.', 'confidence': 0.95186, 'lang': 'ar', 'bounding_box': (8.0, 592.0, 66.0, 608.0)}, {'text': 'Total', 'confidence': 0.99927, 'lang': 'ar', 'bounding_box': (289.0, 582.0, 322.0, 598.0)}, {'text': 'Amount', 'confidence': 0.99931, 'lang': 'ar', 'bounding_box': (289.0, 596.0, 338.0, 611.0)}, {'text': '|21', 'confidence': 0.64093, 'lang': 'ar', 'bounding_box': (383.0, 586.0, 426.0, 627.0)}, {'text': 'AED', 'confidence': 0.9966, 'lang': 'ar', 'bounding_box': (289.0, 609.0, 320.0, 626.0)}, {'text': 'Signature', 'confidence': 0.99814, 'lang': 'ar', 'bounding_box': (201.0, 650.0, 264.0, 670.0)}, {'text': 'النوفيع', 'confidence': 0.82631, 'lang': 'ar', 'bounding_box': (425.0, 651.0, 470.0, 671.0)}, {'text': 'CSCamScanner', 'confidence': 0.96202, 'lang': 'ar', 'bounding_box': (391.0, 686.0, 480.0, 705.0)}], 'field_confidence': {'vendor': 0.2614762442553191, 'date': 0.0, 'currency': 0.5223119255319149, 'amount': 0.8418286489361703, 'vat_rate': 0.7999565, 'vat_amount': 0.4, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.9485750212765958, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** deaSr (0.35)

**Raw text:**

```
.
TUFFCO BUILDING MATERIALS
TRADING L.L.C
DEALERS IN BUILDING MATERIALS
Mob: +971 55 889 9852,Shop no-7, Farhad Building,
Umm Al Thuoob, Umm Al Quwain
E-mail : buildmtr@gmail.com
1052520
No. 1383 TAX INVOICE
Date.4Auy 26
Mr.Ns Blue Rbyhe
Cust. TRN
Description
deaSr
Qty.
Rate
Amount
(Excl.Vat)
VAT 5%
Amount
(Incl.Vat)
Shuttaff
20
20
21
Amount
209
VAT 5%
Total AED
Total
Amount
21
AED
Signature
CS CamScanner
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
توفكو لتجارة مواد السبناء ذمم
TUFFCO BUILDING MATERIALS
TRADING L.L.G
DEALERS IN BUILDING MATERIALS
Mob: +971 55 889 9852,Shop no-7, Farhad Building,
Umm AI Thuoob, Umm AI Quwain
E-mail : buildmtr@gmail.com
فاتورةالضريبية
o 1383TAIICE
Dale.Auy.2التاريخ
M.wsBluebyhe
السيد السادة
Cust. TRN
التفاصيل
الكمية
Qty.
السعر
Rate
Amonالمبلغ ا
(Excl. Vat)
VAT 5%
Amont المبلغ
(Incl.Vat)
Shuttayy
20
20
2/
Amount
20
VAT 5%
Total AED.
Total
Amount
|21
AED
Signature
النوفيع
CSCamScanner
```

## image (3).png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'OAMAR AL MADINA GUPERMARKETLL.C', 'expense_type': None, 'amount': 2.34, 'vat_amount': 0.0, 'total_amount': 2.34, 'currency': None, 'date': '', 'confidence': 0.26, 'field_confidence': {'vendor': 0.262557493926868, 'date': 0.0, 'currency': 0.0, 'amount': 0.9595016224165341, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8563890906200318, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.9595016224165341, 'invoice_number': 0.4775789658187599, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_rate', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'OAMAR AL MADINA GUPERMARKETLL.C', 'confidence': 0.262557493926868, 'evidence': 'OAMAR AL MADINA GUPERMARKETLL.C', 'signals': ['top_of_receipt', 'multiline_header_merge', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 2.34, 'confidence': 0.9595016224165341, 'evidence': '5% 4u.84 2.34 49.18', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 49.25, 'confidence': 0.8563890906200318, 'evidence': 'CASH 49.25', 'signals': ['cash_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 2.34, 'confidence': 0.9595016224165341, 'evidence': '5% 4u.84 2.34 49.18', 'signals': ['total_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'invoice_number': {'value': '0585405699', 'confidence': 0.4775789658187599, 'evidence': '0585405699', 'signals': ['invoice_number_label', 'fuzzy_label_match', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'WS\nwwS\nOAMAR AL MADINA\nGUPERMARKETLL.C\nN y y t Al ( As\nNew Haoyyu tha A Quow 1\n0585405699\nTAX INVDICE\nRN:104645729500013\nonle :79 21-2026 09.4E\nvele 9 ual-c026 09.4t\nD:11 Nu:104\n31T1 Nu104\nPos Mece: Posi\nPiS leve: P9S2\nUter l0: 99\nDascription\nQty Amount\n9965950000000\n330995006000\nCURIANDER LEAF\n2,00 1.98\n9988002000000\nONION (INDTA)\n1.06 3.70\n6291044111119\nS4FA YOGHURT 10KG 1.00 38 00\n9988016000000\n99580 1600000\nGINGER (PRC)\n0.53 4.50\n9989943000000\nCURRY LEAF\n1.00 1.00\nLAQ-5000-BLUL RINE\nGly: 5.59\nRouncing 0.07\nB111 Amount 49.25 49.25\nCASH 49.25\nAnount to return 0.00\nATX Taxable Amount VAI Total\n5% 4u.84 2.34 49.18\n5X 4t.14 2.34 49.18\nFutp hill fai exchange.\nFebp hill tar cochaange.\ntend su far shopoing a pls cure àatn\nHnk riu for chooig a ps cure unha\ni taca befund\ntn Laci Heftol\n00020010420260729', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'WS', 'confidence': 0.5628, 'lang': 'en', 'bounding_box': (189.0, 15.0, 232.0, 40.0)}, {'text': 'OAMAR AL MADINA', 'confidence': 0.93726, 'lang': 'en', 'bounding_box': (149.0, 45.0, 278.0, 61.0)}, {'text': 'SUPERMARKETL.L.C', 'confidence': 0.9651, 'lang': 'en', 'bounding_box': (148.0, 59.0, 280.0, 75.0)}, {'text': 'N y y t Al ( As', 'confidence': 0.60429, 'lang': 'en', 'bounding_box': (146.0, 73.0, 294.0, 87.0)}, {'text': '0585405699', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (160.0, 84.0, 269.0, 104.0)}, {'text': 'TAX INVDICE', 'confidence': 0.93357, 'lang': 'en', 'bounding_box': (164.0, 106.0, 274.0, 121.0)}, {'text': 'RN:104645729500013', 'confidence': 0.98884, 'lang': 'en', 'bounding_box': (169.0, 119.0, 277.0, 136.0)}, {'text': 'onle :79 21-2026 09.4E', 'confidence': 0.68784, 'lang': 'en', 'bounding_box': (111.0, 147.0, 210.0, 161.0)}, {'text': 'D:11 Nu:104', 'confidence': 0.7406, 'lang': 'en', 'bounding_box': (110.0, 160.0, 158.0, 174.0)}, {'text': 'Pos Mece: Posi', 'confidence': 0.77669, 'lang': 'en', 'bounding_box': (220.0, 158.0, 282.0, 174.0)}, {'text': 'Uter l0: 99', 'confidence': 0.8463, 'lang': 'en', 'bounding_box': (111.0, 174.0, 161.0, 188.0)}, {'text': 'Dascription', 'confidence': 0.95442, 'lang': 'en', 'bounding_box': (110.0, 203.0, 171.0, 217.0)}, {'text': 'Qty', 'confidence': 0.99971, 'lang': 'en', 'bounding_box': (258.0, 202.0, 277.0, 216.0)}, {'text': 'Amount', 'confidence': 0.95443, 'lang': 'en', 'bounding_box': (288.0, 200.0, 322.0, 215.0)}, {'text': '9965950000000', 'confidence': 0.95618, 'lang': 'en', 'bounding_box': (110.0, 229.0, 181.0, 245.0)}, {'text': 'CURIANDER LEAF', 'confidence': 0.98443, 'lang': 'en', 'bounding_box': (110.0, 244.0, 185.0, 258.0)}, {'text': '2,00', 'confidence': 0.9322, 'lang': 'en', 'bounding_box': (251.0, 241.0, 277.0, 256.0)}, {'text': '1.98', 'confidence': 0.99946, 'lang': 'en', 'bounding_box': (304.0, 240.0, 329.0, 256.0)}, {'text': '9988002000000', 'confidence': 0.98444, 'lang': 'en', 'bounding_box': (110.0, 257.0, 181.0, 271.0)}, {'text': 'ONION (INDTA)', 'confidence': 0.9556, 'lang': 'en', 'bounding_box': (110.0, 270.0, 180.0, 284.0)}, {'text': '1.06', 'confidence': 0.99775, 'lang': 'en', 'bounding_box': (252.0, 269.0, 277.0, 284.0)}, {'text': '3.70', 'confidence': 0.99985, 'lang': 'en', 'bounding_box': (303.0, 267.0, 329.0, 283.0)}, {'text': '6291044111119', 'confidence': 0.99496, 'lang': 'en', 'bounding_box': (110.0, 284.0, 180.0, 298.0)}, {'text': 'SAFA YOGHURT 10KG', 'confidence': 0.976, 'lang': 'en', 'bounding_box': (110.0, 297.0, 201.0, 312.0)}, {'text': '1.00', 'confidence': 0.98414, 'lang': 'en', 'bounding_box': (253.0, 295.0, 277.0, 311.0)}, {'text': '38 00', 'confidence': 0.8721, 'lang': 'en', 'bounding_box': (298.0, 294.0, 329.0, 311.0)}, {'text': '9988016000000', 'confidence': 0.96896, 'lang': 'en', 'bounding_box': (110.0, 310.0, 181.0, 326.0)}, {'text': 'GINGER (PRC)', 'confidence': 0.99719, 'lang': 'en', 'bounding_box': (110.0, 324.0, 175.0, 340.0)}, {'text': '0.53', 'confidence': 0.99994, 'lang': 'en', 'bounding_box': (252.0, 322.0, 277.0, 338.0)}, {'text': '4.50', 'confidence': 0.99978, 'lang': 'en', 'bounding_box': (303.0, 322.0, 329.0, 337.0)}, {'text': '9989943000000', 'confidence': 0.95554, 'lang': 'en', 'bounding_box': (110.0, 337.0, 180.0, 353.0)}, {'text': 'CURRY LEAF', 'confidence': 0.99894, 'lang': 'en', 'bounding_box': (109.0, 351.0, 164.0, 367.0)}, {'text': '1.00', 'confidence': 0.91387, 'lang': 'en', 'bounding_box': (252.0, 350.0, 277.0, 365.0)}, {'text': '1.00', 'confidence': 0.92168, 'lang': 'en', 'bounding_box': (304.0, 350.0, 329.0, 365.0)}, {'text': 'DAQ-5000-BLUE RINE', 'confidence': 0.95176, 'lang': 'en', 'bounding_box': (111.0, 378.0, 208.0, 394.0)}, {'text': 'Qly: 5.59', 'confidence': 0.90789, 'lang': 'en', 'bounding_box': (108.0, 406.0, 160.0, 422.0)}, {'text': 'Rouncing:', 'confidence': 0.90363, 'lang': 'en', 'bounding_box': (210.0, 419.0, 261.0, 435.0)}, {'text': '0.07', 'confidence': 0.99944, 'lang': 'en', 'bounding_box': (303.0, 420.0, 328.0, 433.0)}, {'text': 'B111 Amount:', 'confidence': 0.89497, 'lang': 'en', 'bounding_box': (170.0, 433.0, 263.0, 446.0)}, {'text': '49.25', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (286.0, 432.0, 328.0, 446.0)}, {'text': '49.25', 'confidence': 0.99571, 'lang': 'en', 'bounding_box': (335.0, 408.0, 423.0, 466.0)}, {'text': 'CASH:', 'confidence': 0.97055, 'lang': 'en', 'bounding_box': (225.0, 446.0, 259.0, 462.0)}, {'text': '49.25', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (298.0, 446.0, 328.0, 462.0)}, {'text': 'Anount to return :', 'confidence': 0.91842, 'lang': 'en', 'bounding_box': (166.0, 462.0, 259.0, 476.0)}, {'text': '0.00', 'confidence': 0.99811, 'lang': 'en', 'bounding_box': (302.0, 460.0, 329.0, 475.0)}, {'text': 'ATX', 'confidence': 0.71702, 'lang': 'en', 'bounding_box': (109.0, 488.0, 133.0, 503.0)}, {'text': 'Taxable Amount', 'confidence': 0.95242, 'lang': 'en', 'bounding_box': (161.0, 489.0, 234.0, 503.0)}, {'text': 'VAI', 'confidence': 0.96542, 'lang': 'en', 'bounding_box': (262.0, 489.0, 281.0, 503.0)}, {'text': 'Total', 'confidence': 0.99967, 'lang': 'en', 'bounding_box': (299.0, 488.0, 328.0, 503.0)}, {'text': '5%', 'confidence': 0.96452, 'lang': 'en', 'bounding_box': (108.0, 513.0, 124.0, 528.0)}, {'text': '4u.84', 'confidence': 0.83743, 'lang': 'en', 'bounding_box': (179.0, 510.0, 211.0, 529.0)}, {'text': '2.34 49.18', 'confidence': 0.96175, 'lang': 'en', 'bounding_box': (261.0, 512.0, 318.0, 528.0)}, {'text': 'Futp hill fai exchange.', 'confidence': 0.78899, 'lang': 'en', 'bounding_box': (171.0, 540.0, 261.0, 553.0)}, {'text': 'tend su far shopoing a pls cure àatn', 'confidence': 0.64016, 'lang': 'en', 'bounding_box': (140.0, 552.0, 300.0, 567.0)}, {'text': 'i taca befund', 'confidence': 0.58843, 'lang': 'en', 'bounding_box': (190.0, 566.0, 248.0, 579.0)}, {'text': '00020010420260729', 'confidence': 0.97236, 'lang': 'en', 'bounding_box': (177.0, 615.0, 262.0, 629.0)}, {'text': 'wwS', 'confidence': 0.51724, 'lang': 'ar', 'bounding_box': (189.0, 15.0, 232.0, 40.0)}, {'text': 'OAMAR AL MADINA', 'confidence': 0.98128, 'lang': 'ar', 'bounding_box': (149.0, 45.0, 278.0, 61.0)}, {'text': 'GUPERMARKETLL.C', 'confidence': 0.98627, 'lang': 'ar', 'bounding_box': (148.0, 59.0, 280.0, 75.0)}, {'text': 'New Haoyyu tha A Quow 1', 'confidence': 0.60502, 'lang': 'ar', 'bounding_box': (146.0, 73.0, 294.0, 87.0)}, {'text': '(0585405699', 'confidence': 0.98202, 'lang': 'ar', 'bounding_box': (160.0, 84.0, 269.0, 104.0)}, {'text': 'TAX INVDICE', 'confidence': 0.95058, 'lang': 'ar', 'bounding_box': (164.0, 106.0, 274.0, 121.0)}, {'text': 'RN: 1046457295000 13', 'confidence': 0.96531, 'lang': 'ar', 'bounding_box': (169.0, 119.0, 277.0, 136.0)}, {'text': 'vele 9 ual-c026 09.4t', 'confidence': 0.69183, 'lang': 'ar', 'bounding_box': (111.0, 147.0, 210.0, 161.0)}, {'text': '31T1 Nu104', 'confidence': 0.76678, 'lang': 'ar', 'bounding_box': (110.0, 160.0, 158.0, 174.0)}, {'text': 'PiS leve: P9S2', 'confidence': 0.69377, 'lang': 'ar', 'bounding_box': (220.0, 158.0, 282.0, 174.0)}, {'text': 'Uer l0: 99', 'confidence': 0.82856, 'lang': 'ar', 'bounding_box': (111.0, 174.0, 161.0, 188.0)}, {'text': 'Dascription', 'confidence': 0.96193, 'lang': 'ar', 'bounding_box': (110.0, 203.0, 171.0, 217.0)}, {'text': 'Qty', 'confidence': 0.99881, 'lang': 'ar', 'bounding_box': (258.0, 202.0, 277.0, 216.0)}, {'text': 'Anount', 'confidence': 0.90252, 'lang': 'ar', 'bounding_box': (288.0, 200.0, 322.0, 215.0)}, {'text': '330995006000', 'confidence': 0.84678, 'lang': 'ar', 'bounding_box': (110.0, 229.0, 181.0, 245.0)}, {'text': 'CURIANDER LEAF', 'confidence': 0.94877, 'lang': 'ar', 'bounding_box': (110.0, 244.0, 185.0, 258.0)}, {'text': '2,00', 'confidence': 0.89941, 'lang': 'ar', 'bounding_box': (251.0, 241.0, 277.0, 256.0)}, {'text': '1.98', 'confidence': 0.97993, 'lang': 'ar', 'bounding_box': (304.0, 240.0, 329.0, 256.0)}, {'text': '9983002000000', 'confidence': 0.95, 'lang': 'ar', 'bounding_box': (110.0, 257.0, 181.0, 271.0)}, {'text': 'ONTON INDTA)', 'confidence': 0.93146, 'lang': 'ar', 'bounding_box': (110.0, 270.0, 180.0, 284.0)}, {'text': '1.0b', 'confidence': 0.88373, 'lang': 'ar', 'bounding_box': (252.0, 269.0, 277.0, 284.0)}, {'text': '3.70', 'confidence': 0.99968, 'lang': 'ar', 'bounding_box': (303.0, 267.0, 329.0, 283.0)}, {'text': '6291041111119', 'confidence': 0.94489, 'lang': 'ar', 'bounding_box': (110.0, 284.0, 180.0, 298.0)}, {'text': 'S4FA YOGHURT 10KG', 'confidence': 0.92649, 'lang': 'ar', 'bounding_box': (110.0, 297.0, 201.0, 312.0)}, {'text': '1.00', 'confidence': 0.99081, 'lang': 'ar', 'bounding_box': (253.0, 295.0, 277.0, 311.0)}, {'text': '38 00', 'confidence': 0.96219, 'lang': 'ar', 'bounding_box': (298.0, 294.0, 329.0, 311.0)}, {'text': '99580 1600000', 'confidence': 0.86584, 'lang': 'ar', 'bounding_box': (110.0, 310.0, 181.0, 326.0)}, {'text': 'GINGER (PRC)', 'confidence': 0.95908, 'lang': 'ar', 'bounding_box': (110.0, 324.0, 175.0, 340.0)}, {'text': '0.53', 'confidence': 0.99821, 'lang': 'ar', 'bounding_box': (252.0, 322.0, 277.0, 338.0)}, {'text': '4.50', 'confidence': 0.99198, 'lang': 'ar', 'bounding_box': (303.0, 322.0, 329.0, 337.0)}, {'text': '9989943000000', 'confidence': 0.9342, 'lang': 'ar', 'bounding_box': (110.0, 337.0, 180.0, 353.0)}, {'text': 'CURRY LLEAF', 'confidence': 0.96481, 'lang': 'ar', 'bounding_box': (109.0, 351.0, 164.0, 367.0)}, {'text': '1.00', 'confidence': 0.97008, 'lang': 'ar', 'bounding_box': (252.0, 350.0, 277.0, 365.0)}, {'text': '1.00', 'confidence': 0.96095, 'lang': 'ar', 'bounding_box': (304.0, 350.0, 329.0, 365.0)}, {'text': 'LAQ-5000-BLUL RINE', 'confidence': 0.95623, 'lang': 'ar', 'bounding_box': (111.0, 378.0, 208.0, 394.0)}, {'text': 'Gly: 5.59', 'confidence': 0.92219, 'lang': 'ar', 'bounding_box': (108.0, 406.0, 160.0, 422.0)}, {'text': 'Rouncing:', 'confidence': 0.88556, 'lang': 'ar', 'bounding_box': (210.0, 419.0, 261.0, 435.0)}, {'text': '0.07', 'confidence': 0.9995, 'lang': 'ar', 'bounding_box': (303.0, 420.0, 328.0, 433.0)}, {'text': 'B1l1 Amount:', 'confidence': 0.80566, 'lang': 'ar', 'bounding_box': (170.0, 433.0, 263.0, 446.0)}, {'text': '49.25', 'confidence': 0.99955, 'lang': 'ar', 'bounding_box': (286.0, 432.0, 328.0, 446.0)}, {'text': '49125', 'confidence': 0.85351, 'lang': 'ar', 'bounding_box': (335.0, 408.0, 423.0, 466.0)}, {'text': 'CASH', 'confidence': 0.98748, 'lang': 'ar', 'bounding_box': (225.0, 446.0, 259.0, 462.0)}, {'text': '49.25', 'confidence': 0.99858, 'lang': 'ar', 'bounding_box': (298.0, 446.0, 328.0, 462.0)}, {'text': 'Anount to return :', 'confidence': 0.88335, 'lang': 'ar', 'bounding_box': (166.0, 462.0, 259.0, 476.0)}, {'text': '0.00', 'confidence': 0.91754, 'lang': 'ar', 'bounding_box': (302.0, 460.0, 329.0, 475.0)}, {'text': 'VATX', 'confidence': 0.55017, 'lang': 'ar', 'bounding_box': (109.0, 488.0, 133.0, 503.0)}, {'text': 'Taxabie Amount', 'confidence': 0.87046, 'lang': 'ar', 'bounding_box': (161.0, 489.0, 234.0, 503.0)}, {'text': 'VAI', 'confidence': 0.80619, 'lang': 'ar', 'bounding_box': (262.0, 489.0, 281.0, 503.0)}, {'text': 'Total', 'confidence': 0.99366, 'lang': 'ar', 'bounding_box': (299.0, 488.0, 328.0, 503.0)}, {'text': '5X', 'confidence': 0.83602, 'lang': 'ar', 'bounding_box': (108.0, 513.0, 124.0, 528.0)}, {'text': '4t.14', 'confidence': 0.73488, 'lang': 'ar', 'bounding_box': (179.0, 510.0, 211.0, 529.0)}, {'text': '2.34 49.18', 'confidence': 0.92611, 'lang': 'ar', 'bounding_box': (261.0, 512.0, 318.0, 528.0)}, {'text': 'Febp hill tar cochaange.', 'confidence': 0.74633, 'lang': 'ar', 'bounding_box': (171.0, 540.0, 261.0, 553.0)}, {'text': 'Hnk riu for chooig a ps cure unha', 'confidence': 0.58259, 'lang': 'ar', 'bounding_box': (140.0, 552.0, 300.0, 567.0)}, {'text': 'tn Laci Heftol', 'confidence': 0.59607, 'lang': 'ar', 'bounding_box': (190.0, 566.0, 248.0, 579.0)}, {'text': '0002001042020729', 'confidence': 0.96598, 'lang': 'ar', 'bounding_box': (177.0, 615.0, 262.0, 629.0)}], 'field_confidence': {'vendor': 0.262557493926868, 'date': 0.0, 'currency': 0.0, 'amount': 0.9595016224165341, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8563890906200318, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.9595016224165341, 'invoice_number': 0.4775789658187599, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_rate', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
WS
OAMAR AL MADINA
SUPERMARKETL.L.C
N y y t Al ( As
0585405699
TAX INVDICE
RN:104645729500013
onle :79 21-2026 09.4E
D:11 Nu:104
Pos Mece: Posi
Uter l0: 99
Dascription
Qty
Amount
9965950000000
CURIANDER LEAF
2,00
1.98
9988002000000
ONION (INDTA)
1.06
3.70
6291044111119
SAFA YOGHURT 10KG
1.00
38 00
9988016000000
GINGER (PRC)
0.53
4.50
9989943000000
CURRY LEAF
1.00
1.00
DAQ-5000-BLUE RINE
Qly: 5.59
Rouncing:
0.07
B111 Amount:
49.25
49.25
CASH:
49.25
Anount to return :
0.00
ATX
Taxable Amount
VAI
Total
5%
4u.84
2.34 49.18
Futp hill fai exchange.
tend su far shopoing a pls cure àatn
i taca befund
00020010420260729
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
wwS
OAMAR AL MADINA
GUPERMARKETLL.C
New Haoyyu tha A Quow 1
(0585405699
TAX INVDICE
RN: 1046457295000 13
vele 9 ual-c026 09.4t
31T1 Nu104
PiS leve: P9S2
Uer l0: 99
Dascription
Qty
Anount
330995006000
CURIANDER LEAF
2,00
1.98
9983002000000
ONTON INDTA)
1.0b
3.70
6291041111119
S4FA YOGHURT 10KG
1.00
38 00
99580 1600000
GINGER (PRC)
0.53
4.50
9989943000000
CURRY LLEAF
1.00
1.00
LAQ-5000-BLUL RINE
Gly: 5.59
Rouncing:
0.07
B1l1 Amount:
49.25
49125
CASH
49.25
Anount to return :
0.00
VATX
Taxabie Amount
VAI
Total
5X
4t.14
2.34 49.18
Febp hill tar cochaange.
Hnk riu for chooig a ps cure unha
tn Laci Heftol
0002001042020729
```

## image (4).png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'M.S OAMAR AL MADINA', 'expense_type': None, 'amount': 45.21, 'vat_amount': 45.21, 'total_amount': 90.42, 'currency': None, 'date': '', 'confidence': 0.24, 'field_confidence': {'vendor': 0.2891666666666667, 'date': 0.0, 'currency': 0.0, 'amount': 0.8306690952380952, 'vat_rate': 0.645431, 'vat_amount': 0.8306690952380952, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8532488095238094, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.4, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'M.S OAMAR AL MADINA', 'confidence': 0.2891666666666667, 'evidence': 'M.S OAMAR AL MADINA', 'signals': ['top_of_receipt', 'multiline_header_merge', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 45.21, 'confidence': 0.8306690952380952, 'evidence': '5% 45.21 2.28 47.49', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'near_percent_marker', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.645431, 'evidence': '5% 45.21 2.28 47.49', 'signals': ['vat_tax_amount_label', 'percent_marker', 'known_vat_rate', 'format_known_vat_rate'], 'low': False}, 'vat_amount': {'value': 45.21, 'confidence': 0.8306690952380952, 'evidence': '5% 45.21 2.28 47.49', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'near_percent_marker', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 47.5, 'confidence': 0.8532488095238094, 'evidence': 'CASH 4/.50 47.50', 'signals': ['cash_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 90.42, 'confidence': 0.4, 'evidence': 'derived: 5% 45.21 2.28 47.49', 'signals': ['derived_arithmetic'], 'low': True, 'warning': 'derived_value'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'M.S\nOAMAR AL MADINA\nSUPERMARKETL.L.C\nNew Hunayya Urmo Al Quwuin-UAE\nNew Hy U Al roun-LAE\n0585405699\nTAX INVOICE\nRN: 104645729500003\npote :05-fug-202% 10:59\nf111 Mo:152\nB111 06:152\nPOS Hene; POS2\nPaS Hene: PUs2\nUser ID: 99\nUEBY TD: 9)\nDescription\nBescrtpt lon\nQty Anont\n9988948000000\n999894100000\nCURRY LEAF\nCIIRPY LEAF\n1.00 1.00\n9988949000000\nMINT LEAF\n2.0) 2.00\n9988002000000\n996800200060\nONTON (INDIA)\nONEON (INDLA)\n1.00 3.49\n9981893000000\n998889 300000\nCHELLY SMALL\n0.16 2.01\n9988950000000\nCORIANDER LEAI\nCOREANDER 1EA]\n1.00 0.99\n6291044111:19\nSAFA YOGHURI 10RG 1.0) 38.\nSAFA MOGHURL TORG 1.0) 38.50\nUAQ-5GOO-BLUE RINE\nDAQ -5000-BLUL RINE\nQiy: b.16\nQ1y: 6.16\nRouncing 0.01\nB111 Anount 47.50\nCASH 4/.50 47.50\nSnount ta return 0.00\nVATN Taxable Amount VAT Ttta\n5% 45.21 2.28 47.49\nREE: b li a epivange\nWEES D 1 "Or NxNge\n)a for chorutng ani sis core Asay\nSu for thury thi an2 +is core 4g9\nNo cmen + ctand\nNo LBon -ctend\n00020016220235806\nb00200142523506', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'M.S', 'confidence': 0.97864, 'lang': 'en', 'bounding_box': (137.0, 24.0, 166.0, 42.0)}, {'text': 'OAMAR AL MADINA', 'confidence': 0.97306, 'lang': 'en', 'bounding_box': (89.0, 50.0, 215.0, 67.0)}, {'text': 'SUPERMARKETL.L.C', 'confidence': 0.96927, 'lang': 'en', 'bounding_box': (88.0, 64.0, 217.0, 81.0)}, {'text': 'New Hunayya Urmo Al Quwuin-UAE', 'confidence': 0.79054, 'lang': 'en', 'bounding_box': (85.0, 79.0, 232.0, 94.0)}, {'text': '0585405699', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (102.0, 92.0, 206.0, 110.0)}, {'text': 'TAX INVOICE', 'confidence': 0.99508, 'lang': 'en', 'bounding_box': (104.0, 114.0, 214.0, 130.0)}, {'text': 'RN: 104645729500003', 'confidence': 0.96712, 'lang': 'en', 'bounding_box': (110.0, 129.0, 214.0, 146.0)}, {'text': 'pote :05-fug-202% 10:59', 'confidence': 0.89711, 'lang': 'en', 'bounding_box': (53.0, 157.0, 149.0, 170.0)}, {'text': 'f111 Mo:152', 'confidence': 0.82267, 'lang': 'en', 'bounding_box': (54.0, 169.0, 98.0, 179.0)}, {'text': 'POS Hene; POS2', 'confidence': 0.7557, 'lang': 'en', 'bounding_box': (160.0, 167.0, 218.0, 179.0)}, {'text': 'User ID: 99', 'confidence': 0.6663, 'lang': 'en', 'bounding_box': (54.0, 179.0, 102.0, 190.0)}, {'text': 'Description', 'confidence': 0.9288, 'lang': 'en', 'bounding_box': (53.0, 203.0, 113.0, 218.0)}, {'text': 'Qty', 'confidence': 0.99951, 'lang': 'en', 'bounding_box': (195.0, 202.0, 215.0, 217.0)}, {'text': 'Anonnt', 'confidence': 0.62869, 'lang': 'en', 'bounding_box': (225.0, 204.0, 257.0, 217.0)}, {'text': '9988948000000', 'confidence': 0.99142, 'lang': 'en', 'bounding_box': (53.0, 229.0, 122.0, 243.0)}, {'text': 'CURRY LEAF', 'confidence': 0.98815, 'lang': 'en', 'bounding_box': (54.0, 242.0, 105.0, 256.0)}, {'text': '1.00', 'confidence': 0.99512, 'lang': 'en', 'bounding_box': (191.0, 240.0, 215.0, 254.0)}, {'text': '1.00', 'confidence': 0.99688, 'lang': 'en', 'bounding_box': (240.0, 241.0, 264.0, 255.0)}, {'text': '9988949000000', 'confidence': 0.99743, 'lang': 'en', 'bounding_box': (53.0, 254.0, 122.0, 269.0)}, {'text': 'MINT LEAF', 'confidence': 0.99188, 'lang': 'en', 'bounding_box': (52.0, 268.0, 101.0, 284.0)}, {'text': '2.00', 'confidence': 0.86585, 'lang': 'en', 'bounding_box': (190.0, 265.0, 215.0, 282.0)}, {'text': '2.00', 'confidence': 0.92491, 'lang': 'en', 'bounding_box': (239.0, 268.0, 264.0, 282.0)}, {'text': '9988002000000', 'confidence': 0.91203, 'lang': 'en', 'bounding_box': (53.0, 281.0, 121.0, 296.0)}, {'text': 'ONTON (INDIA)', 'confidence': 0.95968, 'lang': 'en', 'bounding_box': (53.0, 294.0, 121.0, 309.0)}, {'text': '1.00', 'confidence': 0.99934, 'lang': 'en', 'bounding_box': (191.0, 292.0, 215.0, 307.0)}, {'text': '3.49', 'confidence': 0.99985, 'lang': 'en', 'bounding_box': (239.0, 294.0, 263.0, 308.0)}, {'text': '9981893000000', 'confidence': 0.94104, 'lang': 'en', 'bounding_box': (54.0, 307.0, 122.0, 322.0)}, {'text': 'CHELLY SMALL', 'confidence': 0.92369, 'lang': 'en', 'bounding_box': (54.0, 320.0, 114.0, 334.0)}, {'text': '0.16', 'confidence': 0.99911, 'lang': 'en', 'bounding_box': (190.0, 318.0, 214.0, 332.0)}, {'text': '2.01', 'confidence': 0.89596, 'lang': 'en', 'bounding_box': (239.0, 320.0, 262.0, 333.0)}, {'text': '9988950000000', 'confidence': 0.9851, 'lang': 'en', 'bounding_box': (54.0, 332.0, 121.0, 344.0)}, {'text': 'CORIANDER LEAI', 'confidence': 0.79902, 'lang': 'en', 'bounding_box': (53.0, 344.0, 124.0, 357.0)}, {'text': '1.00', 'confidence': 0.99279, 'lang': 'en', 'bounding_box': (190.0, 342.0, 214.0, 357.0)}, {'text': '0.99', 'confidence': 0.81702, 'lang': 'en', 'bounding_box': (239.0, 343.0, 264.0, 357.0)}, {'text': '6291044111:19', 'confidence': 0.97203, 'lang': 'en', 'bounding_box': (53.0, 356.0, 122.0, 370.0)}, {'text': 'SAFA YOGHURI 10RG', 'confidence': 0.85746, 'lang': 'en', 'bounding_box': (53.0, 368.0, 142.0, 383.0)}, {'text': '1.0)', 'confidence': 0.97331, 'lang': 'en', 'bounding_box': (191.0, 368.0, 215.0, 382.0)}, {'text': '38.', 'confidence': 0.81404, 'lang': 'en', 'bounding_box': (237.0, 368.0, 264.0, 382.0)}, {'text': 'UAQ-5GOO-BLUE RINE', 'confidence': 0.8525, 'lang': 'en', 'bounding_box': (55.0, 394.0, 147.0, 409.0)}, {'text': 'Qiy: b.16', 'confidence': 0.84778, 'lang': 'en', 'bounding_box': (53.0, 420.0, 102.0, 435.0)}, {'text': 'Rouncing:', 'confidence': 0.96432, 'lang': 'en', 'bounding_box': (151.0, 433.0, 198.0, 448.0)}, {'text': '0.01', 'confidence': 0.98236, 'lang': 'en', 'bounding_box': (239.0, 433.0, 261.0, 446.0)}, {'text': 'Bi11 Anount:', 'confidence': 0.89255, 'lang': 'en', 'bounding_box': (112.0, 446.0, 201.0, 459.0)}, {'text': 'CASH:', 'confidence': 0.9415, 'lang': 'en', 'bounding_box': (165.0, 458.0, 199.0, 473.0)}, {'text': '47.50', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (222.0, 445.0, 262.0, 458.0)}, {'text': '4/.50', 'confidence': 0.98009, 'lang': 'en', 'bounding_box': (234.0, 458.0, 263.0, 472.0)}, {'text': '47.50', 'confidence': 0.99903, 'lang': 'en', 'bounding_box': (279.0, 454.0, 350.0, 487.0)}, {'text': 'Snount ta return :', 'confidence': 0.87176, 'lang': 'en', 'bounding_box': (109.0, 470.0, 198.0, 486.0)}, {'text': '0.00', 'confidence': 0.99574, 'lang': 'en', 'bounding_box': (237.0, 469.0, 263.0, 485.0)}, {'text': 'VATN', 'confidence': 0.88461, 'lang': 'en', 'bounding_box': (52.0, 496.0, 76.0, 511.0)}, {'text': 'Taxable Amount', 'confidence': 0.94645, 'lang': 'en', 'bounding_box': (105.0, 496.0, 174.0, 510.0)}, {'text': 'VAT', 'confidence': 0.99953, 'lang': 'en', 'bounding_box': (201.0, 497.0, 218.0, 510.0)}, {'text': 'Ttta', 'confidence': 0.77566, 'lang': 'en', 'bounding_box': (234.0, 496.0, 258.0, 511.0)}, {'text': '5%', 'confidence': 0.96954, 'lang': 'en', 'bounding_box': (52.0, 520.0, 66.0, 533.0)}, {'text': '45.21', 'confidence': 0.99969, 'lang': 'en', 'bounding_box': (121.0, 518.0, 150.0, 534.0)}, {'text': '2.28 47.49', 'confidence': 0.97241, 'lang': 'en', 'bounding_box': (200.0, 519.0, 253.0, 534.0)}, {'text': 'REE: b li a epivange', 'confidence': 0.57574, 'lang': 'en', 'bounding_box': (112.0, 544.0, 198.0, 558.0)}, {'text': ')a for chorutng ani sis core Asay', 'confidence': 0.67106, 'lang': 'en', 'bounding_box': (110.0, 558.0, 233.0, 570.0)}, {'text': 'No cmen + ctand', 'confidence': 0.66424, 'lang': 'en', 'bounding_box': (131.0, 571.0, 188.0, 582.0)}, {'text': '00020016220235806', 'confidence': 0.80742, 'lang': 'en', 'bounding_box': (119.0, 617.0, 200.0, 630.0)}, {'text': 'M.S', 'confidence': 0.90328, 'lang': 'ar', 'bounding_box': (137.0, 24.0, 166.0, 42.0)}, {'text': 'OAMAR AL MADINA', 'confidence': 0.98515, 'lang': 'ar', 'bounding_box': (89.0, 50.0, 215.0, 67.0)}, {'text': 'SUPERMARKETLL.C', 'confidence': 0.95607, 'lang': 'ar', 'bounding_box': (88.0, 64.0, 217.0, 81.0)}, {'text': 'New Hy U Al roun-LAE', 'confidence': 0.68113, 'lang': 'ar', 'bounding_box': (85.0, 79.0, 232.0, 94.0)}, {'text': '0585405699', 'confidence': 0.99962, 'lang': 'ar', 'bounding_box': (102.0, 92.0, 206.0, 110.0)}, {'text': 'TAX TNVOICE', 'confidence': 0.95731, 'lang': 'ar', 'bounding_box': (104.0, 114.0, 214.0, 130.0)}, {'text': 'RN: 104645729500003', 'confidence': 0.97926, 'lang': 'ar', 'bounding_box': (110.0, 129.0, 214.0, 146.0)}, {'text': 'pete :05-fu9-202% 10:59', 'confidence': 0.8612, 'lang': 'ar', 'bounding_box': (53.0, 157.0, 149.0, 170.0)}, {'text': 'B111 06:152', 'confidence': 0.70056, 'lang': 'ar', 'bounding_box': (54.0, 169.0, 98.0, 179.0)}, {'text': 'PaS Hene: PUs2', 'confidence': 0.83831, 'lang': 'ar', 'bounding_box': (160.0, 167.0, 218.0, 179.0)}, {'text': 'UEBY TD: 9)', 'confidence': 0.72626, 'lang': 'ar', 'bounding_box': (54.0, 179.0, 102.0, 190.0)}, {'text': 'Bescrtpt lon', 'confidence': 0.80309, 'lang': 'ar', 'bounding_box': (53.0, 203.0, 113.0, 218.0)}, {'text': 'Qty', 'confidence': 0.99906, 'lang': 'ar', 'bounding_box': (195.0, 202.0, 215.0, 217.0)}, {'text': 'Anont', 'confidence': 0.84547, 'lang': 'ar', 'bounding_box': (225.0, 204.0, 257.0, 217.0)}, {'text': '999894100000', 'confidence': 0.88771, 'lang': 'ar', 'bounding_box': (53.0, 229.0, 122.0, 243.0)}, {'text': 'CIIRPY LEAF', 'confidence': 0.82435, 'lang': 'ar', 'bounding_box': (54.0, 242.0, 105.0, 256.0)}, {'text': '1.00', 'confidence': 0.92707, 'lang': 'ar', 'bounding_box': (191.0, 240.0, 215.0, 254.0)}, {'text': '1.00', 'confidence': 0.861, 'lang': 'ar', 'bounding_box': (240.0, 241.0, 264.0, 255.0)}, {'text': '9988949000000', 'confidence': 0.9908, 'lang': 'ar', 'bounding_box': (53.0, 254.0, 122.0, 269.0)}, {'text': 'MINT LEAF', 'confidence': 0.96383, 'lang': 'ar', 'bounding_box': (52.0, 268.0, 101.0, 284.0)}, {'text': '2.0)', 'confidence': 0.94536, 'lang': 'ar', 'bounding_box': (190.0, 265.0, 215.0, 282.0)}, {'text': '2.00', 'confidence': 0.91107, 'lang': 'ar', 'bounding_box': (239.0, 268.0, 264.0, 282.0)}, {'text': '996800200060', 'confidence': 0.86853, 'lang': 'ar', 'bounding_box': (53.0, 281.0, 121.0, 296.0)}, {'text': 'ONEON (INDLA)', 'confidence': 0.792, 'lang': 'ar', 'bounding_box': (53.0, 294.0, 121.0, 309.0)}, {'text': '1.00', 'confidence': 0.98341, 'lang': 'ar', 'bounding_box': (191.0, 292.0, 215.0, 307.0)}, {'text': '3.49', 'confidence': 0.99956, 'lang': 'ar', 'bounding_box': (239.0, 294.0, 263.0, 308.0)}, {'text': '998889 300000', 'confidence': 0.92678, 'lang': 'ar', 'bounding_box': (54.0, 307.0, 122.0, 322.0)}, {'text': 'CHILLY SMALL', 'confidence': 0.89704, 'lang': 'ar', 'bounding_box': (54.0, 320.0, 114.0, 334.0)}, {'text': '0.16', 'confidence': 0.99753, 'lang': 'ar', 'bounding_box': (190.0, 318.0, 214.0, 332.0)}, {'text': '2.01', 'confidence': 0.84759, 'lang': 'ar', 'bounding_box': (239.0, 320.0, 262.0, 333.0)}, {'text': '9288950000000', 'confidence': 0.79318, 'lang': 'ar', 'bounding_box': (54.0, 332.0, 121.0, 344.0)}, {'text': 'COREANDER 1EA]', 'confidence': 0.82893, 'lang': 'ar', 'bounding_box': (53.0, 344.0, 124.0, 357.0)}, {'text': '1.00', 'confidence': 0.9569, 'lang': 'ar', 'bounding_box': (190.0, 342.0, 214.0, 357.0)}, {'text': '0.99', 'confidence': 0.9597, 'lang': 'ar', 'bounding_box': (239.0, 343.0, 264.0, 357.0)}, {'text': '629104411119', 'confidence': 0.95007, 'lang': 'ar', 'bounding_box': (53.0, 356.0, 122.0, 370.0)}, {'text': 'SAFA MOGHURL TORG', 'confidence': 0.77352, 'lang': 'ar', 'bounding_box': (53.0, 368.0, 142.0, 383.0)}, {'text': '1.0)', 'confidence': 0.97333, 'lang': 'ar', 'bounding_box': (191.0, 368.0, 215.0, 382.0)}, {'text': '38.50', 'confidence': 0.79027, 'lang': 'ar', 'bounding_box': (237.0, 368.0, 264.0, 382.0)}, {'text': 'DAQ -5000-BLUL RINE', 'confidence': 0.8719, 'lang': 'ar', 'bounding_box': (55.0, 394.0, 147.0, 409.0)}, {'text': 'Q1y: 6.16', 'confidence': 0.92431, 'lang': 'ar', 'bounding_box': (53.0, 420.0, 102.0, 435.0)}, {'text': 'Rouncing:', 'confidence': 0.91167, 'lang': 'ar', 'bounding_box': (151.0, 433.0, 198.0, 448.0)}, {'text': '0.01', 'confidence': 0.86529, 'lang': 'ar', 'bounding_box': (239.0, 433.0, 261.0, 446.0)}, {'text': 'B111 Anount:', 'confidence': 0.93294, 'lang': 'ar', 'bounding_box': (112.0, 446.0, 201.0, 459.0)}, {'text': 'CASH:', 'confidence': 0.77919, 'lang': 'ar', 'bounding_box': (165.0, 458.0, 199.0, 473.0)}, {'text': '47.50', 'confidence': 0.99929, 'lang': 'ar', 'bounding_box': (222.0, 445.0, 262.0, 458.0)}, {'text': '47.50', 'confidence': 0.90322, 'lang': 'ar', 'bounding_box': (234.0, 458.0, 263.0, 472.0)}, {'text': '47.50', 'confidence': 0.97516, 'lang': 'ar', 'bounding_box': (279.0, 454.0, 350.0, 487.0)}, {'text': 'amout ta return :', 'confidence': 0.82042, 'lang': 'ar', 'bounding_box': (109.0, 470.0, 198.0, 486.0)}, {'text': '0.00', 'confidence': 0.92713, 'lang': 'ar', 'bounding_box': (237.0, 469.0, 263.0, 485.0)}, {'text': 'VATN', 'confidence': 0.81141, 'lang': 'ar', 'bounding_box': (52.0, 496.0, 76.0, 511.0)}, {'text': 'Taxable Amcunt', 'confidence': 0.89771, 'lang': 'ar', 'bounding_box': (105.0, 496.0, 174.0, 510.0)}, {'text': 'VAT', 'confidence': 0.9958, 'lang': 'ar', 'bounding_box': (201.0, 497.0, 218.0, 510.0)}, {'text': 'T:.ta', 'confidence': 0.74668, 'lang': 'ar', 'bounding_box': (234.0, 496.0, 258.0, 511.0)}, {'text': '51', 'confidence': 0.87407, 'lang': 'ar', 'bounding_box': (52.0, 520.0, 66.0, 533.0)}, {'text': '45.21', 'confidence': 0.99323, 'lang': 'ar', 'bounding_box': (121.0, 518.0, 150.0, 534.0)}, {'text': '2.28 47.49', 'confidence': 0.986, 'lang': 'ar', 'bounding_box': (200.0, 519.0, 253.0, 534.0)}, {'text': 'WEES D 1 "Or NxNge', 'confidence': 0.56597, 'lang': 'ar', 'bounding_box': (112.0, 544.0, 198.0, 558.0)}, {'text': 'Su for thury thi an2 +is core 4g9', 'confidence': 0.68825, 'lang': 'ar', 'bounding_box': (110.0, 558.0, 233.0, 570.0)}, {'text': 'No LBon -ctend', 'confidence': 0.6628, 'lang': 'ar', 'bounding_box': (131.0, 571.0, 188.0, 582.0)}, {'text': 'b00200142523506', 'confidence': 0.65197, 'lang': 'ar', 'bounding_box': (119.0, 617.0, 200.0, 630.0)}], 'field_confidence': {'vendor': 0.2891666666666667, 'date': 0.0, 'currency': 0.0, 'amount': 0.8306690952380952, 'vat_rate': 0.645431, 'vat_amount': 0.8306690952380952, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8532488095238094, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.4, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
M.S
OAMAR AL MADINA
SUPERMARKETL.L.C
New Hunayya Urmo Al Quwuin-UAE
0585405699
TAX INVOICE
RN: 104645729500003
pote :05-fug-202% 10:59
f111 Mo:152
POS Hene; POS2
User ID: 99
Description
Qty
Anonnt
9988948000000
CURRY LEAF
1.00
1.00
9988949000000
MINT LEAF
2.00
2.00
9988002000000
ONTON (INDIA)
1.00
3.49
9981893000000
CHELLY SMALL
0.16
2.01
9988950000000
CORIANDER LEAI
1.00
0.99
6291044111:19
SAFA YOGHURI 10RG
1.0)
38.
UAQ-5GOO-BLUE RINE
Qiy: b.16
Rouncing:
0.01
Bi11 Anount:
CASH:
47.50
4/.50
47.50
Snount ta return :
0.00
VATN
Taxable Amount
VAT
Ttta
5%
45.21
2.28 47.49
REE: b li a epivange
)a for chorutng ani sis core Asay
No cmen + ctand
00020016220235806
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
M.S
OAMAR AL MADINA
SUPERMARKETLL.C
New Hy U Al roun-LAE
0585405699
TAX TNVOICE
RN: 104645729500003
pete :05-fu9-202% 10:59
B111 06:152
PaS Hene: PUs2
UEBY TD: 9)
Bescrtpt lon
Qty
Anont
999894100000
CIIRPY LEAF
1.00
1.00
9988949000000
MINT LEAF
2.0)
2.00
996800200060
ONEON (INDLA)
1.00
3.49
998889 300000
CHILLY SMALL
0.16
2.01
9288950000000
COREANDER 1EA]
1.00
0.99
629104411119
SAFA MOGHURL TORG
1.0)
38.50
DAQ -5000-BLUL RINE
Q1y: 6.16
Rouncing:
0.01
B111 Anount:
CASH:
47.50
47.50
47.50
amout ta return :
0.00
VATN
Taxable Amcunt
VAT
T:.ta
51
45.21
2.28 47.49
WEES D 1 "Or NxNge
Su for thury thi an2 +is core 4g9
No LBon -ctend
b00200142523506
```

## image (5).png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'Mob: 0528194512 QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.L E-mail: qomorolhude.Il@gmoil.com', 'expense_type': None, 'amount': 45.0, 'vat_amount': 2.25, 'total_amount': 47.25, 'currency': None, 'date': '', 'confidence': 0.26, 'field_confidence': {'vendor': 0.2628008135433071, 'date': 0.0, 'currency': 0.0, 'amount': 0.9660795354330708, 'vat_rate': 0.0, 'vat_amount': 1.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.8914019881889763, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Mob: 0528194512 QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.L E-mail: qomorolhude.Il@gmoil.com', 'confidence': 0.2628008135433071, 'evidence': 'Mob: 0528194512 QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.L E-mail: qomorolhude.Il@gmoil.com', 'signals': ['top_of_receipt', 'multiline_header_merge', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 45.0, 'confidence': 0.9660795354330708, 'evidence': 'Ra mil la gague 45.00', 'signals': ['subtotal_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 2.25, 'confidence': 1.0, 'evidence': 'TOTAL INCL VAT 2.25', 'signals': ['vat_tax_amount_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': 2.25, 'confidence': 0.8914019881889763, 'evidence': 'TOTAL INCL VAT 2.25', 'signals': ['card_label', 'same_row', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 47.25, 'confidence': 1.0, 'evidence': '47.25', 'signals': ['total_label', 'previous_line_label', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': "amar Alhuda √\namar Alhuda مر االهدى الجديد للتجارة العامة ذمم\nMob: 0528194512 QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.L\n0528194629 We are Dealing: Sanitary Wares, Plumbing, Electricals, Paints, Hardware, Plywoods & (JOTUN MULTI COLOUR CENTRE)\nE-mail: qomorolhude.Il@gmoil.com\nN:100340280500003 Werehot N0.7,76, 77, Op. A H, D P 1, el 971 4 0, +971 4 9 5545 TAX INVOICE\nN: 100340280500003 Wr . k,T +4 الفاتورة الضريببة\nall kinds of Building Materials\nyor\nBLUE RHINE INDUSTRIES LLC\nPLOT NO 597673 SER-BR//65\nDetivery Note\nInvoice No.\nDelivery Note Date\nDate\nPO BOX 114001\ntoihle rne Pv\nToer THN Pv\nDUBAL, UAE\nBuyer's Order No.\nSupplier's Rief.\nSupplier's Her.\nDated\nMode/Terma of Payment\n1000112464M6058\nاللفاسيل100011246\nDescription\nQuantity Unit Rate ill\nQuantity Unit Rate مستغ بون الضرية الضرية مبتخ الضريبة مبلخ مع الضريبة\nL duagll 1\nالكمبة الوحدة السر\nAmount ExcL VAT VAT% VAT Amount Amount Incl. VAT\nUV RELAY US-UVR-3PHASC\nUSPRO\n1.00 PCS 45.00\n45.00 2.25 47.25\n30a11\nالمجمو\nED\nUAE Dirhams Forty Seven and Twenty Five fis Only\nTOTAL EXCL VAT\nley Sgu bie\nمبتخ بون الضريية\nRa mil la gague 45.00\nمجموعةا الضرية 49.00\nTOTAL VAT\nabove Goode in Good & Sound Cardilien. s é pains not be akon bachescanec\nabove Goode in Good & Soand Condien, oas i b canged.\nTOTAL INCL VAT 2.25\nillea\nميلخ مع الضرية\n47.25", 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'amar Alhuda', 'confidence': 0.98414, 'lang': 'en', 'bounding_box': (25.0, 18.0, 101.0, 37.0)}, {'text': '√', 'confidence': 0.42458, 'lang': 'en', 'bounding_box': (119.0, 9.0, 475.0, 48.0)}, {'text': 'QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.L', 'confidence': 0.97394, 'lang': 'en', 'bounding_box': (122.0, 28.0, 487.0, 68.0)}, {'text': 'Mob: 0528194512', 'confidence': 0.98681, 'lang': 'en', 'bounding_box': (0.0, 46.0, 69.0, 63.0)}, {'text': '0528194629', 'confidence': 0.99987, 'lang': 'en', 'bounding_box': (16.0, 56.0, 68.0, 72.0)}, {'text': 'We are Dealing: Sanitary Wares, Plumbing, Electricals, Paints, Hardware, Plywoods &', 'confidence': 0.99275, 'lang': 'en', 'bounding_box': (120.0, 56.0, 490.0, 86.0)}, {'text': '(JOTUN MULTI COLOUR CENTRE)', 'confidence': 0.99835, 'lang': 'en', 'bounding_box': (226.0, 50.0, 386.0, 71.0)}, {'text': '-mail: qomoralhude.ll@gmoil.com', 'confidence': 0.89951, 'lang': 'en', 'bounding_box': (0.0, 66.0, 117.0, 84.0)}, {'text': 'N:100340280500003', 'confidence': 0.99982, 'lang': 'en', 'bounding_box': (0.0, 80.0, 84.0, 97.0)}, {'text': 'Werehot No. 7,76, 77, Op. A H, D P 1, el 971 4  0, +971 4 9 5545', 'confidence': 0.6578, 'lang': 'en', 'bounding_box': (116.0, 72.0, 490.0, 102.0)}, {'text': 'TAX INVOICE ', 'confidence': 0.87392, 'lang': 'en', 'bounding_box': (160.0, 85.0, 316.0, 107.0)}, {'text': 'all kinds of Building Materials', 'confidence': 0.9939, 'lang': 'en', 'bounding_box': (238.0, 71.0, 371.0, 89.0)}, {'text': 'yor', 'confidence': 0.89549, 'lang': 'en', 'bounding_box': (0.0, 102.0, 11.0, 114.0)}, {'text': 'BLUE RHINE INDUSTRIES LLC', 'confidence': 0.9742, 'lang': 'en', 'bounding_box': (0.0, 118.0, 162.0, 139.0)}, {'text': 'PLOT NO 597673', 'confidence': 0.98201, 'lang': 'en', 'bounding_box': (0.0, 130.0, 80.0, 146.0)}, {'text': 'Deltvery Note', 'confidence': 0.92434, 'lang': 'en', 'bounding_box': (238.0, 125.0, 283.0, 139.0)}, {'text': 'Invoice No.', 'confidence': 0.94022, 'lang': 'en', 'bounding_box': (239.0, 104.0, 276.0, 118.0)}, {'text': 'Delivery Note Date', 'confidence': 0.91683, 'lang': 'en', 'bounding_box': (360.0, 128.0, 421.0, 145.0)}, {'text': 'Date', 'confidence': 0.99631, 'lang': 'en', 'bounding_box': (362.0, 110.0, 382.0, 122.0)}, {'text': 'PO BOX 114001', 'confidence': 0.96209, 'lang': 'en', 'bounding_box': (0.0, 141.0, 71.0, 157.0)}, {'text': 'toihle rne:', 'confidence': 0.35605, 'lang': 'en', 'bounding_box': (0.0, 152.0, 36.0, 171.0)}, {'text': 'DUBAL, UAE', 'confidence': 0.93975, 'lang': 'en', 'bounding_box': (0.0, 165.0, 58.0, 179.0)}, {'text': 'Pv-', 'confidence': 0.79749, 'lang': 'en', 'bounding_box': (85.0, 153.0, 143.0, 178.0)}, {'text': 'SER-BR//65', 'confidence': 0.93357, 'lang': 'en', 'bounding_box': (107.0, 120.0, 222.0, 170.0)}, {'text': "Buyer's Order No.", 'confidence': 0.94809, 'lang': 'en', 'bounding_box': (237.0, 165.0, 294.0, 180.0)}, {'text': "Supplier's Rief.", 'confidence': 0.88687, 'lang': 'en', 'bounding_box': (238.0, 145.0, 285.0, 159.0)}, {'text': 'Dated', 'confidence': 0.92781, 'lang': 'en', 'bounding_box': (359.0, 170.0, 383.0, 183.0)}, {'text': 'Mode/Terma of Payment', 'confidence': 0.93893, 'lang': 'en', 'bounding_box': (360.0, 150.0, 435.0, 165.0)}, {'text': '1000112464M6058', 'confidence': 0.80118, 'lang': 'en', 'bounding_box': (37.0, 181.0, 121.0, 196.0)}, {'text': 'Description', 'confidence': 0.99963, 'lang': 'en', 'bounding_box': (77.0, 191.0, 126.0, 206.0)}, {'text': 'Quantity', 'confidence': 0.99976, 'lang': 'en', 'bounding_box': (199.0, 195.0, 237.0, 211.0)}, {'text': 'L', 'confidence': 0.43137, 'lang': 'en', 'bounding_box': (203.0, 186.0, 233.0, 200.0)}, {'text': 'duagll', 'confidence': 0.4221, 'lang': 'en', 'bounding_box': (238.0, 189.0, 262.0, 201.0)}, {'text': 'Unit', 'confidence': 0.99972, 'lang': 'en', 'bounding_box': (239.0, 198.0, 260.0, 210.0)}, {'text': '1', 'confidence': 0.53418, 'lang': 'en', 'bounding_box': (271.0, 189.0, 294.0, 203.0)}, {'text': 'Rate', 'confidence': 0.99989, 'lang': 'en', 'bounding_box': (272.0, 199.0, 294.0, 212.0)}, {'text': 'ill', 'confidence': 0.48546, 'lang': 'en', 'bounding_box': (300.0, 191.0, 348.0, 204.0)}, {'text': 'Amount ExcL VAT', 'confidence': 0.80892, 'lang': 'en', 'bounding_box': (300.0, 199.0, 349.0, 214.0)}, {'text': 'VAT%', 'confidence': 0.99957, 'lang': 'en', 'bounding_box': (346.0, 202.0, 373.0, 214.0)}, {'text': 'VAT Amount', 'confidence': 0.99948, 'lang': 'en', 'bounding_box': (371.0, 202.0, 422.0, 218.0)}, {'text': 'Amount Incl. VAT', 'confidence': 0.97454, 'lang': 'en', 'bounding_box': (421.0, 203.0, 483.0, 220.0)}, {'text': 'UV RELAY US-UVR-3PHASC', 'confidence': 0.9948, 'lang': 'en', 'bounding_box': (13.0, 222.0, 147.0, 242.0)}, {'text': 'USPRO', 'confidence': 0.9999, 'lang': 'en', 'bounding_box': (13.0, 236.0, 50.0, 250.0)}, {'text': '1.00', 'confidence': 0.99959, 'lang': 'en', 'bounding_box': (211.0, 232.0, 233.0, 246.0)}, {'text': 'PCS', 'confidence': 0.99802, 'lang': 'en', 'bounding_box': (241.0, 232.0, 263.0, 247.0)}, {'text': '45.00', 'confidence': 0.99924, 'lang': 'en', 'bounding_box': (273.0, 231.0, 299.0, 248.0)}, {'text': '45.00', 'confidence': 0.99977, 'lang': 'en', 'bounding_box': (321.0, 236.0, 346.0, 248.0)}, {'text': '2.25', 'confidence': 0.99871, 'lang': 'en', 'bounding_box': (395.0, 238.0, 416.0, 252.0)}, {'text': '47.25', 'confidence': 0.99904, 'lang': 'en', 'bounding_box': (441.0, 239.0, 468.0, 254.0)}, {'text': '30a11', 'confidence': 0.46293, 'lang': 'en', 'bounding_box': (0.0, 544.0, 20.0, 556.0)}, {'text': 'ED', 'confidence': 0.98527, 'lang': 'en', 'bounding_box': (0.0, 553.0, 11.0, 564.0)}, {'text': 'UAE Dirhams Forty Seven and Twenty Five fis Only', 'confidence': 0.9919, 'lang': 'en', 'bounding_box': (20.0, 558.0, 244.0, 583.0)}, {'text': 'TOTAL EXCL VAT', 'confidence': 0.97037, 'lang': 'en', 'bounding_box': (342.0, 566.0, 398.0, 579.0)}, {'text': 'ley Sgu bie', 'confidence': 0.28652, 'lang': 'en', 'bounding_box': (342.0, 556.0, 397.0, 571.0)}, {'text': 'Ra mil la gague', 'confidence': 0.52242, 'lang': 'en', 'bounding_box': (345.0, 576.0, 396.0, 592.0)}, {'text': '45.00', 'confidence': 0.8897, 'lang': 'en', 'bounding_box': (426.0, 574.0, 454.0, 588.0)}, {'text': 'TOTAL VAT', 'confidence': 0.99572, 'lang': 'en', 'bounding_box': (349.0, 586.0, 388.0, 599.0)}, {'text': 'above Goode in Good & Sound Cardilien.', 'confidence': 0.87278, 'lang': 'en', 'bounding_box': (0.0, 605.0, 100.0, 620.0)}, {'text': ' s é pains  not be akon bachescanec', 'confidence': 0.44263, 'lang': 'en', 'bounding_box': (0.0, 612.0, 119.0, 626.0)}, {'text': 'TOTAL INCL VAT', 'confidence': 0.98943, 'lang': 'en', 'bounding_box': (340.0, 606.0, 395.0, 620.0)}, {'text': 'illea', 'confidence': 0.43613, 'lang': 'en', 'bounding_box': (343.0, 596.0, 393.0, 612.0)}, {'text': '47.25', 'confidence': 0.99978, 'lang': 'en', 'bounding_box': (424.0, 620.0, 452.0, 635.0)}, {'text': '2.25', 'confidence': 0.98205, 'lang': 'en', 'bounding_box': (434.0, 600.0, 452.0, 611.0)}, {'text': 'amar Alhuda', 'confidence': 0.98338, 'lang': 'ar', 'bounding_box': (25.0, 18.0, 101.0, 37.0)}, {'text': 'مر االهدى الجديد للتجارة العامة ذمم', 'confidence': 0.80554, 'lang': 'ar', 'bounding_box': (119.0, 9.0, 475.0, 48.0)}, {'text': 'QAMAR ALHUDA ALJADEED GENERAL TRADING LL.L', 'confidence': 0.96657, 'lang': 'ar', 'bounding_box': (122.0, 28.0, 487.0, 68.0)}, {'text': 'Mob: 0528194512', 'confidence': 0.99874, 'lang': 'ar', 'bounding_box': (0.0, 46.0, 69.0, 63.0)}, {'text': '0528194629', 'confidence': 0.99673, 'lang': 'ar', 'bounding_box': (16.0, 56.0, 68.0, 72.0)}, {'text': 'We are Dealing: Sanitary Wares, Plumbing. Electricals, Paints, Hardware, Plywoods &', 'confidence': 0.98683, 'lang': 'ar', 'bounding_box': (120.0, 56.0, 490.0, 86.0)}, {'text': '(JOTUN MULTI COLOUR CENTRE)', 'confidence': 0.97279, 'lang': 'ar', 'bounding_box': (226.0, 50.0, 386.0, 71.0)}, {'text': 'E-mail: qomorolhude.Il@gmoil.com', 'confidence': 0.90527, 'lang': 'ar', 'bounding_box': (0.0, 66.0, 117.0, 84.0)}, {'text': 'N: 100340280500003', 'confidence': 0.94419, 'lang': 'ar', 'bounding_box': (0.0, 80.0, 84.0, 97.0)}, {'text': 'Wr .. k,T +4', 'confidence': 0.53865, 'lang': 'ar', 'bounding_box': (116.0, 72.0, 490.0, 102.0)}, {'text': 'الفاتورة الضريببة', 'confidence': 0.82438, 'lang': 'ar', 'bounding_box': (160.0, 85.0, 316.0, 107.0)}, {'text': 'all kinds of Building Materials', 'confidence': 0.95484, 'lang': 'ar', 'bounding_box': (238.0, 71.0, 371.0, 89.0)}, {'text': 'yor', 'confidence': 0.88658, 'lang': 'ar', 'bounding_box': (0.0, 102.0, 11.0, 114.0)}, {'text': 'BLUE RHINE INDUSTRIES LLC', 'confidence': 0.99829, 'lang': 'ar', 'bounding_box': (0.0, 118.0, 162.0, 139.0)}, {'text': 'PLOT NO 597673', 'confidence': 0.97731, 'lang': 'ar', 'bounding_box': (0.0, 130.0, 80.0, 146.0)}, {'text': 'Detivery Note', 'confidence': 0.98368, 'lang': 'ar', 'bounding_box': (238.0, 125.0, 283.0, 139.0)}, {'text': 'Involce No.', 'confidence': 0.92607, 'lang': 'ar', 'bounding_box': (239.0, 104.0, 276.0, 118.0)}, {'text': 'Delivery Nose Sate', 'confidence': 0.84362, 'lang': 'ar', 'bounding_box': (360.0, 128.0, 421.0, 145.0)}, {'text': 'Date', 'confidence': 0.94568, 'lang': 'ar', 'bounding_box': (362.0, 110.0, 382.0, 122.0)}, {'text': 'PO BOX 114001', 'confidence': 0.95777, 'lang': 'ar', 'bounding_box': (0.0, 141.0, 71.0, 157.0)}, {'text': 'Toer THN:', 'confidence': 0.65489, 'lang': 'ar', 'bounding_box': (0.0, 152.0, 36.0, 171.0)}, {'text': 'DUBAI, UAE', 'confidence': 0.91451, 'lang': 'ar', 'bounding_box': (0.0, 165.0, 58.0, 179.0)}, {'text': 'Pv-', 'confidence': 0.81931, 'lang': 'ar', 'bounding_box': (85.0, 153.0, 143.0, 178.0)}, {'text': 'SER-BR1/65', 'confidence': 0.70837, 'lang': 'ar', 'bounding_box': (107.0, 120.0, 222.0, 170.0)}, {'text': "Buyer's Ordler No.", 'confidence': 0.9235, 'lang': 'ar', 'bounding_box': (237.0, 165.0, 294.0, 180.0)}, {'text': "Supplier's Her.", 'confidence': 0.95112, 'lang': 'ar', 'bounding_box': (238.0, 145.0, 285.0, 159.0)}, {'text': 'Dated', 'confidence': 0.98533, 'lang': 'ar', 'bounding_box': (359.0, 170.0, 383.0, 183.0)}, {'text': 'Mode/Termas of Payment', 'confidence': 0.93476, 'lang': 'ar', 'bounding_box': (360.0, 150.0, 435.0, 165.0)}, {'text': 'اللفاسيل100011246', 'confidence': 0.72715, 'lang': 'ar', 'bounding_box': (37.0, 181.0, 121.0, 196.0)}, {'text': 'Description', 'confidence': 0.96026, 'lang': 'ar', 'bounding_box': (77.0, 191.0, 126.0, 206.0)}, {'text': 'Quantity', 'confidence': 0.95923, 'lang': 'ar', 'bounding_box': (199.0, 195.0, 237.0, 211.0)}, {'text': 'الكمبة', 'confidence': 0.79807, 'lang': 'ar', 'bounding_box': (203.0, 186.0, 233.0, 200.0)}, {'text': 'الوحدة', 'confidence': 0.87974, 'lang': 'ar', 'bounding_box': (238.0, 189.0, 262.0, 201.0)}, {'text': 'Unit', 'confidence': 0.99924, 'lang': 'ar', 'bounding_box': (239.0, 198.0, 260.0, 210.0)}, {'text': 'السر', 'confidence': 0.79143, 'lang': 'ar', 'bounding_box': (271.0, 189.0, 294.0, 203.0)}, {'text': 'Rate', 'confidence': 0.99816, 'lang': 'ar', 'bounding_box': (272.0, 199.0, 294.0, 212.0)}, {'text': 'مستغ بون الضرية', 'confidence': 0.64601, 'lang': 'ar', 'bounding_box': (300.0, 191.0, 348.0, 204.0)}, {'text': 'Anouent Exctl vr', 'confidence': 0.73838, 'lang': 'ar', 'bounding_box': (300.0, 199.0, 349.0, 214.0)}, {'text': 'VAT%', 'confidence': 0.95942, 'lang': 'ar', 'bounding_box': (346.0, 202.0, 373.0, 214.0)}, {'text': 'الضرية', 'confidence': 0.8729, 'lang': 'ar', 'bounding_box': (348.0, 193.0, 374.0, 205.0)}, {'text': 'VAT Amount', 'confidence': 0.99605, 'lang': 'ar', 'bounding_box': (371.0, 202.0, 422.0, 218.0)}, {'text': 'مبتخ الضريبة', 'confidence': 0.73804, 'lang': 'ar', 'bounding_box': (372.0, 192.0, 419.0, 208.0)}, {'text': 'Amount incl, VAT', 'confidence': 0.92398, 'lang': 'ar', 'bounding_box': (421.0, 203.0, 483.0, 220.0)}, {'text': 'مبلخ مع الضريبة', 'confidence': 0.66178, 'lang': 'ar', 'bounding_box': (424.0, 195.0, 480.0, 211.0)}, {'text': 'UV RELAY US-UVR-3PHASC', 'confidence': 0.99665, 'lang': 'ar', 'bounding_box': (13.0, 222.0, 147.0, 242.0)}, {'text': 'USPRO', 'confidence': 0.99891, 'lang': 'ar', 'bounding_box': (13.0, 236.0, 50.0, 250.0)}, {'text': '1.00', 'confidence': 0.94648, 'lang': 'ar', 'bounding_box': (211.0, 232.0, 233.0, 246.0)}, {'text': 'PCS', 'confidence': 0.95464, 'lang': 'ar', 'bounding_box': (241.0, 232.0, 263.0, 247.0)}, {'text': '45.00', 'confidence': 0.93731, 'lang': 'ar', 'bounding_box': (273.0, 231.0, 299.0, 248.0)}, {'text': '45.00', 'confidence': 0.99973, 'lang': 'ar', 'bounding_box': (321.0, 236.0, 346.0, 248.0)}, {'text': '2.25', 'confidence': 0.9991, 'lang': 'ar', 'bounding_box': (395.0, 238.0, 416.0, 252.0)}, {'text': '47.25', 'confidence': 0.98078, 'lang': 'ar', 'bounding_box': (441.0, 239.0, 468.0, 254.0)}, {'text': 'المجمو', 'confidence': 0.86701, 'lang': 'ar', 'bounding_box': (0.0, 544.0, 20.0, 556.0)}, {'text': 'ED', 'confidence': 0.99454, 'lang': 'ar', 'bounding_box': (0.0, 553.0, 11.0, 564.0)}, {'text': 'UAE Dirhams Forty Seven and Twenty Five fis Only', 'confidence': 0.96649, 'lang': 'ar', 'bounding_box': (20.0, 558.0, 244.0, 583.0)}, {'text': 'TOTALEXCL VAT', 'confidence': 0.95748, 'lang': 'ar', 'bounding_box': (342.0, 566.0, 398.0, 579.0)}, {'text': 'مبتخ بون الضريية', 'confidence': 0.63949, 'lang': 'ar', 'bounding_box': (342.0, 556.0, 397.0, 571.0)}, {'text': 'مجموعةا الضرية', 'confidence': 0.81072, 'lang': 'ar', 'bounding_box': (345.0, 576.0, 396.0, 592.0)}, {'text': '49.00', 'confidence': 0.88652, 'lang': 'ar', 'bounding_box': (426.0, 574.0, 454.0, 588.0)}, {'text': 'TOTAL VAT', 'confidence': 0.99345, 'lang': 'ar', 'bounding_box': (349.0, 586.0, 388.0, 599.0)}, {'text': 'above Goode in Good & Soand Condien,', 'confidence': 0.89486, 'lang': 'ar', 'bounding_box': (0.0, 605.0, 100.0, 620.0)}, {'text': 'oas i b  canged.', 'confidence': 0.5331, 'lang': 'ar', 'bounding_box': (0.0, 612.0, 119.0, 626.0)}, {'text': 'TOTAL INCL VAT', 'confidence': 0.97744, 'lang': 'ar', 'bounding_box': (340.0, 606.0, 395.0, 620.0)}, {'text': 'ميلخ مع الضرية', 'confidence': 0.78158, 'lang': 'ar', 'bounding_box': (343.0, 596.0, 393.0, 612.0)}, {'text': '47.25', 'confidence': 0.99924, 'lang': 'ar', 'bounding_box': (424.0, 620.0, 452.0, 635.0)}, {'text': '2.25', 'confidence': 0.84052, 'lang': 'ar', 'bounding_box': (434.0, 600.0, 452.0, 611.0)}], 'field_confidence': {'vendor': 0.2628008135433071, 'date': 0.0, 'currency': 0.0, 'amount': 0.9660795354330708, 'vat_rate': 0.0, 'vat_amount': 1.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.8914019881889763, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** √ (0.42), toihle rne: (0.36), L (0.43), duagll (0.42), ill (0.49), 30a11 (0.46), ley Sgu bie (0.29),  s é pains  not be akon bachescanec (0.44), illea (0.44)

**Raw text:**

```
amar Alhuda
√
QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.L
Mob: 0528194512
0528194629
We are Dealing: Sanitary Wares, Plumbing, Electricals, Paints, Hardware, Plywoods &
(JOTUN MULTI COLOUR CENTRE)
-mail: qomoralhude.ll@gmoil.com
N:100340280500003
Werehot No. 7,76, 77, Op. A H, D P 1, el 971 4  0, +971 4 9 5545
TAX INVOICE
all kinds of Building Materials
yor
BLUE RHINE INDUSTRIES LLC
PLOT NO 597673
Deltvery Note
Invoice No.
Delivery Note Date
Date
PO BOX 114001
toihle rne:
DUBAL, UAE
Pv-
SER-BR//65
Buyer's Order No.
Supplier's Rief.
Dated
Mode/Terma of Payment
1000112464M6058
Description
Quantity
L
duagll
Unit
1
Rate
ill
Amount ExcL VAT
VAT%
VAT Amount
Amount Incl. VAT
UV RELAY US-UVR-3PHASC
USPRO
1.00
PCS
45.00
45.00
2.25
47.25
30a11
ED
UAE Dirhams Forty Seven and Twenty Five fis Only
TOTAL EXCL VAT
ley Sgu bie
Ra mil la gague
45.00
TOTAL VAT
above Goode in Good & Sound Cardilien.
 s é pains  not be akon bachescanec
TOTAL INCL VAT
illea
47.25
2.25
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
amar Alhuda
مر االهدى الجديد للتجارة العامة ذمم
QAMAR ALHUDA ALJADEED GENERAL TRADING LL.L
Mob: 0528194512
0528194629
We are Dealing: Sanitary Wares, Plumbing. Electricals, Paints, Hardware, Plywoods &
(JOTUN MULTI COLOUR CENTRE)
E-mail: qomorolhude.Il@gmoil.com
N: 100340280500003
Wr .. k,T +4
الفاتورة الضريببة
all kinds of Building Materials
yor
BLUE RHINE INDUSTRIES LLC
PLOT NO 597673
Detivery Note
Involce No.
Delivery Nose Sate
Date
PO BOX 114001
Toer THN:
DUBAI, UAE
Pv-
SER-BR1/65
Buyer's Ordler No.
Supplier's Her.
Dated
Mode/Termas of Payment
اللفاسيل100011246
Description
Quantity
الكمبة
الوحدة
Unit
السر
Rate
مستغ بون الضرية
Anouent Exctl vr
VAT%
الضرية
VAT Amount
مبتخ الضريبة
Amount incl, VAT
مبلخ مع الضريبة
UV RELAY US-UVR-3PHASC
USPRO
1.00
PCS
45.00
45.00
2.25
47.25
المجمو
ED
UAE Dirhams Forty Seven and Twenty Five fis Only
TOTALEXCL VAT
مبتخ بون الضريية
مجموعةا الضرية
49.00
TOTAL VAT
above Goode in Good & Soand Condien,
oas i b  canged.
TOTAL INCL VAT
ميلخ مع الضرية
47.25
2.25
```

## image (6).png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'mnymg', 'expense_type': None, 'amount': 49.52, 'vat_amount': 2.48, 'total_amount': 52.0, 'currency': 'USD', 'date': '04/00/2026', 'confidence': 0.32, 'field_confidence': {'vendor': 0.20203221428571427, 'date': 0.2893069285714286, 'currency': 0.7218167857142856, 'amount': 0.805829, 'vat_rate': 0.795971, 'vat_amount': 0.4, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8275599285714285, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'vat_amount', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'mnymg', 'confidence': 0.20203221428571427, 'evidence': 'mnymg', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '04/00/2026', 'confidence': 0.2893069285714286, 'evidence': '04/00/2026 09:19 09 1 137', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': True, 'warning': 'ambiguous_candidates'}, 'currency': {'value': 'USD', 'confidence': 0.7218167857142856, 'evidence': 'USD 7-54', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 49.52, 'confidence': 0.805829, 'evidence': '49.52 52.00 2.48', 'signals': ['subtotal_label', 'previous_line_label', 'fuzzy_label_match', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_rate': {'value': 5.0, 'confidence': 0.795971, 'evidence': '5 83.37 87.54 4.17', 'signals': ['vat_tax_rate_label', 'known_vat_rate', 'format_known_vat_rate', 'arithmetic_reconciled_inclusive'], 'low': False}, 'vat_amount': {'value': 2.48, 'confidence': 0.4, 'evidence': 'derived: TOTAL AMOUNT 52.00 at 5.0%', 'signals': ['derived_arithmetic', 'derived_inclusive'], 'low': True, 'warning': 'derived_value'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': 52.0, 'confidence': 0.8275599285714285, 'evidence': 'Paid Amoutil(MAS) 52.00', 'signals': ['tendered_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money'], 'low': False}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 52.0, 'confidence': 1.0, 'evidence': 'TOTAL AMOUNT 52.00', 'signals': ['total_label', 'same_line', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'arithmetic_reconciled_inclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'mnymg\nl\nmniypy\n5R\nS\n87-54\nUSD 7-54\nPASONS\nCESETSED\nCELTTED\nDubai Investment Park-2 . Dubai , U AE\nPasons S/M&Dept.Store\nSicsE\nS\nPASONS mmes\nSiLEt\nSLEE\nTet 04-8840966, Mob:0557892020\nTRN 100453349100003\nwww.pasonsme.com\nDubai Investment Parlk-2. Dubai . U AE\nDubat lInvesmenl Park-2, Dubai, U AE\nTel 04-0840966 . Mob:0557602020\nPasons S/M&.Depl Slore\n3 87158069 1.000 PCS 4.00\n1 6291031020837 8.000 PCS 5200 Sd." tom Oty Unsi Anoutt\nSr. ltem Cty Unil Amount\nSri."tem Oty Unit Amount\nA esi 2S11 23 2n1\nالذوع الرفم الكبية السع السجرع\n9901125020304 2.030 KGS 13.20\nNezo Set 1Kg Pht Blue\nMarmum Yoghurt 1Kg Full Cresm\nCarrot\nTax Invoice 222\nTax Invoice نتورة ضرية\n1 6291031020837 Mamum Yoghiet 1Kg Full Cream 8.000 PCS 52.00\nA ex3 3s1 x EmJi\nالنوع الرقم الخية السم الجسع\nItem Counl 8\nTax Invoice ji 3 ai\nTax Invoice نتورة ضربية\nTRN 100453349100003\nwww pasonime.comn\nsine pasonvime con\nTOTAL AMOUNT 52.00\n52\n4 990112900055 0.506 KGS 10.10\n9901148020855 2.085 KGS 8.24\nChili India\nCucumber\nTax Inclusive L\nTax Inolusie الشسرية الشفئة\nVAT% Exdl VAT IncI VAT VAT\nPaid Amoutil(MAS) 52.00\n49.52 52.00 2.48\nIlem Count 12 87-50\nPaid Amount(MAS) 87.54\nTOTAL AMOUNT 87.54\n04/00/2026 09:19 09 1 137\nServed by SAFWAN CHANGOTH\nDate Time Store POS Bill\nTax Inclusive\nVAT% Exd.VAT Incl VAT VAT\n5 83.37 87.54 4.17\nNo Cash Refund, Thenk You. Visit Again\nKeep Receipt For Exchange, T&.C Apply\nNo Exchange On Under Garments\nDate Time Store POS Bil\n05/08/2026 09:12 09 1 115\n090120260804137\nKeep Receipt For Exchange, T&C Apply\nNo Exchange On Under Gaments\nNo Cash Refund,Thank You, Visit Again\n090120260805115', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'l', 'confidence': 0.18371, 'lang': 'en', 'bounding_box': (252.0, 59.0, 316.0, 166.0)}, {'text': '5R', 'confidence': 0.39252, 'lang': 'en', 'bounding_box': (395.0, 86.0, 434.0, 131.0)}, {'text': '87-54', 'confidence': 0.98798, 'lang': 'en', 'bounding_box': (171.0, 50.0, 226.0, 113.0)}, {'text': 'PASONS', 'confidence': 0.99952, 'lang': 'en', 'bounding_box': (102.0, 116.0, 176.0, 137.0)}, {'text': 'CESETSED', 'confidence': 0.40033, 'lang': 'en', 'bounding_box': (116.0, 112.0, 164.0, 121.0)}, {'text': 'Dubai Investment Park-2 . Dubai , U AE', 'confidence': 0.95033, 'lang': 'en', 'bounding_box': (72.0, 153.0, 204.0, 169.0)}, {'text': 'Pasons S/M&Dept.Store', 'confidence': 0.99515, 'lang': 'en', 'bounding_box': (96.0, 144.0, 181.0, 159.0)}, {'text': 'SicsE', 'confidence': 0.5031, 'lang': 'en', 'bounding_box': (125.0, 131.0, 155.0, 148.0)}, {'text': 'PASONS', 'confidence': 0.99813, 'lang': 'en', 'bounding_box': (321.0, 135.0, 396.0, 154.0)}, {'text': 'SiLEt', 'confidence': 0.50226, 'lang': 'en', 'bounding_box': (343.0, 150.0, 373.0, 165.0)}, {'text': 'mmes', 'confidence': 0.46039, 'lang': 'en', 'bounding_box': (347.0, 130.0, 382.0, 139.0)}, {'text': 'Tel: 04-8840966 . Mob:0557692020', 'confidence': 0.93668, 'lang': 'en', 'bounding_box': (78.0, 163.0, 199.0, 178.0)}, {'text': 'TRN 100453349100003', 'confidence': 0.99897, 'lang': 'en', 'bounding_box': (96.0, 182.0, 179.0, 197.0)}, {'text': 'www.pasonsme.com', 'confidence': 0.99068, 'lang': 'en', 'bounding_box': (102.0, 174.0, 174.0, 187.0)}, {'text': 'Dubai Investment Parlk-2. Dubai . U AE', 'confidence': 0.87565, 'lang': 'en', 'bounding_box': (292.0, 172.0, 423.0, 184.0)}, {'text': 'Tel 04-0840966 . Mob:0557602020', 'confidence': 0.97061, 'lang': 'en', 'bounding_box': (297.0, 181.0, 418.0, 195.0)}, {'text': 'Pasons S/M&.Depl Slore', 'confidence': 0.95022, 'lang': 'en', 'bounding_box': (316.0, 163.0, 400.0, 175.0)}, {'text': '3 87158069', 'confidence': 0.9985, 'lang': 'en', 'bounding_box': (47.0, 272.0, 97.0, 286.0)}, {'text': '1 6291031020837', 'confidence': 0.97734, 'lang': 'en', 'bounding_box': (48.0, 226.0, 118.0, 240.0)}, {'text': 'Sr. ltem', 'confidence': 0.82093, 'lang': 'en', 'bounding_box': (49.0, 203.0, 91.0, 218.0)}, {'text': 'A esi', 'confidence': 0.29611, 'lang': 'en', 'bounding_box': (52.0, 215.0, 91.0, 228.0)}, {'text': '9901125020304', 'confidence': 0.99993, 'lang': 'en', 'bounding_box': (58.0, 249.0, 116.0, 262.0)}, {'text': 'Nezo Salt 1Kg Pkt Blue', 'confidence': 0.90663, 'lang': 'en', 'bounding_box': (58.0, 283.0, 139.0, 297.0)}, {'text': 'Marmum Yoghurt 1Kg Full Cresm', 'confidence': 0.95224, 'lang': 'en', 'bounding_box': (60.0, 237.0, 173.0, 252.0)}, {'text': 'Carrot', 'confidence': 0.9988, 'lang': 'en', 'bounding_box': (61.0, 261.0, 85.0, 272.0)}, {'text': 'Tax Invoice', 'confidence': 0.99956, 'lang': 'en', 'bounding_box': (90.0, 193.0, 142.0, 207.0)}, {'text': '2S11', 'confidence': 0.38934, 'lang': 'en', 'bounding_box': (130.0, 217.0, 149.0, 228.0)}, {'text': '8.000 PCS', 'confidence': 0.9421, 'lang': 'en', 'bounding_box': (129.0, 226.0, 177.0, 241.0)}, {'text': 'Cty', 'confidence': 0.7663, 'lang': 'en', 'bounding_box': (131.0, 205.0, 147.0, 219.0)}, {'text': '1.000', 'confidence': 0.99896, 'lang': 'en', 'bounding_box': (131.0, 275.0, 153.0, 287.0)}, {'text': '2.030', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (132.0, 253.0, 153.0, 262.0)}, {'text': 'KGS', 'confidence': 0.99991, 'lang': 'en', 'bounding_box': (155.0, 253.0, 176.0, 264.0)}, {'text': 'PCS', 'confidence': 0.99907, 'lang': 'en', 'bounding_box': (154.0, 275.0, 176.0, 288.0)}, {'text': 'Unil', 'confidence': 0.91776, 'lang': 'en', 'bounding_box': (160.0, 207.0, 176.0, 218.0)}, {'text': '23', 'confidence': 0.50858, 'lang': 'en', 'bounding_box': (161.0, 219.0, 177.0, 229.0)}, {'text': '222', 'confidence': 0.30595, 'lang': 'en', 'bounding_box': (181.0, 193.0, 225.0, 208.0)}, {'text': '2n1', 'confidence': 0.34542, 'lang': 'en', 'bounding_box': (193.0, 220.0, 223.0, 230.0)}, {'text': 'Amount', 'confidence': 0.9914, 'lang': 'en', 'bounding_box': (194.0, 208.0, 223.0, 220.0)}, {'text': '52.00', 'confidence': 0.8924, 'lang': 'en', 'bounding_box': (199.0, 230.0, 223.0, 242.0)}, {'text': '13.20', 'confidence': 0.99963, 'lang': 'en', 'bounding_box': (200.0, 253.0, 222.0, 265.0)}, {'text': '4.00', 'confidence': 0.99986, 'lang': 'en', 'bounding_box': (203.0, 277.0, 222.0, 288.0)}, {'text': 'Si.tom', 'confidence': 0.60833, 'lang': 'en', 'bounding_box': (268.0, 220.0, 310.0, 236.0)}, {'text': '1 6291031020837', 'confidence': 0.98544, 'lang': 'en', 'bounding_box': (271.0, 246.0, 337.0, 257.0)}, {'text': 'A ex3', 'confidence': 0.56741, 'lang': 'en', 'bounding_box': (272.0, 234.0, 311.0, 246.0)}, {'text': 'Item Counl 8', 'confidence': 0.96408, 'lang': 'en', 'bounding_box': (274.0, 282.0, 324.0, 293.0)}, {'text': 'Mamum Yoghiet 1Kg Full Cream', 'confidence': 0.91528, 'lang': 'en', 'bounding_box': (280.0, 254.0, 393.0, 269.0)}, {'text': 'Tax Invoice', 'confidence': 0.99957, 'lang': 'en', 'bounding_box': (310.0, 210.0, 361.0, 224.0)}, {'text': 'TRN 100453349100003', 'confidence': 0.98801, 'lang': 'en', 'bounding_box': (317.0, 202.0, 398.0, 212.0)}, {'text': 'www pasonime.comn', 'confidence': 0.88318, 'lang': 'en', 'bounding_box': (321.0, 192.0, 393.0, 204.0)}, {'text': 'TOTAL AMOUNT', 'confidence': 0.99072, 'lang': 'en', 'bounding_box': (331.0, 269.0, 395.0, 283.0)}, {'text': 'Oty', 'confidence': 0.94754, 'lang': 'en', 'bounding_box': (350.0, 224.0, 367.0, 236.0)}, {'text': '3s1', 'confidence': 0.32062, 'lang': 'en', 'bounding_box': (350.0, 235.0, 369.0, 247.0)}, {'text': '8.000 PCS', 'confidence': 0.91311, 'lang': 'en', 'bounding_box': (350.0, 245.0, 396.0, 258.0)}, {'text': 'Uni', 'confidence': 0.88987, 'lang': 'en', 'bounding_box': (379.0, 223.0, 396.0, 236.0)}, {'text': 'x', 'confidence': 0.41964, 'lang': 'en', 'bounding_box': (381.0, 236.0, 396.0, 246.0)}, {'text': '52', 'confidence': 0.99982, 'lang': 'en', 'bounding_box': (381.0, 283.0, 414.0, 306.0)}, {'text': 'ji 3 ai', 'confidence': 0.45117, 'lang': 'en', 'bounding_box': (401.0, 211.0, 444.0, 224.0)}, {'text': 'EmJi', 'confidence': 0.31519, 'lang': 'en', 'bounding_box': (412.0, 235.0, 442.0, 248.0)}, {'text': 'Ancutt', 'confidence': 0.64828, 'lang': 'en', 'bounding_box': (412.0, 222.0, 443.0, 238.0)}, {'text': '52.00', 'confidence': 0.99963, 'lang': 'en', 'bounding_box': (418.0, 271.0, 440.0, 283.0)}, {'text': '52.00', 'confidence': 0.99177, 'lang': 'en', 'bounding_box': (420.0, 246.0, 442.0, 258.0)}, {'text': '4 9001129005055', 'confidence': 0.98447, 'lang': 'en', 'bounding_box': (47.0, 295.0, 116.0, 310.0)}, {'text': '9901148020855', 'confidence': 0.99621, 'lang': 'en', 'bounding_box': (56.0, 320.0, 115.0, 332.0)}, {'text': 'Chil India', 'confidence': 0.94191, 'lang': 'en', 'bounding_box': (58.0, 305.0, 96.0, 321.0)}, {'text': 'Cucumber', 'confidence': 0.9991, 'lang': 'en', 'bounding_box': (58.0, 329.0, 96.0, 342.0)}, {'text': '0.505 KGS', 'confidence': 0.9235, 'lang': 'en', 'bounding_box': (128.0, 296.0, 176.0, 312.0)}, {'text': '2.085 KGS', 'confidence': 0.92784, 'lang': 'en', 'bounding_box': (128.0, 320.0, 175.0, 335.0)}, {'text': '10.10', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (199.0, 300.0, 221.0, 312.0)}, {'text': '8.24', 'confidence': 0.99764, 'lang': 'en', 'bounding_box': (202.0, 324.0, 221.0, 336.0)}, {'text': 'Tax Inclusive', 'confidence': 0.93609, 'lang': 'en', 'bounding_box': (294.0, 308.0, 339.0, 321.0)}, {'text': 'VAT%', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (303.0, 319.0, 337.0, 330.0)}, {'text': 'Paid Amoutil(MAS)', 'confidence': 0.94659, 'lang': 'en', 'bounding_box': (316.0, 293.0, 382.0, 306.0)}, {'text': 'Excl VAT', 'confidence': 0.8601, 'lang': 'en', 'bounding_box': (332.0, 318.0, 368.0, 331.0)}, {'text': '49.52', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (345.0, 330.0, 367.0, 341.0)}, {'text': 'Inci VAT', 'confidence': 0.91149, 'lang': 'en', 'bounding_box': (376.0, 320.0, 406.0, 331.0)}, {'text': '52.00', 'confidence': 0.99989, 'lang': 'en', 'bounding_box': (385.0, 331.0, 406.0, 341.0)}, {'text': 'L', 'confidence': 0.10362, 'lang': 'en', 'bounding_box': (387.0, 309.0, 430.0, 322.0)}, {'text': '52.00', 'confidence': 0.99984, 'lang': 'en', 'bounding_box': (418.0, 295.0, 441.0, 306.0)}, {'text': '2.48', 'confidence': 0.99886, 'lang': 'en', 'bounding_box': (418.0, 331.0, 436.0, 342.0)}, {'text': 'VAT', 'confidence': 0.99994, 'lang': 'en', 'bounding_box': (420.0, 320.0, 438.0, 332.0)}, {'text': 'Ilem Count 12', 'confidence': 0.96368, 'lang': 'en', 'bounding_box': (51.0, 356.0, 105.0, 369.0)}, {'text': 'Paid Amount(MAS)', 'confidence': 0.99241, 'lang': 'en', 'bounding_box': (94.0, 369.0, 161.0, 382.0)}, {'text': 'TOTAL AMOUNT', 'confidence': 0.99303, 'lang': 'en', 'bounding_box': (108.0, 344.0, 173.0, 359.0)}, {'text': '87-50', 'confidence': 0.99572, 'lang': 'en', 'bounding_box': (152.0, 351.0, 205.0, 379.0)}, {'text': '87.54', 'confidence': 0.99513, 'lang': 'en', 'bounding_box': (196.0, 347.0, 218.0, 359.0)}, {'text': '87.54', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (196.0, 372.0, 218.0, 384.0)}, {'text': '04/08/2026', 'confidence': 0.94728, 'lang': 'en', 'bounding_box': (272.0, 366.0, 313.0, 378.0)}, {'text': 'Served by', 'confidence': 0.95401, 'lang': 'en', 'bounding_box': (274.0, 342.0, 312.0, 355.0)}, {'text': 'Date', 'confidence': 0.93554, 'lang': 'en', 'bounding_box': (274.0, 356.0, 294.0, 368.0)}, {'text': '09:19', 'confidence': 0.99535, 'lang': 'en', 'bounding_box': (314.0, 366.0, 339.0, 379.0)}, {'text': 'Time', 'confidence': 0.99027, 'lang': 'en', 'bounding_box': (317.0, 355.0, 338.0, 369.0)}, {'text': 'SAFWAN CHANGOTH', 'confidence': 0.99104, 'lang': 'en', 'bounding_box': (331.0, 343.0, 411.0, 356.0)}, {'text': 'Store', 'confidence': 0.97374, 'lang': 'en', 'bounding_box': (349.0, 357.0, 371.0, 369.0)}, {'text': '09', 'confidence': 0.98846, 'lang': 'en', 'bounding_box': (356.0, 368.0, 369.0, 379.0)}, {'text': 'POS', 'confidence': 0.99887, 'lang': 'en', 'bounding_box': (382.0, 357.0, 402.0, 369.0)}, {'text': '1', 'confidence': 0.99879, 'lang': 'en', 'bounding_box': (388.0, 369.0, 395.0, 378.0)}, {'text': 'Bill', 'confidence': 0.98824, 'lang': 'en', 'bounding_box': (406.0, 359.0, 420.0, 369.0)}, {'text': '137', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (408.0, 369.0, 423.0, 379.0)}, {'text': 'Served by:', 'confidence': 0.9466, 'lang': 'en', 'bounding_box': (51.0, 417.0, 90.0, 430.0)}, {'text': 'Tax Inclusive', 'confidence': 0.97718, 'lang': 'en', 'bounding_box': (72.0, 385.0, 116.0, 396.0)}, {'text': 'VAT%', 'confidence': 0.99992, 'lang': 'en', 'bounding_box': (81.0, 395.0, 114.0, 406.0)}, {'text': '5', 'confidence': 0.73442, 'lang': 'en', 'bounding_box': (89.0, 405.0, 98.0, 414.0)}, {'text': 'Exd.VAT', 'confidence': 0.99113, 'lang': 'en', 'bounding_box': (109.0, 396.0, 145.0, 406.0)}, {'text': 'SAFWAN CHANGOTH', 'confidence': 0.99155, 'lang': 'en', 'bounding_box': (109.0, 419.0, 189.0, 431.0)}, {'text': '83.37', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (122.0, 405.0, 145.0, 417.0)}, {'text': 'Incl VAT', 'confidence': 0.93338, 'lang': 'en', 'bounding_box': (152.0, 395.0, 184.0, 408.0)}, {'text': '87.54', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (162.0, 407.0, 184.0, 417.0)}, {'text': '4.17', 'confidence': 0.99932, 'lang': 'en', 'bounding_box': (196.0, 408.0, 213.0, 417.0)}, {'text': 'VAT', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (197.0, 397.0, 216.0, 408.0)}, {'text': 'No Cash Refund, Thenk You. Visit Again', 'confidence': 0.98825, 'lang': 'en', 'bounding_box': (287.0, 404.0, 422.0, 419.0)}, {'text': 'Keep Receipt For Exchange, T&.C Apply', 'confidence': 0.99115, 'lang': 'en', 'bounding_box': (289.0, 382.0, 423.0, 396.0)}, {'text': 'No Exchange On Under Garments', 'confidence': 0.98152, 'lang': 'en', 'bounding_box': (297.0, 392.0, 412.0, 408.0)}, {'text': 'Date', 'confidence': 0.99673, 'lang': 'en', 'bounding_box': (50.0, 431.0, 70.0, 442.0)}, {'text': '05/08/2026', 'confidence': 0.99987, 'lang': 'en', 'bounding_box': (50.0, 441.0, 90.0, 452.0)}, {'text': '09:12', 'confidence': 0.99994, 'lang': 'en', 'bounding_box': (93.0, 442.0, 116.0, 452.0)}, {'text': 'Time', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (95.0, 432.0, 115.0, 443.0)}, {'text': 'Store', 'confidence': 0.9673, 'lang': 'en', 'bounding_box': (126.0, 433.0, 148.0, 444.0)}, {'text': '09', 'confidence': 0.99654, 'lang': 'en', 'bounding_box': (133.0, 443.0, 146.0, 453.0)}, {'text': 'POS', 'confidence': 0.99902, 'lang': 'en', 'bounding_box': (159.0, 433.0, 180.0, 444.0)}, {'text': '1', 'confidence': 0.99889, 'lang': 'en', 'bounding_box': (166.0, 445.0, 172.0, 452.0)}, {'text': 'Bil', 'confidence': 0.99606, 'lang': 'en', 'bounding_box': (184.0, 435.0, 198.0, 444.0)}, {'text': '115', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (185.0, 444.0, 200.0, 454.0)}, {'text': '090120260804137', 'confidence': 0.99961, 'lang': 'en', 'bounding_box': (324.0, 438.0, 384.0, 451.0)}, {'text': 'Keep Receipt For Exchange, T&C Apply', 'confidence': 0.99529, 'lang': 'en', 'bounding_box': (66.0, 456.0, 201.0, 471.0)}, {'text': 'No Exchange On Under Gaments', 'confidence': 0.99431, 'lang': 'en', 'bounding_box': (74.0, 467.0, 189.0, 482.0)}, {'text': 'No Cash Refund,Thank You, Visit Again', 'confidence': 0.99248, 'lang': 'en', 'bounding_box': (65.0, 478.0, 198.0, 493.0)}, {'text': '090120260805115', 'confidence': 0.9999, 'lang': 'en', 'bounding_box': (101.0, 513.0, 161.0, 525.0)}, {'text': 'mnymg', 'confidence': 0.51831, 'lang': 'ar', 'bounding_box': (36.0, 40.0, 99.0, 140.0)}, {'text': 'mniypy', 'confidence': 0.55856, 'lang': 'ar', 'bounding_box': (252.0, 59.0, 316.0, 166.0)}, {'text': 'S', 'confidence': 0.17153, 'lang': 'ar', 'bounding_box': (395.0, 86.0, 434.0, 131.0)}, {'text': '$7-54', 'confidence': 0.96735, 'lang': 'ar', 'bounding_box': (171.0, 50.0, 226.0, 113.0)}, {'text': 'PASONS', 'confidence': 0.99894, 'lang': 'ar', 'bounding_box': (102.0, 116.0, 176.0, 137.0)}, {'text': 'CELTTED', 'confidence': 0.51282, 'lang': 'ar', 'bounding_box': (116.0, 112.0, 164.0, 121.0)}, {'text': 'Dubai Iivestment Park-2, Dubai , U AE', 'confidence': 0.91389, 'lang': 'ar', 'bounding_box': (72.0, 153.0, 204.0, 169.0)}, {'text': 'Pasons S/M&Dept. Store', 'confidence': 0.9424, 'lang': 'ar', 'bounding_box': (96.0, 144.0, 181.0, 159.0)}, {'text': 'S', 'confidence': 0.48509, 'lang': 'ar', 'bounding_box': (125.0, 131.0, 155.0, 148.0)}, {'text': 'PASONS', 'confidence': 0.99737, 'lang': 'ar', 'bounding_box': (321.0, 135.0, 396.0, 154.0)}, {'text': 'SLEE', 'confidence': 0.58573, 'lang': 'ar', 'bounding_box': (343.0, 150.0, 373.0, 165.0)}, {'text': 'MMMES', 'confidence': 0.3676, 'lang': 'ar', 'bounding_box': (347.0, 130.0, 382.0, 139.0)}, {'text': 'Tet 04-8840966, Mob:0557892020', 'confidence': 0.94668, 'lang': 'ar', 'bounding_box': (78.0, 163.0, 199.0, 178.0)}, {'text': 'TRN 100453349100003', 'confidence': 0.96744, 'lang': 'ar', 'bounding_box': (96.0, 182.0, 179.0, 197.0)}, {'text': 'www. pasonsme.com', 'confidence': 0.93154, 'lang': 'ar', 'bounding_box': (102.0, 174.0, 174.0, 187.0)}, {'text': 'Dubat lInvesmenl Park-2, Dubai, U AE', 'confidence': 0.83172, 'lang': 'ar', 'bounding_box': (292.0, 172.0, 423.0, 184.0)}, {'text': 'Tel 04-0840966, Mob0557692020', 'confidence': 0.95492, 'lang': 'ar', 'bounding_box': (297.0, 181.0, 418.0, 195.0)}, {'text': 'Pasons S/M&.Depl Slore', 'confidence': 0.93, 'lang': 'ar', 'bounding_box': (316.0, 163.0, 400.0, 175.0)}, {'text': '3 87158069', 'confidence': 0.96666, 'lang': 'ar', 'bounding_box': (47.0, 272.0, 97.0, 286.0)}, {'text': '1 6291031020837', 'confidence': 0.9614, 'lang': 'ar', 'bounding_box': (48.0, 226.0, 118.0, 240.0)}, {'text': 'Sri."tem', 'confidence': 0.85346, 'lang': 'ar', 'bounding_box': (49.0, 203.0, 91.0, 218.0)}, {'text': 'الذوع الرفم', 'confidence': 0.81658, 'lang': 'ar', 'bounding_box': (52.0, 215.0, 91.0, 228.0)}, {'text': '990/1125020304', 'confidence': 0.94658, 'lang': 'ar', 'bounding_box': (58.0, 249.0, 116.0, 262.0)}, {'text': 'Nezo Set 1Kg Pht Blue', 'confidence': 0.94606, 'lang': 'ar', 'bounding_box': (58.0, 283.0, 139.0, 297.0)}, {'text': 'Marmum Yoghurt 1Kg Ful Cream', 'confidence': 0.92675, 'lang': 'ar', 'bounding_box': (60.0, 237.0, 173.0, 252.0)}, {'text': 'Carrot', 'confidence': 0.99895, 'lang': 'ar', 'bounding_box': (61.0, 261.0, 85.0, 272.0)}, {'text': 'Tax Invoice', 'confidence': 0.99887, 'lang': 'ar', 'bounding_box': (90.0, 193.0, 142.0, 207.0)}, {'text': 'الكبية', 'confidence': 0.87257, 'lang': 'ar', 'bounding_box': (130.0, 217.0, 149.0, 228.0)}, {'text': '8.000 PCS', 'confidence': 0.87793, 'lang': 'ar', 'bounding_box': (129.0, 226.0, 177.0, 241.0)}, {'text': 'Oty', 'confidence': 0.85913, 'lang': 'ar', 'bounding_box': (131.0, 205.0, 147.0, 219.0)}, {'text': '1.000', 'confidence': 0.9831, 'lang': 'ar', 'bounding_box': (131.0, 275.0, 153.0, 287.0)}, {'text': '2.030', 'confidence': 0.90694, 'lang': 'ar', 'bounding_box': (132.0, 253.0, 153.0, 262.0)}, {'text': 'KGS', 'confidence': 0.99783, 'lang': 'ar', 'bounding_box': (155.0, 253.0, 176.0, 264.0)}, {'text': 'PCS', 'confidence': 0.98292, 'lang': 'ar', 'bounding_box': (154.0, 275.0, 176.0, 288.0)}, {'text': 'Unit', 'confidence': 0.85625, 'lang': 'ar', 'bounding_box': (160.0, 207.0, 176.0, 218.0)}, {'text': 'السع', 'confidence': 0.80372, 'lang': 'ar', 'bounding_box': (161.0, 219.0, 177.0, 229.0)}, {'text': 'نتورة ضرية', 'confidence': 0.84939, 'lang': 'ar', 'bounding_box': (181.0, 193.0, 225.0, 208.0)}, {'text': 'السجرع', 'confidence': 0.61214, 'lang': 'ar', 'bounding_box': (193.0, 220.0, 223.0, 230.0)}, {'text': 'Amount', 'confidence': 0.97884, 'lang': 'ar', 'bounding_box': (194.0, 208.0, 223.0, 220.0)}, {'text': '5200', 'confidence': 0.99853, 'lang': 'ar', 'bounding_box': (199.0, 230.0, 223.0, 242.0)}, {'text': '13.20', 'confidence': 0.95806, 'lang': 'ar', 'bounding_box': (200.0, 253.0, 222.0, 265.0)}, {'text': '4.00', 'confidence': 0.98878, 'lang': 'ar', 'bounding_box': (203.0, 277.0, 222.0, 288.0)}, {'text': 'Sd." tom', 'confidence': 0.70138, 'lang': 'ar', 'bounding_box': (268.0, 220.0, 310.0, 236.0)}, {'text': '1 6291031020837', 'confidence': 0.98681, 'lang': 'ar', 'bounding_box': (271.0, 246.0, 337.0, 257.0)}, {'text': 'النوع الرقم', 'confidence': 0.76973, 'lang': 'ar', 'bounding_box': (272.0, 234.0, 311.0, 246.0)}, {'text': 'Item Counl 8', 'confidence': 0.96014, 'lang': 'ar', 'bounding_box': (274.0, 282.0, 324.0, 293.0)}, {'text': 'Mamum Yoghart 1Kg Fut Creem', 'confidence': 0.92359, 'lang': 'ar', 'bounding_box': (280.0, 254.0, 393.0, 269.0)}, {'text': 'Tax Invoice', 'confidence': 0.99963, 'lang': 'ar', 'bounding_box': (310.0, 210.0, 361.0, 224.0)}, {'text': 'TRN 100453349100003', 'confidence': 0.99516, 'lang': 'ar', 'bounding_box': (317.0, 202.0, 398.0, 212.0)}, {'text': 'sine pasonvime con', 'confidence': 0.80441, 'lang': 'ar', 'bounding_box': (321.0, 192.0, 393.0, 204.0)}, {'text': 'TOTAL AMOUNT', 'confidence': 0.99568, 'lang': 'ar', 'bounding_box': (331.0, 269.0, 395.0, 283.0)}, {'text': 'Oty', 'confidence': 0.98206, 'lang': 'ar', 'bounding_box': (350.0, 224.0, 367.0, 236.0)}, {'text': 'الخية', 'confidence': 0.71984, 'lang': 'ar', 'bounding_box': (350.0, 235.0, 369.0, 247.0)}, {'text': '8.600 PCS', 'confidence': 0.88983, 'lang': 'ar', 'bounding_box': (350.0, 245.0, 396.0, 258.0)}, {'text': 'Unsi', 'confidence': 0.63635, 'lang': 'ar', 'bounding_box': (379.0, 223.0, 396.0, 236.0)}, {'text': 'السم', 'confidence': 0.75902, 'lang': 'ar', 'bounding_box': (381.0, 236.0, 396.0, 246.0)}, {'text': '52', 'confidence': 0.99216, 'lang': 'ar', 'bounding_box': (381.0, 283.0, 414.0, 306.0)}, {'text': 'نتورة ضربية', 'confidence': 0.82163, 'lang': 'ar', 'bounding_box': (401.0, 211.0, 444.0, 224.0)}, {'text': 'الجسع', 'confidence': 0.67052, 'lang': 'ar', 'bounding_box': (412.0, 235.0, 442.0, 248.0)}, {'text': 'Anoutt', 'confidence': 0.70094, 'lang': 'ar', 'bounding_box': (412.0, 222.0, 443.0, 238.0)}, {'text': '52.00', 'confidence': 0.98219, 'lang': 'ar', 'bounding_box': (418.0, 271.0, 440.0, 283.0)}, {'text': '52.00', 'confidence': 0.99128, 'lang': 'ar', 'bounding_box': (420.0, 246.0, 442.0, 258.0)}, {'text': '4 990112900055', 'confidence': 0.9443, 'lang': 'ar', 'bounding_box': (47.0, 295.0, 116.0, 310.0)}, {'text': '9901148020055', 'confidence': 0.91758, 'lang': 'ar', 'bounding_box': (56.0, 320.0, 115.0, 332.0)}, {'text': 'Chili India', 'confidence': 0.94447, 'lang': 'ar', 'bounding_box': (58.0, 305.0, 96.0, 321.0)}, {'text': 'Cucumber', 'confidence': 0.97363, 'lang': 'ar', 'bounding_box': (58.0, 329.0, 96.0, 342.0)}, {'text': '0.506 KGS', 'confidence': 0.97568, 'lang': 'ar', 'bounding_box': (128.0, 296.0, 176.0, 312.0)}, {'text': '2.085 KG8', 'confidence': 0.93929, 'lang': 'ar', 'bounding_box': (128.0, 320.0, 175.0, 335.0)}, {'text': '10.10', 'confidence': 0.93639, 'lang': 'ar', 'bounding_box': (199.0, 300.0, 221.0, 312.0)}, {'text': '8.24', 'confidence': 0.99604, 'lang': 'ar', 'bounding_box': (202.0, 324.0, 221.0, 336.0)}, {'text': 'Tax Inolusie', 'confidence': 0.92049, 'lang': 'ar', 'bounding_box': (294.0, 308.0, 339.0, 321.0)}, {'text': 'VAT%', 'confidence': 0.99737, 'lang': 'ar', 'bounding_box': (303.0, 319.0, 337.0, 330.0)}, {'text': 'Paid Amounil(MAS)', 'confidence': 0.94454, 'lang': 'ar', 'bounding_box': (316.0, 293.0, 382.0, 306.0)}, {'text': 'Exdl VAT', 'confidence': 0.95481, 'lang': 'ar', 'bounding_box': (332.0, 318.0, 368.0, 331.0)}, {'text': '49.52', 'confidence': 0.97144, 'lang': 'ar', 'bounding_box': (345.0, 330.0, 367.0, 341.0)}, {'text': 'IncI VAT', 'confidence': 0.92279, 'lang': 'ar', 'bounding_box': (376.0, 320.0, 406.0, 331.0)}, {'text': '52.00', 'confidence': 0.99955, 'lang': 'ar', 'bounding_box': (385.0, 331.0, 406.0, 341.0)}, {'text': 'الشسرية الشفئة', 'confidence': 0.79839, 'lang': 'ar', 'bounding_box': (387.0, 309.0, 430.0, 322.0)}, {'text': '52.00', 'confidence': 0.99835, 'lang': 'ar', 'bounding_box': (418.0, 295.0, 441.0, 306.0)}, {'text': '2.48', 'confidence': 0.96288, 'lang': 'ar', 'bounding_box': (418.0, 331.0, 436.0, 342.0)}, {'text': 'VAT', 'confidence': 0.99897, 'lang': 'ar', 'bounding_box': (420.0, 320.0, 438.0, 332.0)}, {'text': 'Ilem Count 12', 'confidence': 0.95379, 'lang': 'ar', 'bounding_box': (51.0, 356.0, 105.0, 369.0)}, {'text': 'Paid Amounil(MAS)', 'confidence': 0.88828, 'lang': 'ar', 'bounding_box': (94.0, 369.0, 161.0, 382.0)}, {'text': 'TOTAL AMOUNT', 'confidence': 0.99618, 'lang': 'ar', 'bounding_box': (108.0, 344.0, 173.0, 359.0)}, {'text': '$7-50', 'confidence': 0.88649, 'lang': 'ar', 'bounding_box': (152.0, 351.0, 205.0, 379.0)}, {'text': '87.54', 'confidence': 0.95879, 'lang': 'ar', 'bounding_box': (196.0, 347.0, 218.0, 359.0)}, {'text': '87.54', 'confidence': 0.99876, 'lang': 'ar', 'bounding_box': (196.0, 372.0, 218.0, 384.0)}, {'text': '04/00/2026', 'confidence': 0.97157, 'lang': 'ar', 'bounding_box': (272.0, 366.0, 313.0, 378.0)}, {'text': 'Served by:', 'confidence': 0.98038, 'lang': 'ar', 'bounding_box': (274.0, 342.0, 312.0, 355.0)}, {'text': 'Date', 'confidence': 0.96876, 'lang': 'ar', 'bounding_box': (274.0, 356.0, 294.0, 368.0)}, {'text': '09:19', 'confidence': 0.9983, 'lang': 'ar', 'bounding_box': (314.0, 366.0, 339.0, 379.0)}, {'text': 'Tione', 'confidence': 0.90473, 'lang': 'ar', 'bounding_box': (317.0, 355.0, 338.0, 369.0)}, {'text': 'SAFWAN CHANGOTH', 'confidence': 0.99853, 'lang': 'ar', 'bounding_box': (331.0, 343.0, 411.0, 356.0)}, {'text': 'Store', 'confidence': 0.97964, 'lang': 'ar', 'bounding_box': (349.0, 357.0, 371.0, 369.0)}, {'text': '09', 'confidence': 0.9946, 'lang': 'ar', 'bounding_box': (356.0, 368.0, 369.0, 379.0)}, {'text': 'POS', 'confidence': 0.96288, 'lang': 'ar', 'bounding_box': (382.0, 357.0, 402.0, 369.0)}, {'text': '1', 'confidence': 0.99959, 'lang': 'ar', 'bounding_box': (388.0, 369.0, 395.0, 378.0)}, {'text': 'BI!', 'confidence': 0.77066, 'lang': 'ar', 'bounding_box': (406.0, 359.0, 420.0, 369.0)}, {'text': '137', 'confidence': 0.99983, 'lang': 'ar', 'bounding_box': (408.0, 369.0, 423.0, 379.0)}, {'text': 'Served by:', 'confidence': 0.97644, 'lang': 'ar', 'bounding_box': (51.0, 417.0, 90.0, 430.0)}, {'text': 'Tax Inclusive', 'confidence': 0.99479, 'lang': 'ar', 'bounding_box': (72.0, 385.0, 116.0, 396.0)}, {'text': 'VAT%', 'confidence': 0.99315, 'lang': 'ar', 'bounding_box': (81.0, 395.0, 114.0, 406.0)}, {'text': '5', 'confidence': 0.97314, 'lang': 'ar', 'bounding_box': (89.0, 405.0, 98.0, 414.0)}, {'text': 'Excl. VAT', 'confidence': 0.91014, 'lang': 'ar', 'bounding_box': (109.0, 396.0, 145.0, 406.0)}, {'text': 'SAPWAN CHANGOTH', 'confidence': 0.98241, 'lang': 'ar', 'bounding_box': (109.0, 419.0, 189.0, 431.0)}, {'text': '83.37', 'confidence': 0.99961, 'lang': 'ar', 'bounding_box': (122.0, 405.0, 145.0, 417.0)}, {'text': 'Incl VAT', 'confidence': 0.9299, 'lang': 'ar', 'bounding_box': (152.0, 395.0, 184.0, 408.0)}, {'text': '87.54', 'confidence': 0.99808, 'lang': 'ar', 'bounding_box': (162.0, 407.0, 184.0, 417.0)}, {'text': '4.17', 'confidence': 0.99897, 'lang': 'ar', 'bounding_box': (196.0, 408.0, 213.0, 417.0)}, {'text': 'VAT', 'confidence': 0.99929, 'lang': 'ar', 'bounding_box': (197.0, 397.0, 216.0, 408.0)}, {'text': 'No Cash Refund, Thenk You, Visit Again', 'confidence': 0.92765, 'lang': 'ar', 'bounding_box': (287.0, 404.0, 422.0, 419.0)}, {'text': 'Keep Receipt For Exchange, T&C Apply', 'confidence': 0.98833, 'lang': 'ar', 'bounding_box': (289.0, 382.0, 423.0, 396.0)}, {'text': 'No Exchange On Under Garments', 'confidence': 0.96621, 'lang': 'ar', 'bounding_box': (297.0, 392.0, 412.0, 408.0)}, {'text': 'Date', 'confidence': 0.99774, 'lang': 'ar', 'bounding_box': (50.0, 431.0, 70.0, 442.0)}, {'text': '05/08/2026', 'confidence': 0.99956, 'lang': 'ar', 'bounding_box': (50.0, 441.0, 90.0, 452.0)}, {'text': '09:12', 'confidence': 0.99951, 'lang': 'ar', 'bounding_box': (93.0, 442.0, 116.0, 452.0)}, {'text': 'Time', 'confidence': 0.99936, 'lang': 'ar', 'bounding_box': (95.0, 432.0, 115.0, 443.0)}, {'text': 'Store', 'confidence': 0.91331, 'lang': 'ar', 'bounding_box': (126.0, 433.0, 148.0, 444.0)}, {'text': '09', 'confidence': 0.8919, 'lang': 'ar', 'bounding_box': (133.0, 443.0, 146.0, 453.0)}, {'text': 'POS', 'confidence': 0.99288, 'lang': 'ar', 'bounding_box': (159.0, 433.0, 180.0, 444.0)}, {'text': '1', 'confidence': 0.99948, 'lang': 'ar', 'bounding_box': (166.0, 445.0, 172.0, 452.0)}, {'text': 'Bil', 'confidence': 0.98704, 'lang': 'ar', 'bounding_box': (184.0, 435.0, 198.0, 444.0)}, {'text': '115', 'confidence': 0.9999, 'lang': 'ar', 'bounding_box': (185.0, 444.0, 200.0, 454.0)}, {'text': '090120260804137', 'confidence': 0.99762, 'lang': 'ar', 'bounding_box': (324.0, 438.0, 384.0, 451.0)}, {'text': 'Keep Receipt For Exchange, T&C Apply', 'confidence': 0.97615, 'lang': 'ar', 'bounding_box': (66.0, 456.0, 201.0, 471.0)}, {'text': 'No Exchenge On Under Gaments', 'confidence': 0.96262, 'lang': 'ar', 'bounding_box': (74.0, 467.0, 189.0, 482.0)}, {'text': 'No Cesh Refund, Thenk You, Visit Again', 'confidence': 0.96462, 'lang': 'ar', 'bounding_box': (65.0, 478.0, 198.0, 493.0)}, {'text': '090120260805115', 'confidence': 0.9742, 'lang': 'ar', 'bounding_box': (101.0, 513.0, 161.0, 525.0)}], 'field_confidence': {'vendor': 0.20203221428571427, 'date': 0.2893069285714286, 'currency': 0.7218167857142856, 'amount': 0.805829, 'vat_rate': 0.795971, 'vat_amount': 0.4, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.8275599285714285, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 1.0, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'vat_amount', 'discount', 'service_charge', 'tip', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** l (0.18), 5R (0.39), CESETSED (0.40), mmes (0.46), A esi (0.30), 2S11 (0.39), 222 (0.31), 2n1 (0.35), 3s1 (0.32), x (0.42), ji 3 ai (0.45), EmJi (0.32), L (0.10)

**Raw text:**

```
l
5R
87-54
PASONS
CESETSED
Dubai Investment Park-2 . Dubai , U AE
Pasons S/M&Dept.Store
SicsE
PASONS
SiLEt
mmes
Tel: 04-8840966 . Mob:0557692020
TRN 100453349100003
www.pasonsme.com
Dubai Investment Parlk-2. Dubai . U AE
Tel 04-0840966 . Mob:0557602020
Pasons S/M&.Depl Slore
3 87158069
1 6291031020837
Sr. ltem
A esi
9901125020304
Nezo Salt 1Kg Pkt Blue
Marmum Yoghurt 1Kg Full Cresm
Carrot
Tax Invoice
2S11
8.000 PCS
Cty
1.000
2.030
KGS
PCS
Unil
23
222
2n1
Amount
52.00
13.20
4.00
Si.tom
1 6291031020837
A ex3
Item Counl 8
Mamum Yoghiet 1Kg Full Cream
Tax Invoice
TRN 100453349100003
www pasonime.comn
TOTAL AMOUNT
Oty
3s1
8.000 PCS
Uni
x
52
ji 3 ai
EmJi
Ancutt
52.00
52.00
4 9001129005055
9901148020855
Chil India
Cucumber
0.505 KGS
2.085 KGS
10.10
8.24
Tax Inclusive
VAT%
Paid Amoutil(MAS)
Excl VAT
49.52
Inci VAT
52.00
L
52.00
2.48
VAT
Ilem Count 12
Paid Amount(MAS)
TOTAL AMOUNT
87-50
87.54
87.54
04/08/2026
Served by
Date
09:19
Time
SAFWAN CHANGOTH
Store
09
POS
1
Bill
137
Served by:
Tax Inclusive
VAT%
5
Exd.VAT
SAFWAN CHANGOTH
83.37
Incl VAT
87.54
4.17
VAT
No Cash Refund, Thenk You. Visit Again
Keep Receipt For Exchange, T&.C Apply
No Exchange On Under Garments
Date
05/08/2026
09:12
Time
Store
09
POS
1
Bil
115
090120260804137
Keep Receipt For Exchange, T&C Apply
No Exchange On Under Gaments
No Cash Refund,Thank You, Visit Again
090120260805115
```

### Arabic recognizer

**Low-confidence words (<0.5):** S (0.17), S (0.49), MMMES (0.37)

**Raw text:**

```
mnymg
mniypy
S
$7-54
PASONS
CELTTED
Dubai Iivestment Park-2, Dubai , U AE
Pasons S/M&Dept. Store
S
PASONS
SLEE
MMMES
Tet 04-8840966, Mob:0557892020
TRN 100453349100003
www. pasonsme.com
Dubat lInvesmenl Park-2, Dubai, U AE
Tel 04-0840966, Mob0557692020
Pasons S/M&.Depl Slore
3 87158069
1 6291031020837
Sri."tem
الذوع الرفم
990/1125020304
Nezo Set 1Kg Pht Blue
Marmum Yoghurt 1Kg Ful Cream
Carrot
Tax Invoice
الكبية
8.000 PCS
Oty
1.000
2.030
KGS
PCS
Unit
السع
نتورة ضرية
السجرع
Amount
5200
13.20
4.00
Sd." tom
1 6291031020837
النوع الرقم
Item Counl 8
Mamum Yoghart 1Kg Fut Creem
Tax Invoice
TRN 100453349100003
sine pasonvime con
TOTAL AMOUNT
Oty
الخية
8.600 PCS
Unsi
السم
52
نتورة ضربية
الجسع
Anoutt
52.00
52.00
4 990112900055
9901148020055
Chili India
Cucumber
0.506 KGS
2.085 KG8
10.10
8.24
Tax Inolusie
VAT%
Paid Amounil(MAS)
Exdl VAT
49.52
IncI VAT
52.00
الشسرية الشفئة
52.00
2.48
VAT
Ilem Count 12
Paid Amounil(MAS)
TOTAL AMOUNT
$7-50
87.54
87.54
04/00/2026
Served by:
Date
09:19
Tione
SAFWAN CHANGOTH
Store
09
POS
1
BI!
137
Served by:
Tax Inclusive
VAT%
5
Excl. VAT
SAPWAN CHANGOTH
83.37
Incl VAT
87.54
4.17
VAT
No Cash Refund, Thenk You, Visit Again
Keep Receipt For Exchange, T&C Apply
No Exchange On Under Garments
Date
05/08/2026
09:12
Time
Store
09
POS
1
Bil
115
090120260804137
Keep Receipt For Exchange, T&C Apply
No Exchenge On Under Gaments
No Cesh Refund, Thenk You, Visit Again
090120260805115
```
