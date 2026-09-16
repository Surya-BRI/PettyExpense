from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import (
    CurrentUser,
    allowed_regions_for,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_user_by_id,
)
from config import get_settings
from database.models import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str
    region_code: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


def _user_dict(user, region_code: Optional[str] = None) -> dict:
    return {
        "id": user.user_id,
        "username": user.user_name,
        "display_name": user.display_name,
        "role": user.role.role_code,
        "department_id": user.department_id,
        "email": user.email,
        "region_code": region_code,
    }


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # A multi-region user must pick one of their assigned regions; a single-region user
    # isn't restricted, so whatever (or nothing) they send is accepted as-is.
    allowed = allowed_regions_for(db, user)
    region_code = body.region_code
    if allowed and region_code not in allowed:
        raise HTTPException(
            status_code=400, detail=f"Choose a region to sign in with: {', '.join(allowed)}"
        )

    return TokenResponse(
        access_token=create_access_token(user, region_code),
        refresh_token=create_refresh_token(user, region_code),
        user=_user_dict(user, region_code),
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
    return TokenResponse(
        access_token=create_access_token(user, region_code),
        refresh_token=create_refresh_token(user, region_code),
        user=_user_dict(user, region_code),
    )


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "department_id": user.department_id,
        "email": user.email,
        "region_code": user.region_code,
    }


@router.post("/logout")
def logout():
    return {"ok": True}
