# LoopSleuth: React Migration Plan

## Why Migrate to React?
- **Performance:** True windowed virtualization (e.g., `react-window`) for smooth scrolling with thousands of clips.
- **Modularity:** Components for grid, cards, batch bar, playlists, overlays, etc.
- **Creative UI:** Easier to add advanced/animated/interactive features (PiP, overlays, drag-and-drop, etc.).
- **Maintainability:** Modern state management, hot reload, and robust ecosystem.
- **Future-Proof:** Ready for creative workflows, rapid prototyping, and production use.

## Migration Overview

### 1. **Scaffold React App**
- Use [Vite](https://vitejs.dev/) for fast, modern setup.
- Directory: `src/loopsleuth/web/react/`
- TypeScript for type safety and maintainability.

### 2. **File/Directory Structure**
```
src/loopsleuth/web/react/
  ├── public/
  │   └── index.html
  ├── src/
  │   ├── components/
  │   │   ├── Grid.tsx
  │   │   ├── ClipCard.tsx
  │   │   ├── BatchBar.tsx
  │   │   ├── PlaylistSidebar.tsx
  │   │   └── ... (PiP, overlays, etc.)
  │   ├── App.tsx
  │   ├── api.ts
  │   └── main.tsx
  ├── package.json
  ├── tsconfig.json
  └── vite.config.ts
```

### 3. **Key Components**
- **Grid.tsx:** Virtualized grid using `react-window`.
- **ClipCard.tsx:** Renders a single clip (thumbnail, filename, star, PiP button, etc.).
- **BatchBar.tsx:** Selection and batch actions (add/remove tags, export, etc.).
- **PlaylistSidebar.tsx:** Playlist management and filtering.
- **api.ts:** Functions to call FastAPI endpoints (`/api/clips`, `/batch_tag`, etc.).
- **App.tsx:** Main app layout, routing, and state.

### 4. **Migration Steps**
1. **Scaffold the React app** in `src/loopsleuth/web/react/`.
2. **Implement a minimal virtualized grid** with `react-window` fetching from `/api/clips`.
3. **Port selection and batch bar logic** to React state/components.
4. **Integrate playlist sidebar and overlays** as components.
5. **Connect all actions to FastAPI endpoints** (tagging, playlists, export, etc.).
6. **Polish UI/UX:** Add creative features, animations, and accessibility.
7. **Build and serve** the React app as static files via FastAPI `/static`.

### 5. **Short-Term Patch for Current Grid (if needed)**
- Cancel in-flight fetches on new scroll events.
- Replace, don't append, DOM nodes for the grid window.
- Use IntersectionObserver for lazy image/video loading.
- (Optional) Integrate a more robust vanilla JS virtual scroller (e.g., Virtual Scroller, HyperList) if React migration is delayed.

### 6. **Automated Duplicate Detection**
- Add a background job or endpoint to scan for duplicates (by pHash, filename, etc.) and flag them automatically.
- UI: Show flagged duplicates in the new React grid and review UI.

## Next Actions
- [ ] Scaffold the React app with Vite + TypeScript.
- [ ] Implement minimal grid and API integration.
- [ ] Port selection, batch bar, and playlist logic.
- [ ] Document creative/UX enhancements for future sprints.
- [ ] (Optional) Patch current grid for better performance until React is live.

---

**This migration will unlock a modern, robust, and creative grid experience for LoopSleuth.**

If you want to customize the initial React setup (theme, UI style, etc.), specify your preferences before scaffolding! 