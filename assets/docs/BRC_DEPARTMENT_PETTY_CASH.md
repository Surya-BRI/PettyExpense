# Blue Rhine Contracting — Employee petty cash vs this app

Source: *Petty Cash Advance (PCA) – Replenishment Process* (BRC, 1 page). Responsible person: Roshan Stanly.
Entity in this app: **UAE / Blue Rhine Contracting** (`pca_model: "site"` in its approval matrix).

**Decisions (2026-11-12):**
- BRC has **no HODs**. Bills and top-ups go **Accountant → Head of Accountant → Finance Manager**.
- **One petty cash per employee**, for all their sites. The Accountant sets it.
- Employees submit bills, and every bill names its **site (project OP code)** for site-wise reporting.
- The Accountant prepares the top-up (PCA) from the employee's approved bills.

---

## 1. BRC process (from the PDF)

| Step | Stage | Action |
|---|---|---|
| 1 | PCA limit | Approved limit: 5,000 |
| 2 | Bills submission | Submit bills totalling 1,000 (example) |
| 3 | Prepare PCA | Prepare the PCA based on submitted bills |
| 4 | Verification | Verify bills and supporting documents; Verifier approval |
| 5 | Financial Manager approval | Financial Manager approval |
| 6 | Initiate cash in bank | Cash withdrawal from the bank for reimbursement |
| 7 | Top-up PCA | Replenish the spent amount to restore the limit |

| PCA position | Amount |
|---|---|
| Original PCA limit | 5,000 |
| Bills / cash withdrawal | 1,000 |
| Balance before top-up | 4,000 |
| Limit after top-up | 5,000 |

---

## 2. How the app runs it

| PDF step | In the app | Who |
|---|---|---|
| 1 | Petty cash → **Set petty cash**: pick the employee, enter the amount. Live at once | Accountant (or Admin) |
| 2 | Employee submits a petty-cash bill with its site's OP code. It goes **Accountant → Head of Accountant → Finance Manager**, then comes off the employee's petty cash (5,000 → 4,000) | Employee, then approvers |
| 3 | Petty cash → employee's card → **Prepare top-up**: tick the approved bills; amount = their total | Accountant |
| 4 | Top-ups tab → **Approve** (or Reject with a reason) | Head of Accountant |
| 5–6 | Top-ups tab → **Approve & record payment**: method, bank reference, date | Finance Manager |
| 7 | Petty cash back to its limit (4,000 → 5,000) | System |

Rules:
- A petty-cash bill is blocked if the employee has no petty cash, or the bill is more than what's left (bills still in approval count as used). The employee can submit it as a reimbursement instead.
- The amount can't be set below the employee's bills not yet topped up.
- Below 20% left, the employee and the Accountant are told to prepare a top-up.
- Reimbursements follow the same three approval steps; the Finance Manager pays them from Payments.

Approvals and labels come from the company's matrix (`region_policy.SITE_PCA_SETTINGS`): `stages: [accountant, head_accountant, finance_manager]`, no department split, `payer_roles: [finance_manager]`. The startup seed applies it to UAE (`SITE_PCA_REGIONS`) and moves bills waiting at the old HOD step to the Accountant.

---

## 3. Roles

| App role | Who | How they get it |
|---|---|---|
| Accountant | Sets petty cash, first approval, prepares top-ups | ERP role "Accountant" (102055) |
| Head of Accountant (`head_accountant`) | Second approval of bills and top-ups | Admin → People → **App role**. Or automatically from an ERP role named "Head of Accountant" / "Head of Accounts" / "Head Accountant" / "Chief Accountant" (ERP has none yet) |
| Finance Manager | Final approval, records the bank withdrawal | Admin → People → **App role** |

Admin → Companies → Blue Rhine Contracting → Approvers shows who holds each step.

---

## 4. Setup

- **BRC staff must be under the BRC company in ERP.** ERP subsidiary `BRC` (Blue Rhine Contracting LLC) maps to the app's UAE company (`auth/security.py`). On ERP-Dev (2026-11-12) we added region 46 "BRC UAE" under subsidiary 10 and moved the test users `BRChod` (9036) and `BRCAccount` (9037) into it. ERP-Live needs the same: a region under BRC, with BRC staff in it. Anyone else can be ticked for Blue Rhine Contracting in Admin → People.
- Set a **Head of Accountant** and a **Finance Manager** for Blue Rhine Contracting (Admin → People → App role).
- The Accountant sets each employee's petty cash.
- Department pots left on UAE from before are no longer used.

---

## 5. Code

- `services/region_policy.py`: `SITE_MODEL`, `SITE_PCA_SETTINGS`, `apply_site_settings`, `is_site_model`.
- `services/site_pca_service.py` + `api/routes_site_pca.py` (`/api/site-pca/...`): people, pots, set, replenishable bills, prepare top-up, approve, pay, reject.
- `services/fund_service.py`: a BRC bill comes off the employee's one petty cash (`_fund_portion`); submit check `_require_site_pots`; low alert to the employee and Accountant.
- `auth/security.py`: role `head_accountant`, `APPROVER_ROLES`. `PUT /api/admin/users/{id}/role` (Admin).
- App: `features/pca/site_pca_screen.dart` (Petty cash: Employees · Top-ups), claim form (OP code required, checked against the employee's petty cash), Head of Accountant queue, Admin → People App role, BRC approvers on the company page.
- Tests: `backend/tests/test_site_pca.py`.
