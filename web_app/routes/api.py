import os
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..auth import require_admin
from ..models import (
    BilibiliCookieStatus,
    BilibiliCookieUpdate,
    DownloadRequest,
    DownloadResponse,
    ExtractRequest,
    ExtractResponse,
    ProxySettings,
)
from .. import downloader, database
from ..site_cookies import normalize_bilibili_cookies

router = APIRouter(prefix="/api", dependencies=[Depends(require_admin)])


def _validate_proxy_settings(payload: ProxySettings) -> ProxySettings:
    proxy_url = payload.proxy_url.strip()

    if payload.proxy_enabled:
        if not proxy_url:
            raise HTTPException(status_code=400, detail="启用代理时必须填写代理地址")
        parsed = urlparse(proxy_url)
        if not parsed.scheme or not parsed.netloc:
            raise HTTPException(status_code=400, detail="代理地址格式不正确")

    return ProxySettings(
        proxy_enabled=payload.proxy_enabled,
        proxy_url=proxy_url,
        proxy_mode=payload.proxy_mode,
    )


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


@router.get("/settings", response_model=ProxySettings)
async def get_settings():
    return ProxySettings(**database.get_proxy_settings())


@router.put("/settings/proxy", response_model=ProxySettings)
async def update_settings(payload: ProxySettings):
    normalized = _validate_proxy_settings(payload)
    database.update_proxy_settings(
        proxy_enabled=normalized.proxy_enabled,
        proxy_url=normalized.proxy_url,
        proxy_mode=normalized.proxy_mode,
    )
    return normalized


@router.get("/settings/bilibili", response_model=BilibiliCookieStatus)
async def get_bilibili_settings():
    return BilibiliCookieStatus(**database.get_bilibili_cookie_settings())


@router.put("/settings/bilibili", response_model=BilibiliCookieStatus)
async def update_bilibili_settings(payload: BilibiliCookieUpdate):
    current = database.get_bilibili_cookie_settings(include_secret=True)
    cookies_text = None

    if payload.clear_cookies:
        cookies_text = ""
        payload.cookies_enabled = False
    elif payload.cookies_text.strip():
        try:
            cookies_text = normalize_bilibili_cookies(payload.cookies_text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    effective_cookie_text = (
        cookies_text if cookies_text is not None else current.get("cookies_text", "")
    )
    if payload.cookies_enabled and not effective_cookie_text.strip():
        raise HTTPException(
            status_code=400,
            detail="启用 B 站 Cookie 前，请先粘贴 Cookie 内容",
        )

    database.update_bilibili_cookie_settings(
        cookies_enabled=payload.cookies_enabled,
        cookies_text=cookies_text,
    )
    return BilibiliCookieStatus(**database.get_bilibili_cookie_settings())


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
