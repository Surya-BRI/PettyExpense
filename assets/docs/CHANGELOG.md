# Changelog

Newest first. Each entry says what changed for users, what changed in the code, and anything left to do.

---

## 2026-11-09 — Blue Rhine Contracting (UAE): follows the department flow

Docs only. BRC's *PCA – Replenishment Process* (limit → bills → prepare PCA → Verifier → Financial Manager → bank withdrawal → top-up) is mapped in [`BRC_DEPARTMENT_PETTY_CASH.md`](BRC_DEPARTMENT_PETTY_CASH.md). Decision: BRC keeps the same department flow as Blue Rhine Industries, with no code or settings change. Known differences accepted for now: each bill is still approved HOD → Accountant → Finance Manager before it can go on a top-up, and the Finance Manager approves and records the bank payment in one step.

### Before go-live

- Tick Blue Rhine Contracting for each BRC person in Admin → People (no ERP subsidiary maps to UAE).
- Set the "Site-wise statement" department limit (5,000) for Blue Rhine Contracting, make Roshan Stanly its HOD, and set an Accountant and Finance Manager for the company.

---

## 2026-11-09 — Professional Signs (KSA): Accounts Department petty cash is tracked

Branch: `indra` (not yet committed). PCA PDF section 6. This changes Q4 in [`PS_EMPLOYEE_PCA_COMPARISON.md`](PS_EMPLOYEE_PCA_COMPARISON.md) from "just record it" to tracking a balance.

### What changed for users

- **The Accounts Department's own petty cash now has a balance.** Admin or the KSA Accounts Manager sets its amount; every **Process 2 · Direct payment by Accounts** (a bill on Payments, or an older advance request) takes from it.
- **Process 2 is refused** when the account isn't set up yet, or has less left than the payment ("Refill it from the bank first, or pay by Process 1"). In "Pay N together" each bill is checked in turn; the ones that don't fit are skipped with that reason.
- **Refill from bank:** the Accounts Manager (or Admin) records money put back, with a bank reference and date, up to what has been paid out and not refilled.
- **Low alert:** below 20% left, the Accounts Manager and Admin are notified once per refill cycle.
- **Admin is notified** whenever the Accounts Manager changes the amount ("… changed the Accounts Department petty cash (KSA) from SAR 5,000.00 to 20,000.00", with the reason). Not when Admin changes it.
- **Advances → Accounts cash** (new third tab for the Accounts Manager, Accounts and Admin) shows what's left, paid out, refilled, to refill, a bar, and recent movements. Admin and the Accounts Manager get **Set / Change amount**; the Accounts Manager also gets **Refill from bank**. Admin also sees it as the **Accounts cash** tab on Companies → Professional Signs.
- The payment sheet's Process 2 option shows "From Accounts petty cash · SAR … left", in red when it can't cover the payment.
- Process 1 (bank) and Dubai are unchanged.

### Code

- New tables `ErpExpenseAccountsCash` (one per company: `cashLimit`, `currency`) and `ErpExpenseAccountsCashEntry` (`kind` payout / refill / set), created by `create_all()` on startup. Kept apart from `ErpExpensePettyCashFund` so no fund list or balance picks it up.
- New `services/accounts_cash_service.py`: `take_payout` (no commit; called by `payment_service.record_payment` and `employee_pca_service.pay` before they commit), `after_payout` (low alert), `view`, `set_limit` (Admin; not below what's out), `refill`.
- Routes: `GET /api/pca/accounts-cash?region_id=`, `PUT /api/pca/accounts-cash`, `POST /api/pca/accounts-cash/refills`.
- `routes_notifications._type_ids` ignores `pca_accounts_cash_low_*` (no top-up or fund id in it).
- App: `features/pca/accounts_cash_view.dart`, `AccountsCash` model, three API calls.
- Tests: new `backend/tests/test_accounts_cash.py` (6 tests); `test_employee_pca.py` sets the account up before its Process 2 payment. Backend 373 passed, 5 skipped, 2 xfailed; Flutter 80 passed, "App boots to home" failing as before.

### Before go-live

- Admin or the KSA Accounts Manager must set the Accounts Department amount, or every Process 2 payment is refused.

---

## 2026-11-05 — Professional Signs (KSA): simpler flow after the team's answers

Branch: `indra` (not yet committed). This replaces parts of the 2026-11-04 entry below. Decisions are in [`PS_EMPLOYEE_PCA_COMPARISON.md`](PS_EMPLOYEE_PCA_COMPARISON.md) (Q2, Q7, Q10).

### What changed for users

- **Bills go Employee → own HOD → Accounts Manager.** The Accountant step is gone in KSA. The Accounts Manager enters the **EJV / EJVB** and its journal number when approving. Bulk approve skips these bills (reason `journal_required`), because each needs its own journal. The duplicate-bill comment rule now applies at the Accounts Manager step.
- **One petty cash (PCA) per employee, for all their projects, set by the HOD and usable at once.** A PCA is a limit, not cash handed over, so it has **no Accounts Manager approval or payment**. The HOD (or Admin) opens Advances → **Set petty cash**, picks the employee and enters the full amount. Setting it again replaces the amount; it can't go below the bills not yet topped up. Each change is logged as an advance request with status `set` (amount = the change), and the employee is notified. Any petty-cash bill comes off it, whatever its project. **Money only moves when a top-up or a reimbursement is paid.**
  - **Advances → Employees** (first tab, replaces "By department") lists **every employee** the viewer oversees, by department. An HOD sees their staff; the Accounts Manager, Accountant and Admin see everyone in the company. Each row shows the employee's limit, what's left, spent, to top up and in approval, with a bar that turns orange from 50% used. People without petty cash show **Not set**, and a banner counts them. HOD and Admin tap an employee to set or change their amount (Set petty cash opens with that person picked). Backend: `summary.by_department` now also includes people with no PCA (`fund_id: null`, all figures 0); `advance_count` counts those with one.
  - **Hard limit at 50%.** Bills not yet topped up, whether approved or still in approval, may use at most **50% of the PCA** (SAR 5,000 of 10,000). A petty-cash bill past that is blocked ("You can use only SAR 5,000.00 of your petty cash before a top-up… Raise a top-up with your approved bills, or submit this as a reimbursement"). Once a top-up is **paid**, that part is free again; a top-up still in progress doesn't free anything. The employee's card shows **Can use now**, with "Up to SAR 5,000 of bills before a top-up", or "Limit reached" in orange. Setting `pca_spend_limit_ratio: 0.5` (added to KSA at startup by `apply_employee_settings`); `fund_to_dict` gains `spend_limit` and caps `uncommitted`. Dubai and individual pots have no cap.
  - **"By project" tab removed** from Advances and from Admin → Professional Signs, because the limit is per employee, not per project. Advances now has **Employees · Requests**; Admin's KSA company page has **Employees · Requests · Approvers**. Every bill still saves its OP code, and `GET /api/pca/summary` still returns `by_project`, so the report can come back later.
  - **Employees in both Dubai and KSA** see their KSA petty cash without switching company. **My advances** is in the menu whenever they have KSA petty cash. The drawer card shows both companies, e.g. "Sales petty cash (Dubai) · AED … left" and "Your petty cash (KSA) · SAR … can use now". Bills already follow the company picked on each bill. (`myPcaAdvancesProvider` only makes a request for people who cover more than one company, or who are signed in under KSA.)
  - **Paying approved bills (PDF section 7).** After the Accounts Manager approves a KSA bill, it goes to **Payments → Ready to pay**. That now includes **petty cash** bills ("PETTY CASH · refills PCA") as well as reimbursements.
    - **Recording a payment:** the Accounts Manager picks **Process 1 · Cash withdrawal from bank** or **Process 2 · Direct payment by Accounts**, then enters the reference and date. Ticking several bills from one company pays them together ("Pay N together") with one reference.
    - **Paying a petty-cash bill refills the employee's PCA.** It's logged as a paid top-up of that bill, so the 50% limit frees up straight away.
    - **The employee's "Raise top-up" request is removed for KSA:** `request_topup` refuses, and the button is gone. Requests raised before can still be finished.
    - **The 50% reminder** now goes to the employee, HOD **and Accounts Manager**: "approved bills to pay".
    - **Dubai is unchanged:** petty cash never comes to Payments, and payments ask for a method.
    - **Code:**
      - `payment_service.record_payment` / `record_batch` take `payment_source`, required in KSA; petty cash is allowed there (`_top_up_pca`);
      - `list_claims` includes KSA petty cash;
      - new `ErpExpensePaymentRecord.paymentSource` column (`add_employee_pca_columns.py`);
      - `transaction_to_dict.pays_by_process`, and `payment_status` is unpaid/paid for KSA petty cash.
  - Code: `employee_pca_service.set_advance` replaces `propose_advance`; `POST /api/pca/advances` now sets the total. Older advance rows (submitted/approved) can still be closed with `manager_approve` / `pay` / `reject`.
- **Every KSA bill, petty cash or reimbursement, needs a project OP code**: on the bill, or on every item. Items may name different projects; one bill is no longer limited to one project.
- **Only the Accounts Manager pays** advances, top-ups and KSA reimbursements. Payment source labels follow the PDF: "Cash withdrawal from bank" or "Direct payment by Accounts Department". KSA Accountants no longer get Payments in the menu.
- **Report:** *By department* shows each employee's one advance. *By project* now adds up petty-cash bills by each line's OP code (spent, and in approval), with the employees who spent on it.
- Admin → Approvers for KSA shows two steps: HOD, then Accounts Manager.

### Code

- `region_policy.EMPLOYEE_PCA_SETTINGS`:
  - `stages: [hod, finance_manager]`, `journal_required_at: finance_manager`, `payer_roles: [finance_manager]`, and `stage_labels` for `finance_manager` only;
  - `pca_settings_version: 2`. The new `apply_employee_settings` overwrites these keys once on a company with an older version (so a KSA row seeded on 11-04 is updated), and after that only adds missing keys.
- `fund_service`:
  - `employee_advance` (one pot per employee per company) replaces `advance_for_project`;
  - `project_shares` (bill split by line OP code) and `require_bill_projects` replace `bill_project`;
  - `_fund_portion` no longer matches OP codes.
- `transaction_service._require_project_codes` runs on every submit in an employee-model company.
- `approval_service`: `_review_stage` (duplicate review at the journal stage when there's no Accountant); `bulk_approve` skips journal-stage bills.
- `employee_pca_service`:
  - `propose_advance` has no OP code (`routes_pca` accepts and ignores `op_number` for older clients);
  - `summary.by_project` is built from bills.
- App:
  - Propose advance has no OP field;
  - "My advances" shows one advance card;
  - the drawer card reads "Your petty cash advance";
  - the bill screen needs an OP code for all KSA bills and uses the employee's one advance;
  - only the Accounts Manager or Admin can pay;
  - the report's project tab shows spend.
- Tests: `backend/tests/test_employee_pca.py` rewritten for the new flow (backend: 366 passed, 5 skipped, 2 xfailed; Flutter: 80 passed, with "App boots to home" failing as before).

### Left to do

- Existing KSA advances created on 11-04 with an OP code still work (the OP is ignored). If an employee has more than one from testing, only the oldest is used, so clear the test rows on ERP-Dev before go-live.
- Bills already sitting at the KSA Accountant step are moved to the Accounts Manager by the startup seed when it applies the new settings (`approval_service.realign_open_bills`). They don't need to wait for someone to act on them.
- OP codes are not rechecked against ERP on submit.

---

## 2026-11-04 — Professional Signs (KSA): employee petty cash advances

Branch: `indra` (not yet committed). Source: `PCA_Professional_Documentation.pdf`; comparison and decisions in [`PS_EMPLOYEE_PCA_COMPARISON.md`](PS_EMPLOYEE_PCA_COMPARISON.md).

### What changed for users

Professional Signs no longer follows the Blue Rhine Industries department flow. Dubai is unchanged.

- **Advance (PCA) per employee, per project.** The HOD proposes an amount for one of their staff for one project, giving its **OP code**, which is checked in ERP. The Accounts Manager approves it. The Accounts Department then pays it, from the bank or from its own petty cash, and the advance becomes usable. An employee on two projects has two advances with separate balances. A second advance for the same project raises that project's amount.
- **The OP code is required on KSA petty-cash bills.** The bill comes off the employee's advance for that project. A bill for a project they have no advance for is blocked and must be filed as a reimbursement. A petty-cash bill can only be for one project: if its lines have different OP codes, the employee splits it into separate bills.
- **Bills.** The employee's own HOD approves. Then Accounts approves and must enter the journal: **EJV**, or **EJVB** for a multi-branch transaction, plus its ERP number. The Accounts Manager gives the final approval. The steps show as "Accounts (EJV)" and "Accounts Manager".
- **Other departments' items** (e.g. IT items on a Sales bill) no longer go to that department's HOD in KSA. The whole bill comes off the employee's advance.
- **Over the advance:** a petty-cash bill larger than what's left is blocked, and the message says to file the extra as a reimbursement. An employee with no advance can only file reimbursements.
- **Top-up.** The employee (or their HOD) raises it with their approved bills. The HOD approves; this step is skipped if the HOD raised it. The Accounts Manager verifies, and the Accounts Department pays, recording where the money came from. The advance goes back to its full amount. Every step notifies the next person, and any open step can be rejected with a reason.
- **Reminder** to the employee and HOD once **50%** of the advance is spent on approved bills not yet topped up.
- **No department funding in KSA, Admin included.** Admin sees all advances and can step in at any stage, but doesn't set limits.
- **Advances report** (`GET /api/pca/summary?region_id=`) shows one company's advances in two views:
  - **by department:** each employee given an advance, with their advances per project;
  - **by project (OP code):** each employee on it, with their advance.

  Both views give the advance, the amount waiting (proposed but not paid), spent, waiting for top-up and available, plus overall totals. It's a report only: no department or project fund exists. An HOD sees only their own staff.
- **Reimbursements in KSA** can be paid by Accounts (the Accounts Department) as well as the Accounts Manager.

### Code

- New `services/region_policy.py`: per-company settings in `approvalMatrixJson`. These are `pca_model`, `cross_department_split`, `stage_labels`, `journal_required_at`, `payer_roles` and `pca_reminder_ratio`. All defaults keep the department model. The startup seed merges `EMPLOYEE_PCA_SETTINGS` into KSA's matrix, adding only keys that are missing.
- New `services/employee_pca_service.py` + `api/routes_pca.py` (`/api/pca`):
  - `GET /advances`, `POST /advances`
  - `GET /advances/{fund_id}/replenishable-bills`, `POST /advances/{fund_id}/topups`
  - `GET /requests`, `GET /requests/{id}`
  - `POST /requests/{id}/hod-approve | manager-approve | pay | reject`
  - `GET /payment-sources`
- Projects:
  - `ErpExpensePettyCashFund.opNumber`/`opName` make one advance per (company, employee, OP code).
  - `fund_service.bill_project` finds the bill's single project (claim OP, or the lines' common OP), and `advance_for_project` finds the matching advance.
  - `require_petty_cash_within_limit(..., op_number=)` requires the OP code and checks that project's advance.
  - A per-project advance pays only for bills with its OP code.
  - New `services/opportunity_lookup.py` holds the ERP OP lookup, shared with `GET /api/opportunities/search`; `POST /api/pca/advances` takes `op_number`.
- `services/department_split.py` + `transaction_service._line_cross_department`: no department split when the company turns it off.
- `services/approval_service.py`
  - Company stage-name overrides.
  - `advance(..., journal_type=, journal_reference=)` requires the journal at the journal stage and writes it to the history.
  - `POST /api/approvals/{id}/approve` accepts `journal_type`, `journal_reference`.
  - Claims return `journal_type`, `journal_reference`, `journal_stage`.
- `services/fund_service.py`
  - Top-ups count as replenishment only for `kind != advance`, in status `approved` or `paid`; the open statuses now include `hod_approved`.
  - In an employee-model company, a department pot takes no bills, and creating one is refused.
  - The department top-up endpoints refuse employee advances.
  - `_own_fund` doesn't fall back to a department pot, and an unpaid advance (limit 0) takes no bills.
  - `/api/topups` lists department pots only.
  - The 50% reminder is `check_advance_reminder`.
- `services/payment_service.py` + `routes_payments.py`: payer roles come from the company setting (default: Finance Manager). Accountants see and pay only in companies that list them.
- Schema: `scripts/add_employee_pca_columns.py` (run at startup) adds:
  - on `ErpExpenseFundTopupRequest`: `kind`, `hodApprovedBy`, `hodApprovedOn`, `paymentSource`, `paidBy`; existing rows are backfilled to `kind='topup'`;
  - on `ErpExpenseTransaction`: `journalType`, `journalReference`;
  - on `ErpExpensePettyCashFund`: `opNumber`, `opName`.

### Checks

- New `tests/test_employee_pca.py` (18 tests) also covers:
  - separate advances and balances per project;
  - OP code required, and checked in ERP;
  - no spending on a project without an advance;
  - a bill with two projects must be split.

  It covers:
  - the advance and top-up chains and who may act at each step;
  - the over-advance block;
  - no split in KSA while the UAE still splits;
  - KSA stage names and the journal requirement;
  - the 50% reminder, list scoping, and the KSA-only Accounts payer.
- Full suite: 363 passed, 5 skipped, 2 expected failures. The advances report has its own test. Run `python -m pytest tests`: plain `python -m pytest` in `backend/` also collects `test_one.py`, which calls the live vision API.

### App (Flutter)

Everything below applies when the signed-in company is on the employee model (`AuthUser.pcaModel`, from the new `pca_model` field on login and `/me`); Dubai screens are unchanged.

- New **Advances** screen (`features/pca/advances_screen.dart`, route `/advances`):
  - **HOD, Accounts, Accounts Manager, Admin:** three tabs:
    - **Requests**, with a "Waiting for me" filter. Each request has its step buttons: HOD Approve; Accounts Manager Approve advance / Verify; Accounts Record payment; Reject with a reason.
    - **By project** and **By department:** the report, each group expandable to its employees.
  - HOD and Admin get **Propose advance**: employee (from `GET /api/pca/staff`), OP code looked up in ERP, amount and reason.
  - **Employee:** **My advances** shows one card per project (available, advance, spent) with **Raise top-up**, which picks the approved bills, plus their requests.
  - The pay sheet asks where the money came from: bank, or the Accounts Department's petty cash.
- **Navigation:**
  - The drawer has **Advances / My advances**, and the bottom-nav money tab goes to Advances.
  - Department Funds and Top-ups are hidden, and `/funds` and `/topups` redirect to `/advances`.
  - Accounts gets **Payments** in KSA.
  - The drawer's petty-cash card shows what's left across the employee's advances.
- **Notifications switch company.**
  - Each notification now says which company it is about (`region_code`). For a claim it's the claim's company; for a top-up, advance, low-fund or reminder notice it's the pot's company (`routes_notifications._regions_for`, two queries per page).
  - Tapping one that belongs to another company the user covers switches to that company first ("Switching to KSA…"), then opens it.
  - Advance and top-up notices (`pca_*`) open **Advances**.
- **Admin → company (KSA):**
  - the tabs are **By project / By department / Approvers**, replacing Departments and Top-ups;
  - an **Advance requests** shortcut opens the Advances screen;
  - the Approvers tab describes the Professional Signs steps (HOD proposes and approves; Accounts books the EJV and pays; Accounts Manager approves and verifies);
  - the company list labels KSA "Employee advances by project".
- **Accounts approval:**
  - an **Expense journal** choice (EJV / EJVB) and **Journal number** are required before Approve;
  - claim details show the journal and the OP code.
- **Bill confirm screen (KSA petty cash):**
  - the OP code is required;
  - the balance shown is that project's advance;
  - a bill is blocked with a clear message when it has no OP code, has two projects, has no advance for that project, or is more than what's left.
  - The department split note is hidden, including the per-line "Goes to IT HOD · paid from IT petty cash" note on multi-item bills (`LineItemsEditor.splitsByDepartment`).
- Admin's department **Request top-up** screen no longer offers KSA, which has no department pots.
- Checks: `flutter analyze lib` reports no errors. New `test/pca_journal_test.dart` (2 tests). `flutter test`: 80 passed, and only "App boots to home" fails (already failing before).

### Left for later

- **Waiting on the Professional Signs team (Q10 in `PS_EMPLOYEE_PCA_COMPARISON.md`):** is a PCA held by **one employee** for their project (as built), or is it **one shared pot per project**? If it's a shared pot, the advance moves from (employee, OP) to (OP).
- **Project checks:**
  - An advance is personal (one employee and one OP code); others on the same project need their own.
  - Not checked: whether the employee is on the project in ERP, and the OP code on submit for reimbursements (petty cash must match one of the employee's own advances anyway). Details are in `PS_EMPLOYEE_PCA_COMPARISON.md`, "How advances, employees and projects link".
- **Existing KSA department pots** from the earlier BRI-style setup now take no bills. Bills already charged to them drop out of those pots' figures. Check ERP-Dev for KSA department pots and open department top-ups before deploying.
- Still open with Professional Signs: what makes a bill multi-branch (Q6), whether this applies to Oman (Q8), and how an advance is settled when someone leaves (Q9).

---

## 2026-11-03 — Funds views for approvers

Branch: `indra`, commit `5081ffd`

### What changed for users

Backend only for now: no Flutter or web-admin screen calls these endpoints yet.

- **HOD and Finance Manager** can see which petty-cash pots a bill is paid from, and how much of the bill comes out of each one. A Sales employee's bill with IT items draws on both the Sales pot and the IT pot.
  - The Finance Manager sees every pot the bill draws on, so they can check it fits before final approval.
  - An HOD sees only their own department's pot.
- **Finance Manager** can see the department pots of a company they cover (read only). Admin still sets limits, and top-ups still go HOD request → Accounts verify → FM approve.

### Code

- `api/routes_org.py`
  - `GET /api/approvals/{id}/funds` (roles `hod`, `finance_manager`; Admin also passes). Returns `[{bill_part, fund}]`, biggest part first, or an empty list for a reimbursement. It returns 403 when the user doesn't cover the bill's company. For an HOD the rows are filtered to `my_fund_ids`.
  - `GET /api/funds/department-funds?region_id=` (role `finance_manager`; Admin also passes). It returns 403 when the user doesn't cover the company (`region_scope.user_covers`), and 404 for an unknown company.
- `services/fund_service.py`
  - `bill_funds(db, transaction_id)` returns the bill's `region_id` and one row per pot it draws on. It uses the same split as the balances (`_fund_portion`), so the parts add up to what the pots are charged. The pot figures already include this bill: it is reserved while it waits for approval and counted as spent once approved.
  - `my_fund_ids(db, user)` is a public wrapper around `_my_fund_ids`.

### Checks

- `tests/test_funds_and_regions.py` has four new `bill_funds` tests: one row per pot with its part, a foreign-currency bill converted to the pot's currency, an empty result for a reimbursement, and an unknown claim. The route-level permission filtering (HOD sees only their own pot, the company-coverage 403) has no test.

### Left for later

- A UI for both endpoints: a "Paid from" card on the approval detail screen, and a department-funds view for the Finance Manager.
- The limit is not checked again when the Finance Manager approves. It is checked only at submit and resubmit, as a hard block (see `transaction_service._require_petty_cash_limit`). The region flag `petty_cash_hard_limit_enabled` is still never read.

---

## 2026-11-02 — Company (region) filter on the approval queue

Branch: `indra`, commit `8767a86`

### What changed for users

- The Accountant's claims page (the approval queue) has a company filter: a dropdown at the right end of the status chips row ("All regions", then each region by its short name).
- The filter works on the page itself, together with the status filter (All / New / Disputed). For example, "New" with "KSA" shows only new KSA claims.
- The same queue screen serves HOD and Finance Manager, so they get the filter too.
- The chips show only the companies that person has access to: their home company plus the companies Admin ticked for them in People. This is the same rule the backend uses to send bills to their queue.
- People with no such list (Admin, or older accounts with no company set) see the companies that appear in their queue.
- The dropdown appears only when there is more than one company to choose from.

### Code

- `lib/src/features/approvals/approval_queue_screen.dart`: takes the companies from the signed-in user's `allowedRegions` (set at login by `selectable_regions_for`), falling back to the companies in the loaded queue. It filters the loaded queue by `regionCode` on the device, with no new API call per filter, and the empty message names the company.

### Checks

- Flutter analyze on the file: no issues.
- Flutter tests: `widget_test.dart` "App boots to home" fails with and without this change, so it was already failing.

---

## 2026-11-02 — Vendor matching and the vendor list removed

Branch: `indra`, commit `8767a86`

### What changed for users

- The vendor on a bill is now just the name typed or scanned from the bill. It is no longer matched against a vendor list.
- **Accountant:** the "Link to existing vendor / Confirm as new vendor" step is gone. Accountants approve, dispute or reject as usual.
- **HOD, department HOD and Finance Manager:** the "Unmatched vendor" notice is gone.
- **Web dashboard (app and web-admin):** the "Unmatched vendors" group, the "New vendor" / "Not in vendor list" tags and the vendor icon in the claims list are gone. The "Flagged only" filter now shows possible duplicates only.
- **Claims CSV export (web-admin):** the "Vendor unmatched" column is gone.
- **Admin:** the vendor list (list, add, delete) is gone. There were no vendor screens in the app or web-admin, only the backend endpoints.

### Behaviour change: duplicate check

- The "same employee, vendor, amount and date" duplicate check now compares the vendor name as text.
- Before, it only worked when the vendor matched the vendor list, so bills with an unmatched vendor were never checked. Now every bill is checked.
- Older bills that were linked to a vendor record still match by that vendor's name.

### Code

**Backend**
- `services/transaction_service.py`
  - New bills and draft edits save the vendor name in `vendorRawText` and leave `vendorId` empty.
  - New helper `vendor_display_name(txn)` returns the bill's vendor text, or the linked vendor's name on older bills.
  - `_find_duplicate` compares vendor text.
  - `vendor_unmatched` was removed from the claim API.
- `services/approval_service.py`
  - `resolve_vendor` was removed.
  - Bulk approve at the Accountant stage no longer skips bills with an unmatched vendor; it still skips possible duplicates.
- `api/routes_approvals.py`: `POST /api/approvals/{id}/resolve-vendor` was removed.
- `api/routes_claims.py`: `GET /api/vendors` was removed. It was a read-only list that only fed the resolve picker.
- `api/routes_config.py` and `services/config_service.py`: `GET/POST /api/admin/config/vendors` and `DELETE /api/admin/config/vendors/{id}` were removed.
- `services/ocr_service.py`: the old text-OCR path no longer loads vendor names as hints. The live GPT-vision scanner never used them.
- `services/email_templates.py`: the vendor name comes from the bill text, with a fallback to the linked vendor on older bills.
- `scripts/seed_phase1_reference_data.py`: no longer seeds sample vendors.

**Flutter app**
- `api/api_client.dart`: `resolveVendor()` and `vendors()` were removed.
- `api/models.dart`: `ExpenseClaim.vendorUnmatched` and `VendorRef` were removed.
- `approvals/approval_detail_screen.dart`: the vendor resolve card and the unmatched-vendor notice were removed.
- `web/dashboard_screen.dart` and `web/all_claims_screen.dart`: the unmatched-vendor group, flag and filter were removed.

**Web-admin**
- `api/client.ts` and `api/types.ts`: `resolveVendor`, `vendors`, `VendorRef` and `vendor_unmatched` were removed.
- Pages: the vendor resolver was removed from `ClaimDetailPage.tsx`, and the vendor tags, filter and CSV column were removed from `ClaimsPage.tsx`, `ApprovalsPage.tsx` and `DashboardPage.tsx`.

**Docs:** `README.md` and `web-admin/README.md` no longer list the removed endpoints.

### Checks

- Backend tests: 339 passed, 5 skipped, 2 expected failures. The API loads cleanly.
- Flutter analyze on the changed files found no errors.
- Web-admin was not compiled because its packages aren't installed on this machine. It was checked by hand for leftover references.

### Database

- No migration is needed. `vendorRawText` already exists.
- New bills leave `vendorId` empty. Older bills keep their `vendorId` and still show that vendor's name.

### Left for later

- **The `ErpExpenseVendor` table is still in the database.**
  - Older bills still point to it, and the duplicate check uses those names for those bills.
  - Nothing adds or edits rows in it any more.
  - To drop it: write a one-time script that copies each linked vendor's name into the bill's `vendorRawText`. Then remove the `vendorId` column, the `vendor` relationship and the table, along with the old-row fallbacks in `vendor_display_name`, `email_templates._vendor_name` and `_find_duplicate`.
- **Old history rows** with the action `vendor_resolved` stay in the log. They are hidden from approver history, and the web dashboard still has an icon for them.
- **Older plan docs** that described the removed feature (`PETTY_CASH_PHASED_PLAN.md` Phase 4, `ACCOUNTANT_HOD_WEB_APP_PLAN.md`) now mark it as removed (2026-11-04).
