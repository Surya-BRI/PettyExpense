# Expense Receipt App

Flutter (Android/iOS) + FastAPI for salesman expense reimbursement from bill photos.

Stack: Flutter · Riverpod · go_router · FastAPI · SQLAlchemy + **ERP-Dev SQL Server only** (no local SQLite) · JWT · local or S3 storage · stub/Paddle OCR.

**Scope: UAE and KSA only** — bills are captured in **AED** or **SAR** (currency is chosen at capture time, not auto-defaulted from a single locale). No India/INR support; OCR (bilingual Arabic/English via PaddleOCR) and sample data are built around Dubai (AED) and KSA (SAR) receipts only.

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

### Demo users (JWT login)

Real rows in `ErpAuthExpenseUsers` on ERP-Dev, matching the dropdown in `lib/src/features/authentication/login_screen.dart`:

| Username | Password | Role |
|----------|----------|------|
| `surya` | `surya123` | Employee · Sales |
| `raghu` | `raghu123` | Employee · Sales |
| `vikram` | `vikram123` | Employee · IT |
| `denny` | `denny123` | HOD · IT |
| `sajeesh` | `sajeesh123` | HOD · Sales |
| `anjana` | `anjana123` | Accountant |
| `sandeep` | `sandeep123` | Finance Manager |
| `rajesh` | `rajesh123` | Finance Manager |
| `teja` | `teja123` | Admin |

With `AUTH_MODE=mock`, the API also accepts requests **without** a Bearer token as `salesman-001`. The Flutter app can "Continue as mock salesman" the same way. **Production uses `AUTH_MODE=erp`** — every request needs a real login.

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
4. In the app: **Continue as mock salesman**, or sign in with `surya` / `surya123`.
5. **New claim** → camera or gallery → confirm OCR fields → submit.
6. For approvals: Profile → sign in as `denny` / `denny123` (HOD) or `sandeep` / `sandeep123` (Finance Manager) → **Approvals queue**.

---

## Project layout

```
expense_app/
├── lib/src/
│   ├── features/   # authentication, claims, finance, home, profile
│   ├── api/
│   ├── routing/
│   └── theme/
├── backend/
│   ├── api/        # routes_auth, routes_claims, routes_admin, ...
│   ├── services/   # claims, OCR, S3/local storage, email
│   ├── auth/
│   ├── database/
│   ├── main.py
│   ├── .env.example
│   └── requirements.txt
├── assets/docs/       # schema.sql (legacy reference), OCR_ENGINE_EVALUATION.md, PETTY_CASH_PHASED_PLAN.md
├── assets/ksa/, assets/dubai/  # real bill photos used by the OCR comparison harness
└── EXPENSE_RECEIPT_APP_PLAN.md
```

See [`assets/docs/PETTY_CASH_PHASED_PLAN.md`](assets/docs/PETTY_CASH_PHASED_PLAN.md) for the current, code-verified status of the petty-cash/multi-region rework — the schema, roles, and API surface below describe the original single-approver MVP and are simpler than what's actually running today.

---

## Backend config (`backend/.env`)

Copy from `.env.example`. Important keys:

| Variable | Meaning |
|----------|---------|
| `READER_DB_*` | **Required** ERP-Dev SQL Server (`SERVER`, `NAME`, `USER`, `PASSWORD`, `DRIVER`) — auth + claims live here |
| `STORAGE_BACKEND` | `s3` (default) — receipts in AWS |
| `AWS_*` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_BUCKET`, `AWS_FOLDER` (keys under `{folder}/expense-receipts/`) |
| `OCR_BACKEND` | `paddle` (default) — install PaddleOCR; `stub` is a fallback if Paddle fails to load |
| `AUTH_MODE` | `mock` (no token → salesman) or `erp` (JWT required) |
| `CORS_ORIGINS` | `*` for local dev |
| Graph email + `NOTIFY_EMAIL_ENABLED` | **Deferred** — not in current target (photo → S3 → tables) |

Tables are created on ERP-Dev at backend startup (`create_all`, additive only — it does not backfill columns onto existing tables; see `backend/scripts/add_ocr_document_columns.py` for one-off column migrations). [`assets/docs/schema.sql`](assets/docs/schema.sql) documents only the original MVP tables (`expense_app_users`, `expense_claims`, `expense_receipts`, `expense_claim_history`) and is kept for historical reference — the tables actually in use today are the `Erp*` SQLAlchemy models in `backend/database/models.py` (`ErpExpenseTransaction`, `ErpExpenseDocument`, `ErpExpenseApprovalHistory`, `ErpExpenseRegionConfig`, `ErpExpenseCategory`, `ErpExpenseVendor`, and related config/cache tables) — see [`assets/docs/PETTY_CASH_PHASED_PLAN.md`](assets/docs/PETTY_CASH_PHASED_PLAN.md) for the full model.

---

## API sketch

- Auth: `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me`, `POST /api/auth/logout`
- Claims (salesman): `POST /api/claims/ocr` (upload + OCR in one call), `POST /api/claims/ocr/upload` (store only), `POST /api/claims/receipts/{id}/ocr` (analyze a stored receipt), `POST /api/claims`, `GET /api/claims/mine`, `GET /api/claims/{id}`, `PATCH /api/claims/{id}`, `POST /api/claims/{id}/submit`, `POST /api/claims/{id}/resubmit`
- Approvals (HOD / dept-HOD / Accountant / Finance Manager): `GET /api/approvals/queue`, `GET /api/approvals/{id}`, `POST /api/approvals/{id}/approve`, `POST /api/approvals/{id}/dispute`, `POST /api/approvals/{id}/reject`, `POST /api/approvals/bulk-approve`
- Admin: `GET /api/admin/claims`, `GET /api/admin/claims/{id}`, `POST /api/admin/claims/{id}/mark-paid`
- Admin config: `GET/POST /api/admin/config/{departments,regions,categories,vendors,hod-assignments,delegations}`
- Reference: `GET /api/projects`
- Receipt image: `GET /api/claims/receipts/{id}/image`

---

## Production deployment

Status as of 2026-08-16: backend deployed and running; public HTTPS live and verified.

| Item | Value |
|---|---|
| Server | `ubuntu@ip-172-20-1-210` (same box as Task Lens / other `bri-erp-api` apps) |
| Folder | `~/bri-erp-api/expensetracker-api` |
| PM2 name | `expensetracker-api` |
| Process | Gunicorn + `uvicorn.workers.UvicornWorker` (`ecosystem.config.js`, `--workers 1`) |
| Internal port | `127.0.0.1:5930` |
| Public URL | `https://expensetracker-api.app-brisigns.com` — live. Nginx (`/etc/nginx/sites-available/expensetracker-api.app-brisigns.com.conf` → `localhost:5930`) + Let's Encrypt via `certbot --nginx` (cert auto-renews, expires 2026-11-15). DNS A record (`expensetracker-api` → `3.7.128.46`) added via GoDaddy. Verified end-to-end: `curl https://expensetracker-api.app-brisigns.com/health` → `200 OK`. |
| DB | Same `ERP-Dev` SQL Server as local dev (`13.234.241.125`) — no separate prod DB |
| S3 | Same production bucket as local dev (`bri-erp-production`, folder `live`) |
| `AUTH_MODE` | `erp` (real JWT login required — deliberately **not** `mock` on this deployment, unlike the local-dev default) |
| Logs | `~/.pm2/logs/expensetracker-api-out.log` / `expensetracker-api-error.log` |
| Deploy loop | WinSCP upload of `backend/`'s `main.py`, `api/`, `services/`, `database/`, `auth/`, `config.py`, `requirements.txt`, `scripts/` (never `.venv`, `uploads/`, `.env`) → `pip install -r requirements.txt` if deps changed → `pm2 restart expensetracker-api` |

**Open items:**
- [x] DNS A record + certbot SSL — done. Public HTTPS live and verified.
- [x] Commit + push this session's local changes — done (`6409e0c` on `main`).

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
