# Vision LLM vs current pipeline — `runpod-Qwen3-VL-32B-Instruct-FP8`

Generated 2026-10-23 by `llm_vision_compare.py`. Ground truth: `scripts/ocr_results.csv`.

## Accuracy on bills with ground truth

| Field | Current pipeline | runpod-Qwen3-VL-32B-Instruct-FP8 |
|---|---|---|
| vendor | 0/0 | 0/0 |
| amount | 0/0 | 0/0 |
| vat_amount | 0/0 | 0/0 |
| total_amount | 0/0 | 0/0 |
| currency | 0/0 | 0/0 |
| date | 0/0 | 0/0 |

## Per bill (single-value fields)

| Bill | Engine | Vendor | Amount | VAT | Total | Cur | Date | Bill no |
|---|---|---|---|---|---|---|---|---|
| multi_line/img23.png | current |  |  |  |  |  |  |  |
| multi_line/img23.png | runpod-Qwen3-VL-32B-Instruct-FP8 | Rainbow Led & Display Advertising | 4704.2 | 235.21 | 4939.41 | AED | 2026-09-18 | RB 26/01008 |
| multi_line/img3.jpeg | current |  |  |  |  |  |  |  |
| multi_line/img3.jpeg | runpod-Qwen3-VL-32B-Instruct-FP8 | BAB AL HAYAT PHARMACY LLC | 224.99 | 0 | 224.99 | AED | 2026-07-06 | 50A79618 |
| multi_line/mage.png | current |  |  |  |  |  |  |  |
| multi_line/mage.png | runpod-Qwen3-VL-32B-Instruct-FP8 | BAB AL HAYAT PHARMACY LLC | 438.91 | 1.09 | 440 | AED | 2026-09-11 | 50A86803 |
| new_bills/bill_1.png | current |  |  |  |  |  |  |  |
| new_bills/bill_1.png | runpod-Qwen3-VL-32B-Instruct-FP8 | Jannat Al Naeem Building Materials Trading LLC |  |  |  | AED | 2026-07-21 | 18812 |
| new_bills/bill_2.png | current |  |  |  |  |  |  |  |
| new_bills/bill_2.png | runpod-Qwen3-VL-32B-Instruct-FP8 | error: AI scan timed out. Try again, or use the normal scan. |||||||
| new_bills/bill_3.png | current |  |  |  |  |  |  |  |

## Line items (multi-item flow)

| Bill | Real items | Current | LLM | LLM Σ lines | LLM total | Σ matches |
|---|---|---|---|---|---|---|
| multi_line/img23.png | 7 | 0 | 7 | 4939.41 | 4939.41 | ✅ |
| multi_line/img3.jpeg | 12 | 0 | 11 | 205.86 | 224.99 | ❌ |
| multi_line/mage.png | 13 | 0 | 13 | 440.92 | 440 | ❌ |
| new_bills/bill_1.png | 11 | 0 | 11 | 0 |  | no prices (delivery note?) |

Σ matches checks the app's assumption in `_replace_line_items`: line amounts are VAT-inclusive and sum to the bill total (pre-VAT rows are converted in `_make_lines_vat_inclusive`).

## Backend / Flutter contract check

- **new_bills/bill_1.png**: line 1: amount missing/negative (LineItemIn.amount is required); line 2: amount missing/negative (LineItemIn.amount is required); line 3: amount missing/negative (LineItemIn.amount is required); line 4: amount missing/negative (LineItemIn.amount is required); line 5: amount missing/negative (LineItemIn.amount is required); line 6: amount missing/negative (LineItemIn.amount is required); line 7: amount missing/negative (LineItemIn.amount is required); line 8: amount missing/negative (LineItemIn.amount is required); line 9: amount missing/negative (LineItemIn.amount is required); line 10: amount missing/negative (LineItemIn.amount is required); line 11: amount missing/negative (LineItemIn.amount is required)

## Usage

- Bills sent: 4 · prompt tokens 5,620 · completion tokens 3,492 (avg 1,405 / 873 per bill)
- Latency: avg 107.9s, max 282.1s
