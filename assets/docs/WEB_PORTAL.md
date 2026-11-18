# Web portal: relation to this repo

> Short pointer for developers working in this repo (`d:/expense_app`: Flutter app + FastAPI
> backend). The full guide to the web portal (screens, flows, endpoints, deploy) is in the web
> repo: **`d:/expense_app_web/WEB_PORTAL.md`** (`Surya-BRI/expense_web`). Last updated: 18 Nov 2026.

## What exists

| | Where | Status |
|---|---|---|
| **Web portal** (React + Vite, Vercel) | `d:/expense_app_web` · repo `Surya-BRI/expense_web` | **Current**: HOD, Accountant, Finance Manager, Admin |
| Flutter app (+ its `kIsWeb` dashboard) | this repo, `lib/` | Current: all roles; the only frontend for employees |
| `web-admin/` (in this repo) | this repo | **Old**: first React build, superseded by `d:/expense_app_web` |
| `ACCOUNTANT_HOD_WEB_APP_PLAN.md` | `assets/docs/` | Historical plan for the first version |

## How they fit together

- **One backend** (`backend/`), one database (ERP-Dev), one set of logins. The app and the web
  portal are two frontends on the same API (`https://expensetracker-api.app-brisigns.com`).
- **Rules live in the backend.** Approval steps, petty cash, SLA, backups, payments: change
  them once in `backend/` and both frontends follow.
- **Screens are built twice.** A new screen or button goes into the app (`lib/src/features/...`)
  **and** the web portal (`src/features/...`). The web guide lists the matching file for each.

## Features and where they live

| Feature | Backend | App | Web portal |
|---|---|---|---|
| Approval queue / decide | `services/approval_service.py` | `approvals/approval_queue_screen.dart`, `approval_detail_screen.dart` | `features/approval-queue`, `features/claim-detail` |
| Payments (Spec 5.5) | `services/payment_service.py`, `POST /api/payments` | `payments/payment_sheet.dart` | `features/payments/PaymentsPage.tsx` (`RecordPaymentDialog`) |
| SLA time + escalation (PG-10) | `services/sla_service.py`, `GET/PUT /api/admin/config/regions/{id}/sla` | `admin/approval_time_limits_card.dart` | `features/admin/SlaTimeDialog.tsx` |
| Aging report | `GET /api/admin/reports/aging` | `admin/aging_report_screen.dart` | `features/admin/AgingReportPage.tsx` |
| Backup approvers (Spec 5.2) | `services/delegation_service.py` | `approvals/backup_approver_screen.dart` | `features/backup/*`, `features/admin/PersonPage.tsx` |
| Petty cash "held" figure | `services/fund_service.py` (`uncommitted`, `pending_bills`) | `widgets/app_nav_drawer.dart` | `features/profile/ProfilePage.tsx` |
| Alerts (incl. SLA + backup) | `services/notification_service.py` | `notifications/notifications_screen.dart` | `features/notifications/AlertsPage.tsx` |
| BRC site petty cash | `routes_site_pca.py`, `services/site_pca_service.py` | `pca/site_pca_screen.dart` | `features/site-pca/*` (`/site-pca`) |
| KSA advances + Accounts cash | `routes_pca.py`, `services/employee_pca_service.py`, `accounts_cash_service.py` | `pca/advances_screen.dart`, `pca/accounts_cash_view.dart` | `features/advances/*` (`/advances`) |
| KSA journal (EJV/EJVB) at approval | `approval_service._record_journal` | `approvals/approval_detail_screen.dart` | `features/claim-detail/DecisionActions.tsx` |
| Head of Accountant (BRC) queue | `approval_service` | `role_routes.dart` | `routing/roleLanding.ts` |
| Company logo upload | `services/logo_image.py` | `admin/admin_regions_screen.dart` | — (app only) |
| Offline bill queue | — | `services/offline_bills/*` | — (scanning is app only) |

## Flows in one place

Approval steps per company, petty cash vs reimbursement, payments, SLA, backups and alerts are
described in `d:/expense_app_web/WEB_PORTAL.md` §3. Short version:

- **BRI / Oman:** HOD → Accountant → Finance Manager. **BRC:** Accountant → Head of Accountant →
  Finance Manager. **Professional Signs:** HOD → Accounts Manager.
- **Petty cash** is taken off at the Finance Manager's approval; no payment step (except
  Professional Signs, where paying refills the employee's advance). **Reimbursements** go to
  Payments after the final approval.
- **SLA:** overdue alert to the approver after the SLA time; escalation to the next step + Admin
  after one more SLA time.
- **Backups:** same company, same level or higher, same-department HOD only; bills go to the
  backup during the dates and come back afterwards.

## When you change something

1. Backend change + tests (`backend/tests`), deploy the backend first.
2. App screen here; web screen in `d:/expense_app_web`.
3. Update both docs: this file and `d:/expense_app_web/WEB_PORTAL.md`.
