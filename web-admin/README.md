# Expense Tracker — web dashboard

Web dashboard for the Blue Rhine **Petty Cash & Expense Tracker**. Employees scan bills in the
mobile app; this site shows every claim, where it is in the approval chain (HOD → Accountant →
Finance Manager → Paid), and lets approvers act on it. It signs in with the same accounts as the
mobile app.

Built with React 19 + TypeScript + Vite. It is a static site — all data comes from the existing
FastAPI backend over HTTPS.

## Backend

| | |
|---|---|
| Production API | `https://expensetracker-api.app-brisigns.com` |
| Health check | `https://expensetracker-api.app-brisigns.com/health` |
| Auth | JWT — `POST /api/auth/login` (username, password, region), refreshed automatically |
| CORS | The backend's `CORS_ORIGINS` must allow this site's domain (it is `*` today) |

The site picks the backend from **`VITE_API_BASE_URL`**. If it isn't set, it falls back to the
production API above.

Endpoints used: `/api/auth/*`, `/api/admin/claims`, `/api/claims/*`, `/api/approvals/*`,
`/api/admin/claims/{id}/mark-paid`, `/api/vendors`, `/api/notifications/*`, and
`/api/admin/activity` (the dashboard's activity feed; shows a notice if the backend doesn't have it yet).

## Run locally

```bash
npm install
cp .env.example .env    # then edit if you want a local backend
npm run dev             # http://localhost:5173
```

`.env`:

```env
VITE_API_BASE_URL=https://expensetracker-api.app-brisigns.com   # production (default)
# VITE_API_BASE_URL=http://127.0.0.1:8000                        # local backend
```

Restart `npm run dev` after changing it. A "Local backend" pill shows in the top bar when it points at localhost.

## Deploy on Vercel

1. In Vercel: **Add New → Project → Import** this Git repository.
2. Framework preset **Vite** is detected from `vercel.json` (build `npm run build`, output `dist`).
3. **Settings → Environment Variables**: add `VITE_API_BASE_URL` = `https://expensetracker-api.app-brisigns.com`
   for Production (and Preview if you use it). Optional — the code already defaults to this.
4. **Deploy.** Every push to the main branch redeploys automatically.

`vercel.json` rewrites every path to `index.html`, so deep links like `/claims/51` and page refreshes work.
The page is marked `noindex` so the internal tool stays out of search engines.

## Other hosting

`npm run build` produces `dist/`. Serve it as static files with a fallback to `index.html`, e.g. nginx:

```nginx
location / {
    root /var/www/expense-web;
    try_files $uri /index.html;
}
```

## What each role sees

| Role | Data | Actions |
|---|---|---|
| Employee | Own claims only (`/api/claims/mine`) | Submit draft, resubmit a disputed claim |
| HOD / Accountant / Finance Manager / Admin | Every claim (`/api/admin/claims`) | Approve / dispute / reject at their stage; Accountant resolves unmatched vendors; Finance Manager marks paid |

Buttons only appear when the backend would accept the action; the backend still enforces every rule.

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Dev server with hot reload |
| `npm run build` | Type-check + production build into `dist/` |
| `npm run lint` | Lint (oxlint) |
| `npm run preview` | Serve the built `dist/` locally |
