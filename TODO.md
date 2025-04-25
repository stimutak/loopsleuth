# Project TODOs

## 🚦 Handoff & Next Steps (2024-06)
- **Production-ready:**
  - Modern dark UI, always-visible action/batch bars, batch selection/tagging
  - Export List and Copy to Folder for selected clips (fully implemented)
  - Custom checkboxes, grid scroll restore, robust batch UX
- **Next steps for dev:**
  - Playlist management (create, name, reorder, export playlists)
  - Advanced export (zip, TouchDesigner .tox, etc.)
  - Further UX polish (keyboard shortcuts, accessibility, creative/visual features)
  - Gather user feedback and iterate

## ✅ Completed (2024-06)
- Grid scroll position restore
- Modern dark UI
- Always-visible batch/action bars
- Custom checkboxes
- Export List: User can export selected clip paths as keepers.txt
- Copy to Folder: User can copy selected files to a user-specified folder
- Web app uses main production DB (`loopsleuth.db`) by default
- Clip detail view and all templates robust to missing/null/missing-key fields (no more 500 errors)
- Custom `filesizeformat` Jinja2 filter for human-readable file sizes
- Sidebar in detail view is now on the left (matches grid view)
- Progress bar (tqdm) during scan if tqdm is installed
- Improved error handling: styled 404 and error pages
- Robust template coding: all metadata fields use `clip.get('field')` for creative/production safety

## 🚀 Next Implementation Steps (2024-06)

### ⏭️ Next Planned Features
- Playlist management for selected clips
- Advanced export (.zip, .tox, etc.)
- Further UX polish and creative integrations

## 🚀 UI Modernization (2024-06)
- In progress: Modern, compact, high-contrast look with blue accents (#3fa7ff)
- All cards, bars, and controls are denser, with less padding and smaller text
- Persistent selection bar at the bottom for selected count and actions (export, copy, clear, playlist coming soon)
- Accessibility and keyboard navigation maintained
- Responsive design for grid and controls

## ✅ Batch Tag Editing: Production-Ready (2024-06)
- Batch tag add, remove, and clear actions are fully implemented and robust in both backend and frontend.
- The batch action bar UI is reliable, immediate, and accessible for all tag changes.
- Automated tests for batch tag actions are present and passing (see `tests/test_batch_tag.py`).
- The test suite uses a production-matching schema and covers all batch tag actions for multiple clips.
- The batch tag workflow is now fully production-ready and tested as of this commit.

## 🚀 Next Major Feature: Selection, Export, and Playlists (2024-06)

### (A) Stage 1: Selected Clips Bar & Export/Copy Actions
- [x] UI modernization: compact, blue-accented, persistent selection bar (in progress)
- [ ] Implement a persistent 'Selected Clips' bar in the grid UI, showing the number of selected clips and offering actions:
    - [ ] Export selected clip paths to a text file (e.g., for TouchDesigner Replicator)
    - [ ] Copy/move selected files to a user-specified folder (with overwrite/skip options)
    - [ ] Clear selection button
    - [ ] Toast/snackbar feedback for actions
- [ ] Backend endpoints:
    - [ ] /export_selected (POST): Export selected clip paths as a downloadable file
    - [ ] /copy_selected (POST): Copy/move selected files to a folder
- [ ] UI/UX polish: Selection persists across navigation, clear visual feedback, keyboard accessibility
- [ ] Tests: Automated tests for export/copy endpoints and selection logic

### (B) Stage 2: Playlists (Named, Ordered, Advanced Export)
- [ ] Allow users to create, name, and manage multiple playlists
- [ ] Support drag-and-drop reordering of clips within a playlist
- [ ] Playlist preview: Play all or step through clips in sequence
- [ ] Export playlist as .txt, .zip, or other formats (e.g., .tox for TouchDesigner)
- [ ] Backend endpoints for playlist CRUD and export
- [ ] UI/UX: Playlist management interface, ordering, and feedback
- [ ] Tests: Automated tests for playlist creation, modification, and export

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
    - [x] Unify tag/star JS logic in a shared static file and include in both grid and detail templates.
- [ ] **TUI is now feature-frozen except for critical bugfixes.**

### MVP checklist (hand‑curated)

- [ ] cli.py: Typer entry ‑‑scan/‑‑ui/‑‑export
- [ ] ingest_folder(): tqdm walk, call probe_video(), commit
- [ ] thumbnails: skip if exists & mtime unchanged
- [ ] Textual grid: lazy‑load thumbs (path → Image.open)
- [ ] export_td: write absolute paths, newline‑delimited

### Tag Autocomplete & Deletion Implementation Plan

#### Tag Autocomplete
- [x] Backend: `/tags`

## 🛠️ UI/UX Issues & Polish Needed

- The detail view (single clip) needs significant work:
    - The video player is currently very small and not usable for review/playback.
    - Layout and spacing are off; controls and metadata are cramped or misaligned.
    - Needs a full redesign for usability, aesthetics, and creative workflows (larger video, better tag/playlist controls, responsive layout, etc).
    - Consider inspiration from modern media managers or creative tools (TouchDesigner, DaVinci, etc).

## Troubleshooting
- If you see a 500 error on the detail view, check your DB schema and run the migration logic in `db.py`.
- All templates are now robust to missing/null fields and missing keys.