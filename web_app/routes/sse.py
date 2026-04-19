import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..auth import require_admin
from .. import downloader

router = APIRouter()


@router.get("/api/downloads/{task_id}/progress", dependencies=[Depends(require_admin)])
async def download_progress(task_id: str):
    async def event_generator():
        # Send current state immediately
        current = downloader.get_progress(task_id)
        if current:
            yield f"data: {json.dumps(current, ensure_ascii=False)}\n\n"
            if current.get("status") in ("complete", "error"):
                return

        q = downloader.subscribe_progress(task_id)
        try:
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    if data.get("status") in ("complete", "error"):
                        return
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            downloader.unsubscribe_progress(task_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
