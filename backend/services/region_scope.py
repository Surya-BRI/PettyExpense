"""Which companies (regions) a person handles.

A person covers their home company (ErpAuthExpenseUsers.homeRegionId, saved at login) plus
every company Admin assigned them in ErpExpenseMultiRegionUserRegion. That one set decides
whose bills an HOD, Accountant or Finance Manager approves, which top-ups they can act on,
and which companies an employee may file a bill under.

Someone with no home company recorded yet and no assignments (they haven't signed in since
this was added) is treated as covering every company, so their queue doesn't go empty.
"""
from typing import Optional

from sqlalchemy import and_, exists, or_
from sqlalchemy.orm import Session

from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseMultiRegionUserRegion,
    ErpExpenseRegionConfig,
)


def covers_region(region_id: Optional[int]):
    """SQL filter on ErpAuthExpenseUsers: people who handle bills of this company."""
    if region_id is None:
        return True
    mr = ErpExpenseMultiRegionUserRegion
    assigned_here = exists().where(
        mr.user_id == ErpAuthExpenseUsers.user_id, mr.is_active == 1, mr.region_id == region_id
    )
    any_assignment = exists().where(mr.user_id == ErpAuthExpenseUsers.user_id, mr.is_active == 1)
    return or_(
        ErpAuthExpenseUsers.home_region_id == region_id,
        assigned_here,
        and_(ErpAuthExpenseUsers.home_region_id.is_(None), ~any_assignment),
    )


def belongs_to_region(region_id: int):
    """SQL filter on ErpAuthExpenseUsers: people who are actually in this company -- home
    company, or ticked for it by Admin. Unlike covers_region, someone with no company recorded
    is NOT included (they'd otherwise show up in every company's staff list)."""
    mr = ErpExpenseMultiRegionUserRegion
    return or_(
        ErpAuthExpenseUsers.home_region_id == region_id,
        exists().where(mr.user_id == ErpAuthExpenseUsers.user_id, mr.is_active == 1, mr.region_id == region_id),
    )


def user_region_ids(db: Session, user_id: int) -> Optional[set[int]]:
    """Companies this person covers, or None when unrestricted (see module docstring)."""
    home = db.query(ErpAuthExpenseUsers.home_region_id).filter(ErpAuthExpenseUsers.user_id == user_id).scalar()
    assigned = {
        r
        for (r,) in db.query(ErpExpenseMultiRegionUserRegion.region_id).filter(
            ErpExpenseMultiRegionUserRegion.user_id == user_id,
            ErpExpenseMultiRegionUserRegion.is_active == 1,
        )
    }
    if home is None and not assigned:
        return None
    return assigned | ({home} if home is not None else set())


def user_covers(db: Session, user_id: int, region_id: Optional[int]) -> bool:
    ids = user_region_ids(db, user_id)
    return ids is None or region_id in ids


def region_codes_for(db: Session, region_ids: Optional[set[int]]) -> Optional[set[str]]:
    if region_ids is None:
        return None
    if not region_ids:
        return set()
    return {
        code.upper()
        for (code,) in db.query(ErpExpenseRegionConfig.region_code).filter(
            ErpExpenseRegionConfig.region_id.in_(region_ids)
        )
        if code
    }


def remember_home_region(db: Session, user: ErpAuthExpenseUsers, region_code: Optional[str]) -> None:
    """Saves the ERP home company on the local user row (no-op when unknown or unchanged)."""
    code = (region_code or "").strip().upper()
    if not code:
        return
    region_id = (
        db.query(ErpExpenseRegionConfig.region_id).filter(ErpExpenseRegionConfig.region_code == code).scalar()
    )
    if region_id is None or user.home_region_id == region_id:
        return
    user.home_region_id = region_id
    db.commit()


def require_bill_region_allowed(db: Session, user_id: int, token_region: Optional[str], region_code: str) -> None:
    """An employee files bills only under companies they belong to: their home company, the
    companies Admin assigned them, or the one they're signed in under."""
    allowed = region_codes_for(db, user_region_ids(db, user_id))
    if allowed is None:
        return
    if token_region:
        allowed.add(token_region.strip().upper())
    if (region_code or "").strip().upper() not in allowed:
        raise ValueError("You can only file bills under your own company or companies assigned to you")
