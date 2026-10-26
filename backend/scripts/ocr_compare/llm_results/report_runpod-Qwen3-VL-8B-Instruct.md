# Vision LLM vs current pipeline — `runpod-Qwen3-VL-8B-Instruct`

Generated 2026-10-23 by `llm_vision_compare.py`. Ground truth: `scripts/ocr_results.csv`.

## Accuracy on bills with ground truth

| Field | Current pipeline | runpod-Qwen3-VL-8B-Instruct |
|---|---|---|
| vendor | 2/6 | 6/6 |
| amount | 4/7 | 7/7 |
| vat_amount | 7/7 | 7/7 |
| total_amount | 4/7 | 7/7 |
| currency | 7/7 | 5/7 |
| date | 3/5 | 5/5 |

## Per bill (single-value fields)

| Bill | Engine | Vendor | Amount | VAT | Total | Cur | Date | Bill no |
|---|---|---|---|---|---|---|---|---|
| ksa/ksa1.png | current | ✅ شركة الشارقة | ❌ 51 | ✅ 0 | ❌ 51 | ✅ SAR | – |  |
| ksa/ksa1.png | runpod-Qwen3-VL-8B-Instruct | ✅ SHARJA | ✅ 45 | ✅ 0 | ✅ 45 | ❌ AED | – 2026-07-05 | 90375 |
| ksa/ksa2.png | current | ❌ شركة قمة الخليج المحدودة للأجرة العامة | ✅ 45 | ✅ 0 | ✅ 45 | ✅ SAR | ❌ | 0386 |
| ksa/ksa2.png | runpod-Qwen3-VL-8B-Instruct | ✅ Qema Al-Khaleej Limited Co. | ✅ 45 | ✅ 0 | ✅ 45 | ✅ SAR | ✅ 2026-06-25 | 0386 |
| ksa/ksa3.png | current | ❌ شركة شهد طويق رقم السيارة | ❌ 0.01 | ✅ 0 | ❌ 0.01 | ✅ SAR | ✅ 29-6-26 |  |
| ksa/ksa3.png | runpod-Qwen3-VL-8B-Instruct | ✅ Shahad Tawik Company | ✅ 40 | ✅ 0 | ✅ 40 | ❌ AED | ✅ 2026-06-29 | KA+D 208 |
| ksa/ksa4.png | current | – المطلوب من المكرم | ✅ 55 | ✅ 0 | ✅ 55 | ✅ SAR | ❌ | C/58444 |
| ksa/ksa4.png | runpod-Qwen3-VL-8B-Instruct | – Kingdom Centre | ✅ 55 | ✅ 0 | ✅ 55 | ✅ SAR | ✅ 2026-06-30 | C/58444 |
| ksa/ksa5.png | current | ✅ TAXI AL-AJME | ❌ 1 | ✅ 0 | ❌ 1 | ✅ SAR | – | 20367 |
| ksa/ksa5.png | runpod-Qwen3-VL-8B-Instruct | ✅ TAXI AL-AJME | ✅ 50 | ✅ 0 | ✅ 50 | ✅ SAR | – 2026-07-05 | 20367 |
| ksa/ksa8.png | current | ❌ Al Jubaytas | ✅ 72.9 | ✅ 0 | ✅ 72.9 | ✅ SAR | ✅ Feb 8 |  |
| ksa/ksa8.png | runpod-Qwen3-VL-8B-Instruct | ✅ Uber | ✅ 72.9 | ✅ 0 | ✅ 72.9 | ✅ SAR | ✅ 2026-02-08 |  |
| ksa/ksa9.png | current | ❌ Riyadh | ✅ 42 | ✅ 0 | ✅ 42 | ✅ SAR | ✅ Oct 12 |  |
| ksa/ksa9.png | runpod-Qwen3-VL-8B-Instruct | ✅ Uber | ✅ 42 | ✅ 0 | ✅ 42 | ✅ SAR | ✅ 2026-10-12 |  |
| multi_line/image.png | current | Fabricast FZC / License No.: 03281 | 86 | 4.3 | 90.3 | AED | 9-Jul-2026 | T-INV/26/1854 |
| multi_line/image.png | runpod-Qwen3-VL-8B-Instruct | Fabricast FZC | 86 | 4.3 | 90.3 | AED | 2026-07-09 | T-INV/26/1854 |
| multi_line/img2.jpeg | current | Standard Hardware Trading LLC |  | 252 | 77 | AED | 29-Jul-26 | CASH/SHT/1205 |
| multi_line/img2.jpeg | runpod-Qwen3-VL-8B-Instruct | Standard Hardware Trading LLC | 769.23 | 36.63 | 845.83 | AED | 2026-07-29 | CASH/SHT/1205 |
| multi_line/img23.png | current | Emirate : Dubai | 4704.2 | 235.21 | 4939.41 | AED | 18-Sep-26 | RB 26/01008 |
| multi_line/img23.png | runpod-Qwen3-VL-8B-Instruct | Rainbow Led & Display Advertising | 4704.2 | 235.21 | 4939.41 | AED | 2026-09-18 | RB 26/01008 |
| multi_line/img3.jpeg | current | BAB AL HAYAT PHARMACY LLC | 224.99 | 0 | 224.99 | AED | 06/07/2026 | 50A79618 |
| multi_line/img3.jpeg | runpod-Qwen3-VL-8B-Instruct | BAB AL HAYAT PHARMACY LLC | 224.99 | 0 | 224.99 | AED | 2026-07-06 | 50A79618 |
| multi_line/mage.png | current | BAB AL HAYAT PHARMACY LLC | 438.91 | 0 | 438.91 | AED | 11/09/2026 | 50A86803 |
| multi_line/mage.png | runpod-Qwen3-VL-8B-Instruct | BAB AL HAYAT PHARMACY LLC | 438.91 | 1.09 | 440 | AED | 2026-11-09 | 50A86803 |
| new_bills/bill_1.png | current | Jannat Al Naeem Building Materials Trading LLC Delivery Note No. Dated |  |  |  | AED | 21-Jul-26 | 18812 |
| new_bills/bill_1.png | runpod-Qwen3-VL-8B-Instruct | Jannat Al Naem Building Materials Trading LLC | 5516 | 275.8 | 5516 | AED | 2026-07-21 | 18812 |
| new_bills/bill_2.png | current | Jannat AI Naeem Building Materials Trading LLC |  |  |  | AED | 24-Sep-26 | 19065 |
| new_bills/bill_2.png | runpod-Qwen3-VL-8B-Instruct | Jannat Al Naeem Building Materials Trading LLC | 1150 | 50 | 1150 | AED | 2026-09-24 | 19065 |
| new_bills/bill_3.png | current | Jannat Al Naeem Building Materials Trading LLC | 7416.36 | 370.83 | 7787.19 | AED | 21-Jul-26 | 19578 |
| new_bills/bill_3.png | runpod-Qwen3-VL-8B-Instruct | Jannat Al Naem Building Materials Trading LLC | 7416.36 | 370.83 | 7416.36 | AED | 2026-07-21 | 19578 |

## Line items (multi-item flow)

| Bill | Real items | Current | LLM | LLM Σ lines | LLM total | Σ matches |
|---|---|---|---|---|---|---|
| ksa/ksa4.png | ? | 0 | 1 | 55 | 55 | ✅ |
| multi_line/image.png | 2 | 0 | 2 | 90.3 | 90.3 | ✅ |
| multi_line/img2.jpeg | 3 | 0 | 3 | 769.23 | 845.83 | ❌ |
| multi_line/img23.png | 7 | 7 | 7 | 4939.41 | 4939.41 | ✅ |
| multi_line/img3.jpeg | 12 | 9 | 12 | 224.99 | 224.99 | ✅ |
| multi_line/mage.png | 13 | 12 | 13 | 440 | 440 | ✅ |
| new_bills/bill_1.png | 11 | 19 | 1 | 5516 | 5516 | ✅ |
| new_bills/bill_2.png | ? | 5 | 5 | 1428 | 1150 | ❌ |
| new_bills/bill_3.png | 11 | 20 | 11 | 7416.36 | 7416.36 | ✅ |

Σ matches checks the app's assumption in `_replace_line_items`: line amounts are VAT-inclusive and sum to the bill total (pre-VAT rows are converted in `_make_lines_vat_inclusive`).

## Backend / Flutter contract check

All LLM results map cleanly onto `OcrService.run()` → `_receipt_payload` → `OcrResult.fromJson`.

## Usage

- Bills sent: 15 · prompt tokens 19,737 · completion tokens 7,350 (avg 1,315 / 490 per bill)
- Latency: avg 33.1s, max 147.9s
