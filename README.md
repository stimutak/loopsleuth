# LoopSleuth

> **Note (2024-06-13): LoopSleuth is now web-first!**
> The web UI (FastAPI + Jinja2) is the primary interface for browsing, tagging, and managing video loops. See `STARTUP_MESSAGE.md` for the latest project state, usage, and next steps.

---

## 🚦 Clean Handoff
- This repository is free of large video files and generated data; all such files are ignored and purged from git history.
- Ready for onboarding, collaboration, or handoff—see `STARTUP_MESSAGE.md` and `TODO.md` for all context and next steps.
- You are the primary maintainer; for collaboration, add contributors via GitHub settings.

## 🤝 Collaboration
- To contribute, fork or clone the repo and follow the setup instructions below.
- All technical and project context is in `STARTUP_MESSAGE.md` and `TODO.md`.

## ⚙️ GitHub Actions (CI/CD)
- Automated testing and linting will run on every push and pull request (see `.github/workflows/` for details).
- Add or modify workflows as needed for your development process.

---

A web-first (formerly terminal-first) librarian for video loops.

## Why
- Thumbnail & metadata view for huge DXV/H.264 clip libraries
- ⭐ flag keepers, tag with free text, delete duds
- Export a `keepers.txt` list for a TouchDesigner Replicator

## MVP (v0.1)
1. **Scan**: walk folder → SQLite row per clip (`ffprobe`)
2. **Thumb**: grab frame @ 25 % duration → 256 px JPEG
3. **Hash**: perceptual pHash → find near‑dupes later
4. **Web UI**: Grid and detail views for browsing, starring, tagging, and playback
5. **Export**: write `keepers.txt` with starred clip paths

_Stretch_: duplicate‑collapse, CLIP auto‑tags, .tox export.

## Tech
Python ≥ 3.10, ffmpeg/ffprobe, SQLite, Pillow, imagehash, FastAPI, Jinja2, Textual, Typer.

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/loopsleuth.git # Replace with actual URL later
    cd loopsleuth
    ```
2.  **Install FFmpeg:**
    LoopSleuth relies on `ffmpeg` and `ffprobe` for video processing. You must install FFmpeg separately. Download it from [ffmpeg.org](https://ffmpeg.org/download.html).
    **Important:** Ensure the `ffmpeg` and `ffprobe` executables are available in your system's PATH environment variable. Alternatively, configuration options to specify the paths might be added in the future.
3.  **Set up Python environment:**
    ```bash
    python -m venv .venv
    # Activate the environment (Windows PowerShell)
    .venv\Scripts\Activate.ps1
    # Activate the environment (Bash/Zsh)
    # source .venv/bin/activate
    pip install -r requirements.txt
    ```

