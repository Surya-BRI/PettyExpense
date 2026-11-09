"""Per-company petty-cash settings, read from the company's approvalMatrixJson.

Two models run side by side:

* ``department`` (default; Blue Rhine Industries / Dubai): one pot per department with an
  approved limit; bills with another department's items also go to that department's HOD
  and come off its pot; top-ups go HOD request -> Accounts verify -> FM approve + pay.
* ``employee`` (Professional Signs / KSA, PCA_Professional_Documentation.pdf): each employee
  holds one advance (PCA) for all their projects. The HOD proposes it, the Accounts Manager
  approves and pays it. Bills (each with a project OP code) go Employee -> own HOD ->
  Accounts Manager and petty-cash ones come off the employee's advance. Top-ups go HOD
  approve -> Accounts Manager verify -> Accounts Manager pays (bank withdrawal or direct).

Every key has a default that keeps the department model unchanged, so a company without
these keys behaves exactly as before.
"""
import json
from typing import Any, Optional

from database.models import ErpExpenseRegionConfig

DEPARTMENT_MODEL = "department"
EMPLOYEE_MODEL = "employee"

JOURNAL_TYPES = ("EJV", "EJVB")
JOURNAL_TYPE_LABELS = {"EJV": "Expense Journal (EJV)", "EJVB": "Expense Journal – Branch (EJVB)"}

# Where the money for an advance or top-up came from (PDF section 6 / section 7 Process 1 and 2).
PAYMENT_SOURCES = ("bank", "accounts_petty_cash")
PAYMENT_SOURCE_LABELS = {
    "bank": "Cash withdrawal from bank",
    "accounts_petty_cash": "Direct payment by Accounts Department",
}

# Settings the startup seed applies to Professional Signs' (KSA) matrix. Bills there go
# Employee -> own HOD -> Accounts Manager (no Accountant step); the Accounts Manager books the
# journal (EJV/EJVB) at approval and is the one who pays. Bump EMPLOYEE_PCA_SETTINGS_VERSION
# when these change: a company on an older version gets these keys overwritten once, after
# which only missing keys are added (Admin's later edits are kept).
# 3: re-applies the HOD -> Accounts Manager flow to companies left at 2 with the old values.
EMPLOYEE_PCA_SETTINGS_VERSION = 3
EMPLOYEE_PCA_SETTINGS: dict[str, Any] = {
    "pca_model": EMPLOYEE_MODEL,
    "pca_settings_version": EMPLOYEE_PCA_SETTINGS_VERSION,
    "stages": ["hod", "finance_manager"],
    "cross_department_split": False,
    "stage_labels": {"finance_manager": "Accounts Manager"},
    "journal_required_at": "finance_manager",
    "payer_roles": ["finance_manager"],
    "pca_reminder_ratio": 0.5,
    # Hard limit: bills not yet topped up (approved + in approval) may use at most this share
    # of the employee's PCA; the rest comes back when a top-up is paid.
    "pca_spend_limit_ratio": 0.5,
}


def matrix(region: Optional[ErpExpenseRegionConfig]) -> dict[str, Any]:
    if region is None or not region.approval_matrix_json:
        return {}
    try:
        value = json.loads(region.approval_matrix_json)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def pca_model(region: Optional[ErpExpenseRegionConfig]) -> str:
    return EMPLOYEE_MODEL if matrix(region).get("pca_model") == EMPLOYEE_MODEL else DEPARTMENT_MODEL


def is_employee_model(region: Optional[ErpExpenseRegionConfig]) -> bool:
    return pca_model(region) == EMPLOYEE_MODEL


def splits_by_department(region: Optional[ErpExpenseRegionConfig]) -> bool:
    """Whether another department's items on a bill go to that department (its HOD + its pot)."""
    return bool(matrix(region).get("cross_department_split", True))


def stage_label_overrides(region: Optional[ErpExpenseRegionConfig]) -> dict[str, str]:
    labels = matrix(region).get("stage_labels") or {}
    return {str(k): str(v) for k, v in labels.items() if v} if isinstance(labels, dict) else {}


def journal_stage(region: Optional[ErpExpenseRegionConfig]) -> Optional[str]:
    """The approval stage that must record the journal (EJV/EJVB + number), if any."""
    stage = matrix(region).get("journal_required_at")
    return str(stage) if stage else None


def payer_roles(region: Optional[ErpExpenseRegionConfig]) -> tuple[str, ...]:
    """Roles that record payments for this company (Admin always can)."""
    roles = matrix(region).get("payer_roles")
    if isinstance(roles, list) and roles:
        return tuple(str(r) for r in roles)
    return ("finance_manager",)


def pca_reminder_ratio(region: Optional[ErpExpenseRegionConfig]) -> float:
    """Share of an employee's advance spent at which they are reminded to submit bills."""
    try:
        ratio = float(matrix(region).get("pca_reminder_ratio", 0.5))
    except (TypeError, ValueError):
        return 0.5
    return ratio if 0 < ratio < 1 else 0.5


def pca_spend_limit_ratio(region: Optional[ErpExpenseRegionConfig]) -> Optional[float]:
    """Share of an employee's PCA that bills not yet topped up may use (Professional Signs:
    0.5 -- with SAR 10,000 they can have at most SAR 5,000 of bills out before a top-up).
    None = no cap beyond the PCA itself."""
    value = matrix(region).get("pca_spend_limit_ratio")
    try:
        ratio = float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
    return ratio if ratio is not None and 0 < ratio < 1 else None


def merge_missing(region: ErpExpenseRegionConfig, settings: dict[str, Any]) -> bool:
    """Adds keys the company's matrix doesn't have yet (never overwrites Admin's values).
    Returns True if the row changed."""
    current = matrix(region)
    changed = False
    for key, value in settings.items():
        if key not in current:
            current[key] = value
            changed = True
    if changed:
        region.approval_matrix_json = json.dumps(current)
    return changed


def apply_employee_settings(region: ErpExpenseRegionConfig) -> bool:
    """Startup seed for an employee-advance company: on a settings version older than
    EMPLOYEE_PCA_SETTINGS_VERSION overwrite every key in EMPLOYEE_PCA_SETTINGS once; otherwise
    only add missing keys. Returns True if the row changed."""
    current = matrix(region)
    try:
        version = int(current.get("pca_settings_version") or 0)
    except (TypeError, ValueError):
        version = 0
    if version >= EMPLOYEE_PCA_SETTINGS_VERSION:
        return merge_missing(region, EMPLOYEE_PCA_SETTINGS)
    current.update(EMPLOYEE_PCA_SETTINGS)
    region.approval_matrix_json = json.dumps(current)
    return True
