import asyncio
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR, DOWNLOAD_DIR, HOST, PORT
from .database import init_db
from .routes import api, sse
from . import downloader


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    init_db()
    downloader.set_event_loop(asyncio.get_event_loop())
    yield


app = FastAPI(title="yt-dlp Web", version="1.0.0", lifespan=lifespan)

app.include_router(api.router)
app.include_router(sse.router)


@app.get("/")
async def index():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))


app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)


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
