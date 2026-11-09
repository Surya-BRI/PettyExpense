from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import (
    CurrentUser,
    FALLBACK_REGION_CODE,
    selectable_regions_for,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_user_by_id,
    resolve_default_region_code,
)
from config import get_settings
from database.models import ErpExpenseDepartment, get_db
from services.region_scope import remember_home_region

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str
    region_code: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class SwitchRegionRequest(BaseModel):
    region_code: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


def _pca_model(db: Session, region_code: Optional[str]) -> str:
    """'employee' when the signed-in company gives petty cash advances per employee and
    project (Professional Signs), else 'department' -- the app picks its petty-cash screens
    from this."""
    from database.models import ErpExpenseRegionConfig
    from services.region_policy import pca_model

    if not region_code:
        return "department"
    region = (
        db.query(ErpExpenseRegionConfig)
        .filter(ErpExpenseRegionConfig.region_code == region_code.strip().upper())
        .first()
    )
    return pca_model(region)


def _user_dict(
    user, region_code: Optional[str] = None, allowed_regions: Optional[list] = None, db: Optional[Session] = None
) -> dict:
    return {
        "pca_model": _pca_model(db, region_code) if db is not None else "department",
        "id": user.user_id,
        "username": user.user_name,
        "display_name": user.display_name,
        "role": user.role.role_code,
        "department_id": user.department_id,
        "department_name": user.department.department_name if user.department else None,
        "email": user.email,
        "region_code": region_code,
        "allowed_regions": allowed_regions or ([region_code] if region_code else []),
    }


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Nobody is prompted at sign-in: everyone starts in their ERP home company
    # (employee -> subsidiary). A multi-region user (ErpExpenseMultiRegionUserRegion)
    # switches afterwards via /switch-region from the side menu.
    home = resolve_default_region_code(db, user.user_id)
    allowed = selectable_regions_for(db, user, home)
    # Approval routing reads the home company from the local row (no ERP query per claim).
    remember_home_region(db, user, home)
    if allowed:
        if body.region_code in allowed:
            region_code = body.region_code
        elif home in allowed:
            region_code = home
        else:
            region_code = allowed[0]
    else:
        region_code = home or body.region_code or FALLBACK_REGION_CODE

    return TokenResponse(
        access_token=create_access_token(user, region_code),
        refresh_token=create_refresh_token(user, region_code),
        user=_user_dict(user, region_code, _sorted_allowed(allowed, home) or [region_code], db),
    )


def _sorted_allowed(allowed: list[str], home: Optional[str]) -> list[str]:
    """Home company first so the side-menu switcher lists it at the top."""
    return sorted(allowed, key=lambda c: (c != home, c))


@router.post("/switch-region", response_model=TokenResponse)
def switch_region(
    body: SwitchRegionRequest,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, current.id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    home = resolve_default_region_code(db, user.user_id)
    allowed = selectable_regions_for(db, user, home)
    wanted = (body.region_code or "").strip().upper()
    if wanted not in allowed:
        raise HTTPException(status_code=403, detail="You are not assigned to that company")
    return TokenResponse(
        access_token=create_access_token(user, wanted),
        refresh_token=create_refresh_token(user, wanted),
        user=_user_dict(user, wanted, _sorted_allowed(allowed, home), db),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.refresh_token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user = get_user_by_id(db, int(payload.get("sub", "0")))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    region_code = payload.get("region")
    home = resolve_default_region_code(db, user.user_id)
    remember_home_region(db, user, home)
    allowed = _sorted_allowed(selectable_regions_for(db, user, home), home)
    return TokenResponse(
        access_token=create_access_token(user, region_code),
        refresh_token=create_refresh_token(user, region_code),
        user=_user_dict(user, region_code, allowed, db),
    )


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Department names live behind admin-only config routes, so the profile gets its own here.
    department = (
        db.query(ErpExpenseDepartment).filter(ErpExpenseDepartment.department_id == user.department_id).first()
        if user.department_id
        else None
    )
    orm = get_user_by_id(db, user.id)
    home = resolve_default_region_code(db, orm.user_id) if orm else None
    assigned = _sorted_allowed(selectable_regions_for(db, orm, home), home) if orm else []
    allowed = assigned or ([user.region_code] if user.region_code else [])
    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "department_id": user.department_id,
        "department_name": department.department_name if department else None,
        "email": user.email,
        "region_code": user.region_code,
        "allowed_regions": allowed,
        "pca_model": _pca_model(db, user.region_code),
    }


@router.post("/logout")
def logout():
    return {"ok": True}
