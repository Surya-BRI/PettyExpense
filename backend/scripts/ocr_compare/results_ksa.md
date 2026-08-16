# PaddleOCR results — ksa

Engine: PaddleOCR only (`lang=en` then `lang=ar`).
Summary reflects the merged (production) result — see `ocr_service.merge_bilingual`:
each language pass is parsed separately and merged field-by-field, matching what
`ocr_service._paddle_ocr` actually does for real uploads. The per-image sections below
still show each language pass on its own for debugging, plus the merged result.
Images: `3`.

## Summary

| Image | Vendor (merged) | Amount (merged) | VAT (merged) | Total (merged) | Date (merged) | Currency (merged) |
|---|---|---|---|---|---|---|
| ksa1.png | SHARJA | 1.0 |  |  |  |  |
| ksa2.png | شركة | 45.0 |  |  | 25/06/26 |  |
| ksa3.png | شركة | 2.0 |  |  | 29-6-26 |  |

## ksa1.png

### Merged (production)

**Parsed fields:** `{'vendor': 'SHARJA', 'expense_type': 'Other', 'amount': 1.0, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '', 'confidence': 0.22, 'field_confidence': {'vendor': 0.72, 'expense_type': 0.28, 'date': 0.0, 'amount': 0.3, 'vat_amount': 0.0, 'total_amount': 0.0}, 'low_confidence_fields': ['expense_type', 'date', 'amount', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'SHARJA', 'confidence': 0.72, 'low': False, 'tier': 'heuristic'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'amount': {'value': 1.0, 'confidence': 0.3, 'low': True, 'tier': 'guess'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'SHARJA', 'expense_type': 'Other', 'amount': 1.0, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '', 'confidence': 0.22, 'field_confidence': {'vendor': 0.72, 'expense_type': 0.28, 'amount': 0.3, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'SHARJA', 'confidence': 0.72, 'low': False, 'tier': 'heuristic'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'amount': {'value': 1.0, 'confidence': 0.3, 'low': True, 'tier': 'guess'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** J (0.48), 1 (0.49)

**Raw text:**

```
SHARJA
0583162117:J9
ö
ljajgila
90375
Customer Invoise
Date 22 /06/26.
1/
Customer Name:
Fare 
Place 
J
Notes
alLs
1
451
KAD208
to Dalas
Total
. 
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'الشركة غي مسؤولةعن عدم تواجدرقم الوحة بالفاتورة', 'expense_type': 'Other', 'amount': None, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '', 'confidence': 0.17, 'field_confidence': {'vendor': 0.72, 'expense_type': 0.28, 'amount': 0.0, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'الشركة غي مسؤولةعن عدم تواجدرقم الوحة بالفاتورة', 'confidence': 0.72, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** ا (0.49), ا  (0.50), AIAS (0.34), ا ة (0.42), KA2od (0.42)

**Raw text:**

```
ا
ا 
ي    
AIAS
ا ة
6١:LI1Z91£890
فاتورة راكب
90375
Customer Invoise
Date 2i /
166/26
الموافق
التاريخ
المحترم
اسم الراكب
Customer Name:
الشركة غي مسؤولةعن عدم تواجدرقم الوحة بالفاتورة
رقم اللوحة،
ملاحظات
Fare
Place
المكان
ال
Notes
ريال
هللة
إلى
من
KA2od
..o...
NDalas
Total
الإجمالي
السائق
توقيع
اسم الئقرقم ال
السيارة
أمتعتكم
استلام
التأكد
عزيزي الراكب نرجو
جميع
من
تمنياتنا
مع أجمل
الوصول
سلامة
لكم
السيارة
شكراً
كوب
بر
لتفضلكم
```

## ksa2.png

### Merged (production)

**Parsed fields:** `{'vendor': 'شركة', 'expense_type': 'Other', 'amount': 45.0, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '25/06/26', 'confidence': 0.38, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.28, 'date': 0.81, 'amount': 0.3, 'vat_amount': 0.0, 'total_amount': 0.0}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'شركة', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'date': {'value': '25/06/26', 'confidence': 0.81, 'low': False, 'tier': 'label'}, 'amount': {'value': 45.0, 'confidence': 0.3, 'low': True, 'tier': 'guess'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'Qema Al-Khaleej Limited Co. For General Rent', 'expense_type': 'Other', 'amount': None, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '25/06/26', 'confidence': 0.3, 'field_confidence': {'vendor': 0.72, 'expense_type': 0.28, 'amount': 0.0, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.81}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Qema Al-Khaleej Limited Co. For General Rent', 'confidence': 0.72, 'low': False, 'tier': 'heuristic'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': '25/06/26', 'confidence': 0.81, 'low': False, 'tier': 'label'}}}`

**Low-confidence words (<0.5):** o alas (0.45)

**Raw text:**

```
Qema Al-Khaleej Limited Co. For General Rent
0386
Invoice 25/06/26
!
Kingdomb fores
o alas
45
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'شركة', 'expense_type': 'Other', 'amount': 45.0, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '', 'confidence': 0.24, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.28, 'amount': 0.3, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'شركة', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'amount': {'value': 45.0, 'confidence': 0.3, 'low': True, 'tier': 'guess'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
العامة
للأجرة
المحدودة
قمة
شركة
الخليج
Qema Al-Khaleej
Limited Co. For General Rent
فاتورة
0386
Invoice
التاريخ 5٥6
السعر
إلى
من
ريال
Kingdom
mDalss
45/.
فقط
المجموع
```

## ksa3.png

### Merged (production)

**Parsed fields:** `{'vendor': 'شركة', 'expense_type': 'Other', 'amount': 2.0, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '29-6-26', 'confidence': 0.46, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.28, 'date': 0.87, 'amount': 0.75, 'vat_amount': 0.0, 'total_amount': 0.0}, 'low_confidence_fields': ['expense_type', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'شركة', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'date': {'value': '29-6-26', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'amount': {'value': 2.0, 'confidence': 0.75, 'low': False, 'tier': 'label'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'Shahad Tawik Company', 'expense_type': 'Other', 'amount': 2.0, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '29-6-26', 'confidence': 0.44, 'field_confidence': {'vendor': 0.72, 'expense_type': 0.28, 'amount': 0.75, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.87}, 'low_confidence_fields': ['expense_type', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Shahad Tawik Company', 'confidence': 0.72, 'low': False, 'tier': 'heuristic'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'amount': {'value': 2.0, 'confidence': 0.75, 'low': False, 'tier': 'label'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': '29-6-26', 'confidence': 0.87, 'low': False, 'tier': 'label'}}}`

**Low-confidence words (<0.5):** ら310L0 (0.45)

**Raw text:**

```
Shahad Tawik Company
Car Number (22)
()
Amount
2
Date
Time
409
KAFD 208
29-6-26
to maliz
6
ら310L0
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'شركة', 'expense_type': 'Other', 'amount': 29.0, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '29-6-26', 'confidence': 0.38, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.28, 'amount': 0.3, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.84}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'شركة', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'amount': {'value': 29.0, 'confidence': 0.3, 'low': True, 'tier': 'guess'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': '29-6-26', 'confidence': 0.84, 'low': False, 'tier': 'label'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
Shahad Tawik Company
شهد
شركة
طويق
Car Number (22)
رقم السيارة
Amount
المبلغ
Dat التاريخ
Timeالوقت
40f
KAFD20P
29-6-26
Malez
To
السيارة
عن أي 
مسئولة
داخل
يتركها
شخصية
متعلقات
غير
الشركة
الراكب
لخدمتكم
الفرصة
لإتاحة
ونشكركم
مغادرتها
بعد
٥٦٠٩٩٠٥١٤٠٥٠٠٠٠٦٦٢١
حلاستفسار
```
