# LoopSleuth Startup Message

## Handoff & Path Forward (2024-06)
- Playlist badges in the detail view are now fully interactive and visually synced with the sidebar.
- Selecting a badge highlights it, selects and scrolls to the playlist in the sidebar, and provides immediate feedback.
- See the README for a full onboarding checklist and next steps for playlist/UX polish.

## Handoff Note (2024-06)
- **Production-ready:** Modern dark UI, batch selection/tagging, export (keepers.txt), and copy-to-folder for selected clips. Custom checkboxes, grid scroll restore, robust batch UX.
- **Next steps for dev:** Playlist management (create, name, reorder, export), advanced export (zip, .tox, etc.), further UX polish (keyboard shortcuts, accessibility, creative/visual features), gather user feedback and iterate.

## Project State (2024-06)
- **Web UI** is the primary interface (FastAPI + Jinja2).
- **Tag system is normalized** (tags/clip_tags tables), and tag editing via the web UI is working for single clips. Batch tag autocomplete is now implemented in the batch action bar.
- **All other core features** (grid, detail, starring, thumbnailing, scanning) are working.
- **Recent debugging**: Confirmed backend and DB schema are correct; single-clip tag editing and batch bar UI are working. Batch actions backend integration is next.
- **Next steps**: Implement backend for batch tag actions, wire up frontend, then add feedback and polish.
- **See TODO.md** for precise next actions and troubleshooting notes.
- Per-clip tag editing in the detail view is now fully consistent with the batch editor: chip-style input, autocomplete, keyboard navigation, and ARIA/accessibility are all supported. Tag changes are persisted to the database and reflected in both the detail and grid views.

## Preview Grid Overlay Improvements (2024-06)
- The Preview Grid overlay now uses a fully adaptive, responsive CSS Grid layout.
- Video player cells automatically adjust their size and aspect ratio based on the number of selected clips and the viewport size.
- Videos are maximized within their grid cells, maintaining aspect ratio and filling available vertical space.
- The grid uses `repeat(auto-fit, minmax(320px, 1fr))` for columns, and each cell/video fills the available height and width.
- The overlay is robust for 1 to many selected clips, and the code is modular and ready for further creative/UX enhancements.
- See `src/loopsleuth/web/static/clip_actions.js` for the JS logic and `grid.html` for the template.

## Batch Editing Handoff Checklist

### ✅ What's Implemented
- Batch selection UI: Checkbox, click, shift+click, ctrl/cmd+click for multi/range selection. Visual highlight for selected cards.
- Batch action bar: <div id="batch-action-bar"> present in grid.html template. CSS for floating bar and controls in style.css. JS logic for rendering the bar and handling selection in clip_actions.js.
- Tag editing UI: Add tags, remove tags, clear all tags (UI and backend). Keyboard accessibility and ARIA for tag editing.
- Batch tag autocomplete: Autocomplete dropdown for batch add/remove tag fields in the batch bar, matching single-clip tag UX.
- **Batch tag input now uses chip-style input with autocomplete, keyboard navigation, and removable chips, matching the single-clip edit UX.**
- **Batch add/remove/clear is fully accessible and visually consistent.**
- **Batch remove field is now chip-based:** Chips represent tags present on selected clips, are removable with ×, and only chips in the remove field are removed. Autocomplete suggests only tags present on selected clips and not already chips. UX matches single-clip edit for clarity and accessibility.
- README: Updated with tag editing and batch editing UX, keyboard shortcuts, and accessibility.

### 🟡 What's NOT Done
- [ ] Backend integration for batch tag add/remove/clear (no /batch_tag endpoint yet).
- [ ] No toast/snackbar feedback after batch operations.

### 🚦 Next Steps
- [ ] Implement /batch_tag endpoint in backend.
- [ ] Wire up frontend batch actions to backend.
- [ ] Add feedback (toast/snackbar) after batch actions.

### 📄 File Locations
- Grid template: src/loopsleuth/web/templates/grid.html
- Batch bar JS: src/loopsleuth/web/static/clip_actions.js
- Batch bar CSS: src/loopsleuth/web/static/style.css
- README: Project root

## How to Resume
- All recent fixes and context are documented in `TODO.md` and this message.
- To continue, start a new chat and reference this summary for seamless handoff.
- For any new features, review the last commits and TODOs for guidance.

## ✅ Batch Tag Editing: Production-Ready (2024-06)
- Batch tag add, remove, and clear actions are fully implemented and robust in both backend and frontend.
- The batch action bar UI is reliable, immediate, and accessible for all tag changes.
- Automated tests for batch tag actions are present and passing (see `tests/test_batch_tag.py`).
- The test suite uses a production-matching schema and covers all batch tag actions for multiple clips.
- The batch tag workflow is now fully production-ready and tested as of this commit.

## Video Preview Grid UI Exploration & Handoff (2024-06)

### Context
- The preview grid overlay was iteratively refined to maximize video preview size and maintain a professional, consistent layout.
- The goal was for each video preview to scale up in both width and height as the browser window grows, always maximizing the use of available space, while preserving aspect ratio and avoiding distortion or cropping.

### What Was Tried
- **Pure CSS Grid/Flexbox with object-fit: contain:**
  - Ensures videos are never cropped or distorted, but results in letterboxing/pillarboxing for non-16:9 content.
  - As the grid/cell gets wider, the height increases proportionally (with aspect-ratio), but only up to the limits of the grid and the number of columns.
- **object-fit: cover:**
  - Crops the video to always fill the cell, eliminating letterboxing, but at the cost of losing part of the image.
- **Dynamic aspect ratio per cell:**
  - Explored, but not implemented due to complexity and limited benefit for a grid of mixed aspect ratios.
- **Max-width and aspect-ratio constraints:**
  - Used to prevent cells from stretching excessively wide on large screens with few clips.

### Final Solution
- **Each cell uses a fixed 16:9 aspect ratio and a max width (800px).**
- **Grid uses auto-fit and minmax for responsive columns, centered content, and gap spacing.**
- **Videos use object-fit: contain, width: 100%, height: 100%.**
- This provides a robust, professional, and standards-compliant grid, matching the approach used by major video platforms.
- The grid is visually consistent, responsive, and works for any number of selected clips.

### Technical Constraints & Notes
- With a fixed aspect ratio, the cell's height always grows in proportion to its width. If the grid container is very wide and there are only a few items, the cells will get large, but always in proportion.
- There is no pure CSS/HTML solution to make every video fill both width and height of the overlay for arbitrary aspect ratios, without cropping or distorting the video.
- This is the same limitation and solution used by YouTube, Vimeo, and other professional video gallery UIs.

### Handoff
- The current implementation is robust, maintainable, and ready for further creative or advanced UX enhancements if desired.
- For single-video full-size preview, consider a modal overlay with dynamic aspect ratio.
- For creative/experimental layouts, consider custom canvas/WebGL or dynamic aspect ratio per cell (complex).

## 🚦 Handoff Summary (2024-06)

- Playlist sidebar checkboxes now select target playlists for add/remove actions (not for filtering the grid).
- Filter icon (🔍) next to each playlist name filters the grid by that playlist.
- Grid card checkboxes are larger, lighter, and flush to the upper-left for easy, accessible multi-select.
- Batch add/remove to multiple playlists is fully supported from the grid.
- The grid and sidebar are decoupled for a more flexible, creative workflow.
- The grid view now uses a virtualized, infinite scroll powered by Clusterize.js for robust performance with large libraries.
- The backend exposes `/api/clips` for windowed, paged data to support the virtualized frontend.
- Thumbnails are loaded on demand and sized via a persistent slider (using a CSS variable and localStorage).
- The grid is multi-column, responsive, and batch actions (tagging, selection) are fully supported.
- The batch tag bar and selection bar are always visible and robust to DOM changes.
- All code is modular, maintainable, and ready for creative/production workflows.
- See README for onboarding and file locations.

---
_Last update: 2024-06-XX_

[2024-06-14] Batch bar tag add/remove/autocomplete now robust to DOM state. Toast feedback restored. Selection logic fixed. Batch bar is now resilient to rapid selection/deselection and DOM changes. 

The Preview Grid overlay is robust, adaptive, and ready for further creative/UX enhancements. Code is modular and ready for onboarding. 

## 🚦 New Features & Onboarding (2024-06)

- **Recent Scan Folders:** The scan form now includes a dropdown of your last 8 scanned folders (per user, localStorage). Select or type a folder to scan instantly.
- **Database Selection:** Use the database dropdown in the header/sidebar to switch between libraries. Add new DBs, persist your selection, and reload the app with the chosen DB (via ?db=... param). All actions are scoped to the selected DB.
- **Seamless Multi-Library Workflow:** The backend supports per-request DB switching. Scan, tag, review duplicates, and manage playlists in any selected DB without restarting the server.
- **Duplicate Review Banner:** If any duplicates are flagged, a prominent banner appears in the grid view linking to the batch review UI. Resolve, merge, or ignore duplicates directly from the web UI.
- **Database and scan folder selection are now unified, modern combo boxes (recent + custom entry, styled, with recents persisted per user).**
- **The last-used database and scan folder are always available at the top of their respective dropdowns, unless localStorage is cleared.**
- **All endpoints (grid, playlists, duplicates, etc.) now respect the selected database, enabling seamless multi-library workflows.**
- **Users do not need to re-ingest to see previous scans—just select the same DB and your clips will appear if the DB file is present.**
- **All scan and DB errors are shown as toast notifications in the UI for immediate feedback.**
- **Onboarding and workflow documentation is up to date and reflects these improvements.**

## 🚦 Onboarding Checklist (2024-06)

- **Switch Libraries:** Use the database dropdown to select or add a DB. The app reloads with the selected DB, and all actions (scan, tag, review) apply to that library.
- **Scan Folders:** Use the scan form and recent folders dropdown to quickly rescan or add new locations. Recent folders are remembered per user.
- **Review Duplicates:** If flagged, review and resolve duplicates from the grid banner or the /duplicates page. Merge tags/playlists, keep, delete, or ignore as needed.

### 1. Setup
- Clone the repo and set up a Python 3.10+ virtual environment.
- Install requirements: `pip install -r requirements.txt`
- Ensure ffmpeg/ffprobe are installed and in your PATH.
- Start the FastAPI server: `python src/loopsleuth/web/app.py` (or via your preferred ASGI runner).

### 2. Running the App
- Open the web UI at `http://localhost:8000` (or your configured port).
- Use the scan form to ingest a folder of video clips.
- Thumbnails and metadata will be generated and stored in the database.

### 3. Grid & Selection UX
- The grid supports infinite scroll (Clusterize.js), batch selection, tagging, export, and PiP preview.
- Selection supports shift+click (range), ctrl/cmd+click (multi-toggle), and card/checkbox selection.
- Batch action bar and preview grid button respond to selection.
- Tagging, starring, and batch actions are robust and production-ready.

### 4. Testing
- Run tests with `pytest --maxfail=3 --disable-warnings -q` (set `PYTHONPATH=src` if needed).
- The test suite covers grid card markup and core backend logic.

### 5. Main Logic Locations
- Grid template: `src/loopsleuth/web/templates/grid.html`
- Shared JS (selection, PiP, batch bar): `src/loopsleuth/web/static/clip_actions.js`
- CSS: `src/loopsleuth/web/static/style.css`
- Backend: `src/loopsleuth/web/app.py` and related modules
- Tests: `tests/`

### 6. Known Issues / TODOs
- See `TODO.md` for PiP diagnostics, selection performance, and planned features (saved sets, etc.).
- PiP may need further diagnostics for some browsers.
- Selection performance can be further optimized for very large grids.

### 7. Handoff
- All major features are production-ready and regression-tested.
- Code is modular, maintainable, and ready for further creative/UX enhancements.
- For any new features or bugfixes, check `TODO.md` and recent commit messages for context. 