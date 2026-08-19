# PaddleOCR results — ksa

Engine: PaddleOCR only (`lang=en` then `lang=ar`).
Summary reflects the merged (production) result — see `ocr_service.merge_bilingual`:
each language pass is parsed separately and merged field-by-field, matching what
`ocr_service._paddle_ocr` actually does for real uploads. The per-image sections below
still show each language pass on its own for debugging, plus the merged result.
Images: `9`.

## Summary

| Image | Vendor (merged) | Amount (merged) | VAT (merged) | Total (merged) | Date (merged) | Currency (merged) |
|---|---|---|---|---|---|---|
| ksa1.png | HAIA | 2.0 |  | 8888.0 |  |  |
| ksa2.png | شركة قمة الخليج المحدودة للأجرة العامة | 386.0 |  | 451.0 |  |  |
| ksa3.png | Shahad Tawik Company | 409.0 |  | 409.0 | 29-6-26 |  |
| ksa4.png | Mr.J | 55.0 |  | 55.0 |  |  |
| ksa5.png | TAXIAL-AJME العجمى أجرة عامة | 8.0 |  | 8.0 |  |  |
| ksa6.png | Shaml Al-Doha Company شركة شمل الدوحة | 201.0 |  | 201.0 | 05/07/26 |  |
| ksa7.png | وشريكه شركة سلطان منير الحارثي و | 8.57 | 0.43 | 9.0 |  |  |
| ksa8.png | Ride details | 72.9 |  | 72.9 | Feb 8 | SAR |
| ksa9.png | R4627% | 42.0 |  | 42.0 | Oct 12 | SAR |

## ksa1.png

### Merged (production)

**Parsed fields:** `{'vendor': 'HAIA', 'expense_type': None, 'amount': 2.0, 'vat_amount': None, 'total_amount': 8888.0, 'currency': None, 'date': '', 'confidence': 0.08, 'field_confidence': {'vendor': 0.21504488127435273, 'date': 0.0, 'currency': 0.0, 'amount': 0.38572676818874013, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.6971378005494424, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'HAIA', 'confidence': 0.21504488127435273, 'evidence': 'HAIA', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 2.0, 'confidence': 0.38572676818874013, 'evidence': 'Date 2i /66 /2b الموافق التاريخ', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 8888.0, 'confidence': 0.6971378005494424, 'evidence': 'Total TERR8888an8888a88888Wa88888Rw88an8RE8 الإجمالي', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'HAIA', 'expense_type': None, 'amount': 208.0, 'vat_amount': None, 'total_amount': 208.0, 'currency': None, 'date': '', 'confidence': 0.05, 'field_confidence': {'vendor': 0.2131445078145141, 'date': 0.0, 'currency': 0.0, 'amount': 0.2951597960286879, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.2951597960286879, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'HAIA', 'confidence': 0.2131445078145141, 'evidence': 'HAIA', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 208.0, 'confidence': 0.2951597960286879, 'evidence': 'KASD208 45', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 208.0, 'confidence': 0.2951597960286879, 'evidence': 'KASD208 45', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** 0 (0.40), a11 (0.49)

**Raw text:**

```
R
ć
0
HAIA
éro o
58311119
gil
90375
Customer Invoise
Dt2106/26
//
Customer Name:
Fare
Place
Notes
J
a11
KASD208
45
to Dalay
Total
.
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': '', 'expense_type': None, 'amount': 8.0, 'vat_amount': None, 'total_amount': 8.0, 'currency': 'GBP', 'date': '', 'confidence': 0.12, 'field_confidence': {'vendor': 0.18920964572657292, 'date': 0.0, 'currency': 0.3078328011473219, 'amount': 0.5407178627411324, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.8471378005494424, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': None, 'confidence': 0.18920964572657292, 'evidence': 'AAS', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': 'GBP', 'confidence': 0.3078328011473219, 'evidence': '261:LLIZ9I GBP 8S0', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 8.0, 'confidence': 0.5407178627411324, 'evidence': '261:LLIZ9I GBP 8S0', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 8.0, 'confidence': 0.8471378005494424, 'evidence': 'Total TERR8888an8888a88888Wa88888Rw88an8RE8 الإجمالي', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** ا (0.45), يي   اي  ي (0.40), ا ي (0.43), TERR8888an8888a88888Wa88888Rw88an8RE8 (0.39)

**Raw text:**

```
ا
ا
يي   اي  ي
AAS
ا ي
26١:LLIZ9I£8S0
فاتورة راكب
92375
Customer Invoise
Date 2i /66 /2b
الموافق
التاريخ
المحترم
اسم الراكب
Customer Name:
الشركة غير مسؤولة عن عدم تواجدرقم اللوحة بالفاتورة
رقم اللوحة
ملاحظات
Farالأجرة
Place
المكان
Notes
ريال
هللة
إلى
من
KALD..Q..h
-45
toNalsy
Total
الإجمالي
TERR8888an8888a88888Wa88888Rw88an8RE8
سم اسائقرقم السيارة توقيع السائق
عزيزي الراكب نرجو التأكد من استلام جميع أمتعتكم
مع أجمل تمنياتنا لكم سلامة الوصول
شكرا لتفضلكم بركوب السيارة
```

## ksa2.png

### Merged (production)

**Parsed fields:** `{'vendor': 'شركة قمة الخليج المحدودة للأجرة العامة', 'expense_type': None, 'amount': 386.0, 'vat_amount': None, 'total_amount': 451.0, 'currency': None, 'date': '', 'confidence': 0.12, 'field_confidence': {'vendor': 0.2837043483962927, 'date': 0.0, 'currency': 0.0, 'amount': 0.2244909006170093, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.7998297157068424, 'invoice_number': 0.6030488914438427, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'شركة قمة الخليج المحدودة للأجرة العامة', 'confidence': 0.2837043483962927, 'evidence': 'شركة قمة الخليج المحدودة للأجرة العامة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 386.0, 'confidence': 0.2244909006170093, 'evidence': '0386 Invoice25106/26 Invoice فاتورة', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 451.0, 'confidence': 0.7998297157068424, 'evidence': 'المجموع فقط 451.', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'invoice_number': {'value': '0386', 'confidence': 0.6030488914438427, 'evidence': '0386 Invoice25106/26 Invoice فاتورة', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'Qema Al-Khaleej Limited Co. For General Rent', 'expense_type': None, 'amount': 451.0, 'vat_amount': None, 'total_amount': 451.0, 'currency': None, 'date': '', 'confidence': 0.1, 'field_confidence': {'vendor': 0.28141812875933714, 'date': 0.0, 'currency': 0.0, 'amount': 0.3324354617972545, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3324354617972545, 'invoice_number': 0.6005825237308382, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Qema Al-Khaleej Limited Co. For General Rent', 'confidence': 0.28141812875933714, 'evidence': 'Qema Al-Khaleej Limited Co. For General Rent', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': False}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 451.0, 'confidence': 0.3324354617972545, 'evidence': '451.', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 451.0, 'confidence': 0.3324354617972545, 'evidence': '451.', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': '0386', 'confidence': 0.6005825237308382, 'evidence': '0386 Invoice25106/26', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** J (0.38)

**Raw text:**

```
Qema Al-Khaleej Limited Co. For General Rent
0386
Invoice25106/26
!
J
kingdomp tones.
o malz
451.
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'شركة قمة الخليج المحدودة للأجرة العامة', 'expense_type': None, 'amount': 5106.0, 'vat_amount': None, 'total_amount': 45.0, 'currency': None, 'date': '', 'confidence': 0.12, 'field_confidence': {'vendor': 0.2836808175608136, 'date': 0.0, 'currency': 0.0, 'amount': 0.2267956358708184, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.7707072375453394, 'invoice_number': 0.587882004626866, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'شركة قمة الخليج المحدودة للأجرة العامة', 'confidence': 0.2836808175608136, 'evidence': 'شركة قمة الخليج المحدودة للأجرة العامة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 5106.0, 'confidence': 0.2267956358708184, 'evidence': 'Invoice التاريخ5106', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 45.0, 'confidence': 0.7707072375453394, 'evidence': 'المجموع فقط 45/.', 'signals': ['total_label', 'same_line', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money'], 'low': False}, 'invoice_number': {'value': '5106', 'confidence': 0.587882004626866, 'evidence': 'Invoice التاريخ5106', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': False}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** حم (0.40), ج (0.30), rop (0.26), ل (0.24), f (0.30)

**Raw text:**

```
شركة قمة الخليج المحدودة للأجرة العامة
Qema Al-Khaleej Limited Co. For General Rent
فاتورة
0386
Invoice
التاريخ5١06
للي
حم
ج
rop
ل
Dalog
f
المجموع فقط
45/.
```

## ksa3.png

### Merged (production)

**Parsed fields:** `{'vendor': 'Shahad Tawik Company', 'expense_type': None, 'amount': 409.0, 'vat_amount': None, 'total_amount': 409.0, 'currency': None, 'date': '29-6-26', 'confidence': 0.07, 'field_confidence': {'vendor': 0.27792997377760265, 'date': 0.2938908614098707, 'currency': 0.0, 'amount': 0.28308704451921785, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.28308704451921785, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Shahad Tawik Company', 'confidence': 0.27792997377760265, 'evidence': 'Shahad Tawik Company', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '29-6-26', 'confidence': 0.2938908614098707, 'evidence': '409 KAFD 208 29-6-26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 409.0, 'confidence': 0.28308704451921785, 'evidence': '409 KAFD 208 29-6-26', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 409.0, 'confidence': 0.28308704451921785, 'evidence': '409 KAFD 208 29-6-26', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'Shahad Tawik Company', 'expense_type': None, 'amount': 409.0, 'vat_amount': None, 'total_amount': 409.0, 'currency': None, 'date': '29-6-26', 'confidence': 0.07, 'field_confidence': {'vendor': 0.2780083354952915, 'date': 0.2942185558656605, 'currency': 0.0, 'amount': 0.2827593500634281, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.2827593500634281, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Shahad Tawik Company', 'confidence': 0.2780083354952915, 'evidence': 'Shahad Tawik Company', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '29-6-26', 'confidence': 0.2942185558656605, 'evidence': '409 KAFD 208 29-6-26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 409.0, 'confidence': 0.2827593500634281, 'evidence': '409 KAFD 208 29-6-26', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 409.0, 'confidence': 0.2827593500634281, 'evidence': '409 KAFD 208 29-6-26', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

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
KAFD 208
29-6-26
to malzz
..
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'طويق شركة شهد', 'expense_type': None, 'amount': 2.0, 'vat_amount': None, 'total_amount': 2.0, 'currency': None, 'date': '29-6-26', 'confidence': 0.09, 'field_confidence': {'vendor': 0.26043110924927304, 'date': 0.26491232646659096, 'currency': 0.0, 'amount': 0.42335070328757085, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.42335070328757085, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'طويق شركة شهد', 'confidence': 0.26043110924927304, 'evidence': 'طويق شركة شهد', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '29-6-26', 'confidence': 0.26491232646659096, 'evidence': 'JoH KAfD2o8 29-6-26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 2.0, 'confidence': 0.42335070328757085, 'evidence': 'JoH KAfD2o8 29-6-26', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 2.0, 'confidence': 0.42335070328757085, 'evidence': 'JoH KAfD2o8 29-6-26', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** ل (0.39), junowy (0.35), ايدز (0.48), ا  (0.41), ا ل (0.33)

**Raw text:**

```
طويق
شركة شهد
Shahad Tawik Company
Car Number (22)
٢
السيارة
ل
junowy
ايدز
ا
ا ل
JoH
KAfD2o8
29-6-26
toMalsz
الشركة غير مسئولة عن أي متعلقات شخصية يتركها الراكب داخل السيارة
ونشكركم لإتاحة الفرصة لخدمتكم
بعد مغادرتها
لستفسارجوا٥٠٩٩٠٥١٤٠٥٠٠٠٠٦
```

## ksa4.png

### Merged (production)

**Parsed fields:** `{'vendor': 'Mr.J', 'expense_type': None, 'amount': 55.0, 'vat_amount': None, 'total_amount': 55.0, 'currency': None, 'date': '', 'confidence': 0.08, 'field_confidence': {'vendor': 0.23023017303668927, 'date': 0.0, 'currency': 0.0, 'amount': 0.26201242117505325, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.26201242117505325, 'invoice_number': 0.5723429789117526, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Mr.J', 'confidence': 0.23023017303668927, 'evidence': 'Mr.J', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 55.0, 'confidence': 0.26201242117505325, 'evidence': '55', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 55.0, 'confidence': 0.26201242117505325, 'evidence': '55', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': 'C/58444Invoice', 'confidence': 0.5723429789117526, 'evidence': 'No.:C/58444Invoice Inic فاتورة 14ه التاريخ', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': False}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'Mr./', 'expense_type': None, 'amount': 55.0, 'vat_amount': None, 'total_amount': 55.0, 'currency': None, 'date': '', 'confidence': 0.09, 'field_confidence': {'vendor': 0.23350846520494428, 'date': 0.0, 'currency': 0.0, 'amount': 0.26201242117505325, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.26201242117505325, 'invoice_number': 0.617776568727846, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Mr./', 'confidence': 0.23350846520494428, 'evidence': 'Mr./', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 55.0, 'confidence': 0.26201242117505325, 'evidence': '55', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 55.0, 'confidence': 0.26201242117505325, 'evidence': '55', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': 'C/58444Invoice', 'confidence': 0.617776568727846, 'evidence': 'No.:C/58444Invoice //', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': False}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** 11 (0.41)

**Raw text:**

```
No.:C/58444Invoice
//
.30106126
Mr./
To.
11
From
i
Amount
kingdon
cendu to
molaz
55
Total
WE WILL BE HAPPY TO RECEIVE YOUR OPENIONS FOR
DEVELOPING OUR SEVICES
ASK FOR YOUR INVOICE
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'الموافق26/2', 'expense_type': None, 'amount': 55.0, 'vat_amount': None, 'total_amount': 55.0, 'currency': None, 'date': '', 'confidence': 0.05, 'field_confidence': {'vendor': 0.2330754220621732, 'date': 0.0, 'currency': 0.0, 'amount': 0.26238414433347684, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.26238414433347684, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'الموافق26/2', 'confidence': 0.2330754220621732, 'evidence': 'الموافق26/2', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 55.0, 'confidence': 0.26238414433347684, 'evidence': '55', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 55.0, 'confidence': 0.26238414433347684, 'evidence': '55', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
No.:C/58444!
Inic فاتورة
١٤ه
التاريخ
الموافق26/٢
Mr.J
المطلوب من المكرم
To.
إلى
From
من
Ant المبلغ
kgdom
cadn
To
Noley
55
Total
المجموع
توقيع السائق
رقم السيارة
نسعد بإستقبال أرائكم لتطوير خدماتنا
WE WILL BE HAPPY TO RECEIVE YOUR OPENIONS FOR
DEVELOPING OUR SEVICES
لاتنسي طلب فاتورتك من السائق
ASK FOR YOUR INVOICE
```

## ksa5.png

### Merged (production)

**Parsed fields:** `{'vendor': 'TAXIAL-AJME العجمى أجرة عامة', 'expense_type': None, 'amount': 8.0, 'vat_amount': None, 'total_amount': 8.0, 'currency': None, 'date': '', 'confidence': 0.06, 'field_confidence': {'vendor': 0.2845140451934256, 'date': 0.0, 'currency': 0.0, 'amount': 0.31781974495676646, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.31781974495676646, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'TAXIAL-AJME العجمى أجرة عامة', 'confidence': 0.2845140451934256, 'evidence': 'TAXIAL-AJME العجمى أجرة عامة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 8.0, 'confidence': 0.31781974495676646, 'evidence': 'S8ANSBOABBNER', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 8.0, 'confidence': 0.31781974495676646, 'evidence': 'S8ANSBOABBNER', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'TAXIAL-AJME', 'expense_type': None, 'amount': 2.08, 'vat_amount': None, 'total_amount': 2.08, 'currency': None, 'date': '03/07/26', 'confidence': 0.08, 'field_confidence': {'vendor': 0.2929870825722586, 'date': 0.311323774589545, 'currency': 0.0, 'amount': 0.30017902243319516, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.30017902243319516, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'TAXIAL-AJME', 'confidence': 0.2929870825722586, 'evidence': 'TAXIAL-AJME', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '03/07/26', 'confidence': 0.311323774589545, 'evidence': 'B/N0.20367 03/07/26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 2.08, 'confidence': 0.30017902243319516, 'evidence': 'To: Malaz KAFD 2.08', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 2.08, 'confidence': 0.30017902243319516, 'evidence': 'To: Malaz KAFD 2.08', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** : (0.44)

**Raw text:**

```
TAXIAL-AJME
M
Riyadh - AL-Shifa
Tel.: 4226131
:
03/07/26
B/NO.20367
  /  /
Name of Driver
To: Malaz
KAFD 2.08
S.R. Total
Signature
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'TAXI AL-AJME العجمى أجرة عامة', 'expense_type': None, 'amount': 8.0, 'vat_amount': None, 'total_amount': 8.0, 'currency': None, 'date': '', 'confidence': 0.06, 'field_confidence': {'vendor': 0.2759206766631521, 'date': 0.0, 'currency': 0.0, 'amount': 0.31781974495676646, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.31781974495676646, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'TAXI AL-AJME العجمى أجرة عامة', 'confidence': 0.2759206766631521, 'evidence': 'TAXI AL-AJME العجمى أجرة عامة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 8.0, 'confidence': 0.31781974495676646, 'evidence': 'S8ANSBOABBNER', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 8.0, 'confidence': 0.31781974495676646, 'evidence': 'S8ANSBOABBNER', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** S8ANSBOABBNER (0.42)

**Raw text:**

```
TAXI AL-AJME
M
العجمى أجرة عامة
Riyadh - AL-Shifa
الرياض  الشفا
Tel.: 4226131
تلفون  ٤٢٢٦١٣١
فاتورة راكب
التاريخ١٤ه
B /NO. 20367
الموافق   ٢٠١م
Name of Driver
إسم لسائق
To: Malaq ى
KAD2.0r
مشوارمن
Signatureالتوقيع
S8ANSBOABBNER
```

## ksa6.png

### Merged (production)

**Parsed fields:** `{'vendor': 'Shaml Al-Doha Company شركة شمل الدوحة', 'expense_type': None, 'amount': 201.0, 'vat_amount': None, 'total_amount': 201.0, 'currency': None, 'date': '05/07/26', 'confidence': 0.12, 'field_confidence': {'vendor': 0.267326755348185, 'date': 0.31557878443111853, 'currency': 0.0, 'amount': 0.37173767268925206, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.37173767268925206, 'invoice_number': 0.5655787844311185, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Shaml Al-Doha Company شركة شمل الدوحة', 'confidence': 0.267326755348185, 'evidence': 'Shaml Al-Doha Company شركة شمل الدوحة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '05/07/26', 'confidence': 0.31557878443111853, 'evidence': 'INVOICE 05/07/26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 201.0, 'confidence': 0.37173767268925206, 'evidence': 'Lic. No. : 201', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 201.0, 'confidence': 0.37173767268925206, 'evidence': 'Lic. No. : 201', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': '05/07/26', 'confidence': 0.5655787844311185, 'evidence': 'INVOICE 05/07/26', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': False}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'Shaml Al-Doha Company', 'expense_type': None, 'amount': 351.0, 'vat_amount': None, 'total_amount': 351.0, 'currency': None, 'date': '05/07/26', 'confidence': 0.11, 'field_confidence': {'vendor': 0.28110412705106014, 'date': 0.31029696590204076, 'currency': 0.0, 'amount': 0.33495711855547106, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.33495711855547106, 'invoice_number': 0.5602969659020407, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Shaml Al-Doha Company', 'confidence': 0.28110412705106014, 'evidence': 'Shaml Al-Doha Company', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '05/07/26', 'confidence': 0.31029696590204076, 'evidence': 'INVOICE 05/07/26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 351.0, 'confidence': 0.33495711855547106, 'evidence': '351', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 351.0, 'confidence': 0.33495711855547106, 'evidence': '351', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': '05/07/26', 'confidence': 0.5602969659020407, 'evidence': 'INVOICE 05/07/26', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': False}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
Shaml Al-Doha Company
Lic. No. : 201
Tel.: 4850982 / 4850952
.0/.Y:
P.O.Box : 90604 Riyadh : 11623
K. Fahd Red. Al-Qerwan Quarter
VAT:300396976200002
INVOICE
05/07/26
Mala o ng
Louir
351
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'Shaml Al-Doha Company شركة شمل الدوحة', 'expense_type': None, 'amount': 201.0, 'vat_amount': None, 'total_amount': 201.0, 'currency': None, 'date': '05/02/26', 'confidence': 0.12, 'field_confidence': {'vendor': 0.2670574555277182, 'date': 0.29863758862981676, 'currency': 0.0, 'amount': 0.37173767268925206, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.37173767268925206, 'invoice_number': 0.5486375886298167, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Shaml Al-Doha Company شركة شمل الدوحة', 'confidence': 0.2670574555277182, 'evidence': 'Shaml Al-Doha Company شركة شمل الدوحة', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': '05/02/26', 'confidence': 0.29863758862981676, 'evidence': 'INVOICE 05/02/26', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 201.0, 'confidence': 0.37173767268925206, 'evidence': 'Lic. No. : 201', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 201.0, 'confidence': 0.37173767268925206, 'evidence': 'Lic. No. : 201', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': '05/02/26', 'confidence': 0.5486375886298167, 'evidence': 'INVOICE 05/02/26', 'signals': ['invoice_number_label', 'position_prior_upper'], 'low': False}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
Shaml Al-Doha Company
شركة شمل الدوحة
Lic. No. : 201
ترخيم رقم ٢٠١
Tel.: 4850982 / 4850952
تلفون٤٨٥٠٩٥٥٩٨
P.0.Box : 90604 Rlyadh : 11623
 ب ٩٠٦٠٤لرياض١١٦٧٣
K. Fahd Red. Al-Qerwan Quarter
طريق الملحك فهدصي القيروان
VAT: 300396976200002
الرقمالضري٣٠٠٣٩٦٩٧٢٠٠٠٠٣
فاتورة
INVOICE
05/02/26
التاريخ
رقم السيارة
اسم السائق
المبلغ امطلوبا
tort
وذلك مقابل نقل ركاب من
35/
إلى
توقيع السائق
```

## ksa7.png

### Merged (production)

**Parsed fields:** `{'vendor': 'وشريكه شركة سلطان منير الحارثي و', 'expense_type': None, 'amount': 8.57, 'vat_amount': 0.43, 'total_amount': 9.0, 'currency': None, 'date': '', 'confidence': 0.13, 'field_confidence': {'vendor': 0.2625579397937743, 'date': 0.0, 'currency': 0.0, 'amount': 0.4, 'vat_rate': 0.6252377927303314, 'vat_amount': 0.4, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.46691049304074583, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'وشريكه شركة سلطان منير الحارثي و', 'confidence': 0.2625579397937743, 'evidence': 'وشريكه شركة سلطان منير الحارثي و', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 8.57, 'confidence': 0.4, 'evidence': 'derived: D9az الاجمالي', 'signals': ['derived_arithmetic'], 'low': True, 'warning': 'derived_value'}, 'vat_rate': {'value': 5.0, 'confidence': 0.6252377927303314, 'evidence': 'ضريية القمة المضافة 5', 'signals': ['vat_tax_amount_label', 'known_vat_rate', 'format_known_vat_rate'], 'low': False}, 'vat_amount': {'value': 0.43, 'confidence': 0.4, 'evidence': 'derived: D9az الاجمالي at 5.0%', 'signals': ['derived_arithmetic', 'derived_inclusive'], 'low': True, 'warning': 'derived_value'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 9.0, 'confidence': 0.46691049304074583, 'evidence': 'D9az الاجمالي', 'signals': ['total_label', 'same_line', 'fuzzy_label_match', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'reconciliation_mismatch'], 'low': False}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': '', 'expense_type': None, 'amount': 10.0, 'vat_amount': None, 'total_amount': 10.0, 'currency': None, 'date': '', 'confidence': 0.05, 'field_confidence': {'vendor': 0.13161054676296802, 'date': 0.0, 'currency': 0.0, 'amount': 0.3283528654767155, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3283528654767155, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': None, 'confidence': 0.13161054676296802, 'evidence': 'Date 14 /07/26', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': 10.0, 'confidence': 0.3283528654767155, 'evidence': '10', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 10.0, 'confidence': 0.3283528654767155, 'evidence': '10', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** S (0.40), J2 (0.37), i (0.35), D9az (0.45)

**Raw text:**

```
-/-
.
0098594
Customer Invoice
Date 14 /07/26
1
Customer name:
Notes
Fare
521
Fare
S
J2
Alls
i
kingdoum
45
To der to
D9az
10
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'وشريكه شركة سلطان منير الحارثي و', 'expense_type': None, 'amount': None, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '', 'confidence': 0.08, 'field_confidence': {'vendor': 0.2792760917207686, 'date': 0.0, 'currency': 0.0, 'amount': 0.09407954870376377, 'vat_rate': 0.6252377927303314, 'vat_amount': 0.1565335450960253, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.09407954870376377, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'currency', 'amount', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'وشريكه شركة سلطان منير الحارثي و', 'confidence': 0.2792760917207686, 'evidence': 'وشريكه شركة سلطان منير الحارثي و', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'amount': {'value': None, 'confidence': 0.09407954870376377, 'evidence': 'Date الموافق142', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'vat_rate': {'value': 5.0, 'confidence': 0.6252377927303314, 'evidence': 'ضريية القمة المضافة 5', 'signals': ['vat_tax_amount_label', 'known_vat_rate', 'format_known_vat_rate'], 'low': False}, 'vat_amount': {'value': None, 'confidence': 0.1565335450960253, 'evidence': 'ضريية القمة المضافة 5', 'signals': ['vat_tax_amount_label', 'same_line', 'fuzzy_label_match', 'currency_value', 'no_decimal_point', 'position_prior_lower', 'format_integer_money', 'looks_like_rate_not_amount', 'reconciliation_mismatch'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': None, 'confidence': 0.09407954870376377, 'evidence': 'Date الموافق142', 'signals': ['no_label_bare_number', 'currency_value', 'position_prior_lower', 'format_decimal_money', 'reconciliation_mismatch'], 'low': True, 'warning': 'low_confidence_all_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** +B (0.27)

**Raw text:**

```
وشريكه
شركة سلطان منير الحارثي و
للأجرة العامة
ترخيصرقم ٤٤
٠ يي
الرياضالشفاطريق العارض
الرق الضريبي٣١٠٠٦٢١٠٠٠٣
0098594
فاتورة راكب
Customer Invoice
الموافق142
Date
/
/
التاريخ
Customer name:
اسم الراكب
Notes
ملاحظات
Fare
الأجرة
Fare
المكان
ريال
هلله
إلى
من
Toser
+B
الاجمالي
ضريية القمة المضافة ٥
الاجمالي شامل القيمة المضافة
توقيع السائق؛
رقم السيارة
اسم السائق
عزيزي الراكب نرجو التأكد من إستلام جميع امتعتكم
مع اجمل تمنياتنا لكم بسلامة الوصول
شكرا لتفضلكم بركوب السيارة
```

## ksa8.png

### Merged (production)

**Parsed fields:** `{'vendor': 'Ride details', 'expense_type': None, 'amount': 72.9, 'vat_amount': None, 'total_amount': 72.9, 'currency': 'SAR', 'date': 'Feb 8', 'confidence': 0.1, 'field_confidence': {'vendor': 0.2528313081049528, 'date': 0.33356920070335516, 'currency': 0.32870835881741317, 'amount': 0.34795842457501613, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.34795842457501613, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Ride details', 'confidence': 0.2528313081049528, 'evidence': 'Ride details', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': 'Feb 8', 'confidence': 0.33356920070335516, 'evidence': 'Feb 8 7:10AM', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'SAR', 'confidence': 0.32870835881741317, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 72.9, 'confidence': 0.34795842457501613, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 72.9, 'confidence': 0.34795842457501613, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': '4G87%', 'expense_type': None, 'amount': 72.9, 'vat_amount': None, 'total_amount': 72.9, 'currency': 'SAR', 'date': 'Feb 8', 'confidence': 0.1, 'field_confidence': {'vendor': 0.25669117085486853, 'date': 0.337620919661548, 'currency': 0.3276793421211712, 'amount': 0.3474011479911334, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.3474011479911334, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': '4G87%', 'confidence': 0.25669117085486853, 'evidence': '4G87%', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': 'Feb 8', 'confidence': 0.337620919661548, 'evidence': 'Feb 8 7:10AM', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'SAR', 'confidence': 0.3276793421211712, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 72.9, 'confidence': 0.3474011479911334, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 72.9, 'confidence': 0.3474011479911334, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** aLa (0.43)

**Raw text:**

```
08:06
4G87%
Ride details
.
Sadue
Al Jubaylan
aLa
aianl
Detyah
Riyadh
Dhurma
volal
Google
UberX Saver reserve
ride with Ali
Feb 8 7:10AM
SAR72.90 - Hyundai Accent
Receipt
Invoice
7926 Zayd Ibn Thabit Street Riyadh
7:13 AM
12831
Terminal 5, King Khalid International
8:09 AM
Airport (RUH) - Riyadh 13458
No tip added
Add tip
No rating
Rate
Help & safety
Find lost item
We can help you get in touch with your
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'Ride details', 'expense_type': None, 'amount': 72.9, 'vat_amount': None, 'total_amount': 72.9, 'currency': 'SAR', 'date': 'Feb 8', 'confidence': 0.1, 'field_confidence': {'vendor': 0.252887758653672, 'date': 0.33356920070335516, 'currency': 0.32870835881741317, 'amount': 0.34795842457501613, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.34795842457501613, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Ride details', 'confidence': 0.252887758653672, 'evidence': 'Ride details', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': 'Feb 8', 'confidence': 0.33356920070335516, 'evidence': 'Feb 8 7:10AM', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'SAR', 'confidence': 0.32870835881741317, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 72.9, 'confidence': 0.34795842457501613, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 72.9, 'confidence': 0.34795842457501613, 'evidence': 'SAR72.90 - Hyundai Accent', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
08:06
.atl4G :al
Ride details
AJ Jubaytahs
Riya
Google
Drurma
Map deta E2028 Googis
UberX Saver reserve
ride with Ali
Feb 8 7:10AM
SAR72.90 - Hyundai Accent
Receipt
Invoice
7926 Zayd Ibn Thabit Street Riyadh
12831
7:13 AM
Terminal 5, King Khalid International
8:09 AM
Airport (RUH) - Riyadh 13458
No tip added
Add tip
No rating
Rate
Help & safety
Find lost item
We can help you qet in touch with your
```

## ksa9.png

### Merged (production)

**Parsed fields:** `{'vendor': 'R4627%', 'expense_type': None, 'amount': 42.0, 'vat_amount': None, 'total_amount': 42.0, 'currency': 'SAR', 'date': 'Oct 12', 'confidence': 0.1, 'field_confidence': {'vendor': 0.24195310823871158, 'date': 0.319822101819218, 'currency': 0.31562241673304436, 'amount': 0.36813912242816094, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.36813912242816094, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'R4627%', 'confidence': 0.24195310823871158, 'evidence': 'R4627%', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': 'Oct 12', 'confidence': 0.319822101819218, 'evidence': 'Oct 12 5:04PM', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'SAR', 'confidence': 0.31562241673304436, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 42.0, 'confidence': 0.36813912242816094, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 42.0, 'confidence': 0.36813912242816094, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'R4627%', 'expense_type': None, 'amount': 42.0, 'vat_amount': None, 'total_amount': 42.0, 'currency': 'SAR', 'date': 'Oct 12', 'confidence': 0.1, 'field_confidence': {'vendor': 0.24195310823871158, 'date': 0.319822101819218, 'currency': 0.31617064237429493, 'amount': 0.36863252550528647, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.36863252550528647, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'R4627%', 'confidence': 0.24195310823871158, 'evidence': 'R4627%', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': 'Oct 12', 'confidence': 0.319822101819218, 'evidence': 'Oct 12 5:04PM', 'signals': ['date_format_match', 'position_prior_upper', 'format_date_shape'], 'low': False}, 'currency': {'value': 'SAR', 'confidence': 0.31617064237429493, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 42.0, 'confidence': 0.36863252550528647, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 42.0, 'confidence': 0.36863252550528647, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** E (0.21), AM (0.41)

**Raw text:**

```
18:06
R4627%
Ride details
Riyadh
E
wobJI
AM
UberX Saver ride with
Faisal
Oct 12 5:04PM
SAR42.00 - Ford Taurus
Receipt
Invoice
QP2F+R3F, King Abdullah Dt., Riyadh
12451, Saudi Arabia
5:17 PM
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

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'Ride details', 'expense_type': None, 'amount': 42.0, 'vat_amount': None, 'total_amount': 42.0, 'currency': 'SAR', 'date': '', 'confidence': 0.08, 'field_confidence': {'vendor': 0.22333581341105485, 'date': 0.0, 'currency': 0.31562241673304436, 'amount': 0.36813912242816094, 'vat_rate': 0.0, 'vat_amount': 0.0, 'discount': 0.0, 'service_charge': 0.0, 'tip': 0.0, 'cash_tendered': 0.0, 'card_amount': 0.0, 'change': 0.0, 'total_amount': 0.36813912242816094, 'invoice_number': 0.0, 'transaction_number': 0.0, 'expense_category': 0.0}, 'low_confidence_fields': ['vendor', 'date', 'amount', 'vat_rate', 'vat_amount', 'discount', 'service_charge', 'tip', 'cash_tendered', 'card_amount', 'change', 'total_amount', 'invoice_number', 'transaction_number', 'expense_category'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Ride details', 'confidence': 0.22333581341105485, 'evidence': 'Ride details', 'signals': ['top_of_receipt', 'position_prior_upper'], 'low': True, 'warning': 'ambiguous_candidates'}, 'date': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'currency': {'value': 'SAR', 'confidence': 0.31562241673304436, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['currency_code_match', 'same_line', 'position_prior_upper'], 'low': False}, 'amount': {'value': 42.0, 'confidence': 0.36813912242816094, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'vat_rate': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'discount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'service_charge': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'tip': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'cash_tendered': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'card_amount': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'change': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'total_amount': {'value': 42.0, 'confidence': 0.36813912242816094, 'evidence': 'SAR42.00 - Ford Taurus', 'signals': ['no_label_bare_number', 'currency_marker_adjacent', 'position_prior_lower', 'format_decimal_money', 'arithmetic_reconciled_exclusive'], 'low': True, 'warning': 'ambiguous_candidates'}, 'invoice_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'transaction_number': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}, 'expense_category': {'value': None, 'confidence': 0.0, 'evidence': '', 'signals': [], 'low': True, 'warning': 'no_evidence'}}}`

**Low-confidence words (<0.5):** TLAAN (0.32)

**Raw text:**

```
18:06
R il 46 sil  27%
Ride details
Riyadh
الرباض
TLAAN
UberX Saver ride with
Faisal
Oct 125:04PM
SAR42.00 - Ford Taurus
B
Receipt
=
Invoice
QP2F+R3F, King Abdullah Dt., Riyadh
12451, Saudi Arabia
5:17 PM
8496 AI Nahda Road Riyadh 12833
6:51 PM
No tip added
Add tip
No rating
Rate
Help & safety
Find lost item
We can help you get in touch with your
```
