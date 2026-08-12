# Expense Receipt App — Architecture & Build Plan

Planning document for a **new internal app** that reuses Task Lens tech stack and patterns, but solves a different problem: **salesman expense reimbursement from bill photos**.

This is **not** a fork of Task Lens domain logic (estimation approvals). It is a sibling product with the same engineering foundation.

---

## 1) Problem

Company reimburses salesmen for field expenses (petrol, food, and others) while visiting projects.

**Today**
- Salesman fills petrol / pays for food
- Takes a physical bill
- Manually sends bill to Finance
- Finance reimburses offline

**Pain**
- Slow, easy to lose bills
- Manual data entry for Finance
- No clear audit trail or project linkage

**Goal**
- Capture bill with phone camera
- Extract provider, amount, and date from the bill
- Submit claim to Finance from the app
- Admin / Finance reviews submissions
- Optionally link claim to a project / OP

---

## 2) Product Overview

| Role | What they do |
|------|----------------|
| **Salesman** | Capture / upload receipt, confirm OCR fields, pick category + optional project, submit claim |
| **Finance / Admin** | Review queue, open photo + extracted data, approve / reject with remarks, mark paid |
| **System** | Store image in S3, persist claim/receipt rows, run OCR (assist) |
| **Email (later)** | Graph notify on submit / decision — **deferred** |

### Claim statuses

```
Draft → Submitted → Approved / Rejected → Paid
```

---

## 3) Tech Stack (same as Task Lens)

Reuse the proven stack unless there is a strong reason not to.

### Frontend
- Flutter (Dart)
- Riverpod
- go_router
- Freezed + json_serializable
- Camera + gallery pick plugins
- Secure JWT storage (same auth client patterns)

### Backend
- FastAPI + Uvicorn
- Pydantic settings
- SQLAlchemy / pyodbc (SQL Server)
- JWT access + refresh tokens
- AWS S3 for receipt images (upload + signed URL / proxy)
- Optional Ollama for post-OCR field cleanup (JSON extract from OCR text)
- Microsoft Graph email — **deferred to a later phase** (code stub OK; not in current target)

### Database
- Microsoft SQL Server — **ERP-Dev connection only** (no local SQLite)
- **Own expense tables** on that server (`expense_claims`, `expense_receipts`, `expense_claim_history`, `expense_app_users`)
- Optional read of ERP projects / OPs / employees for dropdowns and identity (later)

### Auth & access
- Mock / seed users OK for current slice; real `ErpAuthUsers` + allowlist later
- Roles: **Salesman** (submit own claims) vs **Finance/Admin** (see all, approve/reject)

### Deploy
- PM2 + Uvicorn on Linux
- Env-driven config (never overwrite prod `.env` blindly)
- Health checks after restart

---

## 4) What to Reuse vs Build New

| Reuse from Task Lens | Build new for this app |
|----------------------|-------------------------|
| Flutter feature folders, Riverpod, go_router | Camera / gallery + claim UI |
| FastAPI router + service split | Claim CRUD + status workflow |
| JWT login, refresh, allowlist | Multipart upload → S3 |
| S3 credential / proxy pattern | OCR pipeline (PaddleOCR + parse) |
| Graph email notify pattern | Finance review queue |
| PM2 / env / CORS / logging | Expense DB schema + history |
| ERP identity (who is logged in) | Optional project / OP picker |

**Do not copy:** estimation approval workflows, OP cost revisions, Task Lens task list semantics.

---

## 5) Suggested Folder Shape

Mirror Task Lens layout so the team can move between apps easily.

```
EXPENSE-APP/   (or similar repo name)
├── lib/src/
│   ├── features/
│   │   ├── authentication/
│   │   ├── claims/          # salesman: capture, form, my claims
│   │   ├── finance/         # admin review queue
│   │   ├── home/
│   │   └── profile/
│   ├── api/
│   ├── routing/
│   └── theme/
├── backend/
│   ├── api/                 # routes_auth, routes_claims, routes_admin, routes_ocr
│   ├── services/            # claim_service, ocr_service, email_service, s3
│   ├── auth/
│   ├── database/
│   └── config.py
└── docs/
```

---

## 6) Data Model (minimal)

### `ExpenseClaim`
- `id`
- `submitted_by` (employee / user id)
- `vendor` / provider name
- `amount`
- `currency` (default INR)
- `bill_date`
- `category` (`petrol` | `food` | `other`)
- `project_id` / `op_number` (optional)
- `status` (`draft` | `submitted` | `approved` | `rejected` | `paid`)
- `remarks` / `finance_remarks`
- `created_at`, `updated_at`, `submitted_at`, `decided_at`, `paid_at`

### `Receipt`
- `id`
- `claim_id`
- `s3_key`
- `content_type`
- `ocr_raw_json` (full OCR output)
- `ocr_vendor`, `ocr_amount`, `ocr_date` (extracted)
- `ocr_confidence` (optional scores)
- `image_hash` (optional duplicate detection)

### `ClaimHistory`
- `id`
- `claim_id`
- `actor_id`
- `action` (`created` | `submitted` | `approved` | `rejected` | `paid` | `edited`)
- `remarks`
- `created_at`

---

## 7) Core User Flows

### Salesman
1. Open camera (or pick from gallery)
2. Upload image → backend stores in S3 and runs OCR
3. Form prefilled with vendor, amount, date (always editable)
4. Select category; optionally select project / OP
5. Submit → status `Submitted`; Finance notified (optional email)

### Finance / Admin
1. List pending claims (filter by person, date, category, project, status)
2. Open claim: original photo + fields + history
3. Approve or reject with remarks → notify salesman
4. Mark paid when reimbursed

### Safeguards
- OCR is assistive only — user must confirm before submit
- Finance always sees original photo
- Keep immutable S3 original for audit
- Optional: warn on likely duplicate (same hash / same amount + date + vendor)

---

## 8) API Sketch

```
Auth (same pattern as Task Lens)
  POST   /api/auth/login
  POST   /api/auth/refresh
  GET    /api/auth/me
  POST   /api/auth/logout

Claims (salesman)
  POST   /api/claims/ocr              # multipart image → OCR draft fields
  POST   /api/claims                  # create draft / submit claim
  GET    /api/claims/mine             # my claims
  GET    /api/claims/{id}
  PATCH  /api/claims/{id}             # edit draft
  POST   /api/claims/{id}/submit

Finance / Admin
  GET    /api/admin/claims            # ?status=submitted&...
  GET    /api/admin/claims/{id}
  POST   /api/admin/claims/{id}/approve
  POST   /api/admin/claims/{id}/reject
  POST   /api/admin/claims/{id}/mark-paid

Reference (optional)
  GET    /api/projects                # ERP projects / OPs for picker

Health
  GET    /health
```

Upload flow recommendation:
1. Client sends image to `POST /api/claims/ocr`
2. Backend writes to S3, runs OCR, returns `{ s3_key, vendor, amount, date, confidence, raw_text }`
3. Client shows editable form; on submit, create claim with confirmed fields + `s3_key`

---

## 9) OCR Strategy (free / self-hosted)

### Recommended pipeline
```
Photo → S3 → PaddleOCR (text) → regex / Ollama JSON extract → editable form → submit
```

### Free Python OCR options

| Library | Notes |
|---------|--------|
| **PaddleOCR** (preferred) | Strong free option for bills; angle classification; Apache-2.0 |
| **EasyOCR** | Simple API; decent English; often slower |
| **docTR** | Good document lines; more setup |
| **Tesseract** | Light and free; weakest on phone photos of thermal slips |
| **Surya** | Strong OCR; check GPL-3.0 before commercial closed use |

### Post-OCR field extraction
OCR alone returns lines of text. Still need to pull:
- provider / vendor
- money / total amount
- date

Options:
1. **Regex / rules** — `₹`, `Rs`, `Total`, date patterns (fast, brittle)
2. **Ollama LLM** — “Extract vendor, amount, date as JSON from this receipt text”
3. Hybrid: regex first, LLM fallback when confidence is low

### Accuracy expectations (honest)
| Receipt type | Reality with free OCR |
|--------------|------------------------|
| Clear printed shop bill | Often good enough after user confirm |
| Thermal petrol slip (glare, crumple, fade) | Frequently wrong amount/date |
| Handwritten | Usually poor |

**Product rule:** never auto-submit OCR results without salesman confirmation; Finance always sees the photo.

### Example (PaddleOCR)
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="en")
result = ocr.ocr("receipt.jpg", cls=True)
# Parse boxes → text lines → extract vendor / amount / date
```

---

## 10) Current target (NOW) — photo → S3 → tables

**Goal of this slice only:** prove the core media + persistence path end-to-end.

```
Camera / gallery → POST /api/claims/ocr
  → upload bytes to S3 (AWS_BUCKET / AWS_FOLDER)
  → insert expense_receipts row (s3_key, hash, OCR draft fields)
  → salesman confirms form
  → POST /api/claims
  → insert expense_claims (+ link receipt, claim history)
```

### Must work
1. Capture or pick receipt photo (Flutter)
2. Upload to backend
3. Save original image in **S3** (`live/expense-receipts/...`)
4. Persist **receipt + claim** rows on **ERP-Dev SQL Server**
5. Return / show image via signed URL or proxy
6. Mock auth OK (no real ERP login required for this slice)
7. Stub OCR OK (editable fields; real PaddleOCR next)

### Explicitly out of this slice
- Microsoft Graph **email notify** (later phase)
- Real ERP login / allowlist
- Finance approve/reject polish (can exist in code; not the success gate)
- Real ERP project/OP dropdown
- GPS, mileage, Excel export, offline, push

---

## 11) MVP Scope (after current target)

### Ship in v1 (next after photo→S3→tables)
1. ERP-style login + allowlist
2. OCR assist (real PaddleOCR) + editable form
3. Category + optional project
4. Submit to Finance queue
5. Admin approve / reject + remarks
6. “My claims” history for salesman

### Defer to later phases
- **Email notify (Microsoft Graph)** on submit / approve / reject / paid
- GPS at pump / geofence
- Mileage calculation
- Bulk Excel / ERP export
- Multi-currency
- Offline capture queue + sync
- Push notifications
- Advanced fraud scoring

---

## 12) Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Wrong OCR amount | Editable fields + Finance sees photo |
| Duplicate / reused bills | Image hash + amount/date/vendor warning |
| Fraud / disputed claim | Immutable S3 original + claim history |
| Poor site connectivity | Later: local queue, sync when online |
| License issues (OCR libs) | Prefer Apache-2.0 (PaddleOCR / EasyOCR / Tesseract) |

---

## 13) Implementation Order (suggested)

### Phase A — Current target (photo → S3 → tables)  ← **NOW**
1. Scaffold Flutter + FastAPI (mock auth)
2. Expense tables on ERP-Dev
3. Multipart upload → S3 + signed URL / proxy
4. Insert `expense_receipts` + `expense_claims` (+ history)
5. Salesman UI: camera → confirm → submit → see claim with photo

### Phase B — Product workflow
6. Stub → real OCR (PaddleOCR + parse)
7. Finance UI: queue → approve / reject / paid
8. Real ERP auth + allowlist
9. ERP project / OP picker

### Phase C — Later
10. **Email notify** (Graph) on submit / decision
11. Hardening: duplicate UX, confidence UI, audit polish
12. Offline / GPS / export (as needed)

---

## 14) Success Criteria

### Current target
- Photo from app lands in S3 under configured folder
- Matching rows exist in `expense_receipts` and `expense_claims` on ERP-Dev
- App can reload claim and show the stored image

### Broader product (later)
- Salesman can submit a petrol/food claim from site in under ~2 minutes
- Finance has a single queue instead of WhatsApp / email photo chaos
- Every paid claim has an immutable bill image + who approved it
- Project / OP linkage available when relevant, not mandatory
- Email notify only after Phase C

---

## 15) Relation to Task Lens

| | Task Lens | Expense Receipt App |
|--|-----------|---------------------|
| Stack | Flutter + FastAPI + SQL Server + JWT + S3 | Same |
| Auth | ERP users + allowlist | Same pattern (mock first for Phase A) |
| Domain | Estimation / OP approval workflows | Expense claims from receipts |
| AI | Ollama text summaries for revisions | OCR (+ optional Ollama JSON extract) |
| Media | Profile photo read/proxy | Receipt upload → S3 + DB |
| Email | Graph notify | **Deferred** to later phase |

Same architecture, different use case.

---

*Document created for planning a sibling internal app. Updated: email deferred; current target is photo upload → S3 → ERP-Dev tables.*
