import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..auth import require_admin
from ..models import (
    DownloadRequest, DownloadResponse, ExtractRequest, ExtractResponse,
)
from .. import downloader, database

router = APIRouter(prefix="/api", dependencies=[Depends(require_admin)])


@router.post("/extract", response_model=ExtractResponse)
async def extract_info(req: ExtractRequest):
    try:
        info = downloader.extract_video_info(req.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download", response_model=DownloadResponse)
async def create_download(req: DownloadRequest):
    # First extract info to get metadata
    try:
        video_info = downloader.extract_video_info(req.url)
    except Exception:
        video_info = None

    task_id = downloader.start_download(
        url=req.url,
        format_str=req.format,
        audio_only=req.audio_only,
        audio_format=req.audio_format,
        remux_video=req.remux_video,
        video_info=video_info,
    )
    return DownloadResponse(
        task_id=task_id,
        status="pending",
        video_id=video_info.get("id") if video_info else None,
        title=video_info.get("title") if video_info else None,
    )


@router.get("/downloads")
async def list_downloads(limit: int = 50, offset: int = 0):
    return database.list_downloads(limit, offset)


@router.get("/downloads/{task_id}")
async def get_download(task_id: str):
    record = database.get_download(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="下载任务不存在")
    return record


@router.delete("/downloads/{task_id}")
async def delete_download(task_id: str):
    record = database.get_download(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="下载任务不存在")
    database.delete_download(task_id)
    return {"ok": True}


@router.get("/downloads/{task_id}/file")
async def download_file(task_id: str):
    record = database.get_download(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="下载任务不存在")
    filepath = record.get("filepath")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在或已被删除")
    return FileResponse(
        filepath,
        filename=record.get("filename") or os.path.basename(filepath),
        media_type="application/octet-stream",
    )
