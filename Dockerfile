FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    YTDLP_HOST=0.0.0.0 \
    YTDLP_PORT=8081 \
    YTDLP_DOWNLOAD_DIR=/data/downloads \
    YTDLP_DB_PATH=/data/ytdlp_web.db \
    YTDLP_NODE_PATH=node

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg nodejs ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY LICENSE README.md pyproject.toml supportedsites.md /app/
COPY yt_dlp /app/yt_dlp
COPY web_app /app/web_app

RUN python -m pip install --upgrade pip \
    && python -m pip install ".[default]" -r web_app/requirements.txt

RUN mkdir -p /data/downloads

EXPOSE 8081

CMD ["python", "-m", "web_app"]
