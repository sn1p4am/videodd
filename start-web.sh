#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
NODE_BIN="${YTDLP_NODE_PATH:-}"
PROXY_URL="${YTDLP_PROXY_URL:-}"

log() {
    printf '[start-web] %s\n' "$*"
}

warn() {
    printf '[start-web] warning: %s\n' "$*" >&2
}

die() {
    printf '[start-web] error: %s\n' "$*" >&2
    exit 1
}

find_python() {
    if [ -n "${PYTHON:-}" ] && command -v "${PYTHON}" >/dev/null 2>&1; then
        command -v "${PYTHON}"
        return 0
    fi
    if [ -x "$VENV_PYTHON" ]; then
        printf '%s\n' "$VENV_PYTHON"
        return 0
    fi
    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return 0
    fi
    if command -v python >/dev/null 2>&1; then
        command -v python
        return 0
    fi
    return 1
}

has_web_deps() {
    "$1" -c 'import fastapi, uvicorn, yt_dlp' >/dev/null 2>&1
}

bootstrap_env() {
    local bootstrap_python="$1"

    if [ ! -x "$VENV_PYTHON" ]; then
        log "creating .venv"
        "$bootstrap_python" -m venv "$ROOT_DIR/.venv"
    fi

    log "installing Python dependencies"
    "$VENV_PYTHON" -m pip install -e ".[default]"
    "$VENV_PYTHON" -m pip install -r web_app/requirements.txt
}

cd "$ROOT_DIR"

PYTHON_BIN="$(find_python)" || die "python3 or python is required"

if ! has_web_deps "$PYTHON_BIN"; then
    bootstrap_env "$PYTHON_BIN"
    PYTHON_BIN="$VENV_PYTHON"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    warn "ffmpeg not found; merge/remux/audio extraction features may fail"
fi

if [ -n "$NODE_BIN" ]; then
    if ! command -v "$NODE_BIN" >/dev/null 2>&1 && [ ! -x "$NODE_BIN" ]; then
        warn "node runtime not found at $NODE_BIN"
    fi
elif ! command -v node >/dev/null 2>&1; then
    warn "node runtime not found in PATH; some sites may fail"
fi

if [ -n "$PROXY_URL" ] && command -v curl >/dev/null 2>&1; then
    case "$PROXY_URL" in
        http://*|https://*)
            if ! curl -fsS "$PROXY_URL" >/dev/null 2>&1; then
                warn "proxy $PROXY_URL is unreachable; proxied downloads may fail"
            fi
            ;;
    esac
fi

HOST="${YTDLP_HOST:-0.0.0.0}"
PORT="${YTDLP_PORT:-8081}"
DISPLAY_HOST="$HOST"
if [ "$DISPLAY_HOST" = "0.0.0.0" ]; then
    DISPLAY_HOST="localhost"
fi

log "using Python: $PYTHON_BIN"
if [ -n "${YTDLP_ADMIN_PASSWORD:-}" ]; then
    log "admin password protection is enabled"
fi
log "starting Web UI at http://$DISPLAY_HOST:$PORT"
exec "$PYTHON_BIN" -m web_app
