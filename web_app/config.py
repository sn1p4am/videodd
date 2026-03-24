import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_DIR = os.environ.get(
    "YTDLP_DOWNLOAD_DIR", os.path.join(BASE_DIR, "downloads")
)
DB_PATH = os.environ.get(
    "YTDLP_DB_PATH", os.path.join(BASE_DIR, "ytdlp_web.db")
)
HOST = os.environ.get("YTDLP_HOST", "0.0.0.0")
PORT = int(os.environ.get("YTDLP_PORT", "8080"))
MAX_CONCURRENT_DOWNLOADS = int(os.environ.get("YTDLP_MAX_CONCURRENT", "3"))
