from fastapi import APIRouter, HTTPException, Request

from ..auth import is_authenticated, login_user, logout_user, verify_password
from ..config import AUTH_ENABLED, SESSION_SECURE
from ..models import AuthStatusResponse, LoginRequest

router = APIRouter(prefix="/api/auth")


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(request: Request):
    return AuthStatusResponse(
        auth_enabled=AUTH_ENABLED,
        authenticated=is_authenticated(request),
        session_secure=SESSION_SECURE,
    )


@router.post("/login", response_model=AuthStatusResponse)
async def login(request: Request, payload: LoginRequest):
    if not verify_password(payload.password):
        logout_user(request)
        raise HTTPException(status_code=401, detail="密码错误")

    login_user(request)
    return AuthStatusResponse(
        auth_enabled=AUTH_ENABLED,
        authenticated=True,
        session_secure=SESSION_SECURE,
    )


@router.post("/logout", response_model=AuthStatusResponse)
async def logout(request: Request):
    logout_user(request)
    return AuthStatusResponse(
        auth_enabled=AUTH_ENABLED,
        authenticated=False,
        session_secure=SESSION_SECURE,
    )
