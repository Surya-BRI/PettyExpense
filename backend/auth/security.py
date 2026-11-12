import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from config import get_settings
from database.models import ErpAuthExpenseUsers, get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)
settings = get_settings()

# Role vocabulary: employee | hod | accountant | head_accountant | finance_manager | admin.
# head_accountant is Blue Rhine Contracting's second accounts level (Accountant -> Head of
# Accountant -> Finance Manager); Admin sets it in People, or ERP_HEAD_ACCOUNTANT_ROLE_NAMES maps it.
# "department_hod" is a workflow *stage* name (Phase 2), not a role row here — whether an
# hod-role user acts on the base "hod" stage or the "department_hod" stage for a given
# transaction is resolved via ErpExpenseHodAssignment, not a distinct role.
ROLE_CODES = ["employee", "hod", "accountant", "head_accountant", "finance_manager", "admin"]
# Roles that approve bills at some stage.
APPROVER_ROLES = ("hod", "accountant", "head_accountant", "finance_manager")

# ERP ErpMasterRole.roleName -> this app's role. ERP has ~50 granular operational roles
# (SalesRep, Estimator, Driver, ...) with no generic "employee" role, so anything not
# listed here defaults to "employee" (see authenticate_user). There is no ERP role for
# "finance_manager" either — that (and any other one-off elevation) is set by hand on the
# local ErpAuthExpenseUsers row and is never overwritten by login (see authenticate_user).
ERP_ROLE_ID_TO_APP_ROLE = {
    1:      "admin",       # Admin
    102055: "accountant",  # Accountant
    102068: "admin",       # Sub Admin
}

# ERP has one HOD role per department (Design HOD, QC HOD, Estimation HOD, HSE HOD,
# Department HOD, ...) rather than a single generic one, so these are matched by a
# "...HOD" name suffix instead of being listed one roleId at a time in the map above.
ERP_HOD_ROLE_NAME_SUFFIX = "HOD"

# ERP role names (any case) that mean Head of Accountant. ERP has no such role yet; add its
# name here when it does. Until then Admin sets the role in People.
ERP_HEAD_ACCOUNTANT_ROLE_NAMES = {"HEAD OF ACCOUNTANT", "HEAD OF ACCOUNTS", "HEAD ACCOUNTANT", "CHIEF ACCOUNTANT"}


def mapped_app_role(role_id: Optional[int], role_name: Optional[str]) -> Optional[str]:
    """ERP roleId / roleName → this app's role. Same rules as first-login mirroring."""
    if role_id in ERP_ROLE_ID_TO_APP_ROLE:
        return ERP_ROLE_ID_TO_APP_ROLE[role_id]
    if (role_name or "").strip().upper() in ERP_HEAD_ACCOUNTANT_ROLE_NAMES:
        return "head_accountant"
    if (role_name or "").strip().upper().endswith(ERP_HOD_ROLE_NAME_SUFFIX):
        return "hod"
    if role_name:
        return "employee"
    return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(user: ErpAuthExpenseUsers, region_code: Optional[str] = None) -> str:
    return create_token(
        {
            "sub": str(user.user_id),
            "role": user.role.role_code,
            "name": user.display_name,
            "region": region_code,
            "type": "access",
        },
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user: ErpAuthExpenseUsers, region_code: Optional[str] = None) -> str:
    # Carries the region too, so a token refresh can recreate the access token without
    # silently losing the region the user originally signed in under.
    return create_token(
        {"sub": str(user.user_id), "region": region_code, "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def allowed_regions_for(db: Session, user: ErpAuthExpenseUsers) -> list[str]:
    """Region codes a user may sign in under. Empty means not multi-region -- unrestricted."""
    from database.models import ErpExpenseMultiRegionUserRegion, ErpExpenseRegionConfig

    rows = (
        db.query(ErpExpenseRegionConfig.region_code)
        .join(ErpExpenseMultiRegionUserRegion, ErpExpenseMultiRegionUserRegion.region_id == ErpExpenseRegionConfig.region_id)
        .filter(ErpExpenseMultiRegionUserRegion.user_id == user.user_id, ErpExpenseMultiRegionUserRegion.is_active == 1)
        .all()
    )
    return [r[0] for r in rows]


def selectable_regions_for(db: Session, user: ErpAuthExpenseUsers, home: Optional[str]) -> list[str]:
    """Companies a multi-company user can switch to and file bills under: Admin's ticks plus
    their ERP home company, even when it isn't ticked (ticks saved before an ERP transfer, or
    written outside Admin -> People). Only ever adds. Empty = single-company user."""
    ticked = allowed_regions_for(db, user)
    home_code = (home or "").strip().upper()
    if ticked and home_code and home_code not in {c.upper() for c in ticked}:
        return [*ticked, home_code]
    return ticked


# ERP is the directory (login, department, subsidiary). Petty-cash limits, bills, and
# top-ups live only in ErpExpense* tables — never written back to ERP master data.
# ErpMasterSubsidiary.subsidiaryCode (the ERP entity an employee's ErpMasterRegion belongs
# to, via subsidiaryId) -> this app's region_code. Two KSA legal entities both map to KSA.
ERP_SUBSIDIARY_TO_REGION_CODE = {
    # BRI UAE = Blue Rhine Industries (Dubai).
    "BRI UAE": "DUBAI",
    # BRC = Blue Rhine Contracting LLC (ERP subsidiary 10, region "BRC UAE") -> app's UAE company.
    "BRC": "UAE",
    "Prosigns KSA": "KSA",
    "BRI PS Saudi": "KSA",
    "Prosigns Oman": "OMAN",
    "ELJO India": "IN",
}


# Company for someone ERP gives no company at all (no region on their employee record, or an
# unmapped subsidiary). Dubai = Blue Rhine Industries, where most staff are -- not UAE
# (Blue Rhine Contracting), which only BRC-subsidiary employees get.
FALLBACK_REGION_CODE = "DUBAI"


def resolve_default_region_code(db: Session, erp_user_id: int) -> Optional[str]:
    """Region derived from the employee's own ERP data: ErpMasterEmployee.regionId ->
    ErpMasterRegion.subsidiaryId -> ErpMasterSubsidiary.subsidiaryCode. Used so a
    single-region user is never asked to pick one at login -- only users in
    ErpExpenseMultiRegionUserRegion (see allowed_regions_for) are prompted. Returns None if
    the employee has no regionId set or maps to a subsidiary we don't recognize; the caller
    decides the fallback in that case."""
    row = db.execute(
        text(
            "SELECT s.subsidiaryCode "
            "FROM ErpMasterEmployee me "
            "JOIN ErpMasterRegion r ON r.regionId = me.regionId "
            "JOIN ErpMasterSubsidiary s ON s.subsidiaryId = r.subsidiaryId "
            "WHERE me.userId = :uid"
        ),
        {"uid": erp_user_id},
    ).first()
    if not row:
        return None
    return ERP_SUBSIDIARY_TO_REGION_CODE.get(row.subsidiaryCode)


def get_user_by_id(db: Session, user_id: int) -> Optional[ErpAuthExpenseUsers]:
    return (
        db.query(ErpAuthExpenseUsers)
        .options(joinedload(ErpAuthExpenseUsers.role), joinedload(ErpAuthExpenseUsers.department))
        .filter(
            ErpAuthExpenseUsers.user_id == user_id,
            ErpAuthExpenseUsers.is_active == 1,
            ErpAuthExpenseUsers.is_deleted == 0,
        )
        .first()
    )


def authenticate_user(db: Session, username: str, password: str) -> Optional[ErpAuthExpenseUsers]:
    """Validate credentials against the shared ERP tables (ErpAuthUsers /
    ErpAuthUserRoleMap / ErpMasterRole / ErpMasterEmployee) and mirror the result into the
    app's local ErpAuthExpenseUsers row, keyed by the real ERP userId. Role on an existing
    local row is never overwritten here, so manual admin elevation sticks. Department is
    copied from ERP only while the local department_id is still empty."""
    erp_user = db.execute(
        text(
            "SELECT TOP 1 u.userId, u.userName, u.password, "
            "me.firstName, me.lastName, me.emailId AS email, "
            "d.departmentName AS departmentName, "
            "r.roleId AS roleId, r.roleName AS roleName "
            "FROM ErpAuthUsers u "
            "LEFT JOIN ErpMasterEmployee me ON me.userId = u.userId "
            "LEFT JOIN ErpMasterDepartment d ON d.departmentId = me.departmentId "
            "LEFT JOIN ErpAuthUserRoleMap m ON m.userId = u.userId AND m.isActive = 1 "
            "LEFT JOIN ErpMasterRole r ON r.roleId = m.roleId AND r.isActive = 1 AND r.isDeleted = 0 "
            "WHERE u.userName = :username AND u.isActive = 1 AND u.isDeleted = 0 "
            "ORDER BY m.mapId DESC"
        ),
        {"username": username},
    ).first()

    if not erp_user or not verify_password(password, erp_user.password):
        return None

    app_role_code = mapped_app_role(erp_user.roleId, erp_user.roleName) or "employee"

    from database.models import ErpMasterExpenseRole

    dept_id = resolve_local_department_id(db, getattr(erp_user, "departmentName", None))

    local_user = get_user_by_id(db, erp_user.userId)
    if local_user:
        local_user.display_name = _erp_display_name(erp_user)
        local_user.email = erp_user.email
        # Fill department only when still empty so a later admin change is not overwritten.
        if local_user.department_id is None and dept_id is not None:
            local_user.department_id = dept_id
        db.commit()
        return get_user_by_id(db, local_user.user_id)

    role = db.query(ErpMasterExpenseRole).filter(ErpMasterExpenseRole.role_code == app_role_code).first()
    local_user = ErpAuthExpenseUsers(
        user_id=erp_user.userId,
        user_name=erp_user.userName,
        display_name=_erp_display_name(erp_user),
        password_hash=hash_password(secrets.token_hex(32)),  # unused — real auth is against ERP
        role_id=role.role_id,
        department_id=dept_id,
        email=erp_user.email,
        is_active=1,
        is_deleted=0,
    )
    # userId is an IDENTITY column on this local table — we're assigning the real ERP
    # userId explicitly (not letting SQL Server generate one), so IDENTITY_INSERT must be
    # toggled on for the duration of this one insert.
    db.execute(text("SET IDENTITY_INSERT ErpAuthExpenseUsers ON"))
    db.add(local_user)
    db.flush()
    db.execute(text("SET IDENTITY_INSERT ErpAuthExpenseUsers OFF"))
    db.commit()
    return get_user_by_id(db, local_user.user_id)


def resolve_local_department_id(db: Session, department_name: Optional[str]) -> Optional[int]:
    """Match or create an ErpExpenseDepartment row for an ERP department name."""
    from database.models import ErpExpenseDepartment

    name = (department_name or "").strip()
    if not name:
        return None
    wanted = name.lower()
    for row in db.query(ErpExpenseDepartment).all():
        if (row.department_name or "").strip().lower() == wanted:
            return row.department_id
    row = ErpExpenseDepartment(department_name=name, is_active=1)
    db.add(row)
    db.flush()
    return row.department_id


def _erp_display_name(erp_user) -> str:
    name = " ".join(part for part in [erp_user.firstName, erp_user.lastName] if part)
    return name or erp_user.userName


class CurrentUser:
    def __init__(
        self,
        id: int,
        display_name: str,
        role: str,
        email: Optional[str] = None,
        department_id: Optional[int] = None,
        region_code: Optional[str] = None,
    ):
        self.id = id
        self.display_name = display_name
        self.role = role
        self.email = email
        self.department_id = department_id
        self.region_code = region_code

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_approver(self) -> bool:
        return self.role in APPROVER_ROLES or self.is_admin


def _to_current_user(user: ErpAuthExpenseUsers, region_code: Optional[str] = None) -> CurrentUser:
    return CurrentUser(user.user_id, user.display_name, user.role.role_code, user.email, user.department_id, region_code)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    user = get_user_by_id(db, int(user_id_raw))
    if not user:
        raise HTTPException(status_code=401, detail="User not found or not allowlisted")
    return _to_current_user(user, payload.get("region"))


def require_role(*role_codes: str):
    """Factory: only the given role codes (or admin) may proceed."""

    def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in role_codes and not user.is_admin:
            raise HTTPException(status_code=403, detail=f"Requires one of roles: {', '.join(role_codes)}")
        return user

    return _dep


require_approver = require_role(*APPROVER_ROLES)
require_admin = require_role("admin")
