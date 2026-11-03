# Changelog

Newest first. Each entry says what changed for users, what changed in the code, and anything left to do.

---

## 2026-11-02 — Company (region) filter on the approval queue

Branch: `indra` (not yet committed)

### What changed for users

- The Accountant's claims page (the approval queue) has a company filter: a dropdown at the right end of the status chips row ("All regions", then each region by its short name).
- The filter works on the page itself, together with the status filter (All / New / Disputed). For example, "New" with "KSA" shows only new KSA claims.
- The same queue screen serves HOD and Finance Manager, so they get the filter too.
- The chips show only the companies that person has access to: their home company plus the companies Admin ticked for them in People. This is the same rule the backend uses to send bills to their queue.
- People with no such list (Admin, or older accounts with no company set) see the companies that appear in their queue.
- The dropdown appears only when there is more than one company to choose from.

### Code

- `lib/src/features/approvals/approval_queue_screen.dart`: takes the companies from the signed-in user's `allowedRegions` (set at login by `selectable_regions_for`), falling back to the companies in the loaded queue. It filters the loaded queue by `regionCode` on the device, with no new API call per filter, and the empty message names the company.

### Checks

- Flutter analyze on the file: no issues.
- Flutter tests: `widget_test.dart` "App boots to home" fails with and without this change, so it was already failing.

---

## 2026-11-02 — Vendor matching and the vendor list removed

Branch: `indra` (not yet committed)

### What changed for users

- The vendor on a bill is now just the name typed or scanned from the bill. It is no longer matched against a vendor list.
- **Accountant:** the "Link to existing vendor / Confirm as new vendor" step is gone. Accountants approve, dispute or reject as usual.
- **HOD, department HOD and Finance Manager:** the "Unmatched vendor" notice is gone.
- **Web dashboard (app and web-admin):** the "Unmatched vendors" group, the "New vendor" / "Not in vendor list" tags and the vendor icon in the claims list are gone. The "Flagged only" filter now shows possible duplicates only.
- **Claims CSV export (web-admin):** the "Vendor unmatched" column is gone.
- **Admin:** the vendor list (list, add, delete) is gone. There were no vendor screens in the app or web-admin, only the backend endpoints.

### Behaviour change: duplicate check

- The "same employee, vendor, amount and date" duplicate check now compares the vendor name as text.
- Before, it only worked when the vendor matched the vendor list, so bills with an unmatched vendor were never checked. Now every bill is checked.
- Older bills that were linked to a vendor record still match by that vendor's name.

### Code

**Backend**
- `services/transaction_service.py`
  - New bills and draft edits save the vendor name in `vendorRawText` and leave `vendorId` empty.
  - New helper `vendor_display_name(txn)` returns the bill's vendor text, or the linked vendor's name on older bills.
  - `_find_duplicate` compares vendor text.
  - `vendor_unmatched` was removed from the claim API.
- `services/approval_service.py`
  - `resolve_vendor` was removed.
  - Bulk approve at the Accountant stage no longer skips bills with an unmatched vendor; it still skips possible duplicates.
- `api/routes_approvals.py`: `POST /api/approvals/{id}/resolve-vendor` was removed.
- `api/routes_claims.py`: `GET /api/vendors` was removed. It was a read-only list that only fed the resolve picker.
- `api/routes_config.py` and `services/config_service.py`: `GET/POST /api/admin/config/vendors` and `DELETE /api/admin/config/vendors/{id}` were removed.
- `services/ocr_service.py`: the old text-OCR path no longer loads vendor names as hints. The live GPT-vision scanner never used them.
- `services/email_templates.py`: the vendor name comes from the bill text, with a fallback to the linked vendor on older bills.
- `scripts/seed_phase1_reference_data.py`: no longer seeds sample vendors.

**Flutter app**
- `api/api_client.dart`: `resolveVendor()` and `vendors()` were removed.
- `api/models.dart`: `ExpenseClaim.vendorUnmatched` and `VendorRef` were removed.
- `approvals/approval_detail_screen.dart`: the vendor resolve card and the unmatched-vendor notice were removed.
- `web/dashboard_screen.dart` and `web/all_claims_screen.dart`: the unmatched-vendor group, flag and filter were removed.

**Web-admin**
- `api/client.ts` and `api/types.ts`: `resolveVendor`, `vendors`, `VendorRef` and `vendor_unmatched` were removed.
- Pages: the vendor resolver was removed from `ClaimDetailPage.tsx`, and the vendor tags, filter and CSV column were removed from `ClaimsPage.tsx`, `ApprovalsPage.tsx` and `DashboardPage.tsx`.

**Docs:** `README.md` and `web-admin/README.md` no longer list the removed endpoints.

### Checks

- Backend tests: 339 passed, 5 skipped, 2 expected failures. The API loads cleanly.
- Flutter analyze on the changed files found no errors.
- Web-admin was not compiled because its packages aren't installed on this machine. It was checked by hand for leftover references.

### Database

- No migration is needed. `vendorRawText` already exists.
- New bills leave `vendorId` empty. Older bills keep their `vendorId` and still show that vendor's name.

### Left for later

- **The `ErpExpenseVendor` table is still in the database.**
  - Older bills still point to it, and the duplicate check uses those names for those bills.
  - Nothing adds or edits rows in it any more.
  - To drop it: write a one-time script that copies each linked vendor's name into the bill's `vendorRawText`. Then remove the `vendorId` column, the `vendor` relationship and the table, along with the old-row fallbacks in `vendor_display_name`, `email_templates._vendor_name` and `_find_duplicate`.
- **Old history rows** with the action `vendor_resolved` stay in the log. They are hidden from approver history, and the web dashboard still has an icon for them.
- **Older plan docs** describe the removed feature: `PETTY_CASH_PHASED_PLAN.md` (Phase 4) and `ACCOUNTANT_HOD_WEB_APP_PLAN.md`. They were not updated.
