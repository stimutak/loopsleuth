"""
LoopSleuth Web Frontend (FastAPI)

- Serves the main grid view of clips (with thumbnails)
- Will support video playback, tagging, starring, and export
- Uses Jinja2 templates and static files
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys
sys.path.append(str((Path(__file__).parent.parent.parent).resolve()))  # Ensure src/ is importable
from loopsleuth.db import get_db_connection, DEFAULT_DB_PATH

# --- App setup ---
# For development/demo: use the test DB with clips
DEFAULT_DB_PATH = Path("temp_thumb_test.db")  # <-- Use test DB for now
app = FastAPI(title="LoopSleuth Web")

# Mount static files (for thumbnails, CSS, JS, etc.)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
def grid(request: Request):
    """
    Main grid view: shows all clips with thumbnails and info.
    """
    # Connect to the database and fetch all clips
    conn = None
    clips = []
    try:
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, thumbnail_path, starred, tags
            FROM clips
            ORDER BY filename ASC
        """)
        for row in cursor.fetchall():
            clips.append(dict(row))
    except Exception as e:
        print(f"[Error] Could not load clips: {e}")
    finally:
        if conn:
            conn.close()
    return templates.TemplateResponse(
        "grid.html", {"request": request, "clips": clips}
    )

@app.get("/clip/{clip_id}", response_class=HTMLResponse)
def clip_detail(request: Request, clip_id: int):
    """
    Detail page for a single clip: video playback and metadata.
    """
    conn = None
    clip = None
    try:
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, path, thumbnail_path, starred, tags
            FROM clips WHERE id = ?
        """, (clip_id,))
        row = cursor.fetchone()
        if row:
            clip = dict(row)
        else:
            raise HTTPException(status_code=404, detail="Clip not found")
    except Exception as e:
        print(f"[Error] Could not load clip {clip_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            conn.close()
    return templates.TemplateResponse(
        "clip_detail.html", {"request": request, "clip": clip}
    )

# TODO: Add API endpoints for clips, tagging, starring, etc.
# TODO: Add video playback route 