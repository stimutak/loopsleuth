# Project TODOs

<!-- CURSOR:KEEP_START -->
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
- [ ] **Thumb:** Store thumbnail path or blob in the database.
- [ ] **Hash:** Calculate perceptual hash (pHash) using `imagehash`.
- [ ] **Hash:** Store pHash in the database.
- [ ] **TUI:** Create basic Textual app structure.
- [ ] **TUI:** Implement grid view to display thumbnails and metadata from the database.
- [ ] **TUI:** Add `<Space>` key binding to toggle a 'starred' flag in the database.
- [ ] **TUI:** Add `t` key binding to open an input field for editing free-text tags (store in DB).
- [ ] **TUI:** Add `d` key binding to mark a clip for deletion (or delete immediately - decide strategy). Handle file deletion and DB update.
- [ ] **Export:** Implement command/feature to query starred clips from the database.
- [ ] **Export:** Write the paths of starred clips to `keepers.txt`.

## Stretch Goals
- [ ] **Duplicates:** Implement logic to find near-duplicates based on stored pHash values.
- [ ] **Duplicates:** Add UI element/feature to view and manage duplicate sets (e.g., collapse, select best).
- [ ] **Auto-Tags:** Research and integrate CLIP (or similar model) for generating automatic tags from thumbnails.
- [ ] **Auto-Tags:** Store generated tags in the database.
- [ ] **TOX Export:** Design `.tox` structure for importing `keepers.txt` into TouchDesigner.
- [ ] **TOX Export:** Implement functionality to generate the `.tox` file.

## Testing
- [ ] Set up testing framework (e.g., `pytest`).
- [ ] Add tests for core utilities (DB interaction, ffmpeg/ffprobe calls, hashing).
- [ ] Add tests for TUI interactions if feasible.
