# RunPod PaddleOCR Accuracy Notes

Source data: [ocr_results.csv](ocr_results.csv). Images from `assets/dubai/` and `assets/ksa/`.
Engine: `pp-ocrv5-arabic` via `onnxruntime` (RunPod GPU endpoint).
Fields tracked match what the Flutter app actually uses (`confirm_claim_screen.dart` / `OcrResult`): vendor, amount (excl VAT), vat_amount, total_amount, currency, date.

## Dubai batch — per-image results

| Image | Vendor | Amount (excl VAT) | VAT Amt | Total | Currency | Date |
|---|---|---|---|---|---|---|
| image (6).png | ✅ PASONS | ❌ not extracted | ❌ not extracted | ❌ got 4.00, actual 87.54 | ✅ AED | ✅ 05/08/2026 |
| image (1).png | ❌ "BlueR" (handwriting) vs FIDA ALMADINA | n/a (not on receipt) | n/a (not on receipt) | ❌ not extracted, actual 29.00 | ❌ not extracted | ❌ not extracted |
| image (2).png | ❌ garbled Arabic vs TUFFCO | ❌ not extracted, actual 20.00 | ❌ not extracted, actual 1.00 | ❌ not extracted, actual 21.00 | ✅ AED | ❌ not extracted |
| image (3).png | ❌ "ww.S" vs QAMAR AL MADINA | ❌ not extracted, actual 46.84 | ❌ not extracted, actual 2.34 | ❌ not extracted, actual 49.18 | ❌ not extracted | ❌ not extracted |
| image (4).png | ❌ "M.S" vs QAMAR AL MADINA | ❌ not extracted, actual 45.21 | ❌ not extracted, actual 2.28 | ❌ not extracted, actual 47.49 | ❌ not extracted | ❌ not extracted |
| image (5).png | ⚠️ "amar Alhuda" (partial) vs QAMAR ALHUDA ALJADEED | ❌ not extracted, actual 45.00 | ❌ not extracted, actual 2.25 | ❌ not extracted, actual 47.25 | ❌ not extracted | n/a (illegible on original) |
| enoc_test.jpg | ❌ garbled Arabic vs ENOC RETAIL LLC | ❌ not extracted, actual ~5.71 | ❌ not extracted, actual 0.29 | ❌ not extracted, actual 6.00 | ✅ AED | ❌ not extracted, actual 8/18/2026 |

Dubai field accuracy (extracted correctly / total applicable):
- Vendor: 1/7 correct, 1/7 partial (14–29%)
- Amount (excl VAT): 0/6 (not present on 1 receipt)
- VAT amount: 0/6
- Total amount: 0/7 (1 wrong value, rest blank)
- Currency: 3/7 (43%)
- Date: 1/6 (17%, excluding 1 illegible original)

## KSA batch — per-image results

Mostly handwritten taxi/general-fare receipts plus 2 Uber app screenshots — no VAT breakdown on any of these (taxi receipts don't itemize VAT separately).

| Image | Vendor | Amount | VAT Amt | Total | Currency | Date |
|---|---|---|---|---|---|---|
| ksa1.png | ❌ "الشارقة" (partial) vs SHARJA | ❌ not extracted, actual 45 | n/a | ❌ not extracted, actual 45 | ❌ not extracted | ❌ not extracted, actual 22/06/2026 |
| ksa2.png | ✅ Qema Al-Khaleej Ltd Co. | ❌ not extracted, actual n/a | n/a | ❌ not extracted, actual 45 | ❌ not extracted | ❌ not extracted, actual 25/06/2026 |
| ksa3.png | ✅ Shahad Tawik Company | ❌ not extracted, actual 40 | n/a | ❌ not extracted, actual 40 | ❌ not extracted | ❌ not extracted, actual 29/06/2026 |
| ksa4.png | ✅ (n/a on receipt, invoice-no only) | ❌ not extracted, actual 55 | n/a | ❌ not extracted, actual 55 | ❌ not extracted | ❌ not extracted, actual 30/06/2026 |
| ksa5.png | ✅ TAXI AL-AJME (close match) | ❌ not extracted, actual 50 | n/a | ❌ not extracted, actual 50 | ❌ not extracted | ❌ not extracted |
| ksa6.png | ✅ Shaml Al-Doha Company | ❌ not extracted, actual 35 | n/a | ❌ not extracted, actual 35 | ❌ not extracted | ❌ got 05/02/26, actual 05/07/2026 (OCR misread 7→2) |
| ksa7.png | ✅ Sultan Munir Al-Harthy & Partner Co. | ❌ not extracted, actual 45 | n/a | ❌ not extracted, actual 45 | ❌ not extracted | ❌ not extracted, actual 14/07/2026 |
| ksa8.png (Uber screenshot) | ❌ "08:06" (status bar clock) vs Uber | ❌ not extracted, actual 72.90 | n/a | ❌ not extracted, actual 72.90 | ❌ not extracted | ❌ not extracted, actual Feb 8 |
| ksa9.png (Uber screenshot) | ❌ "18:06a" (status bar clock) vs Uber | ❌ not extracted, actual 42.00 | n/a | ❌ not extracted, actual 42.00 | ❌ not extracted | ❌ not extracted, actual Oct 1 |

KSA field accuracy:
- Vendor: 6/9 correct or close match (67%)
- Amount: 0/9
- Total amount: 0/9
- Currency: 0/9 (SAR/currency label never surfaced in raw text or missed by regex)
- Date: 0/9 correct (1/9 extracted but wrong value)

## Key takeaway

Most of this is **not an OCR quality problem** — it's the test script's regex extraction being too naive. In several cases (image (3), (4), (5), enoc_test) the correct numbers are sitting right there in the raw OCR `text` field (e.g. enoc_test: `"TOTAL AED\nAEDO. 29"` — total and VAT are both present), but the regex fails because:
- Currency prefix glued to numbers (`AED6.00` instead of `6.00`)
- OCR misreads `0` as letter `O` in some fonts (`AEDO.29`)
- Field labels split across many separate OCR lines with no consistent spacing
- Multi-receipt images (image (6)) confuse "first/last number after label" heuristics

The KSA batch reinforces this: on the 2 Uber app screenshots (ksa8, ksa9), OCR read the digital UI text essentially perfectly (`UberX Saver`, `SAR72.90`, `Feb 8` all present verbatim), but vendor extraction still failed because the naive "first line = vendor" heuristic grabbed the phone's status-bar clock instead.

Where OCR itself genuinely struggles:
- **Vendor name recognition is the weakest OCR signal** on stylized/logo-heavy printed headers — badly garbled or only partially read (worst case: full Arabic gibberish instead of the vendor name). Note: on the KSA taxi receipts, which mostly use plain printed Arabic/English company names, vendor accuracy was actually good (6/9).
- **Handwritten fields are essentially unreadable** — amounts, dates, and vendor names written by hand come out as noise or are dropped entirely. This is the single biggest driver of missed Amount/Total/Date across both batches (nearly every KSA taxi receipt has these fields handwritten).
- Small, low-contrast serif fonts on faded thermal receipts add noise but printed totals/VAT lines are still usually present in the raw text.

## Suggested next step

The real backend parser (the one Flutter's `analyzeReceipt` hits) likely does smarter field extraction than this quick regex test script — worth confirming it isn't hitting the same class of bugs (e.g. currency-prefixed numbers, OCR'd `O`-for-`0`) before trusting these RunPod OCR results for production field extraction.
