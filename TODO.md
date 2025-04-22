# Project TODOs

<!-- CURSOR:KEEP_START -->
### 🚀 Web-Based Migration Plan (2024-06)

- [ ] **Migrate LoopSleuth to a web-based frontend for a modern, rich UX.**
    - [x] Decision: Move from TUI to web UI for better media interaction, tagging, and extensibility.
    - [ ] Scaffold a new web app (FastAPI preferred, Flask as fallback).
    - [ ] Reuse existing backend/database logic for clips, tags, starring, export, etc.
    - [ ] Implement grid view of clips with thumbnails (HTML/CSS, responsive).
    - [ ] Add video playback page/modal (HTML5 `<video>` tag).
    - [ ] Add tagging, starring, and export features in the web UI.
    - [ ] Implement search/filtering and batch actions.
    - [ ] (Optional) Add duplicate detection, advanced metadata, and creative integrations.
    - [ ] Document migration and update README.
- [ ] **TUI is now feature-frozen except for critical bugfixes.**

### MVP checklist (hand‑curated)

- [ ] cli.py: Typer entry ‑‑scan/‑‑ui/‑‑export
- [ ] ingest_folder(): tqdm walk, call probe_video(), commit
- [ ] thumbnails: skip if exists & mtime unchanged
- [ ] Textual grid: lazy‑load thumbs (path → Image.open)
- [ ] export_td: write absolute paths, newline‑delimited
<!-- CURSOR:KEEP_END -->

### AI suggestions (safe to overwrite below)


## Setup & Foundation
- [x] Initialize Python project (e.g., using Poetry or `venv` + `requirements.txt`).
- [x] Add core dependencies: `Pillow`, `imagehash`, `Textual`, `Typer`.
- [x] Set up basic project structure (e.g., `src/loopsleuth`, `tests/`).
- [x] Ensure `ffmpeg` and `ffprobe` are accessible (document installation/path).
- [x] Define SQLite database schema.
- [x] Implement basic database connection and table creation logic.

## MVP (v0.1)
- [x] **Scan:** Implement directory walking to find video files.
- [x] **Scan:** Integrate `ffprobe` execution to extract duration and other relevant metadata.
- [x] **Scan:** Save clip path and metadata to the SQLite database.
- [x] **Thumb:** Implement `ffmpeg` call to extract a frame at 25% duration.
- [x] **Thumb:** Use `Pillow` to resize the frame to 256px width and save as JPEG.
- [x] **Thumb:** Store thumbnail path or blob in the database.
- [x] **Hash:** Calculate perceptual hash (pHash) using `imagehash`.
- [x] **Hash:** Store pHash in the database.
- [x] **TUI:** Create basic Textual app structure.
- [x] **TUI:** Implement grid view to display thumbnails and metadata from the database.
- [x] **TUI:** Add `<Space>` key binding to toggle a 'starred' flag in the database.
- [x] **TUI:** Add `t` key binding to open an input field for editing free-text tags (store in DB).
- [x] **TUI:** Add `d` key binding to mark a clip for deletion (or delete immediately - decide strategy). Handle file deletion and DB update.
- [x] **Export:** Implement command/feature to query starred clips from the database.
- [x] **Export:** Write the paths of starred clips to `keepers.txt`.

## Stretch Goals (next sprint)

### 1  TUI Thumbnails & UX polish
- [x] Attempted to add `Image` widget for inline JPEG render — **Blocked: Image widget not available in Textual 0.76.0 on this platform/environment.**
- [x] Fallback: Static placeholder used for thumbnails in TUI grid.
- [ ] Detect client capability → **Kitty/Sixel/ANSI** fallback (**future: if/when image support is available**)
- [ ] Generate ANSI fallback spritesheet once per run (avoid Pillow in loop)
- [ ] **Lazy‑load:** only decode thumbs for rows in viewport (**future: if/when image support is available**)
- [ ] Hover / focus info pane (resolution, codec, duration)
- [ ] Key‑hints footer & help modal (`?`)

### 2  Duplicate‑Finder Workflow
- [ ] Add `duplicates` table `(clip_id, dup_id, distance)`
- [ ] Batch compare pHash (≤8 Hamming) with fast bit‑ops
- [ ] UI "Dup sets" sidebar → cycle with `Tab`
- [ ] Keep / Drop hotkeys; drop removes file & DB row
- [ ] Auto‑collapse view option (`--collapse-dupes`)

### 3  Smart Auto‑Tagging
- [ ] Integrate OpenAI CLIP or `open_clip` local model
- [ ] Embed thumb → top‑N keywords (score ≥ 0.18)  
- [ ] Store → `auto_tags` column (comma‑sep)
- [ ] UI suggestions panel (`s` key) → ⏎ to accept into `tags`
- [ ] Add `--search tag1 tag2` filter to CLI `ui`

### 4  TouchDesigner Export v2
- [ ] Define `.tox` JSON (COMP, Replicator DAT, Movie File In TOP)
- [ ] Script to build `.tox` using `tdjson` or TD .toe template
- [ ] Embed custom parameter page ("Next clip", "Random")
- [ ] Option: auto‑copy thumbs folder next to .tox for previews

### 5  Testing & CI
- [ ] `pytest` unit: `probe_video`, `hash`, DB insert, export
- [ ] Parametrised test set with tiny sample videos
- [ ] Textual snapshot test using `textual-dev` recorder
- [ ] CLI e2e test (`scan → star → export`) with tmp dir
- [ ] GitHub Actions: Windows + macOS matrix, Python 3.10–3.12

- [ ] Add option to transcode unsupported video formats (e.g., .mov, .avi) to MP4 (H.264/AAC) for browser playback. Consider using FFmpeg for batch conversion.
- [x] Add fallback message and download link for unsupported video formats in the web UI (clip detail page).

- [x] AJAX tag editing now works reliably in both grid and detail views.
- [x] /tag/{clip_id} endpoint updated for JSON payloads.
- [x] Tag editing UX improved: static text always visible, Enter and save button both work, no navigation or reload.
- [x] Star and tag controls are now robust and consistent.
- [x] Documentation and check-in practices reviewed for sync with .cursor/rules.
- [x] Note: HTML5 video playbar seeking is supported by default for compatible files.

