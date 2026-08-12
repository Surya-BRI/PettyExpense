from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.security import (
    CurrentUser,
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


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


def _user_dict(user) -> dict:
    return {
        "id": user.user_id,
        "username": user.user_name,
        "display_name": user.display_name,
        "role": user.role.role_code,
        "department_id": user.department_id,
        "email": user.email,
    }


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        user=_user_dict(user),
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

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        user=_user_dict(user),
    )


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "department_id": user.department_id,
        "email": user.email,
    }


@router.post("/logout")
def logout():
    return {"ok": True}
