# yt-dlp Web

This repository is a trimmed runtime-focused fork of `yt-dlp`.

It keeps:

- the `yt_dlp/` downloader package
- the `web_app/` FastAPI Web UI
- local start scripts and Docker Compose deployment files

It removes upstream CI, tests, release tooling, and other maintenance assets that are not needed to run the project.

## What It Does

- Password-protected Web UI for video/audio downloads
- Metadata extraction before download
- Background downloads with SSE progress updates
- Download history stored in SQLite
- Optional proxy settings managed from the Web UI
- Standard `yt-dlp` Python package and CLI remain available

## Local Run

Requirements:

- Python 3.10+
- `ffmpeg` / `ffprobe`
- `node` available in `PATH` or configured via `YTDLP_NODE_PATH`

Start with the helper script:

```bash
./start-web.sh
```

If you want admin login protection locally:

```bash
YTDLP_ADMIN_PASSWORD='change-me' \
YTDLP_SESSION_SECRET='replace-with-a-random-secret' \
./start-web.sh
```

Manual alternative:

```bash
python -m pip install -e ".[default]"
python -m pip install -r web_app/requirements.txt
python -m web_app
```

Open `http://localhost:8081`.

## Docker Compose

Quick start:

```bash
cp .env.example .env
docker compose up -d --build
```

Open `http://localhost:8081`.

### Server Deployment

```bash
git clone https://github.com/sn1p4am/videodd.git
cd videodd
cp .env.example .env
```

Edit `.env` and set at least:

```dotenv
YTDLP_PUBLIC_PORT=8081
YTDLP_ADMIN_PASSWORD=use-a-strong-password
YTDLP_SESSION_SECRET=use-a-long-random-secret
YTDLP_SESSION_SECURE=true
```

If you are accessing the service over plain `http://` during local or temporary testing, set:

```dotenv
YTDLP_SESSION_SECURE=false
```

Use `YTDLP_SESSION_SECURE=true` only when the browser is actually accessing the site over HTTPS.

Start the service:

```bash
docker compose up -d --build
```

Useful commands:

```bash
docker compose ps
docker compose logs -f yt-dlp-web
docker compose restart yt-dlp-web
docker compose down
```

Update after pulling changes:

```bash
git pull
docker compose up -d --build
```

Persistent data lives in `./data`:

- `./data/downloads` for finished downloads
- `./data/ytdlp_web.db` for history and saved proxy settings

If you expose the service publicly, put it behind HTTPS and keep `YTDLP_SESSION_SECURE=true`.

## Web UI Settings

After login, the header contains a small settings button.

From there you can:

- enable or disable an outbound proxy
- set the proxy URL
- choose whether the proxy applies to foreign sites only or all sites

Proxy is disabled by default.

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `YTDLP_DOWNLOAD_DIR` | `web_app/downloads` | Download directory |
| `YTDLP_DB_PATH` | `web_app/ytdlp_web.db` | SQLite database path |
| `YTDLP_HOST` | `0.0.0.0` | Bind host |
| `YTDLP_PORT` | `8081` | Bind port |
| `YTDLP_MAX_CONCURRENT` | `3` | Max concurrent downloads |
| `YTDLP_NODE_PATH` | auto-detect | Node executable or absolute path |
| `YTDLP_PROXY_URL` | unset | Initial proxy URL on first startup |
| `YTDLP_PROXY_MODE` | `foreign-only` | Initial proxy mode on first startup |
| `YTDLP_ADMIN_PASSWORD` | unset | Enables login protection |
| `YTDLP_SESSION_SECRET` | dev fallback | Session signing secret |
| `YTDLP_SESSION_SECURE` | `false` | Set `true` behind HTTPS |
| `YTDLP_SESSION_MAX_AGE` | `43200` | Session lifetime in seconds |

## Repository Layout

```text
.
├── Dockerfile
├── compose.yml
├── start-web.sh
├── pyproject.toml
├── web_app/
└── yt_dlp/
```
