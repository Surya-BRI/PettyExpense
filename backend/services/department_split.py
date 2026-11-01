"""Which department owns each part of a bill.

A line whose category is owned by another department (e.g. an IT item on a Sales
employee's bill) belongs to that department: it needs that department's HOD approval
and, for petty cash, comes out of that department's fund. Everything else stays with
the employee's own department. Single-item bills use the claim category.
"""
from typing import Optional

from database.models import ErpExpenseCategory, ErpExpenseTransaction

DEPARTMENT_HOD = "department_hod"


def stage_key(department_id: int) -> str:
    return f"{DEPARTMENT_HOD}:{department_id}"


def stage_base(stage: Optional[str]) -> Optional[str]:
    """'department_hod:12' -> 'department_hod'; other stages unchanged."""
    return stage.split(":", 1)[0] if stage else stage


def stage_department_id(stage: Optional[str]) -> Optional[int]:
    if not stage or ":" not in stage:
        return None
    try:
        return int(stage.split(":", 1)[1])
    except ValueError:
        return None


def _other_department(category: Optional[ErpExpenseCategory], own_department_id: Optional[int]) -> Optional[int]:
    dept = category.owning_department_id if category else None
    return dept if dept and dept != own_department_id else None


def _own_department_id(txn: ErpExpenseTransaction) -> Optional[int]:
    return txn.employee.department_id if txn.employee else None


def cross_department_ids(txn: ErpExpenseTransaction) -> list[int]:
    """Departments other than the employee's own that own part of this bill, in line order."""
    own = _own_department_id(txn)
    categories = [li.category or txn.category for li in txn.line_items] if txn.line_items else [txn.category]
    out: list[int] = []
    for category in categories:
        dept = _other_department(category, own)
        if dept and dept not in out:
            out.append(dept)
    return out


def department_shares(txn: ErpExpenseTransaction) -> dict[Optional[int], float]:
    """Bill total (bill currency) split by owning department. Key None = the employee's
    own department; other keys are the cross-department owners. Lines are scaled so the
    shares always add up to the bill total."""
    own = _own_department_id(txn)
    total = float(txn.total_amount or ((txn.amount or 0) + (txn.vat_amount or 0)))
    if not txn.line_items:
        return {_other_department(txn.category, own): total}
    raw: dict[Optional[int], float] = {}
    for li in txn.line_items:
        key = _other_department(li.category or txn.category, own)
        raw[key] = raw.get(key, 0.0) + float(li.amount or 0)
    lines_total = sum(raw.values())
    if lines_total <= 0:
        return {None: total}
    return {key: total * part / lines_total for key, part in raw.items()}
