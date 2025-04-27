# Project TODOs

## 🚦 Handoff & Next Steps (2025-04-26)
- **Production-ready:**
  - Modern dark UI, always-visible action/batch bars, batch selection/tagging
  - Export List and Copy to Folder for selected clips (fully implemented)
  - Custom checkboxes, grid scroll restore, robust batch UX
- **Next steps for dev:**
  - Playlist management (create, name, reorder, export playlists)
  - Advanced export (zip, TouchDesigner .tox, etc.)
  - Further UX polish (keyboard shortcuts, accessibility, creative/visual features)
  - Gather user feedback and iterate
- **Preview features:**
  - Each card has a PiP (Picture-in-Picture) button for floating video preview.
  - The selection bar includes a Preview Grid button to open a floating overlay with a grid of video previews for selected clips.
  - The Preview Grid overlay is now fully adaptive and responsive, maximizing video size and aspect ratio for any number of selected clips. See `clip_actions.js` for details.
- **Grid sorting:** Users can now sort the grid by name, date modified, size, duration, and starred status (favorites).
- **Show starred first:** A checkbox in the sort bar allows prioritizing starred clips in any sort order.
- **Persistent sort bar:** Sorting controls (dropdowns and checkbox) are always visible above the grid.
- All sorting and preview features are production-ready, robust, and tested for creative/visual workflows.
- The Preview Grid overlay is robust, adaptive, and ready for further creative/UX enhancements. Code is modular and ready for onboarding.

## ✅ Completed (2025-04-26)
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
- **Grid sorting:** Users can now sort the grid by name, date modified, size, duration, and starred status (favorites).
- **Show starred first:** A checkbox in the sort bar allows prioritizing starred clips in any sort order.
- **Persistent sort bar:** Sorting controls (dropdowns and checkbox) are always visible above the grid.
- **Preview features:**
  - Each card has a PiP (Picture-in-Picture) button for floating video preview.
  - The selection bar includes a Preview Grid button to open a floating overlay with a grid of video previews for selected clips.
- All sorting and preview features are production-ready, robust, and tested for creative/visual workflows.

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

## [2024-06-15] Batch Action Bar Working Baseline
- The batch action bar (edit bar) is confirmed working as of commit 999d0372cb193b2ff9543ec5783646b4b136b2e2.
- Any regressions after this commit should be compared against this baseline.
- Preserve this commit as a working reference for future UI/UX changes.

## 🚀 Planned Feature: Saved Clip Sets / Fast Switching
- Allow users to save the current set of scanned clips/thumbnails as a named set (e.g., "My VJ Loops", "Beeple Set").
- Add a dropdown menu in the UI to select from saved sets, instantly loading the associated clips/thumbnails without rescanning the folder.
- Provide an option to specify a new path for ingestion (scan), which can be saved as a new set.
- Store sets in the database or as JSON files for fast lookup and switching.
- UX: Dropdown for set selection, button to save current set, and input for new scan path.
- This will dramatically speed up browsing and workflow for large or multiple libraries.

## 🚦 TODO: PiP (Picture-in-Picture) Diagnostics & Robustness
- Add robust diagnostics for PiP button: log errors, check for video element presence, and ensure event handler is attached after every grid update.
- Test PiP in all supported browsers (Chrome, Edge, Safari, Firefox) and document any browser-specific issues.
- Add fallback or user feedback if PiP is not supported or fails to activate.

## 🚦 TODO: Selection Performance & Ctrl/Cmd Multi-Select
- Investigate and optimize selection performance (laggy selection when clicking cards or checkboxes).
- Fix ctrl/cmd (multi-toggle) selection so non-contiguous selection works as expected (should not update anchor, should always toggle selection instantly).
- Profile and refactor selection logic for efficiency, especially with large grids or many DOM updates.