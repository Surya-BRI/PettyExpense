# Department-based approval routing: dev setup, a real multi-HOD bug, and an open perf issue

Session notes, written as a findings record (see git history on `dev-teja` for the actual diffs,
`backend/services/approval_service.py` and `backend/scripts/seed_dev_erp_users.py`).

## 1. Dev accounts restructured around role + department

`backend/scripts/seed_dev_erp_users.py` previously seeded generic `dev_employee`/`dev_hod`/etc.
accounts with no department assigned at all -- confirmed live against `ERP-Dev`: every one of them
had `department_id = None`, so the department-routing logic (§2 below) was never actually
exercisable with them.

Renamed to real-name, role+department-encoded accounts (all password `Test@1234`):

| Account | Role | Department |
|---|---|---|
| `surya_sales_emp` | Employee | Sales |
| `priya_sales_hod` | HOD | Sales |
| `anjana_it_emp` | Employee | IT |
| `vikram_it_hod` | HOD | IT |
| `deepa_accounts_emp` | Employee | Accounts |
| `ravi_accountant` | Accountant | -- (cross-department role) |
| `meera_finance_mgr` | Finance Manager | -- |
| `arjun_admin` | Admin | -- |

The script now looks up department IDs by name and writes `department_id` onto each user's
**local** `ErpAuthExpenseUsers` row -- the one field `authenticate_user()` never overwrites once
the row exists (admin-managed by design, see `auth/security.py`), so this sticks across logins.
`priya_sales_hod`/`vikram_it_hod` also get a real `ErpExpenseHodAssignment` row so the `hod` stage
can actually resolve them. `lib/src/features/authentication/login_screen.dart`'s dev-account
quick-pick dropdown updated to match. `dev_uae`/`dev_ksa`/`dev_oman` (region-testing accounts, a
separate concern from department) were left untouched.

**Bug caught while building this**: the script initially pre-created `vikram_it_hod`'s local row
with a hardcoded `role_code = "employee"` instead of deriving it from the account's actual ERP role
("Department HOD" → `hod`) -- would have silently made the account un-usable as an HOD. Fixed by
deriving role from `erp_role_name` consistently (`ROLE_CODE_BY_ERP_ROLE_NAME`), and made the script
self-correcting: role is now kept in sync on every run for the specific dev user IDs it owns, not
just set once at creation.

## 2. Real bug found: a department with >1 active HOD only let one of them act

Verified end-to-end against the live backend (not just reading code): submitted a real claim as
`surya_sales_emp` (dept Sales) under category "IT Equipment" (`owning_department_id` = IT, already
seeded in `ERP-Dev`). Confirmed `resolve_stage_sequence` correctly produces
`['hod', 'department_hod', 'accountant', 'finance_manager']` -- the department-mismatch splice
works. But the resolved **approver** for `hod` came back as `sajeesh`, not `priya_sales_hod`, even
though `priya_sales_hod` is genuinely an active Sales HOD.

**Root cause**: `_hod_for_department()` (now `_hods_for_department`) used `.filter(...).first()`
with no ordering. `ERP-Dev` already had pre-existing, real, active HOD assignments for Sales/IT
(`sajeesh`/`denny`, user IDs `999999006`/`999999004`) from before this session touched anything.
Once a second active assignment existed for the same department, the query non-deterministically
returned one or the other -- the loser's assignment was **silently dead**: no queue visibility, no
notification, couldn't act even by direct URL. This is a real design gap the system was never built
to handle (it assumed exactly one HOD per department everywhere), not a one-off data conflict.

**Decision (asked, not assumed): support genuine multi-HOD, don't just deactivate the conflicting
real assignment.** `sajeesh`/`denny` were left untouched.

**Fix (`services/approval_service.py`)**:
- `_hod_for_department` → `_hods_for_department`, returns **all** active HODs for a department
  (one joined query, not an assignment lookup followed by a separate user lookup).
- `resolve_stage_approver` → `resolve_stage_approvers`, generalised to **every** stage (hod,
  department_hod, accountant, finance_manager) -- the same single-winner `.first()` pattern existed
  for role-based stages too (confirmed live: `ERP-Dev` already has 2 real accountants and 3 real
  finance managers active simultaneously).
- `resolve_current_approver` → `resolve_current_approvers`.
- Every caller updated: `list_queue`/`advance`/`resolve_vendor`/`bulk_approve` now check **set
  membership** (`user.id in {a.user_id for a in approvers}`) instead of equality to one resolved
  approver; every notification site (`advance`'s next-stage email, `resubmit_after_dispute`,
  `_notify_finance_on_submit`) now loops and notifies **everyone** in the set, deduplicated, with
  delegation still applied per-person.
- `resolve_stage_sequence`'s department_hod auto-skip (don't insert a redundant stage when the
  same person would approve twice) now compares the full HOD **sets** between the employee's own
  department and the category's owning department, not single IDs -- only skips when the sets are
  identical, since any genuinely different reviewer in either set is still a real approval step.

**Verified live**: after the fix, claim 59's `hod` stage resolves to `['priya_sales_hod',
'sajeesh']` -- both, not one replacing the other.

4 new tests in `tests/test_notification_service.py` cover this directly: both resolve as
approvers, both see it in `list_queue`, either one approving advances the stage (first action
wins, not unanimous -- confirmed intentional, not "both must approve"), and submission notifies
both. Full suite: 215 passed, same 8 pre-existing unrelated failures throughout.

## 3. Open, deliberately not fixed this session: `list_queue` is slow against the real DB

Measured live: `priya_sales_hod`'s `hod`-stage queue (5 matching claims) took **58s**, then **26s**
after a partial fix -- both far too slow for 5 rows.

**Fixed this session** (58s → 26s):
- `list_queue` was fetching **every actionable transaction system-wide** (all stages, all
  departments, all regions) with 4 eager joins, then stage-filtering almost all of it away in
  Python. Pushed `current_stage == stage` into the SQL `WHERE` clause instead.
- `resolve_stage_sequence`/`resolve_stage_approvers` were re-querying region/category/employee
  fresh from the DB on every call even though `list_queue` already eager-loads them onto the
  transaction object -- switched to plain relationship access (`txn.region` etc.), removing
  redundant round-trips that were happening **twice per claim** (once for approver resolution,
  once again inside `transaction_to_dict`'s own `resolve_stage_sequence` call for the
  `stage_sequence` field).
- `employee` and `line_items` (+ nested `category`) weren't eager-loaded at all -- `transaction_to_dict`
  accessing `txn.employee.display_name` / `txn.line_items` was lazy-loading them one row at a time.
  Added to the query's eager-load options.
- `_hods_for_department` collapsed from 2 sequential round-trips (assignment lookup, then a
  separate user lookup) to 1 joined query.

**Tried and reverted**: added a 40-candidate SQL ceiling + 6-per-page default (matching
`list_mine`'s existing `limit`/`offset` convention) on the theory that an unbounded candidate scan
was the bottleneck. Measured: **zero effect** -- confirmed only 5 transactions exist at `hod` stage
system-wide right now, so any ceiling above 5 is a no-op. Reverted the `limit`/`offset` API surface
entirely (`routes_approvals.py`'s `/queue` route and `list_queue`'s signature) rather than ship
unused complexity; kept only the proven fixes above.

**Still unexplained**: ~26s for 5 rows is still roughly 5s/row. The DB (`ERP-Dev`,
`13.234.241.125`) is remotely hosted and clearly high-latency from wherever this runs, so the
remaining cost is almost certainly round-trip count × per-trip latency, not row volume. Likely
remaining contributors, not yet profiled:
- `_apply_delegation` does one `ErpExpenseApproverDelegation` query per approver, uncached, inside
  the loop in `resolve_stage_approvers` -- for a stage with N active approvers, that's N round
  trips just for delegation checks.
- `transaction_to_dict`'s own `resolve_stage_sequence(db, txn)` call (for the `stage_sequence`
  field) still re-derives the whole sequence per transaction, including a department-HOD lookup
  when the stages differ -- redundant with the resolution `list_queue` already did for the same
  transaction one line earlier.
- Not measured: whether the remote connection itself has high fixed per-query latency (e.g.
  >200ms/round-trip) such that even a handful of sequential queries per row adds up this way
  regardless of further query-count reduction -- would need actual connection-level timing, not
  just counting queries, to confirm.

**Next step, when revisited**: profile actual query count + per-query timing (not just reasoning
about it) before trying anything further -- avoid another round of "obviously this should help"
changes that don't move the number, same as the 40-candidate-ceiling attempt above.
