from secrets import compare_digest

from fastapi import HTTPException, Request

from .config import ADMIN_PASSWORD, AUTH_ENABLED


def is_authenticated(request: Request) -> bool:
    if not AUTH_ENABLED:
        return True
    return bool(request.session.get("authenticated"))


def verify_password(password: str) -> bool:
    if not AUTH_ENABLED:
        return True
    return compare_digest(password, ADMIN_PASSWORD)


def login_user(request: Request):
    request.session["authenticated"] = True


def logout_user(request: Request):
    request.session.clear()


def require_admin(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="需要管理员密码")
