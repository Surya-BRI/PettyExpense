# Blue Rhine Industries — Department petty cash vs this app

Source: `BRI_Consolidated_Petty_Cash_PCA_Reimbursement_Workflow 1.pdf` (BRI process overview, 3 pages).  
Entity in this app: **DUBAI / Blue Rhine Industries**. Petty cash is **department-level**, never per employee.

---

## 1. BRI rule in one table

| Topic | BRI rule |
|---|---|
| Who holds the money | The **department**, not the employee |
| What Admin sets | An **approved cash limit** per department (example: HR 5,000) |
| Monthly reset | **No.** Limit stays until Admin changes it |
| When money comes back | **Top-up / PCA replenishment** after bills are verified |
| How much is topped up | Equal to **submitted bills** (spend 1,000 → top up 1,000 → back to 5,000) |
| Bank | **One common petty cash bank account** for all BRI departments |
| Multi-region | **Not used for BRI.** Blue Rhine Contracting (UAE) has its own flow (no HODs, one petty cash per employee); see [`BRC_DEPARTMENT_PETTY_CASH.md`](BRC_DEPARTMENT_PETTY_CASH.md) |
| Reimbursement | Separate path: employee paid personally, company pays them back, still checked against the **department limit** |

---

## 2. Petty cash vs reimbursement (BRI)

| | Petty cash (PCA) | Reimbursement |
|---|---|---|
| Whose money first | Company (department float) | Employee’s personal money |
| Who spends | Anyone in that department, against the department pot | The employee |
| After approval | Department pot is **replenished** | Employee is **repaid** |
| Limit | Department approved limit | Same departmental limit is still checked |
| BRI example | HR limit 5,000, bills 1,000, top-up 1,000 | Employee buys, submits receipt, Finance pays the employee |

---

## 3. Petty cash top-up / PCA flow (BRI)

| Step | Who | What happens | HR example (limit 5,000) |
|---|---|---|---|
| 1 | Admin / Finance | Set approved departmental PCA limit | Limit = 5,000 |
| 2 | Department | Spends from the float, keeps bills | Bills = 1,000 |
| 3 | Department | Submits bills and raises a top-up / PCA request | Request 1,000 |
| 4 | Accounts (Verifier) | Verifies bills and documents | Status = verified |
| 5 | Finance Manager | Approves the request | Status = approved |
| 6 | Finance | Bank transfer / cash withdrawal from the **common** petty cash account | Payment ref |
| 7 | System | Credit the department pot by the approved amount | +1,000 |
| 8 | System | Available balance returns to the approved limit | 5,000 again |

Limit does **not** change. Top-up restores what was spent.

| PCA calculation | Amount |
|---|---|
| Approved PCA limit | 5,000 |
| Submitted bills / expenses | 1,000 |
| Balance before top-up | 4,000 |
| Approved top-up | 1,000 |
| Available after top-up | 5,000 |

Formula BRI wants:

```
available = approved_limit - unreplenished_spend
unreplenished_spend = submitted petty-cash bills not yet topped up
top_up_amount = those bills (after Accounts + FM)
after top-up: available = approved_limit again
```

---

## 4. Employee reimbursement flow (BRI)

| Step | Who | What happens |
|---|---|---|
| 1 | Employee | Pays with personal funds, keeps the bill |
| 2 | Employee | Submits reimbursement in the module |
| 3 | Accounts | Checks documents **and** departmental limit |
| 4 | Finance Manager | Approves |
| 5 | Company | Pays the employee (not the department pot) |

---

## 5. Modules and fields the PDF asks for

| Module | Purpose | Suggested fields |
|---|---|---|
| Department petty cash | One pot + limit per department | Subsidiary, Department, Approved Cash Limit, Available Balance, Expense Amount, Supporting Bills, Transaction Reference |
| Expense + top-up | Record spend, attach bills, replenish | Department, Expense Date, Expense Category, Amount, Bill Attachment, Top-Up Amount, Verification Status, Approval Status, Payment Reference |
| Employee reimbursement | Personal spend repaid | Employee, Department, Expense Date, Purpose, Claimed Amount, Receipt, Approved Amount, Approval Status, Payment Status |
| Project / region (BRC only) | Not for BRI Industries | Subsidiary, Project, Derived Region, Region Selection |
| Finance control | One bank, many departments | Department-wise balances, history, bill verification, approval tracking, payment reconciliation |

---

## 6. Difference: PDF vs this app today

| BRI PDF | This app today | Gap |
|---|---|---|
| One pot **per department** | `ErpExpensePettyCashFund` allows `ownerType` department **or** employee | Hide/stop individual pots for DUBAI / BRI |
| **Approved limit** (5,000) never moves on top-up | `openingBalance` + approved top-ups. Top-up **increases** remaining above opening | Need `approvedLimit` separate from remaining. Top-up restores to limit, it does not raise the limit |
| Remaining = limit − unreplenished spend | Remaining = opening + credited − spent | Same idea if top-up = spent, but Admin “credit extra” would break BRI |
| Top-up is raised **against submitted bills** | Top-up is a free amount HOD/Admin types | Link top-up rows to claim/bill IDs; default amount = those bills |
| Accounts **then** Finance Manager | HOD/Admin request → FM/Admin decide. No Accounts verification stage on the top-up | Add verifier (accountant) stage on top-up |
| HOD is not the person who “owns” the float | HOD can request top-up for their department | Keep HOD as requester; Accounts verifies; FM approves |
| Common bank account, payment reference | No payment record on top-up (only status approved/rejected) | Add payment method + reference + date on approved top-up |
| Reimbursement is a **different** path | `ErpExpenseTransaction.type` is already `petty_cash` \| `reimbursement` | Petty cash should debit the **department pot**. Reimbursement should **not** debit the pot; it still checks the department limit |
| BRI ignores multi-region | App is region-based (DUBAI / UAE / KSA / OMAN) | For BRI (DUBAI) ignore extra region picking on petty cash. Keep region on the fund row so KSA/OMAN can differ later |
| Departments from operations (HR, Acrylic, …) | Local `ErpExpenseDepartment` now syncs ERP names for BRI UAE | Keep using ERP department names; one fund row per (DUBAI, department) |
| Show limit, expenses, available, pending top-up, approval, replenishment | Admin list shows opening + remaining; employee sees remaining | Show **limit**, **spent pending replenishment**, **available**, **pending top-up** |

Worked example mapped to **current** math (wrong for BRI if we keep adding top-ups on top of opening):

| Event | BRI available | App today if opening=5000 and we also credit a 1000 top-up |
|---|---|---|
| Set limit 5,000 | 5,000 | 5,000 |
| Bills 1,000 | 4,000 | 4,000 |
| Top-up 1,000 approved | **5,000** (limit unchanged) | **6,000** if we treat top-up as extra credit on opening |

That last row is the important mismatch. For BRI, top-up replaces spend; it does not increase the limit.

---

## 7. How tables should work (department-based)

Keep existing tables. Do **not** create a new fund table. Shape DUBAI / BRI to match the PDF.

### 7.1 Use these tables

| Table | Role for BRI |
|---|---|
| `ErpExpenseDepartment` | Acrylic, HR, Installation, … (from ERP names) |
| `ErpExpenseRegionConfig` | DUBAI = Blue Rhine Industries |
| `ErpAuthExpenseUsers.departmentId` | Puts each employee/HOD on one department pot |
| `ErpExpensePettyCashFund` | **One row per department in DUBAI.** `ownerType = department` only |
| `ErpExpenseTransaction` | Petty-cash bills **debit** that department pot. Reimbursement bills do **not** |
| `ErpExpenseFundTopupRequest` | PCA replenishment: amount + bills + Accounts verify + FM approve + payment |
| `ErpExpenseHodAssignment` | Which HOD may request top-up for which department |

### 7.2 `ErpExpensePettyCashFund` — columns to treat as BRI

| Column (now) | BRI meaning | Change |
|---|---|---|
| `regionId` | Always DUBAI for BRI | Keep |
| `ownerType` | Always `department` | Do not create `employee` rows for DUBAI |
| `departmentId` | The department the pot belongs to | Required, unique with region |
| `employeeId` | Not used for BRI | Leave null |
| `openingBalance` | **Approved PCA limit** | Rename in UI to “Approved limit”. Admin sets/changes this only |
| `currency` | AED | Keep |
| *(computed)* remaining | **Available balance** | `limit − petty_cash_spend_not_yet_replenished` |
| *(computed)* spent | Submitted petty-cash bills in this department + region | Only `type = petty_cash` |
| *(new or on top-up)* pending top-up | Sum of `submitted` top-up requests | Show on the department card |
| *(do not add into remaining)* approved top-up | Marks those bills as replenished | **Do not add on top of the limit** |

Unique key for BRI: `(regionId, departmentId)` where `ownerType = department`.

### 7.3 `ErpExpenseFundTopupRequest` — PCA replenishment

| Column (now) | BRI meaning | Change |
|---|---|---|
| `fundId` | Department pot | Keep |
| `amount` | Should equal attached bills | Default from selected bills |
| `requesterId` | Department HOD (or Admin) | Keep |
| `status` | `submitted` → `verified` → `approved` / `rejected` | Add **Accounts verify** before FM |
| `remarks` | Reason | Keep |
| `decidedBy` / `decidedOn` | FM | Keep |
| *(needed)* `verifiedBy` / `verifiedOn` | Accounts / Verifier | Add |
| *(needed)* bill / transaction ids | The 1,000 of supporting bills | New link table or JSON list |
| *(needed)* `paymentReference`, `paymentDate`, `paymentMethod` | Common bank account movement | Add after FM approve |

Suggested small new table (only if we do not stuff IDs on the request):

| Table | Columns | Why |
|---|---|---|
| `ErpExpenseFundTopupBill` | `topupId`, `transactionId`, `amount` | Ties the 1,000 of bills to the PCA request so Finance can reconcile |

### 7.4 Claims vs the department pot

| Claim `type` | Hits department **available**? | Notes |
|---|---|---|
| `petty_cash` | **Yes** — reduces available until topped up | Company float |
| `reimbursement` | **No** — does not reduce the float | Still **warn/block** if it would exceed the department limit (PDF: “checked against the departmental limit”) |

### 7.5 Who does what

| Role | Department funds |
|---|---|
| Admin | Set/change **approved limit** per department (DUBAI list). Can raise a top-up. Does not land on HOD queue |
| Employee in Acrylic | Sees Acrylic limit + available. Submits petty-cash bills (debits Acrylic) or reimbursement (personal) |
| HOD of Acrylic | Same balances. Raises top-up for Acrylic (and any extra assigned departments) |
| Accountant / Verifier | Verifies bills on the top-up (and on claims as today) |
| Finance Manager | Approves top-up and reimbursement; payment is recorded against the common petty cash account |

---

## 8. Screen mapping (so testers find it)

| BRI words | Where in this app |
|---|---|
| Region / company / logo | Admin → **Regions** → tap Dubai → company name + upload logo |
| Department PCA module | Admin → **Department funds** (Dubai chip) — one card per ERP department |
| Approved cash limit | **Set up opening / Change opening** on that card (treat as limit) |
| Available balance | Remaining on Admin card, employee **Funds**, Profile petty cash |
| Top-up request | HOD/Admin → **Top-ups** → Request top-up |
| Accounts + FM | FM (and Admin) approve on **Top-ups**. Accounts verify stage is the remaining build |
| Reimbursement | Existing claim type `reimbursement` — do not debit the department pot |

---

## 9. What to build next for BRI (order)

1. DUBAI funds are **department-only**; stop offering individual pots.
2. Treat `openingBalance` as **approved limit**. Change remaining math so approved top-ups **replenish spend** and never raise the limit above `openingBalance`.
3. Default top-up amount from selected petty-cash bills of that department.
4. Add Accounts **verify** before Finance Manager on the top-up.
5. Store payment reference on approved top-up (common bank account).
6. Keep reimbursement as a separate type that does not debit the pot.
7. Leave BRC (UAE Contracting) project→region tagging for later; it is out of BRI scope in the PDF.
