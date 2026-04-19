from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    password: str


class AuthStatusResponse(BaseModel):
    auth_enabled: bool
    authenticated: bool


class ExtractRequest(BaseModel):
    url: str


class FormatOption(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    fps: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    filesize_approx: Optional[int] = None
    tbr: Optional[float] = None
    format_note: Optional[str] = None


class ExtractResponse(BaseModel):
    id: str
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[float] = None
    duration_string: Optional[str] = None
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[float] = None
    description: Optional[str] = None
    formats: list[FormatOption] = []


class DownloadRequest(BaseModel):
    url: str
    format: str = "bestvideo+bestaudio/best"
    audio_only: bool = False
    audio_format: str = "mp3"
    remux_video: str = ""


class DownloadResponse(BaseModel):
    task_id: str
    status: str
    video_id: Optional[str] = None
    title: Optional[str] = None


class DownloadRecord(BaseModel):
    id: str
    url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    format: Optional[str] = None
    audio_only: bool = False
    status: str
    filename: Optional[str] = None
    filesize: Optional[int] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
