# Project TODOs

## ✅ Batch Tag Editing: Production-Ready (2024-06)
- Batch tag add, remove, and clear actions are fully implemented and robust in both backend and frontend.
- The batch action bar UI is reliable, immediate, and accessible for all tag changes.
- Automated tests for batch tag actions are present and passing (see `tests/test_batch_tag.py`).
- The test suite uses a production-matching schema and covers all batch tag actions for multiple clips.
- The batch tag workflow is now fully production-ready and tested as of this commit.

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
    - [x] Unify tag/star JS logic in a shared static file and include in both grid and detail templates.
- [ ] **TUI is now feature-frozen except for critical bugfixes.**

### MVP checklist (hand‑curated)

- [ ] cli.py: Typer entry ‑‑scan/‑‑ui/‑‑export
- [ ] ingest_folder(): tqdm walk, call probe_video(), commit
- [ ] thumbnails: skip if exists & mtime unchanged
- [ ] Textual grid: lazy‑load thumbs (path → Image.open)
- [ ] export_td: write absolute paths, newline‑delimited
<!-- CURSOR:KEEP_END -->

### Tag Autocomplete & Deletion Implementation Plan

#### Tag Autocomplete
- [x] Backend: `/tags` endpoint returns all tag names (already implemented).
- [x] Backend: Add `/tags?q=prefix` endpoint for prefix search (now implemented).
- [x] Frontend: On tag input, fetch suggestions from `/tags` (debounced, filter as user types).
- [x] Frontend: Show dropdown of suggestions below the input.
- [x] Frontend: Allow keyboard/mouse selection of suggestions; on select, add tag chip.
- [x] Testing: Verify with similar prefix tags, new tags, and UX polish (pending user feedback).

#### Tag Deletion (chip X)
- [x] Frontend: Render editable tag chips with X for removal (already implemented in JS, but ensure UX is robust).
- [x] Frontend: On X click, remove tag from input and update chips live.
- [x] Frontend: On save, persist tag removal via AJAX to backend.
- [x] Testing: Remove tags, verify persistence and UI update (pending user feedback).

---

**[2024-06-14] Tag autocomplete and deletion changes committed and pushed. Next step: user testing and UX polish as needed.**

### NEXT: Batch Editing & Filtering (after autocomplete/deletion)
- [x] Design and implement multi-select in grid view.
- [x] Add batch action controls (add/remove tags, star/unstar, delete) UI.
- [x] Batch tag autocomplete to batch bar inputs.
- [x] Batch tag input uses chip-style input with autocomplete, keyboard navigation, and removable chips, matching single-clip edit UX.
- [x] Batch add/remove/clear is fully accessible and visually consistent.
- [x] Batch remove field is now chip-based: chips represent tags present on selected clips, are removable with ×, and only chips in the remove field are removed. Autocomplete suggests only tags present on selected clips and not already chips. UX matches single-clip edit for clarity and accessibility.
- [x] Per-clip tag editing in the detail view is now fully consistent with the batch editor (chip-style input, autocomplete, keyboard/ARIA UX). Tag saving is robust and persists to the database.
- [x] Codebase is ready for handoff and onboarding. See STARTUP_MESSAGE.md and README.md for latest state and next steps.
- [x] Backend: Add endpoints for batch tag/star actions and filtering.
- [x] Wire up frontend batch actions to backend.
- [x] Add batch tag autocomplete and polish.
- [x] Testing: Select multiple clips, apply actions, verify DB and UI.

### Troubleshooting
- Batch bar and batch tag autocomplete are working in the UI.
- Backend and DB schema are correct; `/test_tag/{clip_id}` endpoint works with valid JSON.
- Browser AJAX requests for single-clip tag editing are working; batch actions backend integration is next.
- [x] [2024-06-14] Batch bar tag add/remove/autocomplete now robust to DOM state. Toast feedback restored. Selection logic fixed. Batch bar is now resilient to rapid selection/deselection and DOM changes.

