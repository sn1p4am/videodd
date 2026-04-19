import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .auth import is_authenticated
from .config import (
    ALLOWED_HOSTS,
    AUTH_ENABLED,
    BASE_DIR,
    DOWNLOAD_DIR,
    HOST,
    PORT,
    SESSION_COOKIE_NAME,
    SESSION_DOMAIN,
    SESSION_MAX_AGE,
    SESSION_SECRET,
    SESSION_SECURE,
)
from .database import init_db
from .routes import api, auth, sse
from . import downloader

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    init_db()
    downloader.set_event_loop(asyncio.get_event_loop())
    if not AUTH_ENABLED:
        logger.warning(
            "admin password auth is disabled because YTDLP_ADMIN_PASSWORD is not set"
        )
    elif not SESSION_SECURE:
        logger.warning(
            "session cookie secure flag is disabled; enable YTDLP_SESSION_SECURE=true for HTTPS deployments"
        )
    yield


app = FastAPI(title="yt-dlp Web", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie=SESSION_COOKIE_NAME,
    domain=SESSION_DOMAIN,
    max_age=SESSION_MAX_AGE,
    same_site="lax",
    https_only=SESSION_SECURE,
)
if ALLOWED_HOSTS != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.include_router(auth.router)
app.include_router(api.router)
app.include_router(sse.router)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/login")
async def login_page(request: Request):
    if not AUTH_ENABLED or is_authenticated(request):
        return RedirectResponse(url="/", status_code=303)
    return FileResponse(os.path.join(BASE_DIR, "static", "login.html"))


@app.get("/")
async def index(request: Request):
    if AUTH_ENABLED and not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))


def main():
    uvicorn.run(
        "web_app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
