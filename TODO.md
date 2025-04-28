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
- Playlist sidebar checkboxes now select target playlists for add/remove actions (not for filtering the grid)
- Filter icon (🔍) next to each playlist name filters the grid by that playlist
- Grid card checkboxes are larger, lighter, and flush to the upper-left for easy, accessible multi-select
- Batch add/remove to multiple playlists is fully supported from the grid
- The grid and sidebar are decoupled for a more flexible, creative workflow
- **Playlist pills on grid cards now have a remove (✖) button to remove a clip from a playlist, with instant UI update and toast feedback.**
- **Grid view reloads after playlist changes to reflect new playlist membership.**
- **Creating a new playlist with clips selected immediately adds those clips to the new playlist.**
- **All playlist pill rendering is now handled in JS, not Jinja, to avoid context errors and server errors.**
- **Fixed 500 Internal Server Error caused by Jinja referencing 'clip' outside of a valid context.**
- **All core playlist, tagging, and selection workflows are robust and production-ready.**
- **Codebase is stable and ready for handoff.**

## 🚀 Next Implementation Steps (2024-06)

### ⏭️ Next Planned Features
- Playlist reordering (drag-and-drop), playlist folders, playlist export (zip, .tox), playlist preview (play all/step through)
- Advanced export (.zip, .tox, etc.)
- Further UX polish and creative integrations (keyboard shortcuts, accessibility, creative/visual features)
- Detail view polish (larger video, better tag/playlist controls, responsive layout)
- Duplicate detection (pHash, batch review/merge UI, cross-database scan)
- Performance: selection performance with very large grids, further optimization
- Testing: expand automated test coverage, especially for new playlist and batch features

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
    - [x] Unify database selection and custom DB name into a single combo box (recent + custom entry, styled, with recents persisted)
    - [x] Unify scan folder selection into a combo box (recent + custom entry, styled, with recents persisted)
    - [x] All endpoints (grid, playlists, duplicates, etc.) now respect the selected DB for true multi-library support
    - [x] Improved onboarding and workflow documentation
    - [x] Users do not need to re-ingest to see previous scans—just select the same DB and clips will appear if the DB file is present
    - [x] Improved error feedback: all scan and DB errors are shown as toast notifications in the UI
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

## 🚦 Duplicate Detection, Auto-Merge, and Database Reloadability (2024-06)

### 🟡 Duplicate Detection & Management
- **Perceptual Hashing:**
    - Ensure every clip has a perceptual hash (pHash) computed and stored in the database on ingest.
    - On ingest, check for existing pHashes (or near-duplicates using Hamming distance) before inserting a new clip.
    - If a duplicate is found, log, skip, or prompt the user (configurable behavior).
- **Batch Duplicate Review Tool:**
    - Implement a UI tool/button to scan the database for near-duplicate pHashes and present results for manual review.
    - Group and display potential duplicates side-by-side with thumbnails/videos for quick comparison.
    - Allow user to merge, delete, or ignore flagged duplicates.
- **Auto-Merge Option:**
    - For exact pHash matches, provide an option to auto-merge metadata/tags and keep only one file (with user confirmation).
    - Optionally, auto-merge can be enabled for ingest or batch review.
- **Cross-Database Duplicate Scan (Experimental):**
    - Allow scanning for duplicates across multiple databases (for distributed or multi-library workflows).
    - Present cross-DB duplicate groups for review and merging.
- **Filename Uniqueness:**
    - Move away from appending numbers to filenames for uniqueness; rely on pHash for true duplicate detection.

### 🟡 Database Reloadability & Multi-Library Workflow
- **Database Reloadability:**
    - Add a UI/CLI option to "Open Database…" and select a different `.db` file.
    - On open, reload all state (clips, tags, playlists, stars, etc.) from the selected DB.
    - Ensure all user state is always written to the DB, not just held in memory.
    - On DB switch, clear any in-memory caches and reload from the new DB.
- **Multi-Library Support:**
    - Document and support workflows for working on multiple libraries (e.g., VJ sets, project-specific DBs).
    - Add a dropdown or menu for fast switching between recent/opened databases.
    - Ensure all playlist, tag, and selection state is preserved per DB.

### 🚀 Next Steps
- [ ] Implement pHash duplicate check on ingest (with configurable behavior: skip, log, prompt, auto-merge).
- [ ] Add batch duplicate review tool in the UI (side-by-side visual review, merge/delete actions).
- [ ] Add auto-merge option for exact pHash matches (with user confirmation).
- [ ] Implement cross-database duplicate scan (experimental/optional).
- [ ] Add "Open Database" option in UI/CLI for reloadability and multi-library workflows.
- [ ] Document all new workflows and features in the README and onboarding materials.

### 💡 Rationale
- Robust duplicate detection ensures a clean, master list of unique files for creative workflows and export.
- Visual review and auto-merge streamline library management and reduce manual cleanup.
- Database reloadability and multi-library support enable flexible, non-destructive workflows for artists and VJs working across multiple projects or sets.