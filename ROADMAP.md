# LoopSleuth Roadmap (v0.1-web → v0.2)

> A concise, actionable sequence of tasks to evolve LoopSleuth from the current web MVP to a more modular, production-ready application. Each item is sized for effort so you can triage or parallelize as needed.

---

## Legend – Effort Estimates

| Emoji | Effort | Typical Duration |
|:---:|:---|:---|
| 🟢 | **Quick win** | ≤ 1 hour |
| 🟡 | **Small task** | 1 – 4 hours |
| 🟠 | **Sprint-size** | ½ – 2 days |
| 🔵 | **Project-size** | > 2 days |

---

## Priority Task List

| # | Effort | Task | Outcome / Rationale |
|---|:---:|---|---|
| 0 | 🟢 | **Create a `dev` branch and push the current state** | Freeze `main` before large refactors. |
| 1 | 🟢 | **Add Ruff + Black + mypy to CI** | Establish style / type gates while codebase is still small. |
| 2 | 🟡 | **Split `web/app.py` into modular routers & services** | Improves testability and keeps files < 300 LOC. |
| 3 | 🟡 | **Global fetch-error handler in `clip_actions.js`** | User-visible toast on any 4xx/5xx instead of silent failure. |
| 4 | 🟠 | **Background job wrapper for long ops** (`export_zip`, `ingest_directory`) | Prevents blocking FastAPI event loop; foundation for future queue. |
| 5 | 🟡 | **Fix batch-action bar flicker** (z-index + Firefox test) | Restores polished UX across browsers. |
| 6 | 🟠 | **Introduce Alembic (or yoyo-migrations)** | Version-controlled schema; no more manual SQL scripts. |
| 7 | 🟡 | **Front-end build pipeline** (Vite/ESBuild) | Bundled, hashed assets; easier JS modularity. |
| 8 | 🟠 | **Playwright smoke tests** (grid → tag → export flow) | Catch regressions after refactors. |
| 9 | 🟠 | **Incremental scan logic** (skip unchanged files) | 10× faster rescans on large libraries. |
| 10 | 🔵 | **Feature: playlist ZIP & .tox export** via background task | Completes MVP story for TouchDesigner hand-off. |
| 11 | 🔵 | (**Optional**) **React/HTMX migration for sidebar/modals** | Future-proof heavy UI logic; gradual enhancement path. |

---

## Implementation Pointers

### 1 · Module Split Skeleton

    src/loopsleuth/web/
        main.py               # FastAPI factory
        routes/grid.py        # Jinja grid view
        routes/playlist.py    # playlist CRUD & export
        routes/api.py         # JSON endpoints for JS fetch
        services/db_service.py

### 2 · Background Executor Sketch

    from fastapi import BackgroundTasks
    from pathlib import Path, tempfile

    @router.post("/export/zip")
    async def export_zip_endpoint(ids: list[int], tasks: BackgroundTasks):
        outfile = Path(tempfile.mkstemp(suffix=".zip")[1])
        tasks.add_task(export_zip, ids, outfile)
        return {"download": f"/download/{outfile.name}"}

### 3 · Alembic Quick-start

    pip install alembic
    alembic init migrations
    # edit alembic.ini → sqlite:///loopsleuth.db
    alembic revision --autogenerate -m "baseline"
    alembic upgrade head

### 4 · Playwright Test Stub

    # tests/e2e/test_tag_flow.py

    def test_tag_flow(playwright):
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8000")
        page.locator("data-test=clip-0").click()
        page.locator("data-test=tag-input").fill("vibe")
        page.keyboard.press("Enter")
        assert page.locator("text=vibe").is_visible()

---

## Tracking & Milestones

**Create a GitHub Project board** with columns: *Backlog | In-Progress | PR | Done*.

* Map each row in the table above to a GitHub Issue, prefixing the title with the effort emoji (e.g., `🟡 Split web/app.py into modular routers`).
* Milestone **v0.2-web** = Issues #0-#8.  
* Milestone **v0.3-export** = Issues #9-#10.

---

Feel free to reorder or re-estimate tasks as the codebase evolves. Ping me whenever you start an item and need deeper guidance. 