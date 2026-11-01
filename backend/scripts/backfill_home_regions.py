"""Save every user's ERP home company (ErpAuthExpenseUsers.homeRegionId) in one go.

Login already saves it (region_scope.remember_home_region), but only for people who sign in.
Until then a user with no home company and no Admin-ticked companies counts as covering
EVERY company: an Accountant, FM or HOD sees all companies' bills, and an employee can file
under any company. Run this once after deploying the region-scoped approvers.

Same source as login: ErpMasterEmployee.regionId -> ErpMasterRegion.subsidiaryId ->
ErpMasterSubsidiary.subsidiaryCode -> app region (auth.security.ERP_SUBSIDIARY_TO_REGION_CODE),
read for all users in a few bulk queries instead of one per person.

Dry-run by default. To save:

    cd backend
    python -m scripts.backfill_home_regions --apply
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from sqlalchemy import bindparam, text

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from sqlalchemy.orm import joinedload

from auth.security import ERP_SUBSIDIARY_TO_REGION_CODE
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseMultiRegionUserRegion,
    ErpExpenseRegionConfig,
    SessionLocal,
)

APPROVER_ROLES = ("hod", "accountant", "finance_manager")
# SQL Server allows ~2100 parameters per statement.
_CHUNK = 500

_ERP_SQL = text(
    "SELECT me.userId, s.subsidiaryCode "
    "FROM ErpMasterEmployee me "
    "JOIN ErpMasterRegion r ON r.regionId = me.regionId "
    "JOIN ErpMasterSubsidiary s ON s.subsidiaryId = r.subsidiaryId "
    "WHERE me.userId IN :ids"
).bindparams(bindparam("ids", expanding=True))


def fetch_erp_subsidiaries(db, user_ids: list[int]) -> dict[int, set[str]]:
    """userId -> ERP subsidiary codes (normally exactly one)."""
    out: dict[int, set[str]] = {}
    for i in range(0, len(user_ids), _CHUNK):
        for uid, code in db.execute(_ERP_SQL, {"ids": user_ids[i : i + _CHUNK]}).all():
            if code:
                out.setdefault(uid, set()).add(code.strip())
    return out


@dataclass
class Plan:
    changes: list[tuple[ErpAuthExpenseUsers, Optional[int], int]] = field(default_factory=list)
    unchanged: int = 0
    # (user, reason) -- these keep no home company.
    unresolved: list[tuple[ErpAuthExpenseUsers, str]] = field(default_factory=list)


def build_plan(db, users: list[ErpAuthExpenseUsers], erp: dict[int, set[str]]) -> Plan:
    region_ids = {
        (code or "").upper(): rid
        for rid, code in db.query(ErpExpenseRegionConfig.region_id, ErpExpenseRegionConfig.region_code)
    }
    plan = Plan()
    for user in users:
        subsidiaries = erp.get(user.user_id)
        if not subsidiaries:
            plan.unresolved.append((user, "no region on their ERP employee record"))
            continue
        codes = {ERP_SUBSIDIARY_TO_REGION_CODE.get(s) for s in subsidiaries}
        if None in codes:
            unknown = sorted(s for s in subsidiaries if s not in ERP_SUBSIDIARY_TO_REGION_CODE)
            plan.unresolved.append((user, f"ERP subsidiary not mapped to an app company: {', '.join(unknown)}"))
            continue
        if len(codes) > 1:
            plan.unresolved.append((user, f"several ERP companies: {', '.join(sorted(codes))}"))
            continue
        code = codes.pop()
        region_id = region_ids.get(code)
        if region_id is None:
            plan.unresolved.append((user, f"company {code} has no ErpExpenseRegionConfig row"))
            continue
        if user.home_region_id == region_id:
            plan.unchanged += 1
        else:
            plan.changes.append((user, user.home_region_id, region_id))
    return plan


def _role(user: ErpAuthExpenseUsers) -> str:
    return user.role.role_code if user.role else "?"


def _column_exists(db) -> bool:
    if db.get_bind().dialect.name != "mssql":
        return True
    return db.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME = 'ErpAuthExpenseUsers' AND COLUMN_NAME = 'homeRegionId'"
        )
    ).first() is not None


def run(db, apply: bool) -> int:
    if not _column_exists(db):
        print("ErpAuthExpenseUsers.homeRegionId is missing. Start the backend once (or run "
              "scripts/add_currency_region_payment_schema.py) and try again.")
        return 1
    users = (
        db.query(ErpAuthExpenseUsers)
        .options(joinedload(ErpAuthExpenseUsers.role))
        .filter(ErpAuthExpenseUsers.is_active == 1, ErpAuthExpenseUsers.is_deleted == 0)
        .order_by(ErpAuthExpenseUsers.user_id)
        .all()
    )
    erp = fetch_erp_subsidiaries(db, [u.user_id for u in users])
    plan = build_plan(db, users, erp)
    names = {rid: code for rid, code in db.query(ErpExpenseRegionConfig.region_id, ErpExpenseRegionConfig.region_code)}

    print(f"Active users: {len(users)}")
    print(f"  already correct:   {plan.unchanged}")
    print(f"  to set / change:   {len(plan.changes)}")
    print(f"  can't resolve:     {len(plan.unresolved)}")
    if plan.changes:
        print("\nChanges:")
        for user, old, new in plan.changes:
            print(f"  {user.user_name:<28} {_role(user):<16} {names.get(old, '-') if old else '-':>6} -> {names[new]}")

    # People with no home company keep covering every company unless Admin ticked some.
    ticked = {
        uid for (uid,) in db.query(ErpExpenseMultiRegionUserRegion.user_id).filter(
            ErpExpenseMultiRegionUserRegion.is_active == 1
        )
    }
    open_approvers = [
        (u, why) for u, why in plan.unresolved
        if _role(u) in APPROVER_ROLES and u.home_region_id is None and u.user_id not in ticked
    ]
    if plan.unresolved:
        print("\nCan't resolve (left as they are):")
        for user, why in plan.unresolved:
            print(f"  {user.user_name:<28} {_role(user):<16} {why}")
    if open_approvers:
        print(
            f"\nWARNING: {len(open_approvers)} approver(s) above still cover EVERY company. "
            "Tick their companies in Admin -> People:"
        )
        for user, _ in open_approvers:
            print(f"  {user.user_name} ({_role(user)})")

    if not plan.changes:
        print("\nNothing to save.")
        return 0
    if not apply:
        print("\nDry-run only. Re-run with --apply to save these changes.")
        return 0
    for user, _, new in plan.changes:
        user.home_region_id = new
    db.commit()
    print(f"\nSaved home company for {len(plan.changes)} user(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Save every user's ERP home company.")
    parser.add_argument("--apply", action="store_true", help="Save. Without this flag the script only reports.")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        return run(db, args.apply)
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
