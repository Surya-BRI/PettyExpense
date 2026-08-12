# Expense Receipt App

Flutter (Android/iOS) + FastAPI for salesman expense reimbursement from bill photos.

Stack: Flutter · Riverpod · go_router · FastAPI · SQLAlchemy + **ERP-Dev SQL Server only** (no local SQLite) · JWT · local or S3 storage · stub/Paddle OCR.

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
python -m pip install -r requirements.txt
Copy-Item .env.example .env   # only if .env does not exist yet
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### macOS / Linux

```bash
cd backend
python3 -m pip install -r requirements.txt
cp .env.example .env          # only if .env does not exist yet
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Verify backend

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Leave this terminal running while you use the app.

### Demo users (JWT login)

| Username | Password | Role |
|----------|----------|------|
| `salesman` | `salesman123` | salesman |
| `finance` | `finance123` | finance |
| `admin` | `admin123` | admin |

With `AUTH_MODE=mock` (default), the API also accepts requests **without** a Bearer token as `salesman-001`. The Flutter app can “Continue as mock salesman” the same way.

---

## 2) Frontend (Flutter) setup & run

Open a **second** terminal in the project root. Keep the backend running.

### Install deps

```powershell
cd d:\expense_app
flutter pub get
```

### Connect Flutter → backend (`.env`)

Root file [`.env`](.env) (loaded by the app):

```env
API_BASE_URL=http://10.0.2.2:8000
```

| Where the app runs | `API_BASE_URL` |
|--------------------|----------------|
| Android emulator | `http://10.0.2.2:8000` ← default in `.env` |
| iOS simulator / Windows / Chrome | `http://127.0.0.1:8000` |
| Physical phone (same Wi‑Fi) | `http://<your-PC-LAN-IP>:8000` |

`127.0.0.1` inside the Android emulator is the **phone itself**, not your PC — that causes `Connection refused`.

### Run from terminal

```powershell
flutter devices
flutter run -d emulator-5554
```

No `--dart-define` needed if `.env` is set. Full restart after changing `.env` (not just hot reload).

**Windows / Chrome:** set `API_BASE_URL=http://127.0.0.1:8000` in `.env`, then `flutter run -d windows`.

### Run from Android Studio

1. Open `expense_app`, start AVD, Run.
2. Ensure root `.env` has `API_BASE_URL=http://10.0.2.2:8000`.
3. After editing `.env`, stop and Run again (full restart).

Camera / gallery need an emulator camera or a real device; gallery works with sample images.

---

## 3) Typical first-run flow

1. Start **backend** → confirm `/health` returns `"status":"ok"`.
2. Start **emulator / device**.
3. Start **Flutter** with the correct `API_BASE_URL`.
4. In the app: **Continue as mock salesman**, or sign in with `salesman` / `salesman123`.
5. **New claim** → camera or gallery → confirm OCR fields → submit.
6. For Finance: Profile → Sign in as `finance` / `finance123` → **Finance queue**.

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
├── docs/schema.sql
└── EXPENSE_RECEIPT_APP_PLAN.md
```

---

## Backend config (`backend/.env`)

Copy from `.env.example`. Important keys:

| Variable | Meaning |
|----------|---------|
| `READER_DB_*` | **Required** ERP-Dev SQL Server (`SERVER`, `NAME`, `USER`, `PASSWORD`, `DRIVER`) — auth + claims live here |
| `STORAGE_BACKEND` | `s3` (default) — receipts in AWS |
| `AWS_*` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_BUCKET`, `AWS_FOLDER` (keys under `{folder}/expense-receipts/`) |
| `OCR_BACKEND` | `stub` (default) or `paddle` (install PaddleOCR separately) |
| `AUTH_MODE` | `mock` (no token → salesman) or `erp` (JWT required) |
| `CORS_ORIGINS` | `*` for local dev |
| Graph email + `NOTIFY_EMAIL_ENABLED` | **Deferred** — not in current target (photo → S3 → tables) |

Tables are created on ERP-Dev at backend startup (`create_all`). Manual script: [`docs/schema.sql`](docs/schema.sql) (`expense_app_users`, `expense_claims`, `expense_receipts`, `expense_claim_history`).

---

## API sketch

- Auth: `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me`, `POST /api/auth/logout`
- Claims: `POST /api/claims/ocr`, `POST /api/claims`, `GET /api/claims/mine`, `GET /api/claims/{id}`, `PATCH /api/claims/{id}`, `POST /api/claims/{id}/submit`
- Admin: `GET /api/admin/claims`, approve / reject / mark-paid
- Receipt image: `GET /api/claims/receipts/{id}/image`

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
