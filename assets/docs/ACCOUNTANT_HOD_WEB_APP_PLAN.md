# Accountant / HOD Web App — Findings & Plan

> Companion to [`PETTY_CASH_PHASED_PLAN.md`](PETTY_CASH_PHASED_PLAN.md). Scopes a React + TypeScript
> web app for the Accountant and HOD approval roles, reusing the existing FastAPI backend as-is.

---

## 1) Goal

The Flutter app currently serves all roles (employee, hod, accountant, finance_manager, admin) on
mobile. Accountants and HODs mostly work at a desk, so we want a **web app** for those two roles
that talks to the **same backend**, with **no backend fork** and minimal backend changes.

Decisions already made:
- **Same backend** — the web app calls the existing FastAPI endpoints directly (same DB, same JWT
  auth). No separate backend.
- **One React app, two roles** — a single React + TypeScript project with role-based routing,
  not two separate apps. This mirrors how the Flutter app already works (see below).

---

## 2) Key finding: there is no separate "accountant" or "hod" code today

The Flutter app has **no dedicated accountant/hod feature folders**. Both roles (plus
`finance_manager`) share one generic approvals feature, parameterized by role/stage:

- `lib/src/features/approvals/approval_queue_screen.dart` — queue screen, shared across approver roles
- `lib/src/features/approvals/approval_detail_screen.dart` — detail/decision screen, shared
- `lib/src/routing/role_routes.dart` — `homeRouteFor(role)` / `defaultStageFor(role)` maps each
  role to its default landing stage:
  - `employee` → `/claims`
  - `hod` → stage `hod`
  - `accountant` → stage `accountant`
  - `finance_manager` → stage `finance_manager`
  - `admin` → stage `hod`
- `lib/src/features/authentication/login_screen.dart` — after login, routes via
  `context.go(homeRouteFor(role))`
- `lib/src/api/enums.dart` — `UserRole` enum

**Implication:** the new web app should follow the same pattern — one shared "approval queue" +
"claim detail" UI, with role only changing which `stage` is queried and which actions are visible
(e.g. accountant also gets "mark paid" / vendor resolution). Do not build two parallel UIs.

---

## 3) Auth & roles (backend)

Source: `backend/auth/security.py`

- `ROLE_CODES = ["employee", "hod", "accountant", "finance_manager", "admin"]`
- Role is stored in the DB (`ErpMasterExpenseRole`, FK `role_id` on `ErpAuthExpenseUsers`) and
  embedded in the JWT access token as the `role` claim (`create_access_token`).
- `require_role(*codes)` is a dependency factory:
  - `require_approver = require_role("hod", "accountant", "finance_manager")`
  - `require_admin = require_role("admin")`
- **Note:** `department_hod` is a workflow *stage*, not a distinct role — it's resolved via the
  `ErpExpenseHodAssignment` table, not a separate role code.

---

## 4) Relevant API endpoints (all under `/api`)

### Auth — `routes_auth.py` (prefix `/api/auth`)
| Method | Path | Notes |
|---|---|---|
| POST | `/login` | Returns JWT (access + refresh), includes `role` claim |
| POST | `/refresh` | Refresh access token |
| GET | `/me` | Current user + role |
| POST | `/logout` | |

### Approvals — `routes_approvals.py` (prefix `/api/approvals`, all `require_approver`)
| Method | Path | Notes |
|---|---|---|
| GET | `/queue?stage=` | List queue filtered by stage (`hod` / `accountant` / `finance_manager`) |
| GET | `/{transaction_id}` | Claim detail |
| POST | `/{id}/approve` | |
| POST | `/{id}/dispute` | |
| POST | `/{id}/reject` | |
| POST | `/{id}/resolve-vendor` | Vendor match resolution |
| POST | `/bulk-approve` | Batch approve |

### Admin — `routes_admin.py` (prefix `/api/admin`)
| Method | Path | Notes |
|---|---|---|
| GET | `/claims` | List all claims — accessible to hod/accountant/finance_manager |
| GET | `/claims/{claim_id}` | Claim detail (admin-style view) |
| POST | `/claims/{claim_id}/mark-paid` | Finance action (accountant/finance_manager) |
| POST | `/notify/test` | Admin-only |

### Claims — `routes_claims.py` (prefix `/api/claims`)
Mostly employee-facing (`POST /`, `GET /mine`, `PATCH /{id}`, `POST /{id}/submit`, `/resubmit`,
OCR endpoints) — **not** accountant/HOD specific, not needed for this web app's first cut.

### Config — `routes_config.py` (prefix `/api/admin/config`, all `require_admin`)
CRUD for `departments`, `regions`, `categories`, `vendors`, `hod-assignments`, `delegations`.
Admin-only today; out of scope unless accountant/HOD need read access to these for filters.

### Notifications — `routes_notifications.py` (prefix `/api/notifications`)
| Method | Path |
|---|---|
| GET | `` |
| GET | `/unread-count` |
| POST | `/{id}/read` |
| POST | `/read-all` |

### Projects — `routes_projects.py` (prefix `/api`)
`GET /projects` — reference data.

### Public — `routes_public.py` (no prefix)
`GET /claims/{transaction_id}` — public HTML view (e.g. for email links). Not used by the web app.

---

## 5) Backend readiness

From `backend/main.py`:
- CORS already configured via `CORSMiddleware(allow_origins=settings.cors_origin_list,
  allow_credentials=True, allow_methods=["*"], allow_headers=["*"])`.
- `cors_origins` defaults to `"*"` — effectively already open to a web origin. Should be tightened
  to the real web app origin once deployed, but nothing blocks local dev today.
- Routers are mounted with the prefixes listed above; no changes needed to call them from a
  browser.

**Conclusion: no backend changes are required to start building the web app.** Possible later
additions: read-only access to `departments`/`regions`/`categories` for filter dropdowns if
accountant/HOD screens need them (currently admin-only under `/api/admin/config`).

---

## 6) Database (context only, no changes needed)

`backend/database/models.py` (SQLAlchemy, no Alembic — schema changes are ad hoc scripts in
`backend/scripts/`). Relevant tables/models: `ErpMasterExpenseRole`, `ErpExpenseDepartment`,
`ErpAuthExpenseUsers`, `ErpExpenseRegionConfig`, `ErpExpenseCategory`, `ErpExpenseVendor`,
`ErpExpenseMultiRegionUserRegion`, `ErpExpenseEmployeeCache`, `ErpExpenseProjectCache`,
`ErpExpenseTransaction` (claims), `ErpExpenseDocument`, `ErpExpenseHodAssignment`,
`ErpExpenseApprovalHistory`, `ErpExpenseApproverDelegation`, `ErpExpenseNotification`,
`ErpExpenseNotificationPreference`.

---

## 7) Existing `web/` folder — not a conflict

The `web/` directory at the Flutter project root is Flutter's default web-build scaffold
(`favicon.png`, `icons/`, `index.html` with `$FLUTTER_BASE_HREF`, `manifest.json`) — it is **not**
a separate app and will not conflict with a new React project placed elsewhere in the repo (e.g.
`webapp/`).

---

## 8) Proposed web app shape

```
webapp/                     # new React + TypeScript project (Vite)
├── src/
│   ├── api/                # typed client for /api/auth, /api/approvals, /api/admin, /api/notifications
│   ├── auth/                # login, JWT storage, refresh, role from /api/auth/me
│   ├── routing/             # role -> default stage, route guards (mirrors role_routes.dart)
│   ├── features/
│   │   ├── approvals/       # queue + detail screens, shared by accountant & hod
│   │   └── notifications/
│   └── theme/
```

Pages (first cut):
1. **Login** — shared, redirects by role (accountant → stage `accountant`, hod → stage `hod`)
2. **Approval Queue** — list by stage/status, filters
3. **Claim Detail** — approve / reject / dispute, vendor resolution; accountant additionally sees
   "mark paid"
4. **Notifications** — list, unread count, mark read

Out of scope for v1: employee claim submission UI, admin config screens, OCR/upload flows.

---

## 9) Open questions / follow-ups

- Do accountant/HOD screens need departments/regions/categories for filtering? If so, either
  loosen those admin-only config endpoints or add read-only variants.
- Tighten `cors_origin_list` to the real web app origin before production deploy.
- Confirm whether `finance_manager` stage/queue should also be reachable from this same web app,
  or is genuinely out of scope for now.
