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

### Web UI JavaScript
- All AJAX actions for starring and tag editing are handled by a shared static JS file (`src/loopsleuth/web/static/clip_actions.js`).
- Both the grid and detail views include this file for consistent, maintainable behavior.

### Tag System (vNext)
- Tags are now stored in a normalized schema: a `tags` table (unique tag names) and a `clip_tags` join table (many-to-many: clips <-> tags).
- This enables tag reuse, autocomplete, and efficient tag-based search/filtering.

### Tag Editing UX (2024-06)

- **Keyboard Shortcuts:**
  - `e` or `Enter` focuses tag input for editing (when tag area is focused)
  - Arrow keys navigate autocomplete suggestions
  - `Enter`/`Tab` selects a suggestion if highlighted
  - `Backspace` in empty input removes last tag chip
  - `Escape` closes dropdown if open, otherwise saves and exits edit mode
- **Mouse:**
  - Click X to remove tag
  - Click outside tag editor to save and exit
  - Click suggestion to add
- **Visual:**
  - Edit mode is visually indicated with a border and background
- **Accessibility:**
  - Full ARIA roles/attributes for dropdown, input, and chips (screen reader and keyboard accessible)
  - Dropdown scrolls to keep highlight visible (for long lists)
  - Professional compliance: works with screen readers and assistive tech

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

