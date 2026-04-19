import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _read_env(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value is not None:
        return value

    file_path = os.environ.get(f"{name}_FILE")
    if file_path:
        with open(file_path, encoding="utf-8") as handle:
            return handle.read().strip()

    return default


def _read_bool(name: str, default: bool) -> bool:
    raw = _read_env(name, "true" if default else "false")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


DOWNLOAD_DIR = _read_env(
    "YTDLP_DOWNLOAD_DIR", os.path.join(BASE_DIR, "downloads")
)
DB_PATH = _read_env(
    "YTDLP_DB_PATH", os.path.join(BASE_DIR, "ytdlp_web.db")
)
HOST = _read_env("YTDLP_HOST", "0.0.0.0")
PORT = int(_read_env("YTDLP_PORT", "8081"))
MAX_CONCURRENT_DOWNLOADS = int(_read_env("YTDLP_MAX_CONCURRENT", "3"))

NODE_PATH = _read_env("YTDLP_NODE_PATH", "").strip()
PROXY_URL = _read_env("YTDLP_PROXY_URL", "").strip()
PROXY_MODE = _read_env("YTDLP_PROXY_MODE", "foreign-only").strip().lower()

ADMIN_PASSWORD = _read_env("YTDLP_ADMIN_PASSWORD", "")
AUTH_ENABLED = bool(ADMIN_PASSWORD)
SESSION_SECRET = _read_env(
    "YTDLP_SESSION_SECRET", "dev-session-secret-change-me"
)
SESSION_COOKIE_NAME = _read_env(
    "YTDLP_SESSION_COOKIE_NAME", "ytdlp_web_session"
)
SESSION_MAX_AGE = int(_read_env("YTDLP_SESSION_MAX_AGE", "43200"))
SESSION_SECURE = _read_bool("YTDLP_SESSION_SECURE", False)
