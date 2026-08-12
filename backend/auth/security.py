from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload

from config import get_settings
from database.models import ErpAuthExpenseUsers, SessionLocal, get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)
settings = get_settings()

# Role vocabulary: employee | hod | accountant | finance_manager | admin.
# "department_hod" is a workflow *stage* name (Phase 2), not a role row here — whether an
# hod-role user acts on the base "hod" stage or the "department_hod" stage for a given
# transaction is resolved via ErpExpenseHodAssignment, not a distinct role.
ROLE_CODES = ["employee", "hod", "accountant", "finance_manager", "admin"]

DEFAULT_MOCK_USERNAME = "surya"

# Demo users seeded on startup. Departments/regions referenced by name are created by
# backend/scripts/seed_phase1_reference_data.py before these run (main.py calls the
# reference-data seed before seed_users()). surya/raghu sit in Sales, under sajeesh
# (Sales HOD); denny heads IT, so an IT-category claim from surya/raghu picks up denny
# as the department_hod stage.
SEED_USERS = [
    {
        "username": "surya",
        "display_name": "Surya",
        "password": "surya123",
        "role": "employee",
        "department": "Sales",
        "email": "surya@example.com",
    },
    {
        "username": "raghu",
        "display_name": "Raghu",
        "password": "raghu123",
        "role": "employee",
        "department": "Sales",
        "email": "raghu@example.com",
    },
    {
        "username": "denny",
        "display_name": "Denny",
        "password": "denny123",
        "role": "hod",
        "department": "IT",
        "email": "denny@example.com",
    },
    {
        "username": "vikram",
        "display_name": "Vikram",
        "password": "vikram123",
        "role": "employee",
        "department": "IT",
        "email": "vikram@example.com",
    },
    {
        "username": "sajeesh",
        "display_name": "Sajeesh",
        "password": "sajeesh123",
        "role": "hod",
        "department": "Sales",
        "email": "sajeesh@example.com",
    },
    {
        "username": "anjana",
        "display_name": "Anjana",
        "password": "anjana123",
        "role": "accountant",
        "department": None,
        "email": "anjana@example.com",
    },
    {
        "username": "sandeep",
        "display_name": "Sandeep",
        "password": "sandeep123",
        "role": "finance_manager",
        "department": None,
        "email": "sandeep@example.com",
    },
    {
        "username": "rajesh",
        "display_name": "Rajesh",
        "password": "rajesh123",
        "role": "finance_manager",
        "department": None,
        "email": "rajesh@example.com",
    },
    {
        "username": "teja",
        "display_name": "Teja",
        "password": "teja123",
        "role": "admin",
        "department": None,
        "email": "teja@example.com",
    },
]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(user: ErpAuthExpenseUsers) -> str:
    return create_token(
        {
            "sub": str(user.user_id),
            "role": user.role.role_code,
            "name": user.display_name,
            "type": "access",
        },
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user: ErpAuthExpenseUsers) -> str:
    return create_token(
        {"sub": str(user.user_id), "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def seed_users() -> None:
    from database.models import ErpExpenseDepartment, ErpMasterExpenseRole

    db = SessionLocal()
    try:
        role_by_code = {r.role_code: r for r in db.query(ErpMasterExpenseRole).all()}
        dept_by_name = {d.department_name: d for d in db.query(ErpExpenseDepartment).all()}

        for seed in SEED_USERS:
            existing = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_name == seed["username"]).first()
            if existing:
                continue
            role = role_by_code.get(seed["role"])
            if not role:
                continue  # reference data not seeded yet; seed_phase1_reference_data.py runs first
            dept = dept_by_name.get(seed["department"]) if seed["department"] else None
            db.add(
                ErpAuthExpenseUsers(
                    user_name=seed["username"],
                    display_name=seed["display_name"],
                    password_hash=hash_password(seed["password"]),
                    role_id=role.role_id,
                    department_id=dept.department_id if dept else None,
                    email=seed["email"],
                    is_active=1,
                    is_deleted=0,
                )
            )
        db.commit()
    finally:
        db.close()


def get_user_by_id(db: Session, user_id: int) -> Optional[ErpAuthExpenseUsers]:
    return (
        db.query(ErpAuthExpenseUsers)
        .options(joinedload(ErpAuthExpenseUsers.role))
        .filter(
            ErpAuthExpenseUsers.user_id == user_id,
            ErpAuthExpenseUsers.is_active == 1,
            ErpAuthExpenseUsers.is_deleted == 0,
        )
        .first()
    )


def get_user_by_username(db: Session, username: str) -> Optional[ErpAuthExpenseUsers]:
    return (
        db.query(ErpAuthExpenseUsers)
        .options(joinedload(ErpAuthExpenseUsers.role))
        .filter(
            ErpAuthExpenseUsers.user_name == username,
            ErpAuthExpenseUsers.is_active == 1,
            ErpAuthExpenseUsers.is_deleted == 0,
        )
        .first()
    )


def authenticate_user(db: Session, username: str, password: str) -> Optional[ErpAuthExpenseUsers]:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


class CurrentUser:
    def __init__(self, id: int, display_name: str, role: str, email: Optional[str] = None, department_id: Optional[int] = None):
        self.id = id
        self.display_name = display_name
        self.role = role
        self.email = email
        self.department_id = department_id

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_approver(self) -> bool:
        return self.role in ("hod", "accountant", "finance_manager") or self.is_admin


def _to_current_user(user: ErpAuthExpenseUsers) -> CurrentUser:
    return CurrentUser(user.user_id, user.display_name, user.role.role_code, user.email, user.department_id)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    # Mock mode: missing token still yields a default employee so Flutter can ship before auth UI
    if settings.auth_mode == "mock" and credentials is None:
        user = get_user_by_username(db, DEFAULT_MOCK_USERNAME)
        if user:
            return _to_current_user(user)
        return CurrentUser(0, "Mock Employee", "employee")

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
    return _to_current_user(user)


def require_role(*role_codes: str):
    """Factory: only the given role codes (or admin) may proceed."""

    def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in role_codes and not user.is_admin:
            raise HTTPException(status_code=403, detail=f"Requires one of roles: {', '.join(role_codes)}")
        return user

    return _dep


require_approver = require_role("hod", "accountant", "finance_manager")
require_admin = require_role("admin")
