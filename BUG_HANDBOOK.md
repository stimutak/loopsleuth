# LoopSleuth Persistent UI Bugs: Handoff & Debug Handbook

**[2025-04-22 to 2025-04-26] NOTE:** Major UI/UX improvements and new features were implemented over this period:
- Favicons are now present on all pages (grid, detail, error, 404) for consistent branding.
- A thumbnail size slider is available above the grid view, allowing users to adjust thumbnail size in real time (value is persisted per browser).
- The detail view now features fully functional custom video controls (play/pause, seek, frame step, volume) in addition to the native controls.
- All text and icon colors are now a subtle grey for a more elegant look.
- The "Open in System" feature now selects the file in Explorer (Windows) or reveals it in Finder (macOS), and opens the folder on Linux.
- All form elements and buttons use a modern, thin, Notch-inspired typographic style.

---

## 1. Sidebar Still Pinned (Grid View)

### Symptoms
- Playlist sidebar (`#playlist-sidebar`) remains visually "pinned" to the viewport and does not scroll with the rest of the page content in the grid view.
- This persists even after removing all `position`, `min-height`, `height`, and `width` constraints from both `body` and `.main-layout`, and after adding a tall dummy element to force scrolling.
- CSS is confirmed to be loading (debug border appears when added).

### What's Been Tried
- Multiple rounds of CSS cleanup: all fixed/absolute positioning, min-height, and width constraints removed from sidebar, body, and `.main-layout`.
- Confirmed `.main-layout` is the only flex container, and the sidebar is a direct child.
- Added a tall dummy div to force page scrolling for debug.
- Hard refreshes and cache clears.

### Suspected Root Causes
- The flex container (`.main-layout`) or its parent is still constraining the page height, possibly due to a subtle CSS inheritance or browser rendering quirk.
- There may be a parent container or global style (possibly from a browser extension or injected CSS) that is still enforcing a viewport lock.
- The grid content may not be overflowing as expected, or the sidebar is being visually "pinned" by some other means.

### Next Steps for Debug
- Use browser dev tools to inspect the computed styles and layout tree for `.main-layout`, `body`, and `#playlist-sidebar`.
- Temporarily set `body, html, .main-layout { outline: 2px solid red/green/blue; }` to visually debug which element is not scrolling.
- Check for any global CSS, extensions, or JS that might be affecting layout.
- Try moving the sidebar outside of `.main-layout` as a test to see if it scrolls independently.

---

## 2. Batch Tag Bar Autocomplete: Menu Not Clickable, Console Flood

### Symptoms
- The autocomplete dropdown in the batch tag bar (bottom of grid) is not reliably mouse-selectable.
- Clicking a suggestion often causes the menu to disappear before the click registers, or floods the console with repeated `/tags` requests.
- The dropdown sometimes appears/disappears rapidly on mouse movement.

### What's Been Tried
- Refactored JS to ensure only one dropdown is created and reused.
- Debounced the input event handler to reduce excessive `/tags` requests.
- Applied robust mouse selection logic (global flag, onmousedown, delayed blur).
- Added debug logging to trace dropdown creation, input events, and mouse selection.

### Suspected Root Causes
- The dropdown may still be recreated or re-rendered on every input/mouse event, causing event handlers to be lost.
- There may be multiple event listeners or race conditions between input, blur, and mousedown.
- The debounce logic may not be applied consistently, or the input event handler is being attached multiple times.

### Next Steps for Debug
- Use browser dev tools to inspect the DOM for multiple dropdowns and check event listeners.
- Add more granular debug logs to trace the exact event order (input, mousedown, blur).
- Consider using a library for autocomplete or a more robust event delegation pattern.
- Test with a minimal HTML/JS page to isolate the issue outside of the main app.

### Status
- [2024-06-16] Batch action bar and autocomplete are working as of commit ef8fdea. If issues recur, compare against this baseline.

---

## 3. Excessive `/tags` Requests

### Symptoms
- The backend logs show a flood of `/tags?q=...` requests, even with debounce logic in place.
- This can cause performance issues and unnecessary server load.

### What's Been Tried
- Debounced the input event handler for the batch tag bar (120ms).
- Ensured only one event handler is attached per input.

### Suspected Root Causes
- The input event handler may still be attached multiple times (e.g., every time the batch bar is rendered).
- The debounce function may not be correctly scoped or is being recreated on each render.

### Next Steps for Debug
- Add a console log on event handler attachment to ensure it only happens once.
- Use browser dev tools to inspect event listeners on the input.
- Refactor to attach the handler only once, or use event delegation.

---

## Handoff Checklist (2025-04-26)
- All major UI/UX improvements are in place and committed.
- Favicons are present on all pages.
- Thumbnail size slider is implemented and persistent.
- Custom video controls are functional in the detail view.
- All form elements and buttons use the new typographic style.
- Reference this document in your new chat or issue tracker.
- Attach or link to the current `style.css`, `clip_actions.js`, and `grid.html` for context.
- Use the "Next Steps for Debug" sections above as a checklist for the next developer.
- If possible, reproduce the issues in a minimal HTML/JS/CSS test case to isolate from the main app.

---

_Last updated: 2025-04-26_ 