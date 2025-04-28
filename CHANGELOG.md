# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Ongoing bug fixes and UI polish.
- Playlist sidebar checkboxes now select target playlists for add/remove, not for filtering.
- Added filter icon (🔍) for explicit filtering by playlist.
- Grid card checkboxes are now larger, lighter, and flush to the upper-left for better accessibility and usability.
- Multi-playlist add/remove is now fully supported from the grid.
- The grid and sidebar are decoupled for a more flexible, creative workflow.
- **Playlist pills on grid cards now have a remove (✖) button to remove a clip from a playlist, with instant UI update and toast feedback.**
- **Grid view reloads after playlist changes to reflect new playlist membership.**
- **Creating a new playlist with clips selected immediately adds those clips to the new playlist.**
- **All playlist pill rendering is now handled in JS, not Jinja, to avoid context errors and server errors.**
- **Fixed 500 Internal Server Error caused by Jinja referencing 'clip' outside of a valid context.**
- **All core playlist, tagging, and selection workflows are robust and production-ready.**
- **This is a stable handoff point for onboarding or further development.**

## [1.2.0] - 2025-04-26

### 2025-04-22
- Scaffold web frontend: FastAPI app, Jinja2 template, static CSS, and requirements. Documented all steps for migration to web UI.
- Real grid view wired to database. Renders clips with thumbnails, filename, star, and tags. Documented all logic and styling.
- Add video playback detail page. Cards link to /clip/{id}, which shows video, metadata, and back link.
- Serve thumbnails and videos via FastAPI routes. Grid and detail pages now use /thumbs/ and /media/ endpoints for robust media access.
- Add folder scan form and cross-platform folder picker helper.
- AJAX tag editing: update /tag/{clip_id} endpoint for JSON, improve grid/detail UX, document changes.
- Document AJAX tag editing, endpoint fix, UX improvements, and check-in practices.
- Fix /tag/{clip_id} endpoint to use Pydantic model for JSON, resolves 422 error and ensures tag persistence.
- Update startup message date and README for web-first direction. Reference STARTUP_MESSAGE.md for project state.
- Remove data, thumbnails, and movies from repo; add to .gitignore.
- Add clean handoff and CI sections to README; add Python CI workflow.
- Use data-clip-id for event handlers in grid.html to silence linter errors and improve maintainability.
- Unify tag/star AJAX logic in shared static JS, update docs, DRY grid/detail templates.

### 2025-04-24
- Add normalized tag schema (tags, clip_tags tables) for reusable tags; update docs and TODO.
- Add migration script to move tags from clips.tags to tags/clip_tags tables (dry-run by default).
- Backend now uses normalized tag schema; tags as list, new /tags endpoint, tag update logic.
- Tag UI now uses chips, tag editing uses array logic, JS and CSS updated.
- Always send tags as array in saveTags, add error handling for tag save failures.
- Tag autocomplete: backend prefix search and live frontend suggestions. Tag deletion polish.
- Tag edit mode: show editable chips with X, sync with input; static mode shows plain chips only.
- Fix tag edit mode toggling: show editable chips with X in edit mode, static chips in view mode. Chips now render in correct container.
- Refactor to standard tag input: chips with X and single input for new tag in edit mode. UX matches Gmail/Notion style.
- Fix tag edit mode visibility: force display for chips/input, add cancel button and Escape handler for robust toggling.
- Autocomplete UX: arrow keys to navigate, Tab/Enter to select, no duplicate tags (case-insensitive).
- Unify tag edit UI in detail view: chips, single input, save/cancel buttons (matches grid view).
- Fix tag edit cancel/save: always restore or update static chips to match correct tag state.
- Fix: prevent X from being appended to tag names in chips and backend. Chips now only contain tag name as text node.
- Add documented autocomplete to batch tag inputs in batch action bar. Uses /tags endpoint for suggestions, positions dropdown, and inserts tags as comma-separated values. Fully documented and modular, matching single-clip tag UX. Prepares for backend batch tag actions integration.
- Update TODO and STARTUP_MESSAGE for batch tag autocomplete and handoff state. Mark batch tag autocomplete as implemented in batch bar. Clarify next steps: backend integration for batch tag actions. Remove outdated notes about batch bar visibility and autocomplete. Ensure handoff and project state are clear for upgrade or collaboration.
- Batch tag editing: chip-style input, autocomplete, and full UX parity with single-clip edit. Docs updated.
- Batch remove UX: chip-based, removable chips, selection-aware autocomplete, and robust removal. Docs updated.
- UI/UX: Remove per-clip tag editor from grid, batch bar is now sole grid tag editor. Per-clip tag editing remains in detail view only. Docs updated for new workflow.

### 2025-04-25
- Bugfix: batch bar tag add/remove/autocomplete now robust to DOM state, toast feedback restored, selection logic fixed. Batch bar is now resilient to rapid selection/deselection and DOM changes. Docs updated.
- Per-clip tag editing in detail view now matches batch editor: chip input, autocomplete, robust save. Docs and handoff notes updated. Ready for onboarding/handoff.
- Batch tag editing (add/remove/clear) is now robust, production-ready, and fully tested. Updated docs, frontend, and backend. All tests passing.
- Ultra-dark theme, custom scrollbars, and production-ready batch/tag/export/copy UX. Deepened UI palette for true black look. Custom dark scrollbars for all scrollable elements. Batch selection, tagging, export, and copy-to-folder fully implemented. All docs updated for handoff and onboarding. Ready for next dev: playlist, advanced export, further polish.
- Update README for robust flexbox sidebar/grid layout, playlist sidebar, and production-ready responsive UI.
- Web UI: robust detail view, left sidebar, production DB, progress bar, error handling, filesizeformat filter, and doc updates.
- Handoff: Playlist badge/sidebar sync, visual feedback, and onboarding docs. Detail view playlist badges now select, highlight, and scroll sidebar. Updated README and STARTUP_MESSAGE.md with path forward.
- Add BUG_HANDBOOK.md and ROADMAP.md to version control (persistent debug/handoff docs).

### 2025-04-26
- Add test coverage section and instructions; fix test DB isolation; refactor for runtime DB path resolution; remove DEFAULT_DB_PATH imports; all tests passing.
- Fix: ensure batch action bar always appears above sidebar and add visual separation.
- Mark 999d0372cb193b2ff9543ec5783646b4b136b2e2 as working baseline for batch action bar and UI/UX. Update TODO and bug handbook.
- Add favicon assets and update grid.html to reference all favicon sizes.
- Restyle scan folder input and button to match site aesthetic.
- Apply Notch-style elegant, thin typography to all form elements site-wide.
- Restore and improve /open_in_system/{clip_id} endpoint to open containing folder in system file explorer.
- Improve /open_in_system/{clip_id} to select the file in Explorer/Finder (Windows/macOS).
- Add favicon links to clip_detail.html for consistent branding across all pages.
- Add favicon links to error/404 pages and implement thumbnail size slider in grid view.
- Wire up custom video controls in detail view (play/pause, seek, frame step, volume).

#### Grid Sorting, Starred, and Preview Features
- Added grid sorting by name, date modified, size, duration, and starred (favorites)
- Added 'Show starred first' checkbox to prioritize favorites in any sort order
- Persistent sort bar with dropdowns for field and order, always visible above the grid
- Each card now has a PiP (Picture-in-Picture) button for floating video preview
- Selection bar includes a Preview Grid button to open a floating overlay with a grid of video previews for selected clips
- Improved selection logic and batch bar robustness
- All sorting and preview features are robust, accessible, and tested for creative/visual workflows
- Bugfix: grid preview and PiP now use correct file paths and work for all valid clips
- Bugfix: selection and preview bar handlers are now reliably attached after re-renders

## [2024-06] Preview Grid Overlay Improvements
- Refactored the Preview Grid overlay to use a fully adaptive, responsive CSS Grid layout.
- Video player cells now maximize their size and aspect ratio based on the number of selected clips and viewport.
- Videos fill available vertical space and maintain aspect ratio, providing a better review experience.
- Grid columns use `repeat(auto-fit, minmax(320px, 1fr))` for responsive adaptation.
- See `src/loopsleuth/web/static/clip_actions.js` for implementation details.

## [1.3.0] - 2024-06-XX

### Major Handoff/UX Refactor
- Grid view now uses Clusterize.js for virtualized, infinite scrolling (no classic pagination).
- Backend exposes `/api/clips` for windowed, paged data to support the virtualized frontend.
- Multi-column grid layout restored using flex rows; responsive and robust for large libraries.
- Thumbnail slider is fully integrated and controls all visible thumbnails via CSS variable.
- Batch tag bar and selection bar are always visible and robust to DOM changes.
- All code is modular, maintainable, and ready for creative/production workflows.
- See README for handoff summary and onboarding notes.

## [2024-06-XX] Duplicate Detection, Review, and Merge Features

- Added perceptual hash (pHash) duplicate detection on ingestion, with configurable handling (skip, mark-for-review, log, auto-merge).
- Schema: Added `needs_review` and `duplicate_of` columns to `clips` table for robust duplicate tracking and review.
- New batch duplicate review UI at `/duplicates`:
  - Groups flagged duplicates by canonical clip.
  - Shows canonical and duplicate(s) side-by-side with thumbnails, filenames, and metadata.
  - Actions: **Keep**, **Delete**, **Ignore**, **Merge** (merge tags/playlists and delete duplicate).
  - Merge action transfers all tags and playlist memberships from duplicate to canonical, then deletes the duplicate.
  - Toast/snackbar feedback for all actions.
- Grid view now shows a prominent banner linking to `/duplicates` if any duplicates are flagged for review.
- All duplicate review actions are available after re-ingestion with the new logic, or by manually flagging test rows in the DB.
- Backend: `/api/duplicates` (fetch groups), `/api/duplicate_action` (resolve actions).
- All changes are fully documented and modular for further extension.

## [2024-06-XX] Recent Scan Folders & Database Selection

- Added a dropdown for recent scan locations above the scan folder input. Remembers up to 8 recent folders per user (localStorage).
- Added a database selection dropdown in the grid view header/sidebar. User can add, select, and persist DBs (localStorage).
- Selecting a DB reloads the app with a ?db=... query parameter; backend now uses this for all DB operations.
- Enables seamless multi-library workflows and rapid switching between libraries/databases.
- All UI/UX and backend changes are fully documented and modular for further extension.

## [Unreleased] - 2024-06
### Added
- Unified database selection: a single combo box for recent DBs and custom entry, styled to match the UI. No more separate dropdown and manual entry fields.
- Scan folder field is also a modern combo box (recent + custom), with the last-used entry always available unless localStorage is cleared.
- All endpoints (grid, playlists, duplicates, etc.) now respect the selected database, enabling seamless multi-library workflows.
- Users do not need to re-ingest to see previous scans—just select the same DB and clips will appear if the DB file is present.

### Changed
- Improved onboarding and workflow clarity in docs and UI.
- All scan and DB errors are shown as toast notifications in the UI—no more silent failures.
- Code is modular and documented for maintainability.

### Fixed
- Prevented accidental creation of invalid or unsafe database files.
- Prevented scans from running on non-existent or unreadable folders.

---

Older changes and project history can be found in the README and ROADMAP. 