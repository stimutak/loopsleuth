"""
LoopSleuth Web Frontend (FastAPI)

- Serves the main grid view of clips (with thumbnails)
- Will support video playback, tagging, starring, and export
- Uses Jinja2 templates and static files
"""
from fastapi import FastAPI, Request, HTTPException, Form, Body
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys
sys.path.append(str((Path(__file__).parent.parent.parent).resolve()))  # Ensure src/ is importable
from loopsleuth.db import get_db_connection, DEFAULT_DB_PATH
from urllib.parse import unquote
from loopsleuth.scanner import ingest_directory
import mimetypes  # <-- Add this import
from pydantic import BaseModel
from typing import List

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

THUMB_DIR = Path(".loopsleuth_data/thumbnails")

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
            SELECT id, filename, duration, thumbnail_path, starred
            FROM clips
            ORDER BY filename ASC
        """)
        for row in cursor.fetchall():
            clip = dict(row)
            # Fetch tags for this clip
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN clip_tags ct ON t.id = ct.tag_id
                WHERE ct.clip_id = ?
                ORDER BY t.name ASC
            """, (clip['id'],))
            tag_list = [r[0] for r in cursor.fetchall()]
            clip['tags'] = tag_list
            thumb_path = clip.get('thumbnail_path', '')
            if thumb_path:
                clip['thumb_filename'] = thumb_path.replace('\\', '/').split('/')[-1]
            else:
                clip['thumb_filename'] = ''
            clips.append(clip)
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
    video_mime = "video/mp4"  # Default
    try:
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, path, thumbnail_path, starred
            FROM clips WHERE id = ?
        """, (clip_id,))
        row = cursor.fetchone()
        if row:
            clip = dict(row)
            # Fetch tags for this clip
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN clip_tags ct ON t.id = ct.tag_id
                WHERE ct.clip_id = ?
                ORDER BY t.name ASC
            """, (clip['id'],))
            tag_list = [r[0] for r in cursor.fetchall()]
            clip['tags'] = tag_list
            # Guess MIME type from filename
            mime, _ = mimetypes.guess_type(clip['path'])
            if mime and mime.startswith('video/'):
                video_mime = mime
        else:
            raise HTTPException(status_code=404, detail="Clip not found")
    except Exception as e:
        print(f"[Error] Could not load clip {clip_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            conn.close()
    return templates.TemplateResponse(
        "clip_detail.html", {"request": request, "clip": clip, "video_mime": video_mime}
    )

@app.get("/thumbs/{filename}")
def serve_thumbnail(filename: str):
    """
    Serve a thumbnail image from the .loopsleuth_data/thumbnails directory.
    """
    thumb_path = THUMB_DIR / filename
    if not thumb_path.exists():
        return FileResponse(THUMB_DIR / "missing.jpg", status_code=404)  # Optionally serve a placeholder
    return FileResponse(thumb_path)

@app.get("/media/{filename:path}")
def serve_video(filename: str):
    """
    Serve a video file from an absolute or relative path.
    The filename is URL-encoded and may include slashes.
    """
    # Unquote in case of spaces or special chars
    file_path = Path(unquote(filename))
    if not file_path.is_absolute():
        # Try relative to project root
        file_path = Path.cwd() / file_path
    if not file_path.exists():
        return FileResponse("404.mp4", status_code=404)  # Optionally serve a placeholder
    return FileResponse(file_path)

@app.post("/scan_folder")
def scan_folder(folder_path: str = Form(...), force_rescan: bool = Form(False)):
    """
    Scan the given folder for videos and ingest them into the DB.
    Redirects back to the grid after completion.
    """
    try:
        ingest_directory(Path(folder_path), db_path=DEFAULT_DB_PATH, force_rescan=force_rescan)
    except Exception as e:
        print(f"[Error] Scanning folder {folder_path}: {e}")
    return RedirectResponse(url="/", status_code=303)

@app.post("/star/{clip_id}")
def toggle_star(clip_id: int):
    """Toggle the 'starred' flag for a clip and return the new state as JSON."""
    conn = None
    try:
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT starred FROM clips WHERE id = ?", (clip_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({"error": "Clip not found"}, status_code=404)
        new_star = 0 if row[0] else 1
        cursor.execute("UPDATE clips SET starred = ? WHERE id = ?", (new_star, clip_id))
        conn.commit()
        return JSONResponse({"starred": new_star})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

class TagUpdate(BaseModel):
    tags: List[str]

@app.post("/tag/{clip_id}")
def update_tags(clip_id: int, tag_update: TagUpdate = Body(...)):
    """
    Update the tags for a clip. Accepts JSON {"tags": ["tag1", "tag2", ...]}.
    Updates the tags and clip_tags tables. Returns the new tag list as JSON.
    """
    print(f"[DEBUG] Received tag update for clip {clip_id}: {tag_update}")
    tags = [t.strip() for t in tag_update.tags if t.strip()]
    conn = None
    try:
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        # Insert new tags into tags table if not present
        tag_ids = []
        for tag in tags:
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
            row = cursor.fetchone()
            if row:
                tag_id = row[0]
            else:
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag,))
                tag_id = cursor.lastrowid
            tag_ids.append(tag_id)
        # Remove all existing tag links for this clip
        cursor.execute("DELETE FROM clip_tags WHERE clip_id = ?", (clip_id,))
        # Add new tag links
        for tag_id in tag_ids:
            cursor.execute("INSERT INTO clip_tags (clip_id, tag_id) VALUES (?, ?)", (clip_id, tag_id))
        conn.commit()
        return JSONResponse({"tags": tags})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.get("/tags")
def get_all_tags(q: str = None):
    """Return a list of all tag names for autocomplete/suggestions. If 'q' is provided, return only tags starting with the prefix (case-insensitive)."""
    conn = None
    try:
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        if q:
            # Use parameterized LIKE for case-insensitive prefix search
            cursor.execute("SELECT name FROM tags WHERE LOWER(name) LIKE ? ORDER BY name ASC", (q.lower() + '%',))
        else:
            cursor.execute("SELECT name FROM tags ORDER BY name ASC")
        tags = [row[0] for row in cursor.fetchall()]
        return JSONResponse({"tags": tags})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.post("/test_tag/{clip_id}")
async def test_tag(clip_id: int, request: Request):
    data = await request.json()
    print("[DEBUG] /test_tag received:", data)
    return {"received": data}

# TODO: Add API endpoints for clips, tagging, starring, etc.
# TODO: Add video playback route 