import sqlite3
import os
from .config import DB_PATH, PROXY_MODE, PROXY_URL


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            video_id TEXT,
            title TEXT,
            thumbnail TEXT,
            format TEXT,
            audio_only INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            filename TEXT,
            filepath TEXT,
            filesize INTEGER,
            error TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            completed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.executemany(
        "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
        [
            ("proxy_enabled", "1" if PROXY_URL else "0"),
            ("proxy_url", PROXY_URL),
            ("proxy_mode", PROXY_MODE),
        ],
    )
    conn.commit()
    conn.close()


def create_download(task_id, url, video_id=None, title=None,
                    thumbnail=None, format_str=None, audio_only=False):
    conn = get_connection()
    conn.execute(
        """INSERT INTO downloads (id, url, video_id, title, thumbnail, format, audio_only)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (task_id, url, video_id, title, thumbnail, format_str, int(audio_only)),
    )
    conn.commit()
    conn.close()


def update_download(task_id, status, filename=None, filepath=None,
                    filesize=None, error=None):
    conn = get_connection()
    fields = ["status = ?"]
    values = [status]

    if filename is not None:
        fields.append("filename = ?")
        values.append(filename)
    if filepath is not None:
        fields.append("filepath = ?")
        values.append(filepath)
    if filesize is not None:
        fields.append("filesize = ?")
        values.append(filesize)
    if error is not None:
        fields.append("error = ?")
        values.append(error)
    if status in ("complete", "error"):
        fields.append("completed_at = datetime('now', 'localtime')")

    values.append(task_id)
    conn.execute(
        f"UPDATE downloads SET {', '.join(fields)} WHERE id = ?", values
    )
    conn.commit()
    conn.close()


def get_download(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM downloads WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_downloads(limit=50, offset=0):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM downloads ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_download(task_id):
    conn = get_connection()
    row = conn.execute("SELECT filepath FROM downloads WHERE id = ?", (task_id,)).fetchone()
    if row and row["filepath"] and os.path.exists(row["filepath"]):
        os.remove(row["filepath"])
    conn.execute("DELETE FROM downloads WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_proxy_settings():
    conn = get_connection()
    rows = conn.execute(
        "SELECT key, value FROM app_settings WHERE key IN ('proxy_enabled', 'proxy_url', 'proxy_mode')"
    ).fetchall()
    conn.close()

    values = {row["key"]: row["value"] for row in rows}
    proxy_mode = values.get("proxy_mode") or PROXY_MODE
    if proxy_mode not in {"foreign-only", "always", "never"}:
        proxy_mode = "foreign-only"

    return {
        "proxy_enabled": values.get("proxy_enabled", "0") == "1",
        "proxy_url": values.get("proxy_url", ""),
        "proxy_mode": proxy_mode,
    }


def update_proxy_settings(proxy_enabled: bool, proxy_url: str, proxy_mode: str):
    conn = get_connection()
    conn.executemany(
        "INSERT INTO app_settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        [
            ("proxy_enabled", "1" if proxy_enabled else "0"),
            ("proxy_url", proxy_url),
            ("proxy_mode", proxy_mode),
        ],
    )
    conn.commit()
    conn.close()
