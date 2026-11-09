# Professional Signs (KSA) — employee PCA compared with this app

Source: `PCA_Professional_Documentation.pdf` (Petty Cash Advance (PCA), Process Flow & Approval Procedure, 2 pages).
Company in this app: **KSA = Professional Signs** (`seed_phase1_reference_data.COMPANY_BY_REGION`). The ERP subsidiaries `Prosigns KSA` and `BRI PS Saudi` both map to KSA (`auth/security.ERP_SUBSIDIARY_TO_REGION_CODE`).
Companion to [`BRI_DEPARTMENT_PETTY_CASH.md`](BRI_DEPARTMENT_PETTY_CASH.md), which covers the Dubai department model this app was built around.

Every "app today" statement was checked against the code on 2026-11-04 (branch `indra`), **before** the build. Sections 3 and 4 describe the app as it was then.

> **Status 2026-11-05: backend and app built, then simplified after the team's answers** (see [`CHANGELOG.md`](CHANGELOG.md)). Decisions:
> - **Bills: Employee → own HOD → Accounts Manager.** There is no Accountant step in KSA. The Accounts Manager records the EJV / EJVB journal when approving, and pays.
> - **Q2 / Q10 (decided 2026-11-05): one advance per employee, usable for any project.** It isn't tied to an OP code. **The HOD sets the amount and it's live at once.** The PCA is a limit, so the Accounts Manager doesn't approve or pay it. The Accounts Manager only pays top-ups (against approved bills) and reimbursements. Every KSA bill (petty cash or reimbursement) still needs a project OP code, for the project-wise report. A bill's lines may name different projects.
> - Q1: top-ups follow the PDF: HOD approves → Accounts Manager verifies → Accounts Manager pays (cash withdrawal from bank, or direct payment by Accounts).
> - Q3: a petty-cash bill over what's left is blocked; the extra is filed as a reimbursement.
> - Q5: the "respective HOD" (the employee's own) approves, and the whole bill comes off their advance.
> - Q4 and Q7: payment source is recorded, with no balance tracked for the Accounts Department's account. Accounts Manager = `finance_manager` and is the **only** payer in KSA. Accountants have no KSA step.
> - Employees without an advance (e.g. Sajil, Hyder, Hema, who pay from their own cash) file reimbursements.
> - Q6, Q8 and Q9 are still open.

---

## How advances, employees and projects link (as built)

An advance belongs to **one employee in one company**: one `ErpExpensePettyCashFund` row per (company, employee), with no OP code. Every bill names a project OP code, which is used only for reporting.

| Case | Result |
|---|---|
| Ahmed has an advance and submits a petty-cash bill for OP-2201 | Comes off **his** advance |
| Ahmed submits a petty-cash bill for OP-2215 next | Also comes off the same advance |
| One bill with lines for OP-2201 and OP-2215 | Allowed, and comes off the one advance. The project report splits it by line |
| Salim has no advance | Petty cash blocked ("You don't have a petty cash advance in this company…"); he files a reimbursement |
| A bill (petty cash or reimbursement) with no OP code | Blocked on submit: "Enter the project OP code" (or one on every item) |
| HOD sets Ahmed's petty cash again | His one PCA becomes the new amount, straight away (not below his bills not yet topped up) |

**Report (Advances → By department / By project):** By department lists each employee's advance, what's available, what's spent and what's waiting. By project adds up petty-cash bills by the OP code on each line (spent, and in approval), with the employees who spent on it.

**Not checked (open):**
- The OP code is looked up in ERP as you type on the bill screen, but the server only checks that one is filled in. It doesn't check that the code exists in ERP or that the employee is on that project.

Possible tightening, if Professional Signs wants it: check every OP code against ERP on submit.

---

## 1. The Professional Signs flow in brief

| # | Step | Who |
|---|---|---|
| 1 | Decide the advance (PCA) for an **employee**, sized to the project. There is **no fixed limit** | HOD proposes; **Accounts Manager** gives final approval |
| 2 | Pay the advance, usually by **bank transfer**, or directly from the **Accounts Department's own petty cash account** | Accounts Department |
| 3 | Employee spends and submits bills, usually once about **50%** of the advance is used (e.g. SAR 5,000 of SAR 10,000) | Employee |
| 4 | Verify and approve the bills | **HOD** |
| 5 | Book the journal: **EJV**, or **EJVB** for a multi-branch transaction | **Accounts team** |
| 6 | Final approval of the EJV | **Accounts Manager** |
| 7 | Top up the PCA: either (1) cash withdrawal from the bank, or (2) direct payment by the Accounts Department | Accounts Manager verifies; Accounts Department pays |
| — | Employees with **no advance** (e.g. Sajil, Hyder, Hema) pay with their own money and are **reimbursed** | Same approvals, then payment |

## 2. Professional Signs compared with BRI (Dubai)

| Topic | BRI (Dubai), built | Professional Signs (KSA) |
|---|---|---|
| Who holds the cash | The **department** | The **employee** (advance) |
| Limit | Approved department limit set by Admin | No fixed limit; an amount per employee, sized to the project, set by HOD and Accounts Manager |
| Bill approvals | HOD → (other department's HOD) → Accountant → Finance Manager | HOD → Accounts team (books EJV/EJVB) → Accounts Manager |
| Top-up raised by | HOD, with the approved bills | Follows the approved bills; Accounts Manager verifies, Accounts Department pays |
| Paid from | One common petty cash bank account | Bank (withdrawal or transfer) **or** the Accounts Department's petty cash account |
| Reimbursement | Separate type that doesn't touch the pot | Same: separate path for employees with no advance |

## 3. What the app does today, and the gaps for Professional Signs

### 3.1 Data model: mostly there

| Need | App today | Gap |
|---|---|---|
| Pot per employee | `ErpExpensePettyCashFund.ownerType = 'employee'` is supported and blocked only for DUBAI (`fund_service.create`). The employee's bills come off their own pot and never off the department pot (`_fund_portion`, `_fund_bills`) | None in the backend |
| Advance math | Employee pot: `remaining = limit + replenished − spent`, which is the same as `limit − unreplenished` unless Admin credits extra | None. `openingBalance` = advance amount |
| Advance approved by HOD → Accounts Manager | **None.** Admin types the amount directly (`POST /api/admin/funds`, `PUT /api/admin/funds/{id}`) | **G1.** Need an *advance request*: HOD proposes → Accounts Manager approves → paid. Reuse `ErpExpenseFundTopupRequest` with a `kind` column (`advance` \| `topup`); it already has requester, status, verify, decide, payment and history |
| Advance tied to a project | One pot per (company, employee). No `projectId` on the fund | **G2.** Only if an employee can hold several advances at once (see Q2) |
| "No fixed limit" | A petty-cash bill is **hard-blocked** if it's more than what's left of the advance (`require_petty_cash_within_limit`) | **G3.** Decide what happens when bills exceed the advance (Q3) |

### 3.2 Bill approvals

| Need | App today | Gap |
|---|---|---|
| HOD → Accounts → Accounts Manager | Stages come from each company's `approvalMatrixJson.stages`; the default is `hod, accountant, finance_manager`, which already fits | None. Map Accounts team = `accountant` role and Accounts Manager = `finance_manager` role |
| Stage names "Accounts (EJV)" and "Accounts Manager" | Names are hardcoded (`approval_service.resolve_stage_labels`: "Accountant", "Finance Manager") | **G4.** Read optional `stage_labels` from the company's approval matrix |
| Accounts books the EJV or EJVB | The Accountant just approves, with an optional comment | **G5.** At the Accountant stage for KSA, ask for **journal type (EJV/EJVB)** and **journal number**. Store them on the bill (new columns) and show them to the Accounts Manager |
| Approval by the "respective HOD" only | **Bills are split across departments:** an IT-category line on a KSA bill is charged to the **IT department pot** and adds an IT HOD stage (`department_split`, `require_bill_within_limits`) | **G6 (breaks today).** If KSA has no IT department pot, the submit fails with *"This bill has IT items, but no petty cash limit is set for IT"*. Add a per-company switch (e.g. `cross_department_split: false`) so the whole bill comes off the employee's advance (Q5) |

### 3.3 Top-up

| Need | App today | Gap |
|---|---|---|
| Top up an **employee's** advance | Top-ups are department-only. Admin is blocked on non-department pots (`request_topup`: *"Top-ups are raised for department petty cash"*), and an HOD can only use pots in `_my_fund_ids`, which covers their departments and their own pot, **not their staff's pots**. The Flutter top-ups screen lists department pots only (`topups_screen.dart:161`, `:706`) | **G7.** Allow top-ups on employee pots and decide who raises them (Q1) |
| Chain: HOD → Accounts Manager → payment | Chain: HOD request → **Accountant** verify → **FM** approve + payment | **G8.** For KSA the Accounts Manager verifies and the Accounts Department pays. Either make the top-up chain configurable per company, or skip the top-up chain and treat it as a payment (Q1) |
| Paid by bank withdrawal **or** the Accounts Department's petty cash | `paymentMethod` is bank_transfer / cash / payroll / cheque, with no "paid from" | **G9.** Add a **paid-from** field (`bank`, `accounts_petty_cash`) to top-ups and payments. Optionally keep the Accounts Department's own petty cash as a department pot so its balance is tracked (Q4) |
| Who pays | Payments require the `finance_manager` role (`routes_payments.require_payer`) | **G10.** If the Accounts Department (Accountant role) pays in KSA, the payer role must be configurable per company |

### 3.4 Employee and Admin screens

| Need | App today | Gap |
|---|---|---|
| Admin gives an employee an advance | The Admin company screen creates **department** pots only (`admin_company_screen.dart:106`) | **G11.** UI for "Employee advances" in KSA: list, give, change, and close an advance |
| Employee sees their advance | `my_funds_screen.dart:34` shows department pots only. The confirm screen does find an employee pot (`confirm_claim_screen.dart:163`) | **G12.** Show the employee's own advance (amount, spent, waiting for top-up, left) |
| "Submit at ~50%" | The low-fund alert is for department pots only, at 20% left (`check_low_fund`, `LOW_FUND_RATIO = 0.20`) | **G13.** For employee pots, remind the employee (and HOD) once **50%** is spent: "submit your bills" |
| No-advance employees use reimbursement | The type picker shows both options and defaults to reimbursement. A KSA employee with no advance who picks petty cash falls back to the department pot, or gets "no limit set" | **G14.** In KSA, offer **petty cash only to employees who have an advance** |

## 4. Proposed build (order)

1. **Company settings (no UI change for Dubai):** add to KSA's `approvalMatrixJson`:
   ```json
   {"stages": ["hod", "accountant", "finance_manager"],
    "stage_labels": {"accountant": "Accounts (EJV)", "finance_manager": "Accounts Manager"},
    "pca_model": "employee",
    "cross_department_split": false,
    "journal_required_at": "accountant",
    "payer_roles": ["accountant", "finance_manager"]}
   ```
   Read these in `approval_service`, `department_split`/`fund_service` and `routes_payments`. Use the existing unused `allocationModel` column, or `pca_model` inside the JSON. Covers G4, G6 and G10.
2. **Journal fields** (G5): add `journalType` and `journalReference` to `ErpExpenseTransaction`, plus an ALTER script. Require them when an Accountant approves at a company with `journal_required_at`, and show them in detail views and emails.
3. **Employee advances** (G1, G11, G12, G14): `kind = advance` on `ErpExpenseFundTopupRequest`. HOD proposes for a staff member → Accounts Manager approves with payment details → the employee pot's `openingBalance` is set or raised. Add the Admin/HOD "Advances" screen, the employee's "My advance" card, and limit the petty-cash choice to employees with an advance.
4. **Top-ups for employee advances** (G7, G8, G9): see Q1 for the shape. Add a `paymentSource` field.
5. **50% reminder** (G13): extend `check_low_fund` to employee pots, using a per-company threshold.
6. Tests for each step in `tests/test_funds_and_regions.py` and `tests/test_topup_flow.py`, plus checks that Dubai behaves exactly as before.

## 5. Questions for the Professional Signs team (answers change the build)

| # | Question | Proposed default |
|---|---|---|
| Q1 | **How is a top-up triggered?** (a) Automatically: once the Accounts Manager approves the bills, they wait in a "To top up" list and the Accounts Department records the payment, which tops up the advance. (b) A separate request (employee or HOD raises it with the approved bills → HOD → Accounts Manager → payment), as in the PDF's Process 1/2 | **(a).** The PDF's steps 1–2 (HOD, Accounts Manager) are the same approvals the bills already had, so a second chain repeats them |
| Q2 | Can one employee hold **more than one advance** at once (one per project)? | **Decided 2026-11-05: no.** One advance per employee, used for any project (see "How advances, employees and projects link") |
| Q3 | "No fixed limit": if bills are **more than the advance**, block, allow the extra as a reimbursement, or allow and owe the employee? | Block the petty-cash part, and tell them to file the extra as a reimbursement |
| Q4 | Should the app track the **Accounts Department's petty cash account balance**, or just record that a payment came from it? | Just record it (a paid-from field) |
| Q5 | Does a KSA bill with IT or other departments' items need **that department's HOD** too, and should it come off that department's money? | No: the employee's own HOD only, and the whole bill comes off the employee's advance |
| Q6 | **EJV vs EJVB:** what makes a bill "multi-branch"? Are the branches the two ERP subsidiaries (`Prosigns KSA`, `BRI PS Saudi`) or KSA cities? Should the app pick the type, or does Accounts choose? | Accounts chooses EJV/EJVB and types the journal number |
| Q7 | Is the Accounts Manager the same person as the Finance Manager role in the app, and who in the **Accounts Department** records payments (Accountant role)? | **Decided 2026-11-05:** Accounts Manager = `finance_manager`, who approves bills, books the EJV and pays. No Accountant step in KSA |
| Q8 | Does this apply to **Oman** (`Prosigns Oman`) too? | KSA only, until confirmed |
| Q9 | When an employee leaves or a project ends, how is the advance **settled** (bills plus cash returned)? | Add later: a "close advance" action that records the bills and the cash returned |
| Q10 | **Decided 2026-11-05: an advance is held by one employee, for all their projects** (neither per project nor a shared project pot). Original question: When a PCA is given, is the cash handed to **one employee** for their project, or kept as **one pot for the whole project** that several employees spend from? The PDF's §2 says the amount is "determined according to the requirements of the relevant project"; §3, §5 and §8 speak of an "employee receiving a PCA". | **Built as one employee + one project** (A). If the team says one pot per project (B), the advance changes to belong to the OP code; anyone on that project spends from it, and the HOD proposes and tops up per project. |
