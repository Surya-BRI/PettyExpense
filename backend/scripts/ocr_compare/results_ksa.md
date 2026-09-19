# OCR results — ksa

Engine: single shared-detection RapidOCR pipeline (mode=`auto`) — one detection pass,
sequential English + Arabic recognition against the same detected regions.
Summary reflects the actual production result (`OcrService.run`). The per-image
sections below also show each recognizer's raw reading for debugging.
Images: `9`.

## Summary

| Image | Vendor | Amount | VAT | Total | Date | Currency | Mismatch |
|---|---|---|---|---|---|---|---|
| ksa1.png | الشارقة | 208.0 | 0.0 | 208.0 |  | SAR | False |
| ksa2.png | شركة قمة الخليج المحدودة للأجرة العامة | 45.0 | 0.0 | 45.0 |  | SAR | False |
| ksa3.png | Shahad Tawik Company | 0.01 | 0.0 | 0.01 | 29-6-26 |  | False |
| ksa4.png | No.:C/58444 | 55.0 | 0.0 | 1.0 |  |  | False |
| ksa5.png | TAXI AL-AJME | 2.09 | 0.0 | 2.09 |  |  | False |
| ksa6.png | Shaml Al-Doha Company ركة شمل الدوحة | 351.0 | 0.0 | 351.0 | 05/03/26 |  | False |
| ksa7.png | شركة سلطان منير الحارثي وشريكه للأجرة العامة | 45.0 | 0.0 | 45.0 |  | SAR | False |
| ksa8.png | 4 487% | 72.9 | 0.0 | 72.9 | Feb 8 | SAR | False |
| ksa9.png |  | 42.0 | 0.0 | 42.0 | Oct 12 | SAR | False |

## ksa1.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'الشارقة', 'expense_type': None, 'amount': 208.0, 'vat_amount': 0.0, 'total_amount': 208.0, 'currency': 'SAR', 'date': '', 'confidence': 0.15, 'field_confidence': {'vendor': 0.2723645136246787, 'date': 0.0, 'currency': 0.5504159023136247, 'amount': 0.2769369350899743, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.2769369350899743, 'invoice_number': 0.46936804498714657, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'الشارقة', 'confidence': 0.2723645136246787, 'evidence': 'الشارقة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': 'SAR', 'confidence': 0.5504159023136247, 'evidence': 'Notes SAR هللة إلى من', 'signals': ['currency_code_match', 'position_prior_upper'], 'low': False}, 'amount': {'value': 208.0, 'confidence': 0.2769369350899743, 'evidence': 'KAD 208 H51', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'amount_equals_total_no_vat'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 208.0, 'confidence': 0.2769369350899743, 'evidence': 'KAD 208 H51', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': '0583162117', 'confidence': 0.46936804498714657, 'evidence': '0583162117:JI9', 'signals': ['invoice_number_label', 'fuzzy_label_match', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'sL\nالشارقة\nأجرة عامة\nشركة الشارقة\nSHARJA\nأجرة عامة\n0583162117:JI9\nجوال 05831621\n90375 sljajgilá\n92375 فانورة راكب\nCustomer Invoise\nCustomer Invoise\nDate 28 166/26.\nDate 2i /66/2b الموافق التاريخ\n//\nالمحترم\nاسم الراكب\nCustomer Name:.\nCustomer Name:.\nالشركة غير سؤوة عن عدم تواجدرق اوحة بالفاتورة رقم الللوحة،؛\n.\nملاحظات Fare الأجرة Place المكان\nFare Place\nNotes J aLLs\nNotes SAR هللة إلى من\nKAD 208 H51\nKAAD2C 45+\nto Dalay\nDz.\nTotal\nTotal.\nالإجمالي\nرقم السيارة توقيع السائق اسم السائق\nعزيزي الراكب نرجو التأكد من استلام جميع أمتعتكم\nمع أجمل تمنياتنا لكم سلامة الوصول\nشكرا لتفضلكم بركوب السيارة', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'sL', 'confidence': 0.58797, 'lang': 'en', 'bounding_box': (32.0, 9.0, 199.0, 75.0)}, {'text': 'SHARJA', 'confidence': 0.98494, 'lang': 'en', 'bounding_box': (34.0, 66.0, 197.0, 116.0)}, {'text': '0583162117:JI9', 'confidence': 0.95517, 'lang': 'en', 'bounding_box': (387.0, 106.0, 553.0, 142.0)}, {'text': 'sljajgilá', 'confidence': 0.71346, 'lang': 'en', 'bounding_box': (238.0, 143.0, 382.0, 185.0)}, {'text': '90375', 'confidence': 0.89387, 'lang': 'en', 'bounding_box': (89.0, 153.0, 198.0, 197.0)}, {'text': 'Customer Invoise', 'confidence': 0.99992, 'lang': 'en', 'bounding_box': (227.0, 182.0, 391.0, 214.0)}, {'text': 'Date 28 166/26.', 'confidence': 0.83262, 'lang': 'en', 'bounding_box': (47.0, 232.0, 257.0, 271.0)}, {'text': '//', 'confidence': 0.31979, 'lang': 'en', 'bounding_box': (404.0, 236.0, 564.0, 281.0)}, {'text': 'Customer Name:..', 'confidence': 0.96351, 'lang': 'en', 'bounding_box': (58.0, 324.0, 212.0, 352.0)}, {'text': '..', 'confidence': 0.68395, 'lang': 'en', 'bounding_box': (446.0, 359.0, 547.0, 388.0)}, {'text': 'Fare', 'confidence': 0.98373, 'lang': 'en', 'bounding_box': (299.0, 392.0, 406.0, 420.0)}, {'text': 'Place', 'confidence': 0.99989, 'lang': 'en', 'bounding_box': (413.0, 394.0, 468.0, 418.0)}, {'text': 'Notes', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (153.0, 425.0, 210.0, 449.0)}, {'text': 'J', 'confidence': 0.79738, 'lang': 'en', 'bounding_box': (301.0, 420.0, 361.0, 453.0)}, {'text': 'aLLs', 'confidence': 0.5621, 'lang': 'en', 'bounding_box': (358.0, 420.0, 404.0, 448.0)}, {'text': 'KAD 208', 'confidence': 0.91356, 'lang': 'en', 'bounding_box': (86.0, 457.0, 291.0, 498.0)}, {'text': 'H51', 'confidence': 0.76855, 'lang': 'en', 'bounding_box': (287.0, 452.0, 362.0, 506.0)}, {'text': 'to Dalay', 'confidence': 0.90988, 'lang': 'en', 'bounding_box': (75.0, 492.0, 257.0, 543.0)}, {'text': 'Total', 'confidence': 0.99993, 'lang': 'en', 'bounding_box': (58.0, 601.0, 118.0, 628.0)}, {'text': 'الشارقة', 'confidence': 0.98835, 'lang': 'ar', 'bounding_box': (32.0, 9.0, 199.0, 75.0)}, {'text': 'أجرة عامة', 'confidence': 0.94094, 'lang': 'ar', 'bounding_box': (418.0, 17.0, 536.0, 57.0)}, {'text': 'شركة الشارقة', 'confidence': 0.95173, 'lang': 'ar', 'bounding_box': (353.0, 49.0, 581.0, 111.0)}, {'text': 'SHARA', 'confidence': 0.97579, 'lang': 'ar', 'bounding_box': (34.0, 66.0, 197.0, 116.0)}, {'text': 'أجرة عامة', 'confidence': 0.92784, 'lang': 'ar', 'bounding_box': (50.0, 105.0, 142.0, 142.0)}, {'text': 'جوال 05831621', 'confidence': 0.92911, 'lang': 'ar', 'bounding_box': (387.0, 106.0, 553.0, 142.0)}, {'text': 'فانورة راكب', 'confidence': 0.93465, 'lang': 'ar', 'bounding_box': (238.0, 143.0, 382.0, 185.0)}, {'text': '92375', 'confidence': 0.90226, 'lang': 'ar', 'bounding_box': (89.0, 153.0, 198.0, 197.0)}, {'text': 'Customer Invoise', 'confidence': 0.96822, 'lang': 'ar', 'bounding_box': (227.0, 182.0, 391.0, 214.0)}, {'text': 'Date 2i /66/2b', 'confidence': 0.88439, 'lang': 'ar', 'bounding_box': (47.0, 232.0, 257.0, 271.0)}, {'text': 'الموافق', 'confidence': 0.92778, 'lang': 'ar', 'bounding_box': (277.0, 241.0, 372.0, 275.0)}, {'text': 'التاريخ', 'confidence': 0.99113, 'lang': 'ar', 'bounding_box': (404.0, 236.0, 564.0, 281.0)}, {'text': 'المحترم', 'confidence': 0.86565, 'lang': 'ar', 'bounding_box': (55.0, 290.0, 136.0, 319.0)}, {'text': 'اسم الراكب', 'confidence': 0.90734, 'lang': 'ar', 'bounding_box': (457.0, 295.0, 557.0, 321.0)}, {'text': 'Customer Name:..', 'confidence': 0.94462, 'lang': 'ar', 'bounding_box': (58.0, 324.0, 212.0, 352.0)}, {'text': 'الشركة غير سؤوة عن عدم تواجدرق اوحة بالفاتورة', 'confidence': 0.66687, 'lang': 'ar', 'bounding_box': (63.0, 359.0, 336.0, 387.0)}, {'text': 'رقم الللوحة،؛', 'confidence': 0.83898, 'lang': 'ar', 'bounding_box': (446.0, 359.0, 547.0, 388.0)}, {'text': 'ملاحظات', 'confidence': 0.96626, 'lang': 'ar', 'bounding_box': (137.0, 393.0, 221.0, 416.0)}, {'text': 'Fare الأجرة', 'confidence': 0.8797, 'lang': 'ar', 'bounding_box': (299.0, 392.0, 406.0, 420.0)}, {'text': 'Place', 'confidence': 0.99953, 'lang': 'ar', 'bounding_box': (413.0, 394.0, 468.0, 418.0)}, {'text': 'المكان', 'confidence': 0.99825, 'lang': 'ar', 'bounding_box': (475.0, 392.0, 541.0, 419.0)}, {'text': 'Notes', 'confidence': 0.9996, 'lang': 'ar', 'bounding_box': (153.0, 425.0, 210.0, 449.0)}, {'text': 'ريال', 'confidence': 0.97341, 'lang': 'ar', 'bounding_box': (301.0, 420.0, 361.0, 453.0)}, {'text': 'هللة', 'confidence': 0.9384, 'lang': 'ar', 'bounding_box': (358.0, 420.0, 404.0, 448.0)}, {'text': 'إلى', 'confidence': 0.93128, 'lang': 'ar', 'bounding_box': (414.0, 421.0, 459.0, 453.0)}, {'text': 'من', 'confidence': 0.89716, 'lang': 'ar', 'bounding_box': (483.0, 425.0, 518.0, 452.0)}, {'text': 'KAAD2C', 'confidence': 0.57626, 'lang': 'ar', 'bounding_box': (86.0, 457.0, 291.0, 498.0)}, {'text': '45+', 'confidence': 0.50178, 'lang': 'ar', 'bounding_box': (287.0, 452.0, 362.0, 506.0)}, {'text': ' Dz.', 'confidence': 0.47398, 'lang': 'ar', 'bounding_box': (75.0, 492.0, 257.0, 543.0)}, {'text': 'Total.', 'confidence': 0.95539, 'lang': 'ar', 'bounding_box': (58.0, 601.0, 118.0, 628.0)}, {'text': 'الإجمالي', 'confidence': 0.97751, 'lang': 'ar', 'bounding_box': (370.0, 599.0, 467.0, 637.0)}, {'text': 'رقم السيارة  توقيع السائق', 'confidence': 0.91784, 'lang': 'ar', 'bounding_box': (119.0, 645.0, 465.0, 678.0)}, {'text': 'اسم السائق', 'confidence': 0.97451, 'lang': 'ar', 'bounding_box': (456.0, 644.0, 541.0, 675.0)}, {'text': 'عزيزي الراكب نرجو التأكد من استلام جميع أمتعتكم', 'confidence': 0.97736, 'lang': 'ar', 'bounding_box': (100.0, 679.0, 499.0, 712.0)}, {'text': 'مع أجمل تمنياتنا لكم سلامة الوصول', 'confidence': 0.97287, 'lang': 'ar', 'bounding_box': (164.0, 711.0, 435.0, 743.0)}, {'text': 'شكرا لتفضلكم بركوب السيارة', 'confidence': 0.96699, 'lang': 'ar', 'bounding_box': (181.0, 740.0, 417.0, 778.0)}], 'field_confidence': {'vendor': 0.2723645136246787, 'date': 0.0, 'currency': 0.5504159023136247, 'amount': 0.2769369350899743, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.2769369350899743, 'invoice_number': 0.46936804498714657, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** // (0.32)

**Raw text:**

```
sL
SHARJA
0583162117:JI9
sljajgilá
90375
Customer Invoise
Date 28 166/26.
//
Customer Name:..
..
Fare
Place
Notes
J
aLLs
KAD 208
H51
to Dalay
Total
```

### Arabic recognizer

**Low-confidence words (<0.5):**  Dz. (0.47)

**Raw text:**

```
الشارقة
أجرة عامة
شركة الشارقة
SHARA
أجرة عامة
جوال 05831621
فانورة راكب
92375
Customer Invoise
Date 2i /66/2b
الموافق
التاريخ
المحترم
اسم الراكب
Customer Name:..
الشركة غير سؤوة عن عدم تواجدرق اوحة بالفاتورة
رقم الللوحة،؛
ملاحظات
Fare الأجرة
Place
المكان
Notes
ريال
هللة
إلى
من
KAAD2C
45+
 Dz.
Total.
الإجمالي
رقم السيارة  توقيع السائق
اسم السائق
عزيزي الراكب نرجو التأكد من استلام جميع أمتعتكم
مع أجمل تمنياتنا لكم سلامة الوصول
شكرا لتفضلكم بركوب السيارة
```

## ksa2.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'شركة قمة الخليج المحدودة للأجرة العامة', 'expense_type': None, 'amount': 45.0, 'vat_amount': 0.0, 'total_amount': 45.0, 'currency': 'SAR', 'date': '', 'confidence': 0.23, 'field_confidence': {'vendor': 0.2789499462934947, 'date': 0.0, 'currency': 0.5787643645990922, 'amount': 0.7881363441754916, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.7881363441754916, 'invoice_number': 0.6124116611195158, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'شركة قمة الخليج المحدودة للأجرة العامة', 'confidence': 0.2789499462934947, 'evidence': 'شركة قمة الخليج المحدودة للأجرة العامة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': 'SAR', 'confidence': 0.5787643645990922, 'evidence': 'SAR', 'signals': ['currency_code_match', 'position_prior_upper'], 'low': False}, 'amount': {'value': 45.0, 'confidence': 0.7881363441754916, 'evidence': 'المجموع فقط 45/.', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'amount_equals_total_no_vat'], 'low': False}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 45.0, 'confidence': 0.7881363441754916, 'evidence': 'المجموع فقط 45/.', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'invoice_number': {'value': '0386', 'confidence': 0.6124116611195158, 'evidence': '0386 فاتورة', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'شركة قمة الخليج المحدودة للأجرة العامة\nQema Al-Khaleej Limited Co. For General Rent\n0386 فاتورة\n0386 Invoice 25/06/\nIvoie56التاريخ\nإلى من السعر\nJU\nSAR\nkiagdomp toner.\nKiigdomtner\nmalaz\nDrlaz\nالمجموع فقط 45/.\n451.', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'Qema Al-Khaleej Limited Co. For General Rent', 'confidence': 0.98828, 'lang': 'en', 'bounding_box': (53.0, 81.0, 579.0, 128.0)}, {'text': '0386', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (138.0, 154.0, 223.0, 200.0)}, {'text': 'Invoice 25/06/', 'confidence': 0.92315, 'lang': 'en', 'bounding_box': (242.0, 173.0, 583.0, 220.0)}, {'text': 'JU', 'confidence': 0.6349, 'lang': 'en', 'bounding_box': (371.0, 285.0, 439.0, 330.0)}, {'text': 'kiagdomp toner.', 'confidence': 0.8346, 'lang': 'en', 'bounding_box': (95.0, 362.0, 344.0, 412.0)}, {'text': 'malaz', 'confidence': 0.75603, 'lang': 'en', 'bounding_box': (187.0, 411.0, 297.0, 453.0)}, {'text': '451.', 'confidence': 0.83589, 'lang': 'en', 'bounding_box': (367.0, 581.0, 459.0, 661.0)}, {'text': 'شركة قمة الخليج المحدودة للأجرة العامة', 'confidence': 0.94363, 'lang': 'ar', 'bounding_box': (39.0, 23.0, 585.0, 88.0)}, {'text': 'Qema Al-Khaleej Limited Co. For General Rent', 'confidence': 0.98525, 'lang': 'ar', 'bounding_box': (53.0, 81.0, 579.0, 128.0)}, {'text': 'فاتورة', 'confidence': 0.99752, 'lang': 'ar', 'bounding_box': (248.0, 128.0, 358.0, 185.0)}, {'text': '0386', 'confidence': 0.99966, 'lang': 'ar', 'bounding_box': (138.0, 154.0, 223.0, 200.0)}, {'text': 'Ivoie56التاريخ', 'confidence': 0.80838, 'lang': 'ar', 'bounding_box': (242.0, 173.0, 583.0, 220.0)}, {'text': 'السعر', 'confidence': 0.9906, 'lang': 'ar', 'bounding_box': (389.0, 236.0, 498.0, 285.0)}, {'text': 'إلى', 'confidence': 0.96784, 'lang': 'ar', 'bounding_box': (130.0, 249.0, 192.0, 300.0)}, {'text': 'من', 'confidence': 0.96968, 'lang': 'ar', 'bounding_box': (262.0, 259.0, 319.0, 297.0)}, {'text': 'ريال', 'confidence': 0.9903, 'lang': 'ar', 'bounding_box': (371.0, 285.0, 439.0, 330.0)}, {'text': 'Kiigdomtner', 'confidence': 0.69264, 'lang': 'ar', 'bounding_box': (95.0, 362.0, 344.0, 412.0)}, {'text': 'Drlaz', 'confidence': 0.47842, 'lang': 'ar', 'bounding_box': (187.0, 411.0, 297.0, 453.0)}, {'text': 'المجموع فقط', 'confidence': 0.91828, 'lang': 'ar', 'bounding_box': (245.0, 588.0, 356.0, 632.0)}, {'text': '45/.', 'confidence': 0.84809, 'lang': 'ar', 'bounding_box': (367.0, 581.0, 459.0, 661.0)}], 'field_confidence': {'vendor': 0.2789499462934947, 'date': 0.0, 'currency': 0.5787643645990922, 'amount': 0.7881363441754916, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.7881363441754916, 'invoice_number': 0.6124116611195158, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
Qema Al-Khaleej Limited Co. For General Rent
0386
Invoice 25/06/
JU
kiagdomp toner.
malaz
451.
```

### Arabic recognizer

**Low-confidence words (<0.5):** Drlaz (0.48)

**Raw text:**

```
شركة قمة الخليج المحدودة للأجرة العامة
Qema Al-Khaleej Limited Co. For General Rent
فاتورة
0386
Ivoie56التاريخ
السعر
إلى
من
ريال
Kiigdomtner
Drlaz
المجموع فقط
45/.
```

## ksa3.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'Shahad Tawik Company', 'expense_type': None, 'amount': 0.01, 'vat_amount': 0.0, 'total_amount': 0.01, 'currency': None, 'date': '29-6-26', 'confidence': 0.11, 'field_confidence': {'vendor': 0.27125651431127007, 'date': 0.28135878533094816, 'currency': 0.0, 'amount': 0.3207617189624329, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3207617189624329, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Shahad Tawik Company', 'confidence': 0.27125651431127007, 'evidence': 'Shahad Tawik Company', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '29-6-26', 'confidence': 0.28135878533094816, 'evidence': '409 KAFD208 29-6-26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 0.01, 'confidence': 0.3207617189624329, 'evidence': '0.01-.', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'amount_equals_total_no_vat'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 0.01, 'confidence': 0.3207617189624329, 'evidence': '0.01-.', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'Shahad Tawik Company\nشركة شهد طويق\nCar Number (22)\n()\nرقم السيارة\nAmount\nAmount المبلغ Dat التاريخ Timeالوقت\nDate Time\n409 KAFD208 29-6-26\n九 Malzg\nto Maliz\nالشركة غير مسئولة عن أي متعلقات شخصية يتركها الراكب داخل السيارة\nونشكركم لإتاحة الفرصة لخدمتكم\nبعد مغادرتها\n0.01-.\nاتفارجوا990000', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'Shahad Tawik Company', 'confidence': 0.99979, 'lang': 'en', 'bounding_box': (21.0, 84.0, 325.0, 130.0)}, {'text': 'Car Number (22)', 'confidence': 0.9936, 'lang': 'en', 'bounding_box': (30.0, 152.0, 265.0, 189.0)}, {'text': '()', 'confidence': 0.66185, 'lang': 'en', 'bounding_box': (627.0, 155.0, 822.0, 193.0)}, {'text': 'Amount', 'confidence': 0.99994, 'lang': 'en', 'bounding_box': (116.0, 255.0, 233.0, 288.0)}, {'text': 'Date', 'confidence': 0.95349, 'lang': 'en', 'bounding_box': (523.0, 251.0, 669.0, 289.0)}, {'text': 'Time', 'confidence': 0.82918, 'lang': 'en', 'bounding_box': (675.0, 254.0, 813.0, 289.0)}, {'text': '409', 'confidence': 0.83786, 'lang': 'en', 'bounding_box': (120.0, 316.0, 226.0, 387.0)}, {'text': 'KAFD208', 'confidence': 0.90998, 'lang': 'en', 'bounding_box': (324.0, 322.0, 520.0, 367.0)}, {'text': '29-6-26', 'confidence': 0.98449, 'lang': 'en', 'bounding_box': (511.0, 326.0, 663.0, 374.0)}, {'text': '九', 'confidence': 0.7778, 'lang': 'en', 'bounding_box': (315.0, 370.0, 378.0, 423.0)}, {'text': 'Malzg', 'confidence': 0.88392, 'lang': 'en', 'bounding_box': (351.0, 372.0, 516.0, 446.0)}, {'text': '0..01-....', 'confidence': 0.55678, 'lang': 'en', 'bounding_box': (325.0, 527.0, 826.0, 559.0)}, {'text': 'Shahad Tawik Company', 'confidence': 0.9905, 'lang': 'ar', 'bounding_box': (21.0, 84.0, 325.0, 130.0)}, {'text': 'شركة شهد طويق', 'confidence': 0.94169, 'lang': 'ar', 'bounding_box': (537.0, 85.0, 822.0, 136.0)}, {'text': 'Car Number (22)', 'confidence': 0.97373, 'lang': 'ar', 'bounding_box': (30.0, 152.0, 265.0, 189.0)}, {'text': 'رقم السيارة', 'confidence': 0.94039, 'lang': 'ar', 'bounding_box': (627.0, 155.0, 822.0, 193.0)}, {'text': 'Amount', 'confidence': 0.9993, 'lang': 'ar', 'bounding_box': (116.0, 255.0, 233.0, 288.0)}, {'text': 'المبلغ', 'confidence': 0.95368, 'lang': 'ar', 'bounding_box': (379.0, 248.0, 448.0, 294.0)}, {'text': 'Dat التاريخ', 'confidence': 0.91643, 'lang': 'ar', 'bounding_box': (523.0, 251.0, 669.0, 289.0)}, {'text': 'Timeالوقت', 'confidence': 0.96067, 'lang': 'ar', 'bounding_box': (675.0, 254.0, 813.0, 289.0)}, {'text': '40f', 'confidence': 0.83475, 'lang': 'ar', 'bounding_box': (120.0, 316.0, 226.0, 387.0)}, {'text': 'KAF9208', 'confidence': 0.80579, 'lang': 'ar', 'bounding_box': (324.0, 322.0, 520.0, 367.0)}, {'text': '29-6-26', 'confidence': 0.96809, 'lang': 'ar', 'bounding_box': (511.0, 326.0, 663.0, 374.0)}, {'text': 'to', 'confidence': 0.52581, 'lang': 'ar', 'bounding_box': (315.0, 370.0, 378.0, 423.0)}, {'text': 'Maliz', 'confidence': 0.73217, 'lang': 'ar', 'bounding_box': (351.0, 372.0, 516.0, 446.0)}, {'text': 'الشركة غير مسئولة عن أي متعلقات شخصية يتركها الراكب داخل السيارة', 'confidence': 0.95419, 'lang': 'ar', 'bounding_box': (51.0, 460.0, 810.0, 496.0)}, {'text': 'ونشكركم لإتاحة الفرصة لخدمتكم', 'confidence': 0.97031, 'lang': 'ar', 'bounding_box': (92.0, 493.0, 472.0, 527.0)}, {'text': 'بعد مغادرتها', 'confidence': 0.96064, 'lang': 'ar', 'bounding_box': (678.0, 499.0, 814.0, 529.0)}, {'text': 'اتفارجوا٩٩٠٠٠٠', 'confidence': 0.58206, 'lang': 'ar', 'bounding_box': (325.0, 527.0, 826.0, 559.0)}], 'field_confidence': {'vendor': 0.27125651431127007, 'date': 0.28135878533094816, 'currency': 0.0, 'amount': 0.3207617189624329, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3207617189624329, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
Shahad Tawik Company
Car Number (22)
()
Amount
Date
Time
409
KAFD208
29-6-26
九
Malzg
0..01-....
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
Shahad Tawik Company
شركة شهد طويق
Car Number (22)
رقم السيارة
Amount
المبلغ
Dat التاريخ
Timeالوقت
40f
KAF9208
29-6-26
to
Maliz
الشركة غير مسئولة عن أي متعلقات شخصية يتركها الراكب داخل السيارة
ونشكركم لإتاحة الفرصة لخدمتكم
بعد مغادرتها
اتفارجوا٩٩٠٠٠٠
```

## ksa4.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'No.:C/58444', 'expense_type': None, 'amount': 55.0, 'vat_amount': 0.0, 'total_amount': 1.0, 'currency': None, 'date': '', 'confidence': 0.15, 'field_confidence': {'vendor': 0.24061405856115106, 'date': 0.0, 'currency': 0.0, 'amount': 0.7016515035971223, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.22639803237410072, 'invoice_number': 0.6254652985611511, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['date', 'currency', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'No.:C/58444', 'confidence': 0.24061405856115106, 'evidence': 'No.:C/58444', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': False}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 55.0, 'confidence': 0.7016515035971223, 'evidence': '55', 'signals': ['subtotal_label', 'previous_line_label', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 1.0, 'confidence': 0.22639803237410072, 'evidence': 'Mr.1', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': 'C/58444', 'confidence': 0.6254652985611511, 'evidence': 'No.:C/58444', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'Invoice //\nالتاريخ4ه\nNo.:C/58444\nNo.:C/58444 I فاتورة الموافق2\n.30106126 151\nMr.1\nالمطلوب من المكرم\nTo.\nTo. إلى From مسن Amount المبلغ\nFrom il Amount\nkingdon ce dre to\nkugdon caduf\nMolag\nMolay\n55\nTotal\nالمجموع\nتوقيع السائق\nرقم السيارة\nنسعد بإستقبال أرائكم لتطوير خدماتنا\nWE WILL BE HAPPY TO RECEIVE YOUR OPENIONS FOR\nWE WILL BE HAPPY TO RECEIVE YOUR OPENIONS FOR\nDEVELOPING OUR SEVICES\nDEVELOPING OUR SEVICES\nلاتنسى طلب فاتورتك من السائق\nASK FOR YOUR INVOICE\nASK FOR YOUR INVOICE', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': '//', 'confidence': 0.62066, 'lang': 'en', 'bounding_box': (365.0, 54.0, 553.0, 86.0)}, {'text': 'No.:C/58444', 'confidence': 0.96809, 'lang': 'en', 'bounding_box': (24.0, 68.0, 224.0, 115.0)}, {'text': 'Invoice ', 'confidence': 0.93213, 'lang': 'en', 'bounding_box': (216.0, 70.0, 341.0, 102.0)}, {'text': '.30106126 151', 'confidence': 0.88102, 'lang': 'en', 'bounding_box': (371.0, 84.0, 548.0, 116.0)}, {'text': 'Mr.1', 'confidence': 0.9903, 'lang': 'en', 'bounding_box': (31.0, 134.0, 74.0, 161.0)}, {'text': 'To.', 'confidence': 0.99503, 'lang': 'en', 'bounding_box': (41.0, 193.0, 81.0, 224.0)}, {'text': 'From', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (234.0, 194.0, 291.0, 223.0)}, {'text': 'il', 'confidence': 0.90382, 'lang': 'en', 'bounding_box': (359.0, 196.0, 400.0, 219.0)}, {'text': 'Amount ', 'confidence': 0.96407, 'lang': 'en', 'bounding_box': (416.0, 190.0, 531.0, 224.0)}, {'text': 'kingdon', 'confidence': 0.82288, 'lang': 'en', 'bounding_box': (67.0, 221.0, 234.0, 289.0)}, {'text': 'ce dre to', 'confidence': 0.70791, 'lang': 'en', 'bounding_box': (242.0, 234.0, 409.0, 275.0)}, {'text': 'Molag', 'confidence': 0.87558, 'lang': 'en', 'bounding_box': (80.0, 270.0, 235.0, 339.0)}, {'text': '55', 'confidence': 0.99854, 'lang': 'en', 'bounding_box': (418.0, 312.0, 477.0, 354.0)}, {'text': 'Total', 'confidence': 0.99986, 'lang': 'en', 'bounding_box': (54.0, 508.0, 109.0, 538.0)}, {'text': 'WE WILL BE HAPPY TO RECEIVE YOUR OPENIONS FOR', 'confidence': 0.98552, 'lang': 'en', 'bounding_box': (94.0, 620.0, 462.0, 639.0)}, {'text': 'DEVELOPING OUR SEVICES', 'confidence': 0.97629, 'lang': 'en', 'bounding_box': (183.0, 641.0, 372.0, 658.0)}, {'text': 'ASK FOR YOUR INVOICE', 'confidence': 0.98551, 'lang': 'en', 'bounding_box': (194.0, 677.0, 362.0, 695.0)}, {'text': 'التاريخ٤ه', 'confidence': 0.88541, 'lang': 'ar', 'bounding_box': (365.0, 54.0, 553.0, 86.0)}, {'text': 'No.:C/58444', 'confidence': 0.90885, 'lang': 'ar', 'bounding_box': (24.0, 68.0, 224.0, 115.0)}, {'text': 'I فاتورة', 'confidence': 0.87405, 'lang': 'ar', 'bounding_box': (216.0, 70.0, 341.0, 102.0)}, {'text': 'الموافق٢', 'confidence': 0.8593, 'lang': 'ar', 'bounding_box': (371.0, 84.0, 548.0, 116.0)}, {'text': 'Mr..', 'confidence': 0.89236, 'lang': 'ar', 'bounding_box': (31.0, 134.0, 74.0, 161.0)}, {'text': 'المطلوب من المكرم', 'confidence': 0.96344, 'lang': 'ar', 'bounding_box': (407.0, 134.0, 542.0, 161.0)}, {'text': 'To.', 'confidence': 0.98777, 'lang': 'ar', 'bounding_box': (41.0, 193.0, 81.0, 224.0)}, {'text': 'إلى', 'confidence': 0.90745, 'lang': 'ar', 'bounding_box': (179.0, 191.0, 220.0, 223.0)}, {'text': 'From', 'confidence': 0.99908, 'lang': 'ar', 'bounding_box': (234.0, 194.0, 291.0, 223.0)}, {'text': 'مسن', 'confidence': 0.85919, 'lang': 'ar', 'bounding_box': (359.0, 196.0, 400.0, 219.0)}, {'text': 'Amount المبلغ', 'confidence': 0.85086, 'lang': 'ar', 'bounding_box': (416.0, 190.0, 531.0, 224.0)}, {'text': 'kugdon', 'confidence': 0.70379, 'lang': 'ar', 'bounding_box': (67.0, 221.0, 234.0, 289.0)}, {'text': 'caduf', 'confidence': 0.6359, 'lang': 'ar', 'bounding_box': (242.0, 234.0, 409.0, 275.0)}, {'text': 'Molay', 'confidence': 0.66575, 'lang': 'ar', 'bounding_box': (80.0, 270.0, 235.0, 339.0)}, {'text': '55', 'confidence': 0.99736, 'lang': 'ar', 'bounding_box': (418.0, 312.0, 477.0, 354.0)}, {'text': 'Total', 'confidence': 0.99899, 'lang': 'ar', 'bounding_box': (54.0, 508.0, 109.0, 538.0)}, {'text': 'المجموع', 'confidence': 0.98871, 'lang': 'ar', 'bounding_box': (331.0, 503.0, 405.0, 540.0)}, {'text': 'توقيع السائق', 'confidence': 0.97637, 'lang': 'ar', 'bounding_box': (180.0, 560.0, 286.0, 589.0)}, {'text': 'رقم السيارة :', 'confidence': 0.78661, 'lang': 'ar', 'bounding_box': (416.0, 558.0, 515.0, 588.0)}, {'text': 'نسعد بإستقبال أرائكم لتطوير خدماتنا', 'confidence': 0.90694, 'lang': 'ar', 'bounding_box': (150.0, 598.0, 406.0, 621.0)}, {'text': 'WE WILL BE HAPPY TO RECEIVE YOUR OPENIONS FOR', 'confidence': 0.98802, 'lang': 'ar', 'bounding_box': (94.0, 620.0, 462.0, 639.0)}, {'text': 'DEVELOPING OUR SEVICES', 'confidence': 0.99922, 'lang': 'ar', 'bounding_box': (183.0, 641.0, 372.0, 658.0)}, {'text': 'لاتنسى طلب فاتورتك من السائق', 'confidence': 0.96636, 'lang': 'ar', 'bounding_box': (197.0, 661.0, 358.0, 678.0)}, {'text': 'ASK FOR YOUR INVOICE', 'confidence': 0.99894, 'lang': 'ar', 'bounding_box': (194.0, 677.0, 362.0, 695.0)}], 'field_confidence': {'vendor': 0.24061405856115106, 'date': 0.0, 'currency': 0.0, 'amount': 0.7016515035971223, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.22639803237410072, 'invoice_number': 0.6254652985611511, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['date', 'currency', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
//
No.:C/58444
Invoice
.30106126 151
Mr.1
To.
From
il
Amount
kingdon
ce dre to
Molag
55
Total
WE WILL BE HAPPY TO RECEIVE YOUR OPENIONS FOR
DEVELOPING OUR SEVICES
ASK FOR YOUR INVOICE
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
التاريخ٤ه
No.:C/58444
I فاتورة
الموافق٢
Mr..
المطلوب من المكرم
To.
إلى
From
مسن
Amount المبلغ
kugdon
caduf
Molay
55
Total
المجموع
توقيع السائق
رقم السيارة :
نسعد بإستقبال أرائكم لتطوير خدماتنا
WE WILL BE HAPPY TO RECEIVE YOUR OPENIONS FOR
DEVELOPING OUR SEVICES
لاتنسى طلب فاتورتك من السائق
ASK FOR YOUR INVOICE
```

## ksa5.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'TAXI AL-AJME', 'expense_type': None, 'amount': 2.09, 'vat_amount': 0.0, 'total_amount': 2.09, 'currency': None, 'date': '', 'confidence': 0.09, 'field_confidence': {'vendor': 0.2820771291161178, 'date': 0.0, 'currency': 0.0, 'amount': 0.2992571586655113, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.2992571586655113, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'TAXI AL-AJME', 'confidence': 0.2820771291161178, 'evidence': 'TAXI AL-AJME', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 2.09, 'confidence': 0.2992571586655113, 'evidence': 'To: Malag ! KAFD 2.09', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'amount_equals_total_no_vat'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 2.09, 'confidence': 0.2992571586655113, 'evidence': 'To: Malag ! KAFD 2.09', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'TAXI AL-AJME\nTAXI AL-AJME العجمي أجرة عامة\nRiyadh-AL-Shifa M\nالرياض - الشفا\nTel.: 4226131\nE\nتلفون 4631\nفاتورة راكب\nB/N0.20367 103107126\nB /N0.20367 التاريخ4\n.//\nالموافق 1 201م\nName of Driver\nإسم السائق\nTo: Malag ! KAFD 2.09\nTo: Mala 1 KA مشوارمن\nبمبلغ\nSignature\nSignature التوقيع', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'TAXI AL-AJME', 'confidence': 0.96197, 'lang': 'en', 'bounding_box': (46.0, 28.0, 259.0, 66.0)}, {'text': 'M', 'confidence': 0.99987, 'lang': 'en', 'bounding_box': (255.0, 29.0, 353.0, 112.0)}, {'text': 'Riyadh-AL-Shifa', 'confidence': 0.99992, 'lang': 'en', 'bounding_box': (77.0, 63.0, 233.0, 97.0)}, {'text': 'Tel.: 4226131', 'confidence': 0.96135, 'lang': 'en', 'bounding_box': (91.0, 97.0, 217.0, 130.0)}, {'text': 'E:', 'confidence': 0.52428, 'lang': 'en', 'bounding_box': (395.0, 106.0, 527.0, 133.0)}, {'text': '103107126：', 'confidence': 0.8246, 'lang': 'en', 'bounding_box': (345.0, 241.0, 566.0, 280.0)}, {'text': 'B/NO.20367', 'confidence': 0.99865, 'lang': 'en', 'bounding_box': (43.0, 255.0, 246.0, 295.0)}, {'text': './/', 'confidence': 0.70199, 'lang': 'en', 'bounding_box': (346.0, 279.0, 563.0, 317.0)}, {'text': 'Name of Driver', 'confidence': 0.99929, 'lang': 'en', 'bounding_box': (49.0, 365.0, 188.0, 393.0)}, {'text': 'To: Malag !', 'confidence': 0.86325, 'lang': 'en', 'bounding_box': (35.0, 393.0, 250.0, 472.0)}, {'text': 'KAFD 2.09 ', 'confidence': 0.81827, 'lang': 'en', 'bounding_box': (291.0, 394.0, 575.0, 470.0)}, {'text': 'Signature', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (80.0, 540.0, 177.0, 573.0)}, {'text': 'TAXI AL-AJME', 'confidence': 0.96875, 'lang': 'ar', 'bounding_box': (46.0, 28.0, 259.0, 66.0)}, {'text': 'M', 'confidence': 0.99968, 'lang': 'ar', 'bounding_box': (255.0, 29.0, 353.0, 112.0)}, {'text': 'العجمي أجرة عامة', 'confidence': 0.95397, 'lang': 'ar', 'bounding_box': (348.0, 36.0, 573.0, 79.0)}, {'text': 'Riyadh - AL-Shifa', 'confidence': 0.96936, 'lang': 'ar', 'bounding_box': (77.0, 63.0, 233.0, 97.0)}, {'text': 'الرياض - الشفا', 'confidence': 0.89654, 'lang': 'ar', 'bounding_box': (396.0, 79.0, 524.0, 108.0)}, {'text': 'Tel.: 4226131', 'confidence': 0.97826, 'lang': 'ar', 'bounding_box': (91.0, 97.0, 217.0, 130.0)}, {'text': 'تلفون ٤٦٣١', 'confidence': 0.80027, 'lang': 'ar', 'bounding_box': (395.0, 106.0, 527.0, 133.0)}, {'text': 'فاتورة راكب', 'confidence': 0.99121, 'lang': 'ar', 'bounding_box': (229.0, 149.0, 394.0, 199.0)}, {'text': 'التاريخ٤', 'confidence': 0.91131, 'lang': 'ar', 'bounding_box': (345.0, 241.0, 566.0, 280.0)}, {'text': 'B /NO.20367', 'confidence': 0.98703, 'lang': 'ar', 'bounding_box': (43.0, 255.0, 246.0, 295.0)}, {'text': 'الموافق  ١ ٢٠١م', 'confidence': 0.77909, 'lang': 'ar', 'bounding_box': (346.0, 279.0, 563.0, 317.0)}, {'text': 'Name of Driver', 'confidence': 0.97602, 'lang': 'ar', 'bounding_box': (49.0, 365.0, 188.0, 393.0)}, {'text': 'إسم السائق', 'confidence': 0.98017, 'lang': 'ar', 'bounding_box': (450.0, 364.0, 567.0, 404.0)}, {'text': 'To: Mala 1', 'confidence': 0.70115, 'lang': 'ar', 'bounding_box': (35.0, 393.0, 250.0, 472.0)}, {'text': 'KA مشوارمن', 'confidence': 0.85942, 'lang': 'ar', 'bounding_box': (291.0, 394.0, 575.0, 470.0)}, {'text': 'بمبلغ', 'confidence': 0.99317, 'lang': 'ar', 'bounding_box': (507.0, 484.0, 566.0, 521.0)}, {'text': 'Signature', 'confidence': 0.99919, 'lang': 'ar', 'bounding_box': (80.0, 540.0, 177.0, 573.0)}, {'text': 'التوقيع', 'confidence': 0.94548, 'lang': 'ar', 'bounding_box': (201.0, 536.0, 278.0, 577.0)}], 'field_confidence': {'vendor': 0.2820771291161178, 'date': 0.0, 'currency': 0.0, 'amount': 0.2992571586655113, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.2992571586655113, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
TAXI AL-AJME
M
Riyadh-AL-Shifa
Tel.: 4226131
E:
103107126：
B/NO.20367
.//
Name of Driver
To: Malag !
KAFD 2.09
Signature
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
TAXI AL-AJME
M
العجمي أجرة عامة
Riyadh - AL-Shifa
الرياض - الشفا
Tel.: 4226131
تلفون ٤٦٣١
فاتورة راكب
التاريخ٤
B /NO.20367
الموافق  ١ ٢٠١م
Name of Driver
إسم السائق
To: Mala 1
KA مشوارمن
بمبلغ
Signature
التوقيع
```

## ksa6.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'Shaml Al-Doha Company ركة شمل الدوحة', 'expense_type': None, 'amount': 351.0, 'vat_amount': 0.0, 'total_amount': 351.0, 'currency': None, 'date': '05/03/26', 'confidence': 0.11, 'field_confidence': {'vendor': 0.2561132929729729, 'date': 0.3047387837837838, 'currency': 0.0, 'amount': 0.3235300756756757, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3235300756756757, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Shaml Al-Doha Company ركة شمل الدوحة', 'confidence': 0.2561132929729729, 'evidence': 'Shaml Al-Doha Company ركة شمل الدوحة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '05/03/26', 'confidence': 0.3047387837837838, 'evidence': 'INVOICE 05/03/26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 351.0, 'confidence': 0.3235300756756757, 'evidence': '351', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'amount_equals_total_no_vat'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 351.0, 'confidence': 0.3235300756756757, 'evidence': '351', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'Shaml Al-Doha Company 2i\nShaml Al-Doha Company ركة شمل الدوحة\nLic. No. : 201\n1\nترخيص رقم 201\nTel.: 4850982/4850952 E./.\nTel.: 4850982/4850952 لفون 000\nP.O.Box : 90604 Riyadh : 11623 111:119.1.800\nP.O.Box : 90604 Rlyadh : 11623 ب 90الرياض\nK. Fahd Red. AI-Qerwan Quarter\nK. Fahd Red. AI-Qerwan Quarter طريق الملك فهدعي القيروان\nVAT: 300396976200002 .\nVAT: 300396976200002 الرقم الضري3003960\nفاتورة\nINVOICE 05/03/26\nالتاريخ رقم السيارة\nاسم السائق\nMale n\nDالمبلع الطل\nCoutr\ntouts وذلك مقابل نقل ركاب من\n351\n3s+ إلى\nتوقيع السائق', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': 'Shaml Al-Doha Company', 'confidence': 0.97869, 'lang': 'en', 'bounding_box': (57.0, 58.0, 305.0, 98.0)}, {'text': '2i', 'confidence': 0.42197, 'lang': 'en', 'bounding_box': (396.0, 66.0, 602.0, 105.0)}, {'text': 'Lic. No. : 201', 'confidence': 0.96264, 'lang': 'en', 'bounding_box': (113.0, 100.0, 248.0, 122.0)}, {'text': '1', 'confidence': 0.58786, 'lang': 'en', 'bounding_box': (424.0, 103.0, 574.0, 130.0)}, {'text': 'Tel.: 4850982 / 4850952', 'confidence': 0.95551, 'lang': 'en', 'bounding_box': (70.0, 124.0, 294.0, 148.0)}, {'text': 'E./.:', 'confidence': 0.54588, 'lang': 'en', 'bounding_box': (394.0, 125.0, 604.0, 154.0)}, {'text': 'P.O.Box : 90604 Riyadh : 11623', 'confidence': 0.95542, 'lang': 'en', 'bounding_box': (56.0, 148.0, 304.0, 173.0)}, {'text': '111:119.1.800', 'confidence': 0.67204, 'lang': 'en', 'bounding_box': (390.0, 148.0, 608.0, 178.0)}, {'text': 'K. Fahd Red. AI-Qerwan Quarter', 'confidence': 0.95951, 'lang': 'en', 'bounding_box': (57.0, 172.0, 302.0, 199.0)}, {'text': 'VAT: 300396976200002', 'confidence': 0.98661, 'lang': 'en', 'bounding_box': (79.0, 193.0, 285.0, 219.0)}, {'text': '.:', 'confidence': 0.53752, 'lang': 'en', 'bounding_box': (384.0, 192.0, 611.0, 221.0)}, {'text': 'INVOICE', 'confidence': 0.99963, 'lang': 'en', 'bounding_box': (288.0, 233.0, 386.0, 265.0)}, {'text': '05103/26', 'confidence': 0.82881, 'lang': 'en', 'bounding_box': (405.0, 231.0, 574.0, 296.0)}, {'text': 'Male  n', 'confidence': 0.57354, 'lang': 'en', 'bounding_box': (139.0, 368.0, 610.0, 427.0)}, {'text': 'Coutr', 'confidence': 0.72756, 'lang': 'en', 'bounding_box': (158.0, 417.0, 297.0, 459.0)}, {'text': '351', 'confidence': 0.95232, 'lang': 'en', 'bounding_box': (337.0, 451.0, 448.0, 516.0)}, {'text': 'Shaml Al-Doha Company', 'confidence': 0.97429, 'lang': 'ar', 'bounding_box': (57.0, 58.0, 305.0, 98.0)}, {'text': 'ركة شمل الدوحة', 'confidence': 0.97076, 'lang': 'ar', 'bounding_box': (396.0, 66.0, 602.0, 105.0)}, {'text': 'Lic. No. : 201', 'confidence': 0.99884, 'lang': 'ar', 'bounding_box': (113.0, 100.0, 248.0, 122.0)}, {'text': 'ترخيص رقم ٢٠١', 'confidence': 0.90162, 'lang': 'ar', 'bounding_box': (424.0, 103.0, 574.0, 130.0)}, {'text': 'Tel.: 4850982 /4850952', 'confidence': 0.98047, 'lang': 'ar', 'bounding_box': (70.0, 124.0, 294.0, 148.0)}, {'text': 'لفون ٠٠٠', 'confidence': 0.56928, 'lang': 'ar', 'bounding_box': (394.0, 125.0, 604.0, 154.0)}, {'text': 'P.O.Box : 90604 Rlyadh : 11623', 'confidence': 0.96491, 'lang': 'ar', 'bounding_box': (56.0, 148.0, 304.0, 173.0)}, {'text': ' ب ٩٠الرياض', 'confidence': 0.71122, 'lang': 'ar', 'bounding_box': (390.0, 148.0, 608.0, 178.0)}, {'text': 'K. Fahd Red. AI-Qerwan Quarter', 'confidence': 0.96575, 'lang': 'ar', 'bounding_box': (57.0, 172.0, 302.0, 199.0)}, {'text': 'طريق الملك فهدعي القيروان', 'confidence': 0.9172, 'lang': 'ar', 'bounding_box': (384.0, 171.0, 612.0, 200.0)}, {'text': 'VAT: 300396976200002', 'confidence': 0.97975, 'lang': 'ar', 'bounding_box': (79.0, 193.0, 285.0, 219.0)}, {'text': 'الرقم الضري٣٠٠٣٩٦٠', 'confidence': 0.73039, 'lang': 'ar', 'bounding_box': (384.0, 192.0, 611.0, 221.0)}, {'text': 'فاتورة', 'confidence': 0.86325, 'lang': 'ar', 'bounding_box': (288.0, 205.0, 386.0, 242.0)}, {'text': 'INVOICE', 'confidence': 0.9987, 'lang': 'ar', 'bounding_box': (288.0, 233.0, 386.0, 265.0)}, {'text': '05/03/26', 'confidence': 0.8397, 'lang': 'ar', 'bounding_box': (405.0, 231.0, 574.0, 296.0)}, {'text': 'التاريخ', 'confidence': 0.97726, 'lang': 'ar', 'bounding_box': (138.0, 305.0, 211.0, 341.0)}, {'text': 'رقم السيارة', 'confidence': 0.96603, 'lang': 'ar', 'bounding_box': (282.0, 310.0, 375.0, 339.0)}, {'text': 'اسم السائق', 'confidence': 0.97822, 'lang': 'ar', 'bounding_box': (512.0, 311.0, 606.0, 342.0)}, {'text': 'Dالمبلع الطل', 'confidence': 0.50481, 'lang': 'ar', 'bounding_box': (139.0, 368.0, 610.0, 427.0)}, {'text': 'touts', 'confidence': 0.66843, 'lang': 'ar', 'bounding_box': (158.0, 417.0, 297.0, 459.0)}, {'text': 'وذلك مقابل نقل ركاب من', 'confidence': 0.9228, 'lang': 'ar', 'bounding_box': (391.0, 421.0, 604.0, 453.0)}, {'text': '3s+', 'confidence': 0.64431, 'lang': 'ar', 'bounding_box': (337.0, 451.0, 448.0, 516.0)}, {'text': 'إلى', 'confidence': 0.85933, 'lang': 'ar', 'bounding_box': (571.0, 461.0, 605.0, 489.0)}, {'text': 'توقيع السائق', 'confidence': 0.99545, 'lang': 'ar', 'bounding_box': (111.0, 521.0, 223.0, 555.0)}], 'field_confidence': {'vendor': 0.2561132929729729, 'date': 0.3047387837837838, 'currency': 0.0, 'amount': 0.3235300756756757, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3235300756756757, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** 2i (0.42)

**Raw text:**

```
Shaml Al-Doha Company
2i
Lic. No. : 201
1
Tel.: 4850982 / 4850952
E./.:
P.O.Box : 90604 Riyadh : 11623
111:119.1.800
K. Fahd Red. AI-Qerwan Quarter
VAT: 300396976200002
.:
INVOICE
05103/26
Male  n
Coutr
351
```

### Arabic recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
Shaml Al-Doha Company
ركة شمل الدوحة
Lic. No. : 201
ترخيص رقم ٢٠١
Tel.: 4850982 /4850952
لفون ٠٠٠
P.O.Box : 90604 Rlyadh : 11623
 ب ٩٠الرياض
K. Fahd Red. AI-Qerwan Quarter
طريق الملك فهدعي القيروان
VAT: 300396976200002
الرقم الضري٣٠٠٣٩٦٠
فاتورة
INVOICE
05/03/26
التاريخ
رقم السيارة
اسم السائق
Dالمبلع الطل
touts
وذلك مقابل نقل ركاب من
3s+
إلى
توقيع السائق
```

## ksa7.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': 'شركة سلطان منير الحارثي وشريكه للأجرة العامة', 'expense_type': None, 'amount': 45.0, 'vat_amount': 0.0, 'total_amount': 45.0, 'currency': 'SAR', 'date': '', 'confidence': 0.12, 'field_confidence': {'vendor': 0.28180851063829787, 'date': 0.0, 'currency': 0.5308643085106383, 'amount': 0.28742921489361706, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.28742921489361706, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'شركة سلطان منير الحارثي وشريكه للأجرة العامة', 'confidence': 0.28180851063829787, 'evidence': 'شركة سلطان منير الحارثي وشريكه للأجرة العامة', 'signals': ['top_of_receipt', 'multiline_header_merge', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': 'SAR', 'confidence': 0.5308643085106383, 'evidence': 'Notes ملاحظات Fare SAR هلله إلى من', 'signals': ['currency_code_match', 'position_prior_upper'], 'low': False}, 'amount': {'value': 45.0, 'confidence': 0.28742921489361706, 'evidence': 'kingdon 45', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'amount_equals_total_no_vat'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 45.0, 'confidence': 0.28742921489361706, 'evidence': 'kingdon 45', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': 'شركة سلطان منير الحارثي وشريكه\nللأجرة العامة\nترخيص رقم\n.\n0 ية4 وية4\nالرياضالشفا طريق العارض\nلرقم الضريبي 0200\n0098594\n0098594 فاتورة راكب\nCustomer Invoice\nCustomer Invoice\nDate 1410 126\nDate14012الموافق\nالتاريخ\nCustomer name:.\nCustomer name:.\nاسم الرا\nNotes\nNotes ملاحظات Fare SAR هلله إلى من\nFare J4 alls\nالأجرة Fare الكان\nFare üLStI\nkingdon 45\nKringdo +5\nodgo\nBderfo\nDalay\nOto الاجمالي\nضريبة القيمة المضافة\nالاجمالي شامل القيمة الضافة\nتوقيع السائق اسم الساة\nعزيزي الراكب نرجو التأكد من إستلام جميع امتعتكم\nمع اجمل تمنياتنا لكم بسلامة الوصول\nشكرا لتفضلكم بركوب السيارة', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': '.', 'confidence': 0.34105, 'lang': 'en', 'bounding_box': (162.0, 167.0, 537.0, 194.0)}, {'text': '0098594', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (100.0, 251.0, 244.0, 291.0)}, {'text': 'Customer Invoice', 'confidence': 0.99752, 'lang': 'en', 'bounding_box': (291.0, 276.0, 419.0, 297.0)}, {'text': 'Date 1410 126', 'confidence': 0.90204, 'lang': 'en', 'bounding_box': (80.0, 318.0, 348.0, 357.0)}, {'text': 'Customer name:.', 'confidence': 0.98389, 'lang': 'en', 'bounding_box': (87.0, 366.0, 196.0, 386.0)}, {'text': 'Notes', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (116.0, 401.0, 170.0, 424.0)}, {'text': 'Fare', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (313.0, 389.0, 355.0, 413.0)}, {'text': 'J4', 'confidence': 0.62818, 'lang': 'en', 'bounding_box': (322.0, 410.0, 357.0, 434.0)}, {'text': 'alls', 'confidence': 0.86206, 'lang': 'en', 'bounding_box': (394.0, 409.0, 426.0, 430.0)}, {'text': 'Fare', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (455.0, 388.0, 497.0, 410.0)}, {'text': 'üLStI', 'confidence': 0.47132, 'lang': 'en', 'bounding_box': (532.0, 385.0, 568.0, 409.0)}, {'text': 'kingdon', 'confidence': 0.81994, 'lang': 'en', 'bounding_box': (97.0, 445.0, 248.0, 500.0)}, {'text': '45', 'confidence': 0.98136, 'lang': 'en', 'bounding_box': (314.0, 456.0, 363.0, 497.0)}, {'text': 'odgo', 'confidence': 0.51017, 'lang': 'en', 'bounding_box': (110.0, 476.0, 253.0, 533.0)}, {'text': 'Dalay', 'confidence': 0.6718, 'lang': 'en', 'bounding_box': (137.0, 506.0, 237.0, 553.0)}, {'text': 'شركة سلطان منير الحارثي وشريكه', 'confidence': 0.95045, 'lang': 'ar', 'bounding_box': (126.0, 35.0, 574.0, 95.0)}, {'text': 'للأجرة العامة', 'confidence': 0.96306, 'lang': 'ar', 'bounding_box': (268.0, 87.0, 429.0, 136.0)}, {'text': 'ترخيص رقم', 'confidence': 0.92326, 'lang': 'ar', 'bounding_box': (285.0, 143.0, 417.0, 168.0)}, {'text': '٠ ية٤ وية٤', 'confidence': 0.54359, 'lang': 'ar', 'bounding_box': (162.0, 167.0, 537.0, 194.0)}, {'text': 'الرياضالشفا طريق العارض', 'confidence': 0.95225, 'lang': 'ar', 'bounding_box': (247.0, 188.0, 465.0, 214.0)}, {'text': 'لرقم الضريبي ٠٢٠٠', 'confidence': 0.71044, 'lang': 'ar', 'bounding_box': (236.0, 213.0, 471.0, 236.0)}, {'text': '0098594', 'confidence': 0.99956, 'lang': 'ar', 'bounding_box': (100.0, 251.0, 244.0, 291.0)}, {'text': 'فاتورة راكب', 'confidence': 0.96998, 'lang': 'ar', 'bounding_box': (289.0, 247.0, 418.0, 280.0)}, {'text': 'Customer Invoice', 'confidence': 0.99918, 'lang': 'ar', 'bounding_box': (291.0, 276.0, 419.0, 297.0)}, {'text': 'Date14012الموافق', 'confidence': 0.8483, 'lang': 'ar', 'bounding_box': (80.0, 318.0, 348.0, 357.0)}, {'text': 'التاريخ', 'confidence': 0.99267, 'lang': 'ar', 'bounding_box': (498.0, 321.0, 592.0, 351.0)}, {'text': 'Customer name:.', 'confidence': 0.93653, 'lang': 'ar', 'bounding_box': (87.0, 366.0, 196.0, 386.0)}, {'text': 'اسم الرا', 'confidence': 0.93577, 'lang': 'ar', 'bounding_box': (498.0, 359.0, 590.0, 383.0)}, {'text': 'Notes', 'confidence': 0.99967, 'lang': 'ar', 'bounding_box': (116.0, 401.0, 170.0, 424.0)}, {'text': 'ملاحظات', 'confidence': 0.97931, 'lang': 'ar', 'bounding_box': (211.0, 398.0, 280.0, 421.0)}, {'text': 'Fare', 'confidence': 0.99304, 'lang': 'ar', 'bounding_box': (313.0, 389.0, 355.0, 413.0)}, {'text': 'ريال', 'confidence': 0.98093, 'lang': 'ar', 'bounding_box': (322.0, 410.0, 357.0, 434.0)}, {'text': 'الأجرة', 'confidence': 0.94626, 'lang': 'ar', 'bounding_box': (389.0, 388.0, 435.0, 411.0)}, {'text': 'هلله', 'confidence': 0.96031, 'lang': 'ar', 'bounding_box': (394.0, 409.0, 426.0, 430.0)}, {'text': 'Fare', 'confidence': 0.99781, 'lang': 'ar', 'bounding_box': (455.0, 388.0, 497.0, 410.0)}, {'text': 'إلى', 'confidence': 0.78945, 'lang': 'ar', 'bounding_box': (459.0, 409.0, 487.0, 432.0)}, {'text': 'الكان', 'confidence': 0.8962, 'lang': 'ar', 'bounding_box': (532.0, 385.0, 568.0, 409.0)}, {'text': 'من', 'confidence': 0.92398, 'lang': 'ar', 'bounding_box': (539.0, 408.0, 561.0, 428.0)}, {'text': 'Kringdo', 'confidence': 0.55921, 'lang': 'ar', 'bounding_box': (97.0, 445.0, 248.0, 500.0)}, {'text': '+5', 'confidence': 0.76864, 'lang': 'ar', 'bounding_box': (314.0, 456.0, 363.0, 497.0)}, {'text': 'Bderfo', 'confidence': 0.40211, 'lang': 'ar', 'bounding_box': (110.0, 476.0, 253.0, 533.0)}, {'text': 'Oto', 'confidence': 0.46965, 'lang': 'ar', 'bounding_box': (137.0, 506.0, 237.0, 553.0)}, {'text': 'الاجمالي', 'confidence': 0.979, 'lang': 'ar', 'bounding_box': (224.0, 525.0, 288.0, 550.0)}, {'text': 'ضريبة القيمة المضافة ', 'confidence': 0.87769, 'lang': 'ar', 'bounding_box': (135.0, 550.0, 284.0, 571.0)}, {'text': 'الاجمالي شامل القيمة الضافة', 'confidence': 0.81147, 'lang': 'ar', 'bounding_box': (113.0, 569.0, 286.0, 594.0)}, {'text': 'توقيع السائق', 'confidence': 0.91004, 'lang': 'ar', 'bounding_box': (190.0, 609.0, 290.0, 641.0)}, {'text': 'اسم الساة', 'confidence': 0.76107, 'lang': 'ar', 'bounding_box': (328.0, 593.0, 586.0, 635.0)}, {'text': 'عزيزي الراكب نرجو التأكد من إستلام جميع امتعتكم', 'confidence': 0.91294, 'lang': 'ar', 'bounding_box': (200.0, 633.0, 487.0, 670.0)}, {'text': 'مع اجمل تمنياتنا لكم بسلامة الوصول', 'confidence': 0.91702, 'lang': 'ar', 'bounding_box': (240.0, 655.0, 450.0, 687.0)}, {'text': 'شكرا لتفضلكم بركوب السيارة', 'confidence': 0.83808, 'lang': 'ar', 'bounding_box': (261.0, 672.0, 431.0, 705.0)}], 'field_confidence': {'vendor': 0.28180851063829787, 'date': 0.0, 'currency': 0.5308643085106383, 'amount': 0.28742921489361706, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.28742921489361706, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** . (0.34), üLStI (0.47)

**Raw text:**

```
.
0098594
Customer Invoice
Date 1410 126
Customer name:.
Notes
Fare
J4
alls
Fare
üLStI
kingdon
45
odgo
Dalay
```

### Arabic recognizer

**Low-confidence words (<0.5):** Bderfo (0.40), Oto (0.47)

**Raw text:**

```
شركة سلطان منير الحارثي وشريكه
للأجرة العامة
ترخيص رقم
٠ ية٤ وية٤
الرياضالشفا طريق العارض
لرقم الضريبي ٠٢٠٠
0098594
فاتورة راكب
Customer Invoice
Date14012الموافق
التاريخ
Customer name:.
اسم الرا
Notes
ملاحظات
Fare
ريال
الأجرة
هلله
Fare
إلى
الكان
من
Kringdo
+5
Bderfo
Oto
الاجمالي
ضريبة القيمة المضافة
الاجمالي شامل القيمة الضافة
توقيع السائق
اسم الساة
عزيزي الراكب نرجو التأكد من إستلام جميع امتعتكم
مع اجمل تمنياتنا لكم بسلامة الوصول
شكرا لتفضلكم بركوب السيارة
```

## ksa8.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': '4 487%', 'expense_type': None, 'amount': 72.9, 'vat_amount': 0.0, 'total_amount': 72.9, 'currency': 'SAR', 'date': 'Feb 8', 'confidence': 0.2, 'field_confidence': {'vendor': 0.22938524406779665, 'date': 0.33367537288135596, 'currency': 0.6764538559322033, 'amount': 0.3534588940677966, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3534588940677966, 'invoice_number': 0.5764538559322033, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': '4 487%', 'confidence': 0.22938524406779665, 'evidence': '4 487%', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': 'Feb 8', 'confidence': 0.33367537288135596, 'evidence': 'Feb 8 7:10AM', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'SAR', 'confidence': 0.6764538559322033, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 72.9, 'confidence': 0.3534588940677966, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'amount_equals_total_no_vat'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 72.9, 'confidence': 0.3534588940677966, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': 'SAR72', 'confidence': 0.5764538559322033, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': '08:06\n4 487%\nil 40: 87%\nRide details\nwL Sadus\nسدوي Sackue\nAl Jubaytas\nA Jubrlin\n0\no\naudonll\nالعمارية\nRiyadh\nvolo\nقباض\nGoogle Dhurma\nUberX Saver reserve\nride with Ali\nFeb 8 7:10AM\nSAR72.90 - Hyundai Accent\nReceipt Invoice\no 7926 Zayd Ibn Thabit Street Riyadh 12831\n7:13 AM\nO Terminal 5, King Khalid International Airport (RUH) - Riyadh 13458 8:09 AM\nNo tip added\nAdd tip\n☆ No rating\nRate\nHelp & safety\nFind lost item\na We can help you qet in touch with your', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': '08:06', 'confidence': 0.99993, 'lang': 'en', 'bounding_box': (82.0, 42.0, 113.0, 57.0)}, {'text': '  4 487%', 'confidence': 0.68005, 'lang': 'en', 'bounding_box': (262.0, 38.0, 355.0, 60.0)}, {'text': 'Ride details', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (106.0, 75.0, 189.0, 92.0)}, {'text': 'wL', 'confidence': 0.18884, 'lang': 'en', 'bounding_box': (108.0, 137.0, 133.0, 150.0)}, {'text': 'Sadus', 'confidence': 0.95731, 'lang': 'en', 'bounding_box': (110.0, 131.0, 132.0, 141.0)}, {'text': 'Al Jubaytas', 'confidence': 0.70158, 'lang': 'en', 'bounding_box': (147.0, 148.0, 186.0, 162.0)}, {'text': '0', 'confidence': 0.38006, 'lang': 'en', 'bounding_box': (283.0, 133.0, 297.0, 146.0)}, {'text': 'audonll', 'confidence': 0.41043, 'lang': 'en', 'bounding_box': (151.0, 175.0, 174.0, 185.0)}, {'text': 'Riyadh', 'confidence': 0.99985, 'lang': 'en', 'bounding_box': (194.0, 187.0, 230.0, 202.0)}, {'text': 'volo', 'confidence': 0.36539, 'lang': 'en', 'bounding_box': (196.0, 197.0, 227.0, 213.0)}, {'text': 'Google', 'confidence': 0.99893, 'lang': 'en', 'bounding_box': (76.0, 216.0, 120.0, 231.0)}, {'text': 'Dhurma', 'confidence': 0.9469, 'lang': 'en', 'bounding_box': (95.0, 209.0, 124.0, 222.0)}, {'text': 'UberX Saver reserve', 'confidence': 0.99409, 'lang': 'en', 'bounding_box': (72.0, 240.0, 285.0, 266.0)}, {'text': 'ride with Ali', 'confidence': 0.99987, 'lang': 'en', 'bounding_box': (72.0, 269.0, 197.0, 293.0)}, {'text': 'Feb 8 7:10AM', 'confidence': 0.99922, 'lang': 'en', 'bounding_box': (72.0, 304.0, 155.0, 321.0)}, {'text': 'SAR72.90 - Hyundai Accent', 'confidence': 0.98215, 'lang': 'en', 'bounding_box': (72.0, 325.0, 237.0, 344.0)}, {'text': 'Receipt', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (107.0, 363.0, 159.0, 381.0)}, {'text': 'Invoice', 'confidence': 0.99988, 'lang': 'en', 'bounding_box': (210.0, 363.0, 259.0, 381.0)}, {'text': 'O', 'confidence': 0.42204, 'lang': 'en', 'bounding_box': (85.0, 423.0, 92.0, 431.0)}, {'text': '7926 Zayd Ibn Thabit Street Riyadh', 'confidence': 0.99945, 'lang': 'en', 'bounding_box': (109.0, 411.0, 290.0, 428.0)}, {'text': '12831', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (111.0, 427.0, 144.0, 443.0)}, {'text': '7:13 AM', 'confidence': 0.99968, 'lang': 'en', 'bounding_box': (318.0, 418.0, 363.0, 435.0)}, {'text': '□', 'confidence': 0.36019, 'lang': 'en', 'bounding_box': (82.0, 476.0, 95.0, 490.0)}, {'text': 'Terminal 5, King Khalid International', 'confidence': 0.99739, 'lang': 'en', 'bounding_box': (111.0, 469.0, 296.0, 483.0)}, {'text': 'Airport (RUH) - Riyadh 13458', 'confidence': 0.96982, 'lang': 'en', 'bounding_box': (111.0, 483.0, 259.0, 500.0)}, {'text': '8:09 AM', 'confidence': 0.97867, 'lang': 'en', 'bounding_box': (315.0, 475.0, 362.0, 490.0)}, {'text': 'No tip added', 'confidence': 0.99965, 'lang': 'en', 'bounding_box': (110.0, 529.0, 192.0, 546.0)}, {'text': 'Add tip', 'confidence': 0.99987, 'lang': 'en', 'bounding_box': (310.0, 530.0, 355.0, 548.0)}, {'text': '☆', 'confidence': 0.99767, 'lang': 'en', 'bounding_box': (76.0, 580.0, 102.0, 605.0)}, {'text': 'No rating', 'confidence': 0.99993, 'lang': 'en', 'bounding_box': (109.0, 582.0, 172.0, 602.0)}, {'text': 'Rate', 'confidence': 0.99998, 'lang': 'en', 'bounding_box': (321.0, 584.0, 351.0, 600.0)}, {'text': 'Help & safety', 'confidence': 0.98733, 'lang': 'en', 'bounding_box': (71.0, 631.0, 194.0, 659.0)}, {'text': 'Find lost item', 'confidence': 0.99963, 'lang': 'en', 'bounding_box': (111.0, 667.0, 197.0, 685.0)}, {'text': 'a', 'confidence': 0.90171, 'lang': 'en', 'bounding_box': (72.0, 681.0, 104.0, 708.0)}, {'text': 'We can help you qet in touch with your', 'confidence': 0.98901, 'lang': 'en', 'bounding_box': (109.0, 690.0, 310.0, 707.0)}, {'text': '08:06', 'confidence': 0.99951, 'lang': 'ar', 'bounding_box': (82.0, 42.0, 113.0, 57.0)}, {'text': 'il 40: 87%', 'confidence': 0.60194, 'lang': 'ar', 'bounding_box': (262.0, 38.0, 355.0, 60.0)}, {'text': 'Ride details', 'confidence': 0.99921, 'lang': 'ar', 'bounding_box': (106.0, 75.0, 189.0, 92.0)}, {'text': 'سدوي', 'confidence': 0.83614, 'lang': 'ar', 'bounding_box': (108.0, 137.0, 133.0, 150.0)}, {'text': 'Sackue', 'confidence': 0.76215, 'lang': 'ar', 'bounding_box': (110.0, 131.0, 132.0, 141.0)}, {'text': 'A Jubrlin', 'confidence': 0.6996, 'lang': 'ar', 'bounding_box': (147.0, 148.0, 186.0, 162.0)}, {'text': 'o', 'confidence': 0.5376, 'lang': 'ar', 'bounding_box': (283.0, 133.0, 297.0, 146.0)}, {'text': 'العمارية', 'confidence': 0.8927, 'lang': 'ar', 'bounding_box': (151.0, 175.0, 174.0, 185.0)}, {'text': 'Riyadh', 'confidence': 0.99249, 'lang': 'ar', 'bounding_box': (194.0, 187.0, 230.0, 202.0)}, {'text': 'قباض', 'confidence': 0.69115, 'lang': 'ar', 'bounding_box': (196.0, 197.0, 227.0, 213.0)}, {'text': 'Google', 'confidence': 0.99725, 'lang': 'ar', 'bounding_box': (76.0, 216.0, 120.0, 231.0)}, {'text': 'Dhurma', 'confidence': 0.94093, 'lang': 'ar', 'bounding_box': (95.0, 209.0, 124.0, 222.0)}, {'text': 'UberX Saver reserve', 'confidence': 0.99853, 'lang': 'ar', 'bounding_box': (72.0, 240.0, 285.0, 266.0)}, {'text': 'ride with Ali', 'confidence': 0.99751, 'lang': 'ar', 'bounding_box': (72.0, 269.0, 197.0, 293.0)}, {'text': 'Feb 87:10AM', 'confidence': 0.99386, 'lang': 'ar', 'bounding_box': (72.0, 304.0, 155.0, 321.0)}, {'text': 'SAR72.90 - Hyundai Accent', 'confidence': 0.94876, 'lang': 'ar', 'bounding_box': (72.0, 325.0, 237.0, 344.0)}, {'text': 'Receipt', 'confidence': 0.99937, 'lang': 'ar', 'bounding_box': (107.0, 363.0, 159.0, 381.0)}, {'text': 'Invoice', 'confidence': 0.99984, 'lang': 'ar', 'bounding_box': (210.0, 363.0, 259.0, 381.0)}, {'text': 'o', 'confidence': 0.97088, 'lang': 'ar', 'bounding_box': (85.0, 423.0, 92.0, 431.0)}, {'text': '7926 Zayd Ibn Thabit Street Riyadh', 'confidence': 0.98967, 'lang': 'ar', 'bounding_box': (109.0, 411.0, 290.0, 428.0)}, {'text': '12831', 'confidence': 0.99961, 'lang': 'ar', 'bounding_box': (111.0, 427.0, 144.0, 443.0)}, {'text': '7:13 AM', 'confidence': 0.99899, 'lang': 'ar', 'bounding_box': (318.0, 418.0, 363.0, 435.0)}, {'text': 'O', 'confidence': 0.59533, 'lang': 'ar', 'bounding_box': (82.0, 476.0, 95.0, 490.0)}, {'text': 'Terminal 5, King Khalid International', 'confidence': 0.99115, 'lang': 'ar', 'bounding_box': (111.0, 469.0, 296.0, 483.0)}, {'text': 'Airport (RUH) - Riyadh 13458', 'confidence': 0.98502, 'lang': 'ar', 'bounding_box': (111.0, 483.0, 259.0, 500.0)}, {'text': '8:09 AM', 'confidence': 0.99808, 'lang': 'ar', 'bounding_box': (315.0, 475.0, 362.0, 490.0)}, {'text': 'No tip added', 'confidence': 0.99945, 'lang': 'ar', 'bounding_box': (110.0, 529.0, 192.0, 546.0)}, {'text': 'Add tip', 'confidence': 0.95279, 'lang': 'ar', 'bounding_box': (310.0, 530.0, 355.0, 548.0)}, {'text': '{', 'confidence': 0.10841, 'lang': 'ar', 'bounding_box': (76.0, 580.0, 102.0, 605.0)}, {'text': 'No rating', 'confidence': 0.99867, 'lang': 'ar', 'bounding_box': (109.0, 582.0, 172.0, 602.0)}, {'text': 'Rate', 'confidence': 0.9977, 'lang': 'ar', 'bounding_box': (321.0, 584.0, 351.0, 600.0)}, {'text': 'Help & safety', 'confidence': 0.99919, 'lang': 'ar', 'bounding_box': (71.0, 631.0, 194.0, 659.0)}, {'text': 'Find lost item', 'confidence': 0.99062, 'lang': 'ar', 'bounding_box': (111.0, 667.0, 197.0, 685.0)}, {'text': '9', 'confidence': 0.73305, 'lang': 'ar', 'bounding_box': (72.0, 681.0, 104.0, 708.0)}, {'text': 'We can help you get in touch with your', 'confidence': 0.96433, 'lang': 'ar', 'bounding_box': (109.0, 690.0, 310.0, 707.0)}], 'field_confidence': {'vendor': 0.22938524406779665, 'date': 0.33367537288135596, 'currency': 0.6764538559322033, 'amount': 0.3534588940677966, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3534588940677966, 'invoice_number': 0.5764538559322033, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** wL (0.19), 0 (0.38), audonll (0.41), volo (0.37), O (0.42), □ (0.36)

**Raw text:**

```
08:06
  4 487%
Ride details
wL
Sadus
Al Jubaytas
0
audonll
Riyadh
volo
Google
Dhurma
UberX Saver reserve
ride with Ali
Feb 8 7:10AM
SAR72.90 - Hyundai Accent
Receipt
Invoice
O
7926 Zayd Ibn Thabit Street Riyadh
12831
7:13 AM
□
Terminal 5, King Khalid International
Airport (RUH) - Riyadh 13458
8:09 AM
No tip added
Add tip
☆
No rating
Rate
Help & safety
Find lost item
a
We can help you qet in touch with your
```

### Arabic recognizer

**Low-confidence words (<0.5):** { (0.11)

**Raw text:**

```
08:06
il 40: 87%
Ride details
سدوي
Sackue
A Jubrlin
o
العمارية
Riyadh
قباض
Google
Dhurma
UberX Saver reserve
ride with Ali
Feb 87:10AM
SAR72.90 - Hyundai Accent
Receipt
Invoice
o
7926 Zayd Ibn Thabit Street Riyadh
12831
7:13 AM
O
Terminal 5, King Khalid International
Airport (RUH) - Riyadh 13458
8:09 AM
No tip added
Add tip
{
No rating
Rate
Help & safety
Find lost item
9
We can help you get in touch with your
```

## ksa9.png

### Production (mode=auto)

**Parsed fields:** `{'vendor': '', 'expense_type': None, 'amount': 42.0, 'vat_amount': 0.0, 'total_amount': 42.0, 'currency': 'SAR', 'date': 'Oct 12', 'confidence': 0.19, 'field_confidence': {'vendor': 0.18898094, 'date': 0.3160635, 'currency': 0.6639495, 'amount': 0.36964830000000004, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.36964830000000004, 'invoice_number': 0.5639495, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': None, 'confidence': 0.18898094, 'evidence': 'R 4 4 27%', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'date': {'value': 'Oct 12', 'confidence': 0.3160635, 'evidence': 'Oct 12 5:04PM', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'SAR', 'confidence': 0.6639495, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 42.0, 'confidence': 0.36964830000000004, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive', 'amount_equals_total_no_vat'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': 0.0, 'confidence': 0.6, 'evidence': '', 'signals': ['no_vat_evidence_assumed_zero'], 'low': False}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 42.0, 'confidence': 0.36964830000000004, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': 'SAR42', 'confidence': 0.5639495, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}, 'raw_text': '18:06\nR 4 4 27%\nRai 4 Ml 276\n←\n\nRide details\nRiyadh\nuouJI\nالرياض\nUberX Saver ride with\nFaisal\nOct 12 5:04PM\nSAR42.00 - Ford Taurus\nReceipt 日 Invoice\nQP2F+R3F, King Abdullah Dt., Riyadh 5:17 PM\n12451, Saudi Arabia\n8496 Al Nahda Road Riyadh 12833 6:51 PM\nNo tip added\nAdd tip\nNo rating\nRate\nHelp & safety\nFind lost item\nWe can help you get in touch with your', 'raw_json': {'engine': 'rapidocr', 'mode': 'auto', 'words': [{'text': '18:06', 'confidence': 0.99982, 'lang': 'en', 'bounding_box': (213.0, 146.0, 253.0, 159.0)}, {'text': ' R 4 4  27%', 'confidence': 0.53442, 'lang': 'en', 'bounding_box': (360.0, 144.0, 448.0, 159.0)}, {'text': '←', 'confidence': 0.99537, 'lang': 'en', 'bounding_box': (206.0, 172.0, 225.0, 192.0)}, {'text': 'Ride details', 'confidence': 0.99995, 'lang': 'en', 'bounding_box': (204.0, 197.0, 325.0, 222.0)}, {'text': 'Riyadh', 'confidence': 0.99994, 'lang': 'en', 'bounding_box': (255.0, 258.0, 297.0, 277.0)}, {'text': 'uouJI', 'confidence': 0.57284, 'lang': 'en', 'bounding_box': (256.0, 270.0, 294.0, 289.0)}, {'text': 'UberX Saver ride with', 'confidence': 0.98529, 'lang': 'en', 'bounding_box': (204.0, 326.0, 397.0, 349.0)}, {'text': 'Faisal', 'confidence': 0.99997, 'lang': 'en', 'bounding_box': (202.0, 350.0, 261.0, 376.0)}, {'text': 'Oct 12 5:04PM', 'confidence': 0.98209, 'lang': 'en', 'bounding_box': (204.0, 381.0, 283.0, 399.0)}, {'text': 'SAR42.00 - Ford Taurus', 'confidence': 0.98284, 'lang': 'en', 'bounding_box': (205.0, 402.0, 328.0, 417.0)}, {'text': 'Receipt', 'confidence': 0.99984, 'lang': 'en', 'bounding_box': (215.0, 431.0, 280.0, 450.0)}, {'text': '日', 'confidence': 0.99455, 'lang': 'en', 'bounding_box': (307.0, 433.0, 324.0, 449.0)}, {'text': 'Invoice', 'confidence': 0.93503, 'lang': 'en', 'bounding_box': (321.0, 433.0, 366.0, 449.0)}, {'text': 'QP2F+R3F, King Abdullah Dt., Riyadh', 'confidence': 0.99842, 'lang': 'en', 'bounding_box': (236.0, 475.0, 398.0, 489.0)}, {'text': '5:17 PM', 'confidence': 0.99428, 'lang': 'en', 'bounding_box': (415.0, 480.0, 455.0, 496.0)}, {'text': '12451, Saudi Arabia', 'confidence': 0.99924, 'lang': 'en', 'bounding_box': (237.0, 490.0, 325.0, 503.0)}, {'text': '8496 Al Nahda Road Riyadh 12833', 'confidence': 0.97649, 'lang': 'en', 'bounding_box': (236.0, 524.0, 389.0, 539.0)}, {'text': '6:51 PM', 'confidence': 0.95093, 'lang': 'en', 'bounding_box': (415.0, 522.0, 455.0, 539.0)}, {'text': 'No tip added', 'confidence': 0.99677, 'lang': 'en', 'bounding_box': (236.0, 563.0, 308.0, 578.0)}, {'text': 'Add tip', 'confidence': 0.99884, 'lang': 'en', 'bounding_box': (409.0, 564.0, 448.0, 580.0)}, {'text': '★', 'confidence': 0.98937, 'lang': 'en', 'bounding_box': (210.0, 611.0, 228.0, 626.0)}, {'text': 'No rating', 'confidence': 0.99996, 'lang': 'en', 'bounding_box': (235.0, 609.0, 291.0, 627.0)}, {'text': 'Rate', 'confidence': 0.99994, 'lang': 'en', 'bounding_box': (417.0, 610.0, 445.0, 626.0)}, {'text': 'Help & safety', 'confidence': 0.98101, 'lang': 'en', 'bounding_box': (203.0, 651.0, 311.0, 676.0)}, {'text': 'Find lost item', 'confidence': 0.99937, 'lang': 'en', 'bounding_box': (235.0, 681.0, 313.0, 701.0)}, {'text': 'We can help you get in touch with your', 'confidence': 0.97959, 'lang': 'en', 'bounding_box': (234.0, 700.0, 411.0, 720.0)}, {'text': '18:06', 'confidence': 0.99791, 'lang': 'ar', 'bounding_box': (213.0, 146.0, 253.0, 159.0)}, {'text': 'Rai 4 Ml  276', 'confidence': 0.54174, 'lang': 'ar', 'bounding_box': (360.0, 144.0, 448.0, 159.0)}, {'text': '-', 'confidence': 0.13745, 'lang': 'ar', 'bounding_box': (206.0, 172.0, 225.0, 192.0)}, {'text': 'Ride details', 'confidence': 0.96311, 'lang': 'ar', 'bounding_box': (204.0, 197.0, 325.0, 222.0)}, {'text': 'Riyadh', 'confidence': 0.99318, 'lang': 'ar', 'bounding_box': (255.0, 258.0, 297.0, 277.0)}, {'text': 'الرياض', 'confidence': 0.85526, 'lang': 'ar', 'bounding_box': (256.0, 270.0, 294.0, 289.0)}, {'text': 'UberX Saver ride with', 'confidence': 0.99666, 'lang': 'ar', 'bounding_box': (204.0, 326.0, 397.0, 349.0)}, {'text': 'Faisal', 'confidence': 0.99633, 'lang': 'ar', 'bounding_box': (202.0, 350.0, 261.0, 376.0)}, {'text': 'Oct 125:04PM', 'confidence': 0.9673, 'lang': 'ar', 'bounding_box': (204.0, 381.0, 283.0, 399.0)}, {'text': 'SAR42.00 - Ford Taurus', 'confidence': 0.99508, 'lang': 'ar', 'bounding_box': (205.0, 402.0, 328.0, 417.0)}, {'text': 'Receipt', 'confidence': 0.89887, 'lang': 'ar', 'bounding_box': (215.0, 431.0, 280.0, 450.0)}, {'text': 'B', 'confidence': 0.82382, 'lang': 'ar', 'bounding_box': (307.0, 433.0, 324.0, 449.0)}, {'text': 'Invoice', 'confidence': 0.99961, 'lang': 'ar', 'bounding_box': (321.0, 433.0, 366.0, 449.0)}, {'text': 'QP2F+R3F, King Abdullah Dt., Riyadh', 'confidence': 0.9305, 'lang': 'ar', 'bounding_box': (236.0, 475.0, 398.0, 489.0)}, {'text': '5:17 PM', 'confidence': 0.97104, 'lang': 'ar', 'bounding_box': (415.0, 480.0, 455.0, 496.0)}, {'text': '12451, Saudi Arabia', 'confidence': 0.97883, 'lang': 'ar', 'bounding_box': (237.0, 490.0, 325.0, 503.0)}, {'text': '8496 Al Nahda Road Riyadh 12833', 'confidence': 0.97244, 'lang': 'ar', 'bounding_box': (236.0, 524.0, 389.0, 539.0)}, {'text': '6:51 PM', 'confidence': 0.99866, 'lang': 'ar', 'bounding_box': (415.0, 522.0, 455.0, 539.0)}, {'text': 'No tip added', 'confidence': 0.99974, 'lang': 'ar', 'bounding_box': (236.0, 563.0, 308.0, 578.0)}, {'text': 'Add tip', 'confidence': 0.99877, 'lang': 'ar', 'bounding_box': (409.0, 564.0, 448.0, 580.0)}, {'text': 'No rating', 'confidence': 0.99962, 'lang': 'ar', 'bounding_box': (235.0, 609.0, 291.0, 627.0)}, {'text': 'Rate', 'confidence': 0.99925, 'lang': 'ar', 'bounding_box': (417.0, 610.0, 445.0, 626.0)}, {'text': 'Help & safety', 'confidence': 0.99802, 'lang': 'ar', 'bounding_box': (203.0, 651.0, 311.0, 676.0)}, {'text': 'Find lost item', 'confidence': 0.96897, 'lang': 'ar', 'bounding_box': (235.0, 681.0, 313.0, 701.0)}, {'text': 'We can help you get in touch with your', 'confidence': 0.99441, 'lang': 'ar', 'bounding_box': (234.0, 700.0, 411.0, 720.0)}], 'field_confidence': {'vendor': 0.18898094, 'date': 0.3160635, 'currency': 0.6639495, 'amount': 0.36964830000000004, 'vat_rate': 0.0, 'vat_amount': 0.6, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.36964830000000004, 'invoice_number': 0.5639495, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'expense_type': None}}`

### English recognizer

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
18:06
 R 4 4  27%
←
Ride details
Riyadh
uouJI
UberX Saver ride with
Faisal
Oct 12 5:04PM
SAR42.00 - Ford Taurus
Receipt
日
Invoice
QP2F+R3F, King Abdullah Dt., Riyadh
5:17 PM
12451, Saudi Arabia
8496 Al Nahda Road Riyadh 12833
6:51 PM
No tip added
Add tip
★
No rating
Rate
Help & safety
Find lost item
We can help you get in touch with your
```

### Arabic recognizer

**Low-confidence words (<0.5):** - (0.14)

**Raw text:**

```
18:06
Rai 4 Ml  276
-
Ride details
Riyadh
الرياض
UberX Saver ride with
Faisal
Oct 125:04PM
SAR42.00 - Ford Taurus
Receipt
B
Invoice
QP2F+R3F, King Abdullah Dt., Riyadh
5:17 PM
12451, Saudi Arabia
8496 Al Nahda Road Riyadh 12833
6:51 PM
No tip added
Add tip
No rating
Rate
Help & safety
Find lost item
We can help you get in touch with your
```
