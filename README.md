# Expense Receipt App

Flutter (Android/iOS) + FastAPI for salesman expense reimbursement from bill photos.

Stack: Flutter · Riverpod · go_router · FastAPI · SQLAlchemy + **ERP-Dev SQL Server only** (no local SQLite) · JWT · local or S3 storage · stub/RapidOCR.

**Scope: UAE and KSA only** — bills are captured in **AED** or **SAR** (currency is chosen at capture time — OCR never silently defaults it, the employee must confirm AED or SAR before submitting). No India/INR support; OCR (bilingual Arabic/English via RapidOCR/ONNXRuntime) and sample data are built around Dubai (AED) and KSA (SAR) receipts only.

---

## Prerequisites

| Tool | Notes |
|------|--------|
| **Python 3.11+** | Backend |
| **ODBC Driver 17 for SQL Server** | Required — app DB is ERP-Dev only |
| **Flutter 3.x** | Frontend (`flutter doctor` should be clean enough to run) |
| **Android Studio** | Emulator or physical device for Android |
| **Git** (optional) | Clone / sync |

---

## 1) Backend setup & run

Open a terminal in the project root (`expense_app`).

### Windows (PowerShell)

```powershell
cd backend
python -m venv .venv                          # only if .venv does not exist yet
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env   # only if .env does not exist yet
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### macOS / Linux

```bash
cd backend
python3 -m venv .venv                         # only if .venv does not exist yet
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env          # only if .env does not exist yet
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Always activate `.venv` before running `pip` or `uvicorn` — the deps (FastAPI, PaddleOCR, pyodbc, etc.) live there, not in a global Python install. Re-run the `Activate.ps1` / `activate` line in every new terminal.

### Verify backend

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Leave this terminal running while you use the app.

### Login (real ERP auth)

Login validates directly against the shared ERP tables (`ErpAuthUsers` / `ErpAuthUserRoleMap` /
`ErpMasterRole` / `ErpMasterEmployee`) on ERP-Dev — sign in with a real ERP username/password.
A user needs `ErpMasterEmployee.isAllowLogin = 1` to be let in; on first successful login a
local `ErpAuthExpenseUsers` row is created for them (role defaults to `employee` unless their
ERP role maps to something higher — see `ERP_ROLE_ID_TO_APP_ROLE` in `backend/auth/security.py`).
Elevating someone to `hod`/`accountant`/`finance_manager`/`admin`, or assigning their
department, is currently done by hand against that local row (no admin UI for it yet).
The companies a person covers are set in the app (Admin → People); their home company is
saved at login.

---

## 2) Frontend (Flutter) setup & run

Open a **second** terminal in the project root. Keep the backend running.

### Install deps

```powershell
cd d:\expense_app
flutter pub get
```

### Connect Flutter → backend (`.env`)

Root file [`.env`](.env) (loaded by the app) — a single `API_BASE_URL`, **defaulting to production**:

```env
API_BASE_URL=https://expensetracker-api.app-brisigns.com
```

The file's top comments list the alternative dev URLs to copy in when you want a local backend instead:

| Where the app runs | `API_BASE_URL` |
|--------------------|----------------|
| Production (default) | `https://expensetracker-api.app-brisigns.com` |
| Android emulator, local backend | `http://10.0.2.2:8000` |
| iOS simulator / Windows / Chrome, local backend | `http://127.0.0.1:8000` |
| Physical phone, local backend (same Wi‑Fi) | `http://<your-PC-LAN-IP>:8000` |

`127.0.0.1` inside the Android emulator is the **phone itself**, not your PC — that causes `Connection refused`.

One-off override without editing the file: `flutter run --dart-define=API_BASE_URL=http://...`

### Run from terminal

```powershell
flutter devices
flutter run -d emulator-5554
```

Hits production by default (see above). Full restart after changing `.env` (not just hot reload).

**Local backend on Windows / Chrome:** set `API_BASE_URL=http://127.0.0.1:8000` in `.env`, then `flutter run -d windows`.

### Run from Android Studio

1. Open `expense_app`, start AVD, Run. Hits production by default.
2. For a local backend: set `API_BASE_URL=http://10.0.2.2:8000` in root `.env`.
3. After editing `.env`, stop and Run again (full restart).

Camera / gallery need an emulator camera or a real device; gallery works with sample images.

---

## 3) Typical first-run flow

1. Start **backend** → confirm `/health` returns `"status":"ok"`.
2. Start **emulator / device**.
3. Start **Flutter** with the correct `API_BASE_URL`.
4. In the app: sign in with a real ERP username/password (see "Login (real ERP auth)" above).
5. **New claim** → camera or gallery → confirm OCR fields → submit.
6. For approvals: sign in as a user whose role maps to `hod`/`accountant`/`finance_manager` → **Approvals queue**.

---

## Project layout

```
expense_app/
├── lib/src/
│   ├── features/   # admin (people, companies, funds, top-ups), approvals, authentication,
│   │               # claims, home, notifications, payments, pca (employee advances), profile,
│   │               # web (dashboard)
│   ├── api/
│   ├── routing/
│   ├── widgets/
│   └── theme/
├── backend/
│   ├── api/          # routes_auth, routes_claims, routes_approvals, routes_payments, routes_org
│   │                 # (regions, branding, users, funds, top-ups), routes_config, routes_admin, ...
│   ├── services/     # transaction, approval, fund, payment, region_scope, currency/exchange_rate,
│   │                 # department_split, OCR + llm_vision, notifications/email, storage
│   ├── extraction/   # OCR-line → structured-field pipeline (candidates, scoring, validation, select)
│   ├── auth/
│   ├── database/
│   ├── scripts/      # one-off schema/backfill/seed scripts
│   ├── tests/        # pytest — see "Backend tests" below
│   ├── main.py
│   ├── .env.example
│   └── requirements.txt
├── web-admin/         # React web admin (see web-admin/README.md)
├── assets/docs/       # plans, findings and CHANGELOG.md — see "Docs" below
├── assets/ksa/, assets/dubai/  # real bill photos used by the OCR comparison harness
└── EXPENSE_RECEIPT_APP_PLAN.md
```

### Docs

| Doc | What it is |
|---|---|
| [`assets/docs/CHANGELOG.md`](assets/docs/CHANGELOG.md) | What changed recently, for users and in code. Start here |
| [`assets/docs/EXPENSE_FLOW_GAP_ANALYSIS_AND_PLAN.md`](assets/docs/EXPENSE_FLOW_GAP_ANALYSIS_AND_PLAN.md) | Plan and status for currency, region approvers, payments, top-ups and cross-department routing |
| [`assets/docs/BRI_DEPARTMENT_PETTY_CASH.md`](assets/docs/BRI_DEPARTMENT_PETTY_CASH.md) | BRI department petty cash rules (limit, top-up, reimbursement) mapped to this app |
| [`assets/docs/PS_EMPLOYEE_PCA_COMPARISON.md`](assets/docs/PS_EMPLOYEE_PCA_COMPARISON.md) | Professional Signs (KSA) employee advances compared with the app: gaps, build order and open questions |
| [`assets/docs/PETTY_CASH_PHASED_PLAN.md`](assets/docs/PETTY_CASH_PHASED_PLAN.md) | Phase-by-phase status against the v1.2 spec |
| [`assets/docs/APPROVAL_WORKFLOW_FINDINGS.md`](assets/docs/APPROVAL_WORKFLOW_FINDINGS.md) | Approval workflow findings and ERP-Dev query timing |
| `assets/docs/*OCR*`, `AI_VISION_SCAN_FINDINGS.md` | OCR engine and vision-model evaluations |

---

## Backend config (`backend/.env`)

Copy from `.env.example`. Important keys:

| Variable | Meaning |
|----------|---------|
| `READER_DB_*` | **Required** ERP-Dev SQL Server (`SERVER`, `NAME`, `USER`, `PASSWORD`, `DRIVER`) — auth + claims live here |
| `STORAGE_BACKEND` | `s3` (default) — receipts in AWS |
| `AWS_*` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_BUCKET`, `AWS_FOLDER` (keys under `{folder}/expense-receipts/`) |
| `OCR_BACKEND` | `paddle` (default; **name is stale** — this literal value now runs RapidOCR, not PaddleOCR, see below) — single shared PP-OCRv6 text-detection pass, then sequential English + Arabic RapidOCR/ONNXRuntime recognizer passes over the same detected regions; `stub` is a fallback if RapidOCR fails to load. PaddleOCR/PaddlePaddle are no longer used anywhere in this repo — only the config value's name wasn't updated when the engine switched (`config.py`'s `ocr_backend: str = "paddle"` and the `if settings.ocr_backend == "paddle":` check in `ocr_service.py`), so `/health` still reports `"ocr_backend":"paddle"` |
| `CORS_ORIGINS` | `*` for local dev |
| `PUBLIC_BASE_URL` | Default `http://localhost:8000` — used to build the "View this claim" link in HTML notification emails (points at the new unauthenticated `GET /claims/{id}` fallback page below) |
| Graph email + `NOTIFY_EMAIL_ENABLED` | **Deferred** — not in current target (photo → S3 → tables) |

Tables are created on ERP-Dev at backend startup (`create_all`, additive only — it does not backfill columns onto existing tables; see `backend/scripts/add_ocr_document_columns.py` for one-off column migrations). [`assets/docs/schema.sql`](assets/docs/schema.sql) documents only the original MVP tables (`expense_app_users`, `expense_claims`, `expense_receipts`, `expense_claim_history`) and is kept for historical reference — the tables actually in use today are the `Erp*` SQLAlchemy models in `backend/database/models.py` (`ErpExpenseTransaction`, `ErpExpenseDocument`, `ErpExpenseApprovalHistory`, `ErpExpenseRegionConfig`, `ErpExpenseCategory`, `ErpExpenseVendor`, and related config/cache tables) — see [`assets/docs/PETTY_CASH_PHASED_PLAN.md`](assets/docs/PETTY_CASH_PHASED_PLAN.md) for the full model.

---

## API sketch

Approvers only see bills for the companies they cover: their home company plus any companies Admin ticked for them (`services/region_scope.py`).

- Auth: `POST /api/auth/login`, `POST /api/auth/switch-region`, `POST /api/auth/refresh`, `GET /api/auth/me`, `POST /api/auth/logout`
- Claims (employee): `POST /api/claims/ocr` (upload + OCR in one call), `POST /api/claims/ocr/upload` (store only), `POST /api/claims/receipts/{id}/ocr` (analyze a stored receipt), `GET /api/claims/exchange-rate?from=&region_code=` (preview conversion), `POST /api/claims`, `GET /api/claims/mine`, `GET /api/claims/{id}`, `PATCH /api/claims/{id}`, `POST /api/claims/{id}/submit`, `POST /api/claims/{id}/resubmit`
- Approvals (HOD / dept-HOD / Accountant / Finance Manager): `GET /api/approvals/queue`, `GET /api/approvals/history`, `GET /api/approvals/{id}`, `GET /api/approvals/{id}/funds` (the pots a petty-cash bill is paid from: all of them for the FM, only the HOD's own pot for an HOD), `POST /api/approvals/{id}/approve`, `POST /api/approvals/{id}/dispute`, `POST /api/approvals/{id}/reject`, `POST /api/approvals/bulk-approve` (backend-complete; **no Flutter UI calls this today**)
- Payments (Finance Manager / Admin): `GET /api/payments?status=unpaid|paid&region_code=`, `POST /api/payments`, `POST /api/payments/batch`, `GET /api/payments/methods`
- Funds: `GET /api/funds/mine`, `GET /api/funds/department-funds?region_id=` (FM, read-only, companies they cover), `GET /api/funds/{id}/replenishable-bills`, `POST /api/funds/{id}/topups`
- Top-ups (HOD request → Accountant verify → FM approve with payment): `GET /api/topups`, `POST /api/topups/{id}/verify`, `POST /api/topups/{id}/return`, `POST /api/topups/{id}/approve`, `POST /api/topups/{id}/reject`
- Employee advances (Professional Signs / companies with `pca_model: employee`): `GET/POST /api/pca/advances`, `GET /api/pca/summary?region_id=` (by department and by project, with employees), `GET /api/pca/staff?region_id=` (who an HOD/Admin can propose for), `GET /api/pca/advances/{fund_id}/replenishable-bills`, `POST /api/pca/advances/{fund_id}/topups`, `GET /api/pca/requests`, `GET /api/pca/requests/{id}`, `POST /api/pca/requests/{id}/{hod-approve|manager-approve|pay|reject}`, `GET /api/pca/payment-sources`
- Regions and branding: `GET /api/regions`, `GET /api/branding/{region_code}`, `GET /api/branding/{region_code}/logo`
- Admin: `GET /api/admin/claims`, `GET /api/admin/claims/{id}`, `GET /api/admin/activity`, `POST /api/admin/claims/{id}/mark-paid` (kept as a wrapper around payments), `GET /api/admin/users`, `GET /api/admin/users/{id}`, `PUT /api/admin/users/{id}/regions`, `GET/POST /api/admin/funds`, `PUT /api/admin/funds/{id}`, `POST /api/admin/funds/{id}/credit`, `GET /api/admin/department-funds`
- Admin config: `GET/POST /api/admin/config/{departments,regions,categories,hod-assignments,delegations}`, `PUT /api/admin/config/regions/{id}`, `GET /api/admin/config/regions/{id}/approvers`, `POST /api/admin/config/regions/{id}/logo`, `PUT/DELETE /api/admin/config/categories/{id}`
- Reference (any authenticated user, read-only): `GET /api/projects`, `GET /api/opportunities/search`, `GET /api/categories`. The vendor on a bill is plain text from the bill; there is no vendor matching or resolve step.
- Receipt image: `GET /api/claims/receipts/{id}/image`, `GET /api/claims/receipts/{id}/pages/{page_no}/image`
- Notifications: `GET /api/notifications`, `GET /api/notifications/unread-count`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all` — backed by an `ErpExpenseNotification` table (email + in-app, per-user language for plain-text bodies, HTML email bodies are English-only, dedup'd per event); see [`assets/docs/PETTY_CASH_PHASED_PLAN.md`](assets/docs/PETTY_CASH_PHASED_PLAN.md) Phase 5 for what's still missing (push/FCM, preference UI)
- Public (no auth): `GET /claims/{id}` — plain HTML fallback page the "View this claim" button in notification emails links to; shows no claim data, just confirms the id, since the link isn't scoped to the recipient

---

## Backend tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt   # pulls in pytest (test-only, listed in requirements.txt)
python -m pytest tests
```

Pass `tests`: a bare `python -m pytest` in `backend/` also collects `test_one.py`, a scratch script that calls the live vision API.

Covers the `extraction/` pipeline, duplicate detection and notifications. It also covers funds and regions, top-ups, currency and payments, cross-department routing, and dispute → resubmit, plus known OCR regression cases (e.g. ENOC receipts). No live ERP-Dev DB or OCR engine is required; workflow tests run against an in-memory SQLite database.

---

## Production deployment

Status as of 2026-08-16: backend deployed and running; public HTTPS live and verified.

| Item | Value |
|---|---|
| Server | `ubuntu@ip-172-20-1-210` (same box as Task Lens / other `bri-erp-api` apps) |
| Folder | `~/bri-erp-api/expensetracker-api` |
| PM2 name / id | `expensetracker-api` / `75` — use `pm2 restart 75` or `pm2 restart expensetracker-api` interchangeably |
| Process | Gunicorn + `uvicorn.workers.UvicornWorker` (`ecosystem.config.js`, `--workers 1`) |
| Internal port | `127.0.0.1:5930` |
| Public URL | `https://expensetracker-api.app-brisigns.com` — live. Nginx (`/etc/nginx/sites-available/expensetracker-api.app-brisigns.com.conf` → `localhost:5930`) + Let's Encrypt via `certbot --nginx` (cert auto-renews, expires 2026-11-15). DNS A record (`expensetracker-api` → `3.7.128.46`) added via GoDaddy. Verified end-to-end: `curl https://expensetracker-api.app-brisigns.com/health` → `200 OK`. |
| DB | Same `ERP-Dev` SQL Server as local dev (`13.234.241.125`) — no separate prod DB |
| S3 | Same production bucket as local dev (`bri-erp-production`, folder `live`) |
| Logs | `~/.pm2/logs/expensetracker-api-out.log` / `expensetracker-api-error.log` |
| Deploy loop | WinSCP upload of `backend/`'s `main.py`, `api/`, `services/`, `database/`, `auth/`, `config.py`, `requirements.txt`, `scripts/` (never `.venv`, `uploads/`, `.env`) → `pip install -r requirements.txt` if deps changed → `pm2 restart expensetracker-api` |

**Open items:**

- [x] DNS A record + certbot SSL — done. Public HTTPS live and verified.
- [x] Commit + push this session's local changes — done (`6409e0c` on `main`).
- [ ] Confirm `pm2 save` actually completed for `expensetracker-api` (id `75`) — needed so it survives a server reboot; a `pm2 restart 75` was confirmed, but `pm2 save`'s own success output hasn't been.

**Known deployment gotcha:** `passlib[bcrypt]>=1.7.4` (2020) is incompatible with `bcrypt>=4.1` — passlib's internal self-test hits a `ValueError: password cannot be longer than 72 bytes` on *any* login attempt, not because of the actual user's password length. Fixed by pinning `bcrypt<4.1` in `requirements.txt`. If a fresh `pip install` on a new box still shows this, run `pip install "bcrypt<4.1"` and restart.

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| App cannot reach API on Android emulator | Use `API_BASE_URL=http://10.0.2.2:8000`, and run uvicorn with `--host 0.0.0.0` |
| `compileSdk` / `android-37` Gradle error | Project sets `compileSdk = 37`; ensure Android SDK Platform 37 is installed in SDK Manager |
| Kotlin “different roots” (C: vs D:) build error | `android/gradle.properties` already has `kotlin.incremental=false` |
| Camera permission denied | Grant Camera / Photos in the emulator app settings |
| Backend port in use | Stop the other process or change `--port` and match `API_BASE_URL` |
| `JAVA_HOME` invalid | Fix JAVA_HOME, or let Flutter use its bundled JDK via Android Studio / Flutter tooling |
| Login returns 500, log shows `ValueError: password cannot be longer than 72 bytes` | `bcrypt>=4.1` breaks `passlib[bcrypt]==1.7.4`'s internal self-test (unrelated to actual password length) — run `pip install "bcrypt<4.1"` and restart |
| Flutter build fails: `doclens_screen.dart` — `No named parameter with the name 'onReorderItem'` | Published `doclens` (0.0.8 and 0.0.12) calls a nonexistent Flutter API param — should be `onReorder`. Patched locally in [`third_party/doclens`](third_party/doclens) (one-line fix) and wired in via `dependency_overrides` in [`pubspec.yaml`](pubspec.yaml). Remove the override once a fixed `doclens` version is published upstream |
