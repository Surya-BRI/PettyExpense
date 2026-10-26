# Vision LLM vs current pipeline — `gpt-5.4-mini`

Generated 2026-10-26 by `llm_vision_compare.py`. Ground truth: `scripts/ocr_results.csv`.

## Accuracy on bills with ground truth

| Field | Current pipeline | gpt-5.4-mini |
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
| uploads/enoc_fuel_150aed.jpeg | current |  |  |  |  |  |  |  |
| uploads/enoc_fuel_150aed.jpeg | gpt-5.4-mini | ENOC RETAIL LLC | 142.86 | 7.14 | 150 | AED | 2026-08-20 | 886117 |
| uploads/enoc_icebag_6aed.jpg | current |  |  |  |  |  |  |  |
| uploads/enoc_icebag_6aed.jpg | gpt-5.4-mini | ENOC RETAIL LLC | 6 | 0.29 | 6 | AED | 2026-08-18 | 584439 |
| uploads/ksa2_qema_taxi_45sar.png | current |  |  |  |  |  |  |  |
| uploads/ksa2_qema_taxi_45sar.png | gpt-5.4-mini | Qema Al-Khaleej Limited Co. For General Rent | 45 | 0 | 45 | NULL | 2025-06-25 | 0386 |

## Line items (multi-item flow)

| Bill | Real items | Current | LLM | LLM Σ lines | LLM total | Σ matches |
|---|---|---|---|---|---|---|
| uploads/enoc_fuel_150aed.jpeg | ? | 0 | 1 | 150 | 150 | ✅ |
| uploads/enoc_icebag_6aed.jpg | ? | 0 | 1 | 6 | 6 | ✅ |
| uploads/ksa2_qema_taxi_45sar.png | ? | 0 | 1 | 45 | 45 | ✅ |

Σ matches checks the app's assumption in `_replace_line_items`: line amounts are VAT-inclusive and sum to the bill total (pre-VAT rows are converted in `_make_lines_vat_inclusive`).

## Backend / Flutter contract check

All LLM results map cleanly onto `OcrService.run()` → `_receipt_payload` → `OcrResult.fromJson`.

## Usage

- Bills sent: 3 · prompt tokens 6,860 · completion tokens 536 (avg 2,286 / 178 per bill)
- Latency: avg 4.6s, max 5.4s
