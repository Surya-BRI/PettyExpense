# Petty Cash & Expense Bill Scanning Module — Phased Implementation Plan

Source spec: "Petty Cash & Expense Bill Scanning Module — Development Documentation v1.2" (Denny Joseph, 2026-08-10).
This plan translates that spec into buildable phases on top of the **existing codebase** (Flutter + FastAPI + SQL Server, see [`EXPENSE_RECEIPT_APP_PLAN.md`](../../EXPENSE_RECEIPT_APP_PLAN.md)).

## Where we are today (gap baseline)

Current app is a single-region MVP:
- 1 approver role (`finance`), flat status chain `draft → submitted → approved/rejected → paid`
- Tables: `expense_app_users`, `expense_claims`, `expense_receipts`, `expense_claim_history`
- OCR is a stub; no duplicate detection, no fund balances, no NetSuite, no notifications, no Arabic/RTL, no region config

The v1.2 spec requires: region-configurable approval matrix, multi-level approval (HOD → dept-HOD → Accountant → Finance Manager), petty cash fund + reimbursement settlement, NetSuite posting, notifications, budget forecasting, multi-region users, Arabic UI/RTL + Arabic OCR, and a full audit trail. This is a rewrite of the data model and workflow engine, not an incremental patch — hence phased below so each phase ships something testable.

Each phase below = one deliverable slice. Do not start phase N+1 until phase N is demo-able end-to-end (backend + minimal UI), per the "implement phase by phase" instruction.

## Status as of 2026-08-16 (verified against actual code, not assumed)

| Phase | Status | Notes |
|---|---|---|
| 1 — Foundation: Config-Driven Data Model | 🟡 Partial | Schema + CRUD live; no migration/backfill — legacy tables are dropped, not migrated |
| 2 — Multi-Level Approval Workflow | ✅ Done | JSON-driven stage sequencing, cross-dept HOD, dispute/resubmit all verified in code; only the SLA escalation job is missing (unreachable dead code) |
| 3 — Petty Cash Fund & Settlement | ⬜ Not started | No fund/top-up/payment/NetSuite tables; hard-limit config flag exists but is never read |
| 4 — Bill Capture & OCR Enhancements | 🟡 Partial | Per-field confidence + always-editable fields genuinely done; duplicate flag column never actually gets set; unmatched vendors auto-create instead of flagging; no image-quality block |
| 5 — Notifications | ⬜ Not started | In-app "Notifications" screen is a client-side feed re-derived from claim data each load — not backed by any notifications table or event log |
| 6 — Branding & Multi-Region Users | ⬜ Not started | Region still hardcoded on every claim (now `'UAE'`, was `'IN'`); `UAE`/`KSA` region_config rows seeded 2026-08-17 but no picker consumes them yet; branding is a static asset, ignoring the per-region fields the backend already serves |
| 7 — Arabic UI, RTL & Arabic OCR | 🟡 Partial | Bilingual (en/ar) OCR is real and solid; zero Flutter localization/RTL infrastructure exists |
| 8 — Budget Forecasting & Dashboards | ⬜ Not started | No forecasting table, no dashboard screens of any kind |
| 9 — Hardening (audit/offline/security) | ⬜ Not started | No dedicated field-level audit log, no offline capture queue, coarse document visibility, no encryption/retention config |

---

## Phase 1 — Foundation: Config-Driven Data Model
**Spec refs:** §3 Master Data Ownership, §6 Rules 8/17/19, §7 schema

- [x] New tables: `region_config`, `expense_categories` (with `owning_department_id`), `vendors`, `multi_region_user_regions`, `employees_cache`, `projects_cache` — all tables exist, but `multi_region_user_regions` is unwired (no service/route reads or writes it) and `employees_cache` has no route (admin-seeded only)
- [x] Rework `expense_transactions` (replaces `expense_claims`): `type`, `region`, `project_id`, `category_id`, `vendor_id`, `currency`, `exchange_rate`, `amount`, `vat_amount`, `total_amount`, `duplicate_flag`, `ocr_confidence_json`
- [x] `expense_documents` replaces `expense_receipts` fields (`s3_key`, `hash`)
- [x] Admin CRUD APIs: region config, categories (+ department mapping), vendors
- [ ] Migration script + backfill from existing `expense_claims`/`expense_receipts` (don't drop old data) — **not done**: only `scripts/drop_legacy_tables.py` exists, which drops the legacy tables outright; old data is discarded, not backfilled

**Demo gate:** Admin can create/edit a region config and a category with an owning department via API; new transaction schema is live on ERP-Dev. — ✅ passes, but the "don't drop old data" sub-requirement is currently violated.

## Phase 2 — Multi-Level Approval Workflow Engine ✅ Done
**Spec refs:** §5.2, §5.11, §6 Rules 1/2/9/19/20

- [x] `approval_history` table; stage enum `hod | department_hod | accountant | finance_manager`
- [x] Stage sequencing driven by `region_config.approval_matrix` (JSON), not hardcoded — verified genuinely JSON-driven (`approval_service.resolve_stage_sequence` reads `region.approval_matrix_json["stages"]`), not decorative
- [x] Approve / Dispute / Reject actions; dispute returns to the employee and back to the **disputing stage** on resubmit (not restart)
- [x] Cross-department HOD insertion: when category's `owning_department_id` ≠ employee's department, insert `department_hod` stage after `hod`; auto-skip if same person
- [x] Roles & permission checks per stage (HOD / dept-HOD / Accountant / Finance Manager)
- [ ] SLA fields (`stage_due_at`) + delegation table (`approver_delegations`: approver, backup, date range) — escalation job can be a stub/log for now — **fields + delegation table are done and in use**, but the escalation job itself (`sla_service.check_overdue_stages`) is dead code: defined but never called from any route or scheduler, weaker than even the "stub/log" bar the plan allows
- [x] Bulk-approve endpoint (amount threshold, no flags)

**Demo gate:** A bill routes HOD → (dept HOD if applicable) → Accountant → Finance Manager; dispute/reject/approve all work; an IT-category bill from a non-IT employee correctly picks up the IT HOD stage. — ✅ passes.

## Phase 3 — Petty Cash Fund & Reimbursement Settlement ⬜ Not started
**Spec refs:** §5.3, §5.4, §5.5, §5.6, §6 Rules 3/4

- [ ] `petty_cash_funds`, `fund_topup_requests` tables + top-up approval chain (configurable, can differ from expense chain) — no such tables/routes exist
- [ ] Soft check (warning) + hard check (block, per `region_config.petty_cash_hard_limit_enabled`) at submission and at Finance Manager stage — the config flag exists and is admin-settable, but is never read anywhere; `approval_service.py` has an explicit `# TODO(Phase 3): petty-cash hard/soft balance check` marking this as deliberately deferred
- [ ] Reimbursement flow: `Approved — Unpaid` → `payment_records` → `Paid` (method, reference, date) — `mark_paid()` only flips `status` to `"paid"` with a timestamp and free-text remarks; there is no `payment_records` table capturing method/reference/date as structured data
- [ ] `netsuite_postings` table + posting trigger **only** after Finance Manager approval: Journal Entry (petty cash) vs Vendor Bill (reimbursement); failure → reconciliation queue, does not block workflow — no NetSuite integration of any kind exists yet

**Demo gate:** Petty cash bill posts as a Journal Entry stub after FM approval; reimbursement claim reaches Paid with a payment record; hard-limit region blocks over-limit submission. — ❌ would fail on all three today.

## Phase 4 — Bill Capture & OCR Enhancements 🟡 Partial
**Spec refs:** §5.1, §6 Rules 6/9/10, §8 validation table

- [x] Extract Vendor, Expense Type, Amount, VAT, Total, Bill Date with per-field confidence — genuinely done, tiered confidence (`label/table/heuristic/bare/guess/missing/mismatch`) consumed by the confirm screen
- [ ] Vendor auto-match against `vendors`; unmatched → flag for Accountant stage (not blocking) — **effectively bypassed**: `_resolve_vendor` auto-creates a new vendor row whenever there's no match, instead of leaving it unmatched/flagged, so the Accountant essentially never sees a real "unmatched vendor" state
- [ ] Duplicate detection (hash + vendor+amount+date) — warn, allow-with-justification, flag persists for approvers — detection itself works and shows a UI warning, but `duplicate_flag` is never actually set to `true` anywhere in `create_claim`, and there's no justification-capture workflow beyond the warning banner
- [x] All fields always editable regardless of confidence (already partly true — verify) — confirmed: every OCR field renders as a normal editable `TextField`, no read-only gating
- [ ] Image-quality-too-low hard block on capture — not implemented; capture only sets a JPEG compression parameter, no blur/quality detection

**Demo gate:** Scanning a bill returns per-field confidence, flags a duplicate, and flags an unmatched vendor for the Accountant. — 🟡 confidence + duplicate warning both work; the unmatched-vendor-to-Accountant flag does not actually trigger in practice.

## Phase 5 — Notifications ⬜ Not started
**Spec refs:** §5.7, §6 Rule 15

- [ ] `notifications`, `notification_preferences` tables — neither exists
- [ ] Emit on every status-changing event: submit, dispute, reject, each approval, posting, SLA breach, low balance, top-up approved, paid — `email_service.notify()` only fires on submit and paid/reject paths; nothing on dispute or individual approval-stage transitions (posting/SLA/low-balance/top-up don't exist yet regardless)
- [ ] Push (start with a pluggable stub/FCM) + email fallback; delivery status logged — no push/FCM code; email fallback logs a "[STUB EMAIL]" line when disabled, but nothing persists delivery status
- [ ] Per-user preference toggles — no preferences table or UI

**Important caveat:** the in-app **"Notifications" screen already exists** (`lib/src/features/notifications/notifications_screen.dart`) and looks fully functional — but it's a client-side feed re-derived from `myClaims()`/`approvalsQueue()` responses on every load, not backed by any backend notifications table or event log. Don't mistake it for this phase being done.

**Demo gate:** Each workflow transition from Phases 2–3 produces a logged notification to the correct recipient. — ❌ would fail — nothing is persisted/logged server-side.

## Phase 6 — Region-Aware Branding & Multi-Region Users ⬜ Not started
**Spec refs:** §5.9, §6 Rules 16/17/18

- [ ] Branding (company name, logo, accent) resolved from `region_config`, cached client-side, refreshed on Admin update — `BrandAppBar` hardcodes a static logo asset and app name; the backend already returns `company_name`/`logo_url`/`brand_color` per region but the Flutter app never reads them
- [ ] Multi-region user: explicit region picker per new bill (never inferred); selection drives branding, approval chain, fund, compliance rules for that transaction only — `confirm_claim_screen.dart` still hardcodes a single `region_code` on every claim (now `'UAE'`, previously `'IN'`); no picker UI exists. `UAE` and `KSA` `region_config` rows now exist on ERP-Dev (2026-08-17, both seeded with the same approval matrix as the pre-existing `IN` row) so a picker has real regions to select from, but nothing selects between them yet — every claim still hits `UAE` regardless of which country the bill is actually from. Approver assignment (`ErpExpenseHodAssignment`) also isn't region-scoped — UAE and KSA claims would resolve to the same HOD/Accountant/Finance Manager today even with a picker.
- [ ] Region-split dashboard (no blending across regions) — no dashboards exist at all yet (see Phase 8)
- [ ] Approvers see the transaction under its selected region, not their own — trivially true only because there's a single region in practice; nothing built or tested for multiple

**Demo gate:** A multi-region test user creates one UAE bill and one KSA bill in the same session; branding, approver chain, and fund debited differ correctly per bill. — ❌ would fail completely — region is hardcoded, no branding switch, no fund concept exists.

## Phase 7 — Arabic UI, RTL & Arabic-Script OCR 🟡 Partial
**Spec refs:** §5.10, §6 Rule 21

- [ ] Flutter localization (en/ar) + RTL mirroring across nav, forms, tables, dashboards, notifications — no `flutter_localizations` dependency, no `Locale`/`Directionality`/RTL handling anywhere in `lib/`
- [x] Arabic-script OCR extraction (evaluate engine per §10 open question); mixed-script numeric fields extract correctly regardless of surrounding script — genuinely done: PaddleOCR runs separate `en`/`ar` passes, merged field-by-field, with Arabic-Indic digit normalization and bilingual vendor extraction. Engine choice (PaddleOCR) evaluated and documented in [`OCR_ENGINE_EVALUATION.md`](OCR_ENGINE_EVALUATION.md); a run of image-preprocessing (grayscale/contrast/sharpen) to improve handwritten-amount accuracy was tried and reverted after it measurably regressed a real sample — see that doc's evaluation notes
- [ ] Arabic keyboard input on correction fields (mobile + web) — standard text fields only, no RTL layout to support it meaningfully yet
- [ ] Generated documents/emails respect recipient language preference — `email_service.py` sends hardcoded English strings only

**Demo gate:** An Arabic-script bill goes through the same confidence/edit/approval flow as an English one, with full RTL UI, no reduced functionality. — 🟡 the OCR half passes; "full RTL UI" fails outright — no localization layer exists in the Flutter app.

## Phase 8 — Budget Forecasting & Reporting Dashboards ⬜ Not started
**Spec refs:** §5.8, §9, §6 Rule 14

- [ ] `budget_forecasts` table; trailing 3-month average burn-rate projection, recalculated on posting (or daily job) — no such table/service
- [ ] Dashboards: Consumption (allocated/spent/remaining by region/dept/employee/category), Aging/Pending Approvals w/ SLA breach, Anomaly View, Trend Analysis, Reconciliation Report, Budget Forecast View — no dashboard screens exist in `lib/src/features/` at all; the home screen is a simple landing page, not a dashboard
- [ ] Forecast is advisory only — never blocks submission (only hard limits from Phase 3 can) — N/A, nothing built yet to check

**Demo gate:** Dashboard shows projected-vs-allocated for a department and flags one trending over budget; forecast never blocks a submission. — ❌ would fail entirely — no forecasting, no dashboards.

## Phase 9 — Hardening: Audit Trail, Offline Sync, Security & Compliance ⬜ Not started
**Spec refs:** §6 Rule 7, §8, Data flow "Offline handling", §10 open questions

- [ ] Immutable `audit_log` (who/when/old/new) covering every field edit, approval, dispute, rejection — not started as a dedicated log; `approval_history` only logs coarse stage actions (approve/dispute/reject/created/submitted/edited as a label), with no old/new value diffing on edits
- [ ] Offline capture queue on device; sync + duplicate-submission resolution by hash on reconnect — not started; no local persistence package (`sqlite`/`hive`/`drift`/`isar`) in `pubspec.yaml`, capture uploads directly
- [ ] Role-based document visibility scoping (employee sees own only; approvers per scope) — partial: basic ownership checks exist (an employee can't see another's claim), but any approver can currently see any document rather than being scoped per department/region/stage
- [ ] S3 encryption at rest + signed URLs; document retention policy per region (pending Legal/Finance confirmation, §10) — partial: signed URLs exist; encryption-at-rest config and retention policy are not implemented anywhere
- [ ] Resolve remaining §10 open questions before UAT: OCR engine choice, ZATCA/TRN validation scope, data residency, NetSuite auto-vendor-create, retention period, payment method per region, multi-region source of truth, branding assets, cross-department category seed list — OCR engine choice is the one resolved item here (PaddleOCR, see `OCR_ENGINE_EVALUATION.md`); the rest remain open

**Demo gate:** Security/audit review pass; every mutation is traceable; offline-then-sync scenario doesn't create duplicate transactions. — ❌ would fail — no dedicated audit log, and no offline sync mechanism exists to even test against.

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
