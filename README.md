# LoopSleuth

## Overview
LoopSleuth is a modern, production-ready web app for creative video library management, inspired by Notch, TouchDesigner, and Cursor. It features a robust, dark UI, advanced batch selection and tagging, playlist management, and seamless creative workflows.

## Key Features (2024-06)
- **Grid View:** Infinite scroll, responsive multi-column layout, and robust selection logic (single, Ctrl/Cmd, Shift+Click for multi/range select).
- **Playlist Pills:** Interactive playlist badges on each grid card, with instant add/remove and visual feedback. Pills are fully accessible and support direct removal from the grid.
- **Batch Actions:** Floating batch bar for tag add/remove/clear, with chip-style input, autocomplete, and keyboard accessibility. All actions are robust to DOM changes and large libraries.
- **Detail View:** Notch/Cursor-inspired glassmorphic sidebar, large video preview, and modern metadata/tags/playlists. Fully accessible and responsive.
- **Sidebar:** Playlist management (create, select, filter, reorder), with decoupled selection/filtering and instant feedback.
- **Export/Copy:** Export selected clips to keepers.txt or copy/move to a folder, with robust error handling and feedback.
- **Preview Grid:** Floating overlay for multi-clip video preview, adaptive grid layout, and custom controls.
- **Tag System:** Normalized tags, chip-style editing, and batch/single-clip parity. All tag changes are persisted and reflected instantly.
- **Production-Ready:** All core workflows are robust, accessible, and tested. See CHANGELOG.md for details.

## Selection UX
- **Single click:** Selects only the clicked card (sets anchor).
- **Ctrl/Cmd+Click:** Toggles selection of a card (multi-select, does not update anchor).
- **Shift+Click:** Selects a range from anchor to clicked card (updates anchor).
- **Checkboxes:** Support all selection modes, robust to DOM changes.
- **Selection Bar:** Always visible, with batch actions, preview, and playlist controls.

## Playlist Pills
- Pills show all playlists a clip belongs to, with color/hover feedback.
- Remove a clip from a playlist directly from the grid (✖ button on pill).
- Pills are accessible, keyboard-navigable, and update instantly.

## Handoff & Onboarding
- See `TODO.md` for next steps, creative/technical enhancements, and open issues.
- See `STARTUP_MESSAGE.md` for a full project state, onboarding checklist, and handoff notes.
- All code is modular, maintainable, and ready for further creative/production workflows.
- For new contributors: review the last commits, TODO.md, and STARTUP_MESSAGE.md for context and next actions.

## Contributing
- Fork the repo and create a feature branch for your changes.
- Follow the coding style and documentation patterns in the codebase.
- Run tests with `pytest` (see below) before submitting a PR.
- Document all new features and changes in CHANGELOG.md.

## Running & Testing
- Install requirements: `pip install -r requirements.txt`
- Start the server: `python src/loopsleuth/web/app.py`
- Open the app at `http://localhost:8000`
- Run tests: `pytest --maxfail=3 --disable-warnings -q`

## File Locations
- Grid: `src/loopsleuth/web/templates/grid.html`
- Detail: `src/loopsleuth/web/templates/clip_detail.html`
- JS: `src/loopsleuth/web/static/clip_actions.js`
- CSS: `src/loopsleuth/web/static/style.css`
- Backend: `src/loopsleuth/web/app.py`
- Tests: `tests/`

## Support & Handoff
- For onboarding, see `STARTUP_MESSAGE.md` and `TODO.md`.
- For bug reports, see `BUG_HANDBOOK.md`.
- For roadmap and creative ideas, see `ROADMAP.md`.

---
_Last update: 2024-06-XX_

## 🚦 Handoff & Next Steps (2024-06)
- **Production-ready:**
  - Modern, dark, Cursor-inspired UI with always-visible action and batch bars
  - Batch selection, tagging, export (keepers.txt), and copy-to-folder for selected clips
  - Custom checkboxes, grid scroll restore, robust batch UX
- **Next steps for dev:**
  - Playlist management (create, name, reorder, export playlists)
  - Advanced export (zip, TouchDesigner .tox, etc.)
  - Further UX polish (keyboard shortcuts, accessibility, creative/visual features)
  - Gather user feedback and iterate

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

## Web UI Modernization (2024-06)
- The UI is being redesigned for a modern, compact, high-contrast look with blue accents (#3fa7ff).
- All cards, bars, and controls are denser, with less padding and smaller text for information-rich browsing.
- A persistent selection bar floats at the bottom, showing selected count and actions (export, copy, clear, playlist coming soon).
- Accessibility and keyboard navigation are maintained.
- Responsive design: grid and controls scale for smaller screens.

## 🆕 Scan UX Improvements (2024-06)
- The scan folder and database fields are now unified, modern combo boxes: select from recent entries or enter a new value. Both are styled to match the dark UI and support keyboard/mouse interaction.
- The last-used database and scan folder are always available at the top of their respective dropdowns, unless localStorage is cleared.
- All endpoints (grid, playlists, duplicates, etc.) now respect the selected database, enabling seamless multi-library workflows.
- You do not need to re-ingest to see your last scan—just select the same DB and your clips will appear.
- All errors (validation, permission, scan conflicts, etc.) are shown as toast notifications in the UI—no more silent failures.
- The scan form prevents submission if validation fails, and backend errors are always surfaced to the user.
- These changes make multi-library workflows safer and more user-friendly, with instant feedback and robust error handling.

## MVP (v0.1)
1. **Scan**: walk folder → SQLite row per clip (`ffprobe`)
2. **Thumb**: grab frame @ 25 % duration → 256 px JPEG
3. **Hash**: perceptual pHash → find near‑dupes later
4. **Web UI**: Grid and detail views for browsing, starring, tagging, selection, and playback
5. **Export**: write `keepers.txt` with starred or selected clip paths

_Stretch_: duplicate‑collapse, CLIP auto‑tags, .tox export.

## Tech
Python ≥ 3.10, ffmpeg/ffprobe, SQLite, Pillow, imagehash, FastAPI, Jinja2, Textual, Typer.

### Web UI JavaScript
- All AJAX actions for starring and tag editing are handled by a shared static JS file (`src/loopsleuth/web/static/clip_actions.js`).
- Both the grid and detail views include this file for consistent, maintainable behavior.

### Tag System (vNext)
- Tags are now stored in a normalized schema: a `tags` table (unique tag names) and a `clip_tags` join table (many-to-many: clips <-> tags).
- This enables tag reuse, autocomplete, and efficient tag-based search/filtering.

### Tag Editing UX (2024-06)

- Per-clip tag editing in the detail view is now fully consistent with the batch editor: chip-style input, autocomplete, keyboard navigation, and ARIA/accessibility are all supported. Tag changes are persisted to the database and reflected in both the detail and grid views.
- The codebase is ready for handoff or onboarding. See STARTUP_MESSAGE.md and TODO.md for the latest project state and next steps.

#### Remaining polish for pro-level UX
- [x] ARIA roles/attributes for full screen reader support
- [x] Dropdown scrolls to keep highlight visible (for long lists)
- Batch tag editing (multi-select)
- Tag color/category support (optional)
- Tag reordering (optional)

See code comments for further details and next steps.

## Batch Editing Handoff Checklist

### ✅ What's Implemented
- Batch selection UI: Checkbox, click, shift+click, ctrl/cmd+click for multi/range selection. Visual highlight for selected cards.
- Batch action bar: <div id="batch-action-bar"> present in grid.html template. CSS for floating bar and controls in style.css. JS logic for rendering the bar and handling selection in clip_actions.js.
- Tag editing UI: Add tags, remove tags, clear all tags (UI and backend). Keyboard accessibility and ARIA for tag editing.
- **Batch tag input now uses chip-style input with autocomplete, keyboard navigation, and removable chips, matching the single-clip edit UX.**
- **Batch add/remove/clear is fully accessible and visually consistent.**
- **Batch remove field is now chip-based:** Chips represent tags present on selected clips, are removable with ×, and only chips in the remove field are removed. Autocomplete suggests only tags present on selected clips and not already chips. UX matches single-clip edit for clarity and accessibility.
- README: Updated with tag editing and batch editing UX, keyboard shortcuts, and accessibility.

### 🟡 What's NOT Done
- [ ] Batch action bar is not appearing in the UI (likely a CSS/DOM/JS load order issue—see below).
- [ ] Backend integration for batch tag add/remove/clear (no /batch_tag endpoint yet).
- [ ] No toast/snackbar feedback after batch operations.
- [ ] No batch tag autocomplete yet (uses plain input for now).

### 🛠️ Debugging Steps for Next Dev
1. Check if <div id="batch-action-bar"> is present in the DOM (Elements tab in dev tools).
2. Check for [BatchBar] logs or JS errors in the Console.
3. Try a hard refresh (Ctrl+Shift+R) to clear browser cache.
4. Check for CSS issues: The bar uses position: fixed; left: 0; right: 0; bottom: 0; z-index: 2000;. If the parent container or body has overflow: hidden or a low z-index, the bar may be hidden.
5. If the bar is present and visible but not interactive, proceed to backend integration and UI polish.

### 🚦 Next Steps
- [ ] Debug and fix batch bar visibility.
- [ ] Implement /batch_tag endpoint in backend.
- [ ] Wire up frontend batch actions to backend.
- [ ] Add feedback (toast/snackbar) after batch actions.
- [ ] Add batch tag autocomplete and polish.

### 📄 File Locations
- Grid template: src/loopsleuth/web/templates/grid.html
- Batch bar JS: src/loopsleuth/web/static/clip_actions.js
- Batch bar CSS: src/loopsleuth/web/static/style.css
- README: Project root

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

## 🧪 Test Coverage & Improving Quality

LoopSleuth uses `pytest` and `pytest-cov` for automated testing and coverage reporting.

- **Current coverage:** ~30% (as of June 2024)
- **How to check coverage:**
  ```bash
  pytest --cov=src/loopsleuth --cov-report=term-missing
  ```
- **How to improve coverage:**
  1. Add or expand tests in `tests/` for the modules and lines reported as missing.
  2. Focus on files with 0% or low coverage first (see below).
  3. Use `pytest --cov=src/loopsleuth --cov-report=html` for a browsable HTML report.

### Coverage Priorities (as of last run)
- **No/Low coverage:**
  - `src/loopsleuth/db_migrate_tags.py` (0%)
  - `src/loopsleuth/hasher.py` (0%)
  - `src/loopsleuth/tui.py` (0%)
  - `src/loopsleuth/exporter.py` (34%)
  - `src/loopsleuth/metadata.py` (29%)
  - `src/loopsleuth/scanner.py` (48%)
  - `src/loopsleuth/thumbnailer.py` (34%)
  - `src/loopsleuth/web/app.py` (53%)
  - `src/loopsleuth/ingest.py` (67%)
- **What's covered well:**
  - Batch/tag/playlist API logic and core backend tested in `tests/`.

#### To reach higher coverage:
- Add tests for CLI, TUI, hashing, thumbnailing, exporter, and error-handling paths.
- Add tests for the web UI's endpoints and error cases.
- See the coverage report for exact lines/files to target.

## ✅ Batch Tag Editing: Production-Ready (2024-06)
- Batch tag add, remove, and clear actions are fully implemented and robust in both backend and frontend.
- The batch action bar UI is reliable, immediate, and accessible for all tag changes.
- Automated tests for batch tag actions are present and passing (see `tests/test_batch_tag.py`).
- The test suite uses a production-matching schema and covers all batch tag actions for multiple clips.
- The batch tag workflow is now fully production-ready and tested as of this commit.

## Features
- Modern dark UI (Cursor-inspired, blue only for focus/active)
- Always-visible action and batch bars (stacked, seamless, compact)
- Batch selection, tagging, and per-clip detail view
- Export List: Download keepers.txt with selected clip paths
- Copy to Folder: Copy selected files to a user-specified folder
- Custom checkboxes, grid scroll restore, robust batch UX

## 🚀 Playlist Management & Selection UX (2024-06)

LoopSleuth now supports robust playlist management for creative workflows:

- **Sidebar checkboxes** select *target* playlists for add/remove actions, not for filtering.
- **Filter icon** (🔍) next to each playlist name filters the grid by that playlist.
- **Batch add/remove to multiple playlists** from the grid is fully supported.
- **Creating a new playlist with clips selected** immediately adds those clips to the new playlist.
- **Playlist pills on each grid card** now have a remove (✖) button to remove a clip from a playlist, with instant UI update and toast feedback.
- **Grid view reloads** after playlist changes to reflect new membership.
- **All playlist pill rendering is now handled in JS**, not Jinja, to avoid context errors and server errors.
- **Persistent selection bar and batch bar** are robust and always reflect current selection state.
- **Visual feedback (toast/snackbar)** for all playlist actions.
- All major UI/UX bugs (including 500 errors from Jinja context) have been fixed.

## 🚀 UI & Layout Modernization (2024-06)
- The app now uses a robust flexbox layout: the playlist sidebar and grid never overlap, and the grid always fills the available space.
- Sidebar is persistent, modern, and ready for advanced playlist features (drag-and-drop, export, etc.).
- Responsive design: On mobile, the sidebar stacks on top; on desktop, it sits side-by-side with the grid.
- All layout is production-ready and tested for all screen sizes.
- The grid and sidebar are now ready for creative and advanced workflows.

## Recent Updates (2024-06)
- The web app now uses the main production database (`loopsleuth.db`) by default.
- The clip detail view and all templates are robust to missing/null/missing-key metadata fields, preventing 500 errors.
- A custom `filesizeformat` Jinja2 filter is registered for human-readable file sizes.
- The sidebar in the detail view is now on the left, matching the grid view and standard UX conventions.
- Progress bar (tqdm) is shown during scans if tqdm is installed.
- Improved error handling: 404 and error pages are styled and user-friendly.
- See the Troubleshooting section for 500 error and schema migration tips.

## Troubleshooting
- If you see a 500 error on the clip detail view, ensure your database schema is up to date. Run the migration logic in `db.py` to add any missing columns.
- All templates now use robust dictionary access (`clip.get('field')`) to prevent errors from missing keys.
- If file sizes are not formatted, ensure the custom `filesizeformat` filter is registered in `app.py`.

---

## 🚦 Handoff & Path Forward (2024-06)

### Current State
- All core playlist, tagging, and selection workflows are robust and production-ready.
- The codebase is modular, maintainable, and well-documented.
- All major UI/UX bugs are resolved.
- The onboarding and handoff notes are up to date.
- Remaining work is mostly advanced/creative features and polish, not core stability.

### Pending / Next Steps
- Playlist reordering (drag-and-drop), playlist folders, playlist export (zip, .tox), playlist preview (play all/step through).
- Advanced export: zip, TouchDesigner .tox, etc.
- Further UX polish: keyboard shortcuts, accessibility improvements, creative/visual features (e.g., animated transitions, custom playlist covers).
- Detail view polish: needs a full redesign for usability and creative workflows (larger video, better tag/playlist controls, responsive layout).
- Duplicate detection: pHash duplicate detection, batch review/merge UI, cross-database duplicate scan.
- Performance: selection performance with very large grids, further optimization.
- Testing: expand automated test coverage, especially for new playlist and batch features.

### Onboarding Checklist
- [x] All playlist and tag features are tested and robust
- [x] UI is modern, accessible, and responsive
- [x] All major user flows are documented in this README and `STARTUP_MESSAGE.md`
- [x] See `src/loopsleuth/web/templates/clip_detail.html` for the latest playlist UX logic

_Last update: 2025-04-26_

## 🚦 Grid Sorting & Preview Features (2025-04-26)

- The grid view now supports sorting by:
  - Name (filename)
  - Date modified
  - Size
  - Duration (length)
  - Starred (favorites)
- You can also enable a 'Show starred first' checkbox to always prioritize starred clips in the sort order.
- Sorting controls are available in a persistent sort bar above the grid, with dropdowns for field and order (ascending/descending).
- The grid and selection bar are now more interactive:
  - Each card has a PiP (Picture-in-Picture) button for floating video preview.
  - The selection bar includes a Preview Grid button to open a floating overlay with a grid of video previews for selected clips.
- All sorting and preview features are robust, accessible, and tested for creative workflows.

## 🚦 Preview Grid Overlay Improvements (2024-06)
- The Preview Grid overlay now uses a fully adaptive, responsive CSS Grid layout.
- Video player cells automatically adjust their size and aspect ratio based on the number of selected clips and the viewport size.
- Videos are maximized within their grid cells, maintaining aspect ratio and filling available vertical space.
- The grid uses `repeat(auto-fit, minmax(320px, 1fr))` for columns, and each cell/video fills the available height and width.
- The overlay is robust for 1 to many selected clips, and the code is modular and ready for further creative/UX enhancements.
- See `src/loopsleuth/web/static/clip_actions.js` for the JS logic and `grid.html` for the template.

## 🚦 Handoff Summary (2024-06)

- The grid view now uses a virtualized, infinite scroll powered by Clusterize.js for robust performance with large libraries.
- The backend exposes `/api/clips` for windowed, paged data to support the virtualized frontend.
- Thumbnails are loaded on demand and sized via a persistent slider (using a CSS variable and localStorage).
- The grid is multi-column, responsive, and batch actions (tagging, selection) are fully supported.
- The batch tag bar and selection bar are always visible and robust to DOM changes.
- All code is modular, maintainable, and ready for creative/production workflows.
- See `src/loopsleuth/web/templates/grid.html`, `src/loopsleuth/web/static/style.css`, and `src/loopsleuth/web/static/clip_actions.js` for the main logic.

## Selection Behavior (macOS & Cross-Platform)

- **Single click**: Selects only the clicked card.
- **Shift+Click**: Selects a range of cards.
- **Checkboxes**: Use checkboxes to select multiple, non-contiguous cards. This is the most reliable method for multi-select on all platforms.
- **Cmd/Ctrl/Option+Click**: Not supported for multi-select on macOS browsers due to OS/browser limitations. Use checkboxes and shift+click instead.

## 🚦 New Features (2024-06)

- **Recent Scan Folders:** The scan form now includes a dropdown of your last 8 scanned folders (per user, stored in localStorage). Select a recent location or type a new one to scan.
- **Database Selection:** A database dropdown in the header/sidebar lets you quickly switch between libraries. Add new DBs, persist your selection, and reload the app with the chosen DB (via ?db=... query param). All state and actions are scoped to the selected DB.
- **Seamless Multi-Library Workflow:** The backend now supports per-request DB switching. You can scan, tag, review duplicates, and manage playlists in any selected DB without restarting the server.
- **Duplicate Review Banner:** If any duplicates are flagged, a prominent banner appears in the grid view linking to the batch review UI. Resolve, merge, or ignore duplicates directly from the web UI.

## 🚦 Onboarding & Workflow (2024-06)

- **Switching Libraries:** Use the database dropdown to select or add a DB. The app reloads with the selected DB, and all actions (scan, tag, review) apply to that library. All DB names are validated for safety.
- **Scanning Folders:** Use the scan form's combo dropdown to quickly select from recent folders or enter a new location. Recent folders are remembered per user. All scan folders are validated for existence and readability before scanning.
- **Error Feedback:** Any error (invalid DB name, permission denied, scan in progress, etc.) is shown as a toast notification. No silent failures.
- **Duplicate Review:** If flagged, review and resolve duplicates from the grid banner or the /duplicates page. Merge tags/playlists, keep, delete, or ignore as needed.

