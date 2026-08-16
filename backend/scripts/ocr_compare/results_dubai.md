# PaddleOCR results — dubai

Engine: PaddleOCR only (`lang=en` then `lang=ar`).
Summary reflects the merged (production) result — see `ocr_service.merge_bilingual`:
each language pass is parsed separately and merged field-by-field, matching what
`ocr_service._paddle_ocr` actually does for real uploads. The per-image sections below
still show each language pass on its own for debugging, plus the merged result.
Images: `6`.

## Summary

| Image | Vendor (merged) | Amount (merged) | VAT (merged) | Total (merged) | Date (merged) | Currency (merged) |
|---|---|---|---|---|---|---|
| image (1).png | HYPERMARKET LLC |  |  |  | 03-Aug-2026 | SAR |
| image (2).png | TRADING L.L.C | 20.0 | 20.0 | 21.0 |  | AED |
| image (3).png | SUPERMARKETL.L.C | 46.84 | 2.24 | 49.18 |  |  |
| image (4).png | SUPERMARKETLL.C | 45.21 | 2.28 | 47.49 | 05-Aug-202 |  |
| image (5).png | QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.U | 45.0 | 2.25 | 47.25 |  |  |
| image (6).png | Pasons S/M&Dept.Store | 49.52 | 2.48 | 52.0 | 04/08/2026 |  |

## image (1).png

### Merged (production)

**Parsed fields:** `{'vendor': 'HYPERMARKET LLC', 'expense_type': 'Food', 'amount': None, 'vat_amount': None, 'total_amount': None, 'currency': 'SAR', 'date': '03-Aug-2026', 'confidence': 0.36, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.45, 'date': 0.87, 'amount': 0.0, 'vat_amount': 0.0, 'total_amount': 0.0}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'HYPERMARKET LLC', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'date': {'value': '03-Aug-2026', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'HYPERMARKET LLC', 'expense_type': 'Food', 'amount': None, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '03-Aug-2026', 'confidence': 0.36, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.45, 'amount': 0.0, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.87}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'HYPERMARKET LLC', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': '03-Aug-2026', 'confidence': 0.87, 'low': False, 'tier': 'label'}}}`

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
Tax Lcanee Namber : 18051005
FIS Haw: P058
 0: 412
180000
ate
:03-Aug-2026 17:40
Bi11 No :236191
OS Name: POS8
User ID : ARSHINA
1.No DescrIption
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
14 1.25
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

**Parsed fields:** `{'vendor': 'HYPERMARKET LLC', 'expense_type': 'Food', 'amount': None, 'vat_amount': None, 'total_amount': None, 'currency': 'SAR', 'date': '', 'confidence': 0.22, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.45, 'amount': 0.0, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'HYPERMARKET LLC', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** n1 (0.40), 1 (0.50)

**Raw text:**

```
5075
.4-665
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
1
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

**Parsed fields:** `{'vendor': 'TRADING L.L.C', 'expense_type': 'Other', 'amount': 20.0, 'vat_amount': 20.0, 'total_amount': 21.0, 'currency': 'AED', 'date': '', 'confidence': 0.29, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.28, 'date': 0.0, 'amount': 0.2, 'vat_amount': 0.2, 'total_amount': 0.2}, 'low_confidence_fields': ['expense_type', 'date', 'amount', 'vat_amount', 'total_amount'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'TRADING L.L.C', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'amount': {'value': 20.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}, 'vat_amount': {'value': 20.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}, 'total_amount': {'value': 21.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'TRADING L.L.C', 'expense_type': 'Other', 'amount': 20.0, 'vat_amount': 20.0, 'total_amount': 21.0, 'currency': 'AED', 'date': '', 'confidence': 0.29, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.28, 'amount': 0.2, 'vat_amount': 0.2, 'total_amount': 0.2, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'amount', 'vat_amount', 'total_amount', 'date'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'TRADING L.L.C', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'amount': {'value': 20.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}, 'vat_amount': {'value': 20.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}, 'total_amount': {'value': 21.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

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
Mr.ms Blue Rbybe
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

**Parsed fields:** `{'vendor': 'سجازف 90اد / TUFFCO BUILDING MATERIALS TRADING L.L.G', 'expense_type': 'Other', 'amount': 20.0, 'vat_amount': 20.0, 'total_amount': 21.0, 'currency': 'AED', 'date': '', 'confidence': 0.22, 'field_confidence': {'vendor': 0.45, 'expense_type': 0.28, 'amount': 0.2, 'vat_amount': 0.2, 'total_amount': 0.2, 'date': 0.0}, 'low_confidence_fields': ['vendor', 'expense_type', 'amount', 'vat_amount', 'total_amount', 'date'], 'reconciliation_mismatch': True, 'fields': {'vendor': {'value': 'سجازف 90اد / TUFFCO BUILDING MATERIALS TRADING L.L.G', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'expense_type': {'value': 'Other', 'confidence': 0.28, 'low': True, 'tier': 'bare'}, 'amount': {'value': 20.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}, 'vat_amount': {'value': 20.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}, 'total_amount': {'value': 21.0, 'confidence': 0.2, 'low': True, 'tier': 'mismatch'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** | (0.18)

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

**Parsed fields:** `{'vendor': 'SUPERMARKETL.L.C', 'expense_type': 'Food', 'amount': 46.84, 'vat_amount': 2.24, 'total_amount': 49.18, 'currency': None, 'date': '', 'confidence': 0.66, 'field_confidence': {'vendor': 0.86, 'expense_type': 0.45, 'date': 0.0, 'amount': 0.84, 'vat_amount': 0.89, 'total_amount': 0.89}, 'low_confidence_fields': ['expense_type', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'SUPERMARKETL.L.C', 'confidence': 0.86, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'amount': {'value': 46.84, 'confidence': 0.84, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.24, 'confidence': 0.89, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 49.18, 'confidence': 0.89, 'low': False, 'tier': 'table'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'SUPERMARKETL.L.C', 'expense_type': 'Food', 'amount': 46.84, 'vat_amount': 2.24, 'total_amount': 49.18, 'currency': None, 'date': '', 'confidence': 0.66, 'field_confidence': {'vendor': 0.86, 'expense_type': 0.45, 'amount': 0.84, 'vat_amount': 0.89, 'total_amount': 0.89, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'SUPERMARKETL.L.C', 'confidence': 0.86, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': 46.84, 'confidence': 0.84, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.24, 'confidence': 0.89, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 49.18, 'confidence': 0.89, 'low': False, 'tier': 'table'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

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
PO57
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

**Parsed fields:** `{'vendor': 'GUPERMARKETL.L.C', 'expense_type': 'Food', 'amount': 49.25, 'vat_amount': None, 'total_amount': None, 'currency': None, 'date': '', 'confidence': 0.36, 'field_confidence': {'vendor': 0.84, 'expense_type': 0.45, 'amount': 0.87, 'vat_amount': 0.0, 'total_amount': 0.0, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'vat_amount', 'total_amount', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'GUPERMARKETL.L.C', 'confidence': 0.84, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': 49.25, 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'vat_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'total_amount': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
OAMAR AL MADINA
GUPERMARKETL.L.C
Nrw Hy  A 
( 0585405699
TaX InVdICE
RN: 104645729500013
snle :29 4l-2026 69.4t
31٦1 N0:104
PU'S Neve: PHa
Uter 10: 99
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
VETX
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

**Parsed fields:** `{'vendor': 'SUPERMARKETLL.C', 'expense_type': 'Food', 'amount': 45.21, 'vat_amount': 2.28, 'total_amount': 47.49, 'currency': None, 'date': '05-Aug-202', 'confidence': 0.81, 'field_confidence': {'vendor': 0.86, 'expense_type': 0.45, 'date': 0.82, 'amount': 0.9, 'vat_amount': 0.9, 'total_amount': 0.9}, 'low_confidence_fields': ['expense_type'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'SUPERMARKETLL.C', 'confidence': 0.86, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'date': {'value': '05-Aug-202', 'confidence': 0.82, 'low': False, 'tier': 'label'}, 'amount': {'value': 45.21, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.28, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 47.49, 'confidence': 0.9, 'low': False, 'tier': 'table'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'SUPERMARKETLL.', 'expense_type': 'Food', 'amount': 45.21, 'vat_amount': 2.28, 'total_amount': 47.49, 'currency': None, 'date': '05-Aug-202', 'confidence': 0.8, 'field_confidence': {'vendor': 0.82, 'expense_type': 0.45, 'amount': 0.9, 'vat_amount': 0.9, 'total_amount': 0.9, 'date': 0.82}, 'low_confidence_fields': ['expense_type'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'SUPERMARKETLL.', 'confidence': 0.82, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': 45.21, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.28, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 47.49, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'date': {'value': '05-Aug-202', 'confidence': 0.82, 'low': False, 'tier': 'label'}}}`

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
UAQ-5000-BLUE RINE
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

**Parsed fields:** `{'vendor': 'SUPERMARKETLL.C', 'expense_type': 'Food', 'amount': 45.21, 'vat_amount': 2.28, 'total_amount': 47.49, 'currency': None, 'date': '', 'confidence': 0.66, 'field_confidence': {'vendor': 0.86, 'expense_type': 0.45, 'amount': 0.86, 'vat_amount': 0.89, 'total_amount': 0.89, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'SUPERMARKETLL.C', 'confidence': 0.86, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': 45.21, 'confidence': 0.86, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.28, 'confidence': 0.89, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 47.49, 'confidence': 0.89, 'low': False, 'tier': 'table'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** (none)

**Raw text:**

```
M.S
OAMAR AL MADINA
SUPERMARKETLL.C
New Hannyya Uguo Al Qurwin-UAE
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
9398948000000
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
9695000000
COREANDER IEAI
1.00
0.99)
6291044111:19
SAFA VOGKURT TUKG
1.0)
38.00
UA0-500D- BLUE RINE
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
*EEr D T1 "Or NLsaNge
Thenk you for grustny ao2 pis core Rga1
No Leun -ctod
```

## image (5).png

### Merged (production)

**Parsed fields:** `{'vendor': 'QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.U', 'expense_type': 'Food', 'amount': 45.0, 'vat_amount': 2.25, 'total_amount': 47.25, 'currency': None, 'date': '', 'confidence': 0.67, 'field_confidence': {'vendor': 0.86, 'expense_type': 0.45, 'date': 0.0, 'amount': 0.9, 'vat_amount': 0.9, 'total_amount': 0.9}, 'low_confidence_fields': ['expense_type', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.U', 'confidence': 0.86, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}, 'amount': {'value': 45.0, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.25, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 47.25, 'confidence': 0.9, 'low': False, 'tier': 'table'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.U', 'expense_type': 'Food', 'amount': 45.0, 'vat_amount': 2.25, 'total_amount': 47.25, 'currency': None, 'date': '', 'confidence': 0.67, 'field_confidence': {'vendor': 0.86, 'expense_type': 0.45, 'amount': 0.9, 'vat_amount': 0.9, 'total_amount': 0.9, 'date': 0.0}, 'low_confidence_fields': ['expense_type', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'QAMAR ALHUDA ALJADEED GENERAL TRADING L.L.U', 'confidence': 0.86, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': 45.0, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.25, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 47.25, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** 1 (0.14), dangi (0.44), d l   (0.49), Apa (0.41), Aa uat  (0.40), d uil da g (0.48), das uchll o ilas (0.47)

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
ment Pork 1, Tel.: + 971 4 884 8200, +971 4 889 5541
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
Aa uat 
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
UAE Dirhams Forty Seven and Twenty Five fiis Only
d uil da g
TOTAL VAT
das uchll o ilas
225
TOTAL INCL VAT
```

### PaddleOCR (lang=ar)

**Parsed fields:** `{'vendor': 'حارة العامةذمم / QAMAR ALHUDA ALJADEED GENERAL TRADING LL.L', 'expense_type': 'IT Equipment', 'amount': 45.0, 'vat_amount': 2.25, 'total_amount': 47.25, 'currency': None, 'date': '', 'confidence': 0.59, 'field_confidence': {'vendor': 0.45, 'expense_type': 0.45, 'amount': 0.9, 'vat_amount': 0.85, 'total_amount': 0.89, 'date': 0.0}, 'low_confidence_fields': ['vendor', 'expense_type', 'date'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'حارة العامةذمم / QAMAR ALHUDA ALJADEED GENERAL TRADING LL.L', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'expense_type': {'value': 'IT Equipment', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': 45.0, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.25, 'confidence': 0.85, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 47.25, 'confidence': 0.89, 'low': False, 'tier': 'table'}, 'date': {'value': None, 'confidence': 0.0, 'low': True, 'tier': 'missing'}}}`

**Low-confidence words (<0.5):** nد (0.48)

**Raw text:**

```
amar Alhuda
حارة العامةذمم
QAMAR ALHUDA ALJADEED GENERAL TRADING LL.L
nد
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
AIW
TOTAL EXCL VAT
مبلغ دون الضرية
UAE Dirhams Forty Seven and Twenty Five fis Only
مجموعة الضريية
TOTAL VAT
TOTAL INCL VAT
مبلغمع الضريية
```

## image (6).png

### Merged (production)

**Parsed fields:** `{'vendor': 'Pasons S/M&Dept.Store', 'expense_type': 'Food', 'amount': 49.52, 'vat_amount': 2.48, 'total_amount': 52.0, 'currency': None, 'date': '04/08/2026', 'confidence': 0.81, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.45, 'date': 0.87, 'amount': 0.9, 'vat_amount': 0.9, 'total_amount': 0.9}, 'low_confidence_fields': ['expense_type'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Pasons S/M&Dept.Store', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'date': {'value': '04/08/2026', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'amount': {'value': 49.52, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.48, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 52.0, 'confidence': 0.9, 'low': False, 'tier': 'table'}}}`

### PaddleOCR (lang=en)

**Parsed fields:** `{'vendor': 'Pasons S/M&Dept.Store', 'expense_type': 'Food', 'amount': 49.52, 'vat_amount': 2.48, 'total_amount': 52.0, 'currency': None, 'date': '04/08/2026', 'confidence': 0.82, 'field_confidence': {'vendor': 0.87, 'expense_type': 0.45, 'amount': 0.9, 'vat_amount': 0.9, 'total_amount': 0.9, 'date': 0.87}, 'low_confidence_fields': ['expense_type'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'Pasons S/M&Dept.Store', 'confidence': 0.87, 'low': False, 'tier': 'label'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': 49.52, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 2.48, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 52.0, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'date': {'value': '04/08/2026', 'confidence': 0.87, 'low': False, 'tier': 'label'}}}`

**Low-confidence words (<0.5):** 99 (0.32), GLE (0.48), y  & j g (0.40), AEN (0.44), 2 (0.31), 2s2 (0.31)

**Raw text:**

```
BlueRhn
BlueRhi
99
65t8
PASONS
305
PASONS
Pasons S/M&Dept.Store
Dubai Investment Park-2, Dubai, U AE
GLE
Tel: 04-8640966 . Mob:0557692020
Pasons S/M&Depl Store
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
7
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
Keep Receipt For Exchange, T&C Apply
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

**Parsed fields:** `{'vendor': 'T5ن', 'expense_type': 'Food', 'amount': 83.37, 'vat_amount': 4.17, 'total_amount': 87.54, 'currency': None, 'date': '04/08/2026', 'confidence': 0.73, 'field_confidence': {'vendor': 0.39, 'expense_type': 0.45, 'amount': 0.9, 'vat_amount': 0.89, 'total_amount': 0.9, 'date': 0.87}, 'low_confidence_fields': ['vendor', 'expense_type'], 'reconciliation_mismatch': False, 'fields': {'vendor': {'value': 'T5ن', 'confidence': 0.39, 'low': True, 'tier': 'heuristic'}, 'expense_type': {'value': 'Food', 'confidence': 0.45, 'low': True, 'tier': 'heuristic'}, 'amount': {'value': 83.37, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'vat_amount': {'value': 4.17, 'confidence': 0.89, 'low': False, 'tier': 'table'}, 'total_amount': {'value': 87.54, 'confidence': 0.9, 'low': False, 'tier': 'table'}, 'date': {'value': '04/08/2026', 'confidence': 0.87, 'low': False, 'tier': 'label'}}}`

**Low-confidence words (<0.5):** T5ن (0.34), CHV (0.41), لسع (0.50), لح (0.43), g (0.41), BO (0.49)

**Raw text:**

```
Shte Rhrnis
B(ueRhonm
6sts
SNOSAd
T5ن
PASONS
CHV
Dubai Investment Park-2, Dubai , U AE
Pasons S/M&Depl Slore
SLENC
Tet(4-0640966Mob:0557692020
PasonsS/M&Depl Slore
www.pesonsme.com
Dubal Imvnsmeat Park-2 OubaiU AE
TRN 100453349100003
Tel 04-8840966Mob 0557692020
Tax Invoice
نتورة ضرية
'anew pasansime.com
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
الخوة
لح
الجحع
2 9901125020304
1
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
