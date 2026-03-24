# yt-dlp + Web UI

This repository is a fork of [yt-dlp](https://github.com/yt-dlp/yt-dlp). It keeps the upstream command-line downloader and adds a small `web_app/` service for browser-based downloads.

This fork is optimized for a simple workflow:
- keep the upstream `yt-dlp` core available
- add a lightweight Web UI for interactive downloads
- keep this README short and link to upstream for exhaustive CLI documentation

## Highlights

- Browser UI for pasting a URL and starting a download
- Video/audio mode selection with format preferences
- Real-time progress updates over Server-Sent Events (SSE)
- Download history stored in SQLite
- Finished files can be downloaded back from the browser
- The regular `yt-dlp` CLI is still available from this checkout

# INSTALLATION

## Web UI

### Requirements

- Python 3.10+
- `ffmpeg` / `ffprobe` recommended; required for merge, remux, and audio extraction tasks handled by `yt-dlp`
- A Node runtime available at `~/.nvm/versions/node/v22.22.0/bin/node` (current implementation detail in `web_app/downloader.py`)
- For non-domestic sites, the current `web_app` code routes requests through `http://127.0.0.1:7897`

### Run from this repository

```bash
python -m pip install -e ".[default]"
python -m pip install -r web_app/requirements.txt
python -m web_app
```

Open `http://localhost:8080` in your browser.

### Current behavior to know about

- `web_app` currently supports **single video URLs only**; playlists are rejected
- Downloads default to `web_app/downloads/`
- Download history defaults to `web_app/ytdlp_web.db`
- The UI can extract metadata, start downloads, stream progress, list history, delete records, and serve completed files

## CLI

If you want to use the CLI from this checkout:

```bash
python -m pip install -e ".[default]"
python -m yt_dlp --version
python -m yt_dlp --help
```

If you only need the standard downloader experience, the upstream project is the best reference:

- Upstream project: https://github.com/yt-dlp/yt-dlp
- Upstream installation wiki: https://github.com/yt-dlp/yt-dlp/wiki/Installation
- Supported sites list: [supportedsites.md](supportedsites.md)

## Web UI

### What it does

The `web_app/` service adds a small HTTP layer around `yt-dlp`:

- `POST /api/extract` extracts title, thumbnail, uploader, duration, and available formats
- `POST /api/download` creates a background download task
- `GET /api/downloads/{task_id}/progress` streams task progress over SSE
- `GET /api/downloads` returns download history
- `GET /api/downloads/{task_id}/file` serves the completed file
- `DELETE /api/downloads/{task_id}` removes the history record and the downloaded file if it still exists

### Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `YTDLP_DOWNLOAD_DIR` | `web_app/downloads` | Directory used for downloaded files |
| `YTDLP_DB_PATH` | `web_app/ytdlp_web.db` | SQLite database path for download history |
| `YTDLP_HOST` | `0.0.0.0` | FastAPI bind host |
| `YTDLP_PORT` | `8080` | FastAPI bind port |
| `YTDLP_MAX_CONCURRENT` | `3` | Maximum concurrent background downloads |

Example:

```bash
YTDLP_PORT=9090 YTDLP_DOWNLOAD_DIR=/data/downloads python -m web_app
```

## Project structure

```text
.
├── yt_dlp/                 # Upstream downloader package
├── web_app/                # FastAPI + Vue-based Web UI extension
│   ├── main.py             # App bootstrap
│   ├── downloader.py       # yt-dlp integration and background jobs
│   ├── database.py         # SQLite persistence
│   ├── routes/             # API and SSE endpoints
│   └── static/index.html   # Browser UI
├── supportedsites.md       # Supported extractor list
├── CONTRIBUTING.md         # Upstream-oriented contribution guide
└── README.md               # This fork-specific overview
```

## Upstream documentation

This README intentionally stays short. For the full `yt-dlp` documentation, use the upstream project:

- Main documentation: https://github.com/yt-dlp/yt-dlp#readme
- Installation: https://github.com/yt-dlp/yt-dlp/wiki/Installation
- FAQ: https://github.com/yt-dlp/yt-dlp/wiki/FAQ
- Embedding guide: https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp
- Full option reference: https://github.com/yt-dlp/yt-dlp#usage-and-options

# USAGE AND OPTIONS

## General Options:

The detailed CLI option list is maintained by upstream `yt-dlp` and can be regenerated from the standard help output when needed.

# CONFIGURATION

For full configuration syntax and examples, use the upstream documentation:
- https://github.com/yt-dlp/yt-dlp#configuration
- https://github.com/yt-dlp/yt-dlp/wiki/FAQ

The Web UI in this fork is configured primarily through environment variables documented above.

# COMPILE

This repository still follows the upstream `yt-dlp` build flow.

If you need to build binaries or package artifacts, start with the upstream instructions:
- https://github.com/yt-dlp/yt-dlp#compile

For normal local development of this fork, the editable install plus `python -m web_app` is usually enough.

# EMBEDDING YT-DLP

The Python package remains available from this checkout, so upstream embedding guidance still applies:
- https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp

# CHANGES FROM YOUTUBE-DL

This fork inherits the behavior of `yt-dlp` relative to `youtube-dl`.

Use the upstream reference for the complete migration notes:
- https://github.com/yt-dlp/yt-dlp#changes-from-youtube-dl

## Differences in default behavior

See:
- https://github.com/yt-dlp/yt-dlp#differences-in-default-behavior

## Deprecated options

See:
- https://github.com/yt-dlp/yt-dlp#deprecated-options

## Format Selection

For format selection details in this fork, use the upstream documentation:
- https://github.com/yt-dlp/yt-dlp#format-selection

## Sorting Formats

For format sorting details, use the upstream documentation:
- https://github.com/yt-dlp/yt-dlp#sorting-formats

## Preset Aliases

For preset alias details, use the upstream documentation:
- https://github.com/yt-dlp/yt-dlp#preset-aliases

## Internet Shortcut Options

For internet shortcut option details, use the upstream documentation:
- https://github.com/yt-dlp/yt-dlp#internet-shortcut-options

## SponSkrub SponsorBlock Options

For SponsorBlock-related option details, use the upstream documentation:
- https://github.com/yt-dlp/yt-dlp#sponskrub-sponsorblock-options

## Release Files

This fork may produce the usual upstream-style release artifacts such as source archives, PyPI files, and platform builds.

For this fork, use the workflow and filenames attached to the release itself as the source of truth.


Upstream `yt-dlp` is licensed under the [Unlicense](LICENSE). This fork keeps the same project base and should be reviewed together with the upstream licensing and bundled dependency notes when distributing binaries or modified builds.
