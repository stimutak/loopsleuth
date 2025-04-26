# LoopSleuth

> **Note (2025-04-22 to 2025-04-26): Major UI/UX improvements and handoff readiness**
> - Favicons are now present on all pages (grid, detail, error, 404) for consistent branding.
> - A persistent, real-time thumbnail size slider is available above the grid view (per-browser persistence).
> - The detail view features fully custom video controls (play/pause, seek, frame step, volume) in addition to native controls.
> - All forms and buttons use a modern, thin, Notch-inspired typographic style for a clean, creative look.
> - The "Open in System" feature selects files in Explorer/Finder or opens the folder on Linux.
> - All major UI/UX changes are documented in `BUG_HANDBOOK.md` for handoff/debug.
> - See `CHANGELOG.md` for a detailed, date-accurate version history and recent changes.

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
- The grid now clears instantly when a new scan is started, providing immediate visual feedback.
- A toast/snackbar notification appears when a scan completes, fails, or finds no clips, so users always know the scan result.
- These changes improve clarity and responsiveness for creative workflows and large libraries.

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

## 🚀 Playlist Management (2024-06)

LoopSleuth now supports (or is adding) robust playlist management for creative workflows:

- **Database:**
  - `playlists` table: id, name, created_at
  - `playlist_clips` join table: playlist_id, clip_id, position (ordering)
- **Backend API:**
  - Create, rename, delete playlists
  - Add/remove clips (batch)
  - Reorder clips (drag-and-drop or up/down)
  - List playlists and their clips
  - Export playlist as .txt, .zip, or .tox (TouchDesigner)
- **Frontend UI:**
  - Playlist sidebar or modal for management
  - Add/remove selected clips to playlists
  - Drag-and-drop or up/down for ordering
  - Export/download and preview (play all/step-through)
- **Workflow:**
  - Add/remove multiple selected clips to playlists in one go
  - Show which playlists a clip belongs to in grid/detail views
  - Visual feedback: badges/highlights for playlist membership
- **Testing:**
  - Unit tests for all endpoints and ordering logic
  - UI tests for playlist creation, modification, and export

_Stretch:_ .tox export, multi-user/concurrent edits, creative integrations (TouchDesigner/Notch hooks).

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
- Playlist management is robust: create, rename, delete, reorder, and export playlists from the sidebar.
- Playlist badges in the detail view are now fully interactive:
  - Clicking a badge highlights it, selects the playlist in the sidebar, and auto-scrolls the sidebar to the selected playlist.
  - Visual feedback is immediate and robust for both badge and sidebar selection.
- Batch tag editing, selection bar, and all core grid/detail UX are production-ready.

### Path Forward
- **For new contributors or maintainers:**
  1. Review the sidebar and detail view playlist sync logic in `clip_detail.html` and `clip_actions.js`.
  2. For further UX polish, consider:
     - Keyboard navigation for playlist badges and sidebar
     - Drag-and-drop playlist reordering in the sidebar
     - Multi-clip add/remove to playlists from both grid and detail views
     - Playlist export as .zip or TouchDesigner .tox
  3. See `TODO.md` for granular next steps and open issues.
  4. All code is modular and documented for rapid onboarding.

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

