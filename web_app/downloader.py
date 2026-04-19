import asyncio
import os
import shutil
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

from .config import (
    DOWNLOAD_DIR,
    MAX_CONCURRENT_DOWNLOADS,
    NODE_PATH,
)
from .database import create_download, get_proxy_settings, update_download

# Global state
_progress_data: dict[str, dict] = {}
_progress_queues: dict[str, list[asyncio.Queue]] = defaultdict(list)
_executor = ThreadPoolExecutor(
    max_workers=MAX_CONCURRENT_DOWNLOADS, thread_name_prefix="ytdlp"
)
_event_loop: asyncio.AbstractEventLoop | None = None


def set_event_loop(loop: asyncio.AbstractEventLoop):
    global _event_loop
    _event_loop = loop


def get_progress(task_id: str) -> dict | None:
    return _progress_data.get(task_id)


def subscribe_progress(task_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _progress_queues[task_id].append(q)
    return q


def unsubscribe_progress(task_id: str, q: asyncio.Queue):
    queues = _progress_queues.get(task_id, [])
    if q in queues:
        queues.remove(q)
    if not queues:
        _progress_queues.pop(task_id, None)


# 国内站点不走代理
_DOMESTIC_DOMAINS = (
    "bilibili.com", "b23.tv", "bilivideo.com",
    "acfun.cn", "ixigua.com", "douyin.com",
    "kuaishou.com", "youku.com", "iqiyi.com",
    "qq.com", "weibo.com", "xiaohongshu.com",
)


def _needs_proxy(url: str) -> bool:
    try:
        hostname = urlparse(url).hostname or ""
        return not any(
            hostname == d or hostname.endswith("." + d)
            for d in _DOMESTIC_DOMAINS
        )
    except Exception:
        return True


def _base_ydl_opts(url: str = "") -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
    }

    node_path = NODE_PATH or shutil.which("node") or ""
    if node_path:
        opts["js_runtimes"] = {"node": {"path": node_path}}

    proxy_settings = get_proxy_settings()
    proxy_url = proxy_settings["proxy_url"].strip()
    proxy_mode = proxy_settings["proxy_mode"]
    if proxy_settings["proxy_enabled"] and proxy_url:
        if proxy_mode == "always" or (proxy_mode != "never" and (not url or _needs_proxy(url))):
            opts["proxy"] = proxy_url

    return opts


def extract_video_info(url: str) -> dict:
    """Extract video metadata without downloading."""
    ydl_opts = {
        **_base_ydl_opts(url),
        "extract_flat": False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            raise ValueError("无法提取视频信息")
        info = ydl.sanitize_info(info)

    # Reject playlists for now
    if info.get("_type") == "playlist":
        raise ValueError("暂不支持播放列表，请输入单个视频链接")

    # Build simplified format list
    formats = []
    for f in info.get("formats", []):
        formats.append({
            "format_id": f.get("format_id", ""),
            "ext": f.get("ext", ""),
            "resolution": f.get("resolution", ""),
            "fps": f.get("fps"),
            "vcodec": f.get("vcodec", "none"),
            "acodec": f.get("acodec", "none"),
            "filesize": f.get("filesize") or f.get("filesize_approx"),
            "tbr": f.get("tbr"),
            "format_note": f.get("format_note", ""),
        })

    return {
        "id": info.get("id", ""),
        "title": info.get("title", "未知标题"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "duration_string": info.get("duration_string"),
        "uploader": info.get("uploader"),
        "upload_date": info.get("upload_date"),
        "view_count": info.get("view_count"),
        "description": (info.get("description") or "")[:500],
        "formats": formats,
    }


def start_download(url: str, format_str: str, audio_only: bool,
                   audio_format: str, remux_video: str = "",
                   video_info: dict | None = None) -> str:
    """Create a download task and submit to thread pool. Returns task_id."""
    task_id = uuid.uuid4().hex[:12]
    video_id = video_info.get("id") if video_info else None
    title = video_info.get("title") if video_info else None
    thumbnail = video_info.get("thumbnail") if video_info else None

    create_download(
        task_id, url, video_id=video_id, title=title,
        thumbnail=thumbnail, format_str=format_str, audio_only=audio_only,
    )
    _progress_data[task_id] = {"status": "pending", "percent": 0}

    _executor.submit(
        _run_download, task_id, url, format_str, audio_only, audio_format,
        remux_video,
    )
    return task_id


def _notify(task_id: str, data: dict):
    """Thread-safe notification to all SSE listeners."""
    _progress_data[task_id] = data
    if _event_loop is None:
        return
    for q in _progress_queues.get(task_id, []):
        _event_loop.call_soon_threadsafe(q.put_nowait, data)


def _make_progress_hook(task_id: str):
    def hook(d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0
            _notify(task_id, {
                "status": "downloading",
                "percent": round(percent, 1),
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "speed": d.get("speed", 0),
                "eta": d.get("eta", 0),
            })
        elif status == "finished":
            _notify(task_id, {
                "status": "merging",
                "percent": 100,
                "filename": os.path.basename(d.get("filename", "")),
            })
        elif status == "error":
            _notify(task_id, {
                "status": "error",
                "error": "下载过程中出错",
            })
    return hook


def _make_postprocessor_hook(task_id: str):
    def hook(d):
        status = d.get("status")
        if status == "started":
            _notify(task_id, {
                "status": "processing",
                "percent": 100,
                "postprocessor": d.get("postprocessor", ""),
            })
    return hook


def _run_download(task_id: str, url: str, format_str: str,
                  audio_only: bool, audio_format: str, remux_video: str):
    """Run download in background thread."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    postprocessors = []
    if audio_only:
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format or "mp3",
            "preferredquality": "192",
        })
    elif remux_video:
        postprocessors.append({
            "key": "FFmpegVideoRemuxer",
            "preferedformat": remux_video,
        })

    effective_format = format_str
    if audio_only and format_str in ("bestvideo+bestaudio/best", ""):
        effective_format = "bestaudio/best"

    ydl_opts = {
        **_base_ydl_opts(url),
        "format": effective_format or None,
        "outtmpl": {"default": "%(title).100s [%(id)s].%(ext)s"},
        "paths": {"home": DOWNLOAD_DIR},
        "progress_hooks": [_make_progress_hook(task_id)],
        "postprocessor_hooks": [_make_postprocessor_hook(task_id)],
        "postprocessors": postprocessors,
        "overwrites": True,
        "noprogress": False,
    }

    try:
        update_download(task_id, "downloading")
        _notify(task_id, {"status": "downloading", "percent": 0})

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Find actual output file
        filename = None
        filepath = None
        filesize = None
        if info:
            requested = info.get("requested_downloads", [])
            if requested:
                filepath = requested[-1].get("filepath") or requested[-1].get("filename")
                filename = os.path.basename(filepath) if filepath else None
                if filepath and os.path.exists(filepath):
                    filesize = os.path.getsize(filepath)

        update_download(task_id, "complete", filename=filename,
                        filepath=filepath, filesize=filesize)
        _notify(task_id, {
            "status": "complete",
            "filename": filename or "",
            "filesize": filesize or 0,
        })

    except Exception as e:
        error_msg = str(e)
        update_download(task_id, "error", error=error_msg)
        _notify(task_id, {"status": "error", "error": error_msg})
