# Petty Cash & Expense Bill Scanning Module — Phased Implementation Plan

Source spec: "Petty Cash & Expense Bill Scanning Module — Development Documentation v1.2" (Denny Joseph, 2026-08-10).
This plan translates that spec into buildable phases on top of the **existing codebase** (Flutter + FastAPI + SQL Server, see [`EXPENSE_RECEIPT_APP_PLAN.md`](../EXPENSE_RECEIPT_APP_PLAN.md)).

## Where we are today (gap baseline)

Current app is a single-region MVP:
- 1 approver role (`finance`), flat status chain `draft → submitted → approved/rejected → paid`
- Tables: `expense_app_users`, `expense_claims`, `expense_receipts`, `expense_claim_history`
- OCR is a stub; no duplicate detection, no fund balances, no NetSuite, no notifications, no Arabic/RTL, no region config

The v1.2 spec requires: region-configurable approval matrix, multi-level approval (HOD → dept-HOD → Accountant → Finance Manager), petty cash fund + reimbursement settlement, NetSuite posting, notifications, budget forecasting, multi-region users, Arabic UI/RTL + Arabic OCR, and a full audit trail. This is a rewrite of the data model and workflow engine, not an incremental patch — hence phased below so each phase ships something testable.

Each phase below = one deliverable slice. Do not start phase N+1 until phase N is demo-able end-to-end (backend + minimal UI), per the "implement phase by phase" instruction.

---

## Phase 1 — Foundation: Config-Driven Data Model
**Spec refs:** §3 Master Data Ownership, §6 Rules 8/17/19, §7 schema

- [ ] New tables: `region_config`, `expense_categories` (with `owning_department_id`), `vendors`, `multi_region_user_regions`, `employees_cache`, `projects_cache`
- [ ] Rework `expense_transactions` (replaces `expense_claims`): `type`, `region`, `project_id`, `category_id`, `vendor_id`, `currency`, `exchange_rate`, `amount`, `vat_amount`, `total_amount`, `duplicate_flag`, `ocr_confidence_json`
- [ ] `expense_documents` replaces `expense_receipts` fields (`s3_key`, `hash`)
- [ ] Admin CRUD APIs: region config, categories (+ department mapping), vendors
- [ ] Migration script + backfill from existing `expense_claims`/`expense_receipts` (don't drop old data)

**Demo gate:** Admin can create/edit a region config and a category with an owning department via API; new transaction schema is live on ERP-Dev.

## Phase 2 — Multi-Level Approval Workflow Engine
**Spec refs:** §5.2, §5.11, §6 Rules 1/2/9/19/20

- [ ] `approval_history` table; stage enum `hod | department_hod | accountant | finance_manager`
- [ ] Stage sequencing driven by `region_config.approval_matrix` (JSON), not hardcoded
- [ ] Approve / Dispute / Reject actions; dispute returns to the employee and back to the **disputing stage** on resubmit (not restart)
- [ ] Cross-department HOD insertion: when category's `owning_department_id` ≠ employee's department, insert `department_hod` stage after `hod`; auto-skip if same person
- [ ] Roles & permission checks per stage (HOD / dept-HOD / Accountant / Finance Manager)
- [ ] SLA fields (`stage_due_at`) + delegation table (`approver_delegations`: approver, backup, date range) — escalation job can be a stub/log for now
- [ ] Bulk-approve endpoint (amount threshold, no flags)

**Demo gate:** A bill routes HOD → (dept HOD if applicable) → Accountant → Finance Manager; dispute/reject/approve all work; an IT-category bill from a non-IT employee correctly picks up the IT HOD stage.

## Phase 3 — Petty Cash Fund & Reimbursement Settlement
**Spec refs:** §5.3, §5.4, §5.5, §5.6, §6 Rules 3/4

- [ ] `petty_cash_funds`, `fund_topup_requests` tables + top-up approval chain (configurable, can differ from expense chain)
- [ ] Soft check (warning) + hard check (block, per `region_config.petty_cash_hard_limit_enabled`) at submission and at Finance Manager stage
- [ ] Reimbursement flow: `Approved — Unpaid` → `payment_records` → `Paid` (method, reference, date)
- [ ] `netsuite_postings` table + posting trigger **only** after Finance Manager approval: Journal Entry (petty cash) vs Vendor Bill (reimbursement); failure → reconciliation queue, does not block workflow

**Demo gate:** Petty cash bill posts as a Journal Entry stub after FM approval; reimbursement claim reaches Paid with a payment record; hard-limit region blocks over-limit submission.

## Phase 4 — Bill Capture & OCR Enhancements
**Spec refs:** §5.1, §6 Rules 6/9/10, §8 validation table

- [ ] Extract Vendor, Expense Type, Amount, VAT, Total, Bill Date with per-field confidence
- [ ] Vendor auto-match against `vendors`; unmatched → flag for Accountant stage (not blocking)
- [ ] Duplicate detection (hash + vendor+amount+date) — warn, allow-with-justification, flag persists for approvers
- [ ] All fields always editable regardless of confidence (already partly true — verify)
- [ ] Image-quality-too-low hard block on capture

**Demo gate:** Scanning a bill returns per-field confidence, flags a duplicate, and flags an unmatched vendor for the Accountant.

## Phase 5 — Notifications
**Spec refs:** §5.7, §6 Rule 15

- [ ] `notifications`, `notification_preferences` tables
- [ ] Emit on every status-changing event: submit, dispute, reject, each approval, posting, SLA breach, low balance, top-up approved, paid
- [ ] Push (start with a pluggable stub/FCM) + email fallback; delivery status logged
- [ ] Per-user preference toggles

**Demo gate:** Each workflow transition from Phases 2–3 produces a logged notification to the correct recipient.

## Phase 6 — Region-Aware Branding & Multi-Region Users
**Spec refs:** §5.9, §6 Rules 16/17/18

- [ ] Branding (company name, logo, accent) resolved from `region_config`, cached client-side, refreshed on Admin update
- [ ] Multi-region user: explicit region picker per new bill (never inferred); selection drives branding, approval chain, fund, compliance rules for that transaction only
- [ ] Region-split dashboard (no blending across regions)
- [ ] Approvers see the transaction under its selected region, not their own

**Demo gate:** A multi-region test user creates one UAE bill and one KSA bill in the same session; branding, approver chain, and fund debited differ correctly per bill.

## Phase 7 — Arabic UI, RTL & Arabic-Script OCR
**Spec refs:** §5.10, §6 Rule 21

- [ ] Flutter localization (en/ar) + RTL mirroring across nav, forms, tables, dashboards, notifications
- [ ] Arabic-script OCR extraction (evaluate engine per §10 open question); mixed-script numeric fields extract correctly regardless of surrounding script
- [ ] Arabic keyboard input on correction fields (mobile + web)
- [ ] Generated documents/emails respect recipient language preference

**Demo gate:** An Arabic-script bill goes through the same confidence/edit/approval flow as an English one, with full RTL UI, no reduced functionality.

## Phase 8 — Budget Forecasting & Reporting Dashboards
**Spec refs:** §5.8, §9, §6 Rule 14

- [ ] `budget_forecasts` table; trailing 3-month average burn-rate projection, recalculated on posting (or daily job)
- [ ] Dashboards: Consumption (allocated/spent/remaining by region/dept/employee/category), Aging/Pending Approvals w/ SLA breach, Anomaly View, Trend Analysis, Reconciliation Report, Budget Forecast View
- [ ] Forecast is advisory only — never blocks submission (only hard limits from Phase 3 can)

**Demo gate:** Dashboard shows projected-vs-allocated for a department and flags one trending over budget; forecast never blocks a submission.

## Phase 9 — Hardening: Audit Trail, Offline Sync, Security & Compliance
**Spec refs:** §6 Rule 7, §8, Data flow "Offline handling", §10 open questions

- [ ] Immutable `audit_log` (who/when/old/new) covering every field edit, approval, dispute, rejection
- [ ] Offline capture queue on device; sync + duplicate-submission resolution by hash on reconnect
- [ ] Role-based document visibility scoping (employee sees own only; approvers per scope)
- [ ] S3 encryption at rest + signed URLs; document retention policy per region (pending Legal/Finance confirmation, §10)
- [ ] Resolve remaining §10 open questions before UAT: OCR engine choice, ZATCA/TRN validation scope, data residency, NetSuite auto-vendor-create, retention period, payment method per region, multi-region source of truth, branding assets, cross-department category seed list

**Demo gate:** Security/audit review pass; every mutation is traceable; offline-then-sync scenario doesn't create duplicate transactions.

---

## Open questions to resolve before/during relevant phases (spec §10)
These block specific phases and need answers from Finance/Legal/Admin:
- OCR engine choice + regional data-residency fit (Assumption 1) — Phase 4/7
- ZATCA e-invoicing / Fatoora QR requirement for KSA — Phase 9 (or earlier if it blocks Phase 4 field extraction)
- VAT/TRN format validation for UAE — Phase 4
- Data residency for scanned documents/transaction data per region — Phase 9
- **Middleware API filtering capability** (active-employees-only, projects-by-region) — needed to size the `employees_cache`/`projects_cache` sync job — Phase 1/6
- NetSuite auto-vendor-creation vs. always-manual-mapping — Phase 3
- Document retention period per region (recommend 7 years pending Legal/Finance) — Phase 9
- Reimbursement payment method per region (bank transfer / payroll / cash) — Phase 3
- Multi-region user source of truth: middleware-provided vs. admin-owned locally — Phase 6
- Branding assets (final logos, legal names, accent colors per region) — Phase 1/6
- Arabic OCR engine's proven accuracy on handwritten/mixed-script GCC bills — Phase 7
- Cross-department category-to-department seed list (IT, Admin/Facilities, HR, etc.) — Phase 1/2

## Risks & Controls (spec §11)

| Risk | Control | Where it lives |
|---|---|---|
| Fraudulent duplicate submissions | Hash-based duplicate detection + persistent approver-visible flag | Phase 4 |
| Petty cash overspend beyond allocation | Region-configurable hard limit check at submission and at Finance Manager approval | Phase 3 |
| OCR misreads amount, causing incorrect posting | Mandatory employee review/edit step before submission; confidence flagging | Phase 4 (employee-edit already true today) |
| NetSuite posting failure going unnoticed | Dedicated reconciliation queue, decoupled from approval completion, with alerting | Phase 3 (queue), Phase 5 (alerting) |
| Sensitive financial documents exposed | Role-based visibility scoping, S3 encryption at rest, signed URL expiry, mobile biometric/PIN lock | Phase 9 |
| Region config drift (hardcoded exceptions creeping into code) | All region-specific behavior routed through `region_config`; code review gate against hardcoded region checks | Phase 1 (schema), ongoing code-review discipline every phase |
| Approval bottleneck (approver on leave) | Delegation/backup routing + SLA escalation | Phase 2 (delegation table + SLA fields exist; escalation job itself is a Phase 5/9 stub today) |

## Future Scalability (spec §12)
Explicitly **out of scope** for Phases 1–9 — noted here so they're not forgotten, not because any phase above builds them:

| Area | Enhancement | Not before |
|---|---|---|
| Multi-currency reporting | Consolidated single-base-currency reporting with historical FX rates | Post Phase 8 |
| AI-based anomaly detection | Pattern-based fraud/anomaly scoring beyond duplicate hash, across employee spend history | Post Phase 9 |
| Auto vendor creation in NetSuite | Skip manual mapping once matching confidence is proven over time | Post Phase 3, once real posting volume exists |
| Advanced ML-based forecasting | Seasonality-aware / ML prediction beyond the Phase 8 trailing-average model | Post Phase 8 |
| ERP-ready export | Structured export for finance-system consolidation beyond NetSuite | Not scheduled |

## Suggested order rationale
Phases 1–3 rebuild the transactional core (config → workflow → money movement) since nothing later works without them. Phase 4 (richer OCR) and 5 (notifications) layer onto a working workflow. Phase 6–7 (multi-region, Arabic) are UI/config-heavy and easier once the core is stable. Phase 8 (forecasting) needs real transaction history to be meaningful. Phase 9 (hardening) closes out before UAT.
