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
from typing import List, Dict, Optional
import tempfile
import os
import shutil

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
        
        # --- Remove orphaned tags (tags not referenced by any clip) ---
        cursor.execute("""
            DELETE FROM tags
            WHERE id NOT IN (SELECT tag_id FROM clip_tags)
        """)
        # ------------------------------------------------------------
        
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

class BatchTagUpdate(BaseModel):
    clip_ids: List[int]
    add_tags: Optional[List[str]] = None
    remove_tags: Optional[List[str]] = None
    clear: Optional[bool] = False

@app.post("/batch_tag")
def batch_tag_update(batch_update: BatchTagUpdate = Body(...)):
    """
    Batch tag editing endpoint. Accepts JSON with:
      - clip_ids: list of clip IDs
      - add_tags: tags to add (optional)
      - remove_tags: tags to remove (optional)
      - clear: if true, remove all tags from selected clips
    Returns: {clip_id: [updated tags, ...], ...}
    """
    conn = None
    try:
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        add_tags = [t.strip() for t in (batch_update.add_tags or []) if t.strip()]
        remove_tags = [t.strip() for t in (batch_update.remove_tags or []) if t.strip()]
        result: Dict[int, List[str]] = {}
        for clip_id in batch_update.clip_ids:
            # Fetch current tag IDs and names for this clip
            cursor.execute("""
                SELECT t.id, t.name FROM tags t
                JOIN clip_tags ct ON t.id = ct.tag_id
                WHERE ct.clip_id = ?
            """, (clip_id,))
            tag_rows = cursor.fetchall()
            current_tag_ids = {row[0]: row[1] for row in tag_rows}
            current_tag_names = set(current_tag_ids.values())
            if batch_update.clear:
                # Remove all tags for this clip
                cursor.execute("DELETE FROM clip_tags WHERE clip_id = ?", (clip_id,))
                result[clip_id] = []
                continue
            # Remove tags if specified
            if remove_tags:
                remove_tag_ids = []
                for tag in remove_tags:
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                    row = cursor.fetchone()
                    if row:
                        remove_tag_ids.append(row[0])
                for tag_id in remove_tag_ids:
                    cursor.execute("DELETE FROM clip_tags WHERE clip_id = ? AND tag_id = ?", (clip_id, tag_id))
            # Add tags if specified
            if add_tags:
                for tag in add_tags:
                    # Insert tag if not present
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                    row = cursor.fetchone()
                    if row:
                        tag_id = row[0]
                    else:
                        cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag,))
                        tag_id = cursor.lastrowid
                    # Add link if not already present
                    cursor.execute("SELECT 1 FROM clip_tags WHERE clip_id = ? AND tag_id = ?", (clip_id, tag_id))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO clip_tags (clip_id, tag_id) VALUES (?, ?)", (clip_id, tag_id))
            # Fetch updated tags for this clip
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN clip_tags ct ON t.id = ct.tag_id
                WHERE ct.clip_id = ?
                ORDER BY t.name ASC
            """, (clip_id,))
            updated_tags = [row[0] for row in cursor.fetchall()]
            result[clip_id] = updated_tags
        # Remove orphaned tags (tags not referenced by any clip)
        cursor.execute("""
            DELETE FROM tags
            WHERE id NOT IN (SELECT tag_id FROM clip_tags)
        """)
        conn.commit()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

class ExportSelectedRequest(BaseModel):
    clip_ids: List[int]

@app.post("/export_selected")
def export_selected(export_req: ExportSelectedRequest = Body(...)):
    """
    Export the absolute paths of selected clips as a downloadable keepers.txt file.
    Accepts JSON: {"clip_ids": [1,2,3,...]}
    Returns: keepers.txt (text/plain, one absolute path per line)
    """
    conn = None
    try:
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        paths = []
        for clip_id in export_req.clip_ids:
            cursor.execute("SELECT path FROM clips WHERE id = ?", (clip_id,))
            row = cursor.fetchone()
            if row and row[0]:
                paths.append(str(row[0]))
        if not paths:
            return JSONResponse({"error": "No valid paths for selected clips."}, status_code=400)
        # Write to a temporary file
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as tmp:
            for p in paths:
                tmp.write(p + "\n")
            tmp_path = tmp.name
        # Return as a downloadable file
        return FileResponse(tmp_path, filename="keepers.txt", media_type="text/plain")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()
        # Clean up temp file after response (handled by OS, but can add background task if needed)

class CopySelectedRequest(BaseModel):
    clip_ids: List[int]
    dest_folder: str

@app.post("/copy_selected")
def copy_selected(copy_req: CopySelectedRequest = Body(...)):
    """
    Copy the selected clips to the specified destination folder.
    Accepts JSON: {"clip_ids": [1,2,3,...], "dest_folder": "/path/to/folder"}
    Returns: {"results": {filename: "ok"|"error: ...", ...}}
    """
    conn = None
    results = {}
    try:
        dest = Path(copy_req.dest_folder)
        if not dest.exists() or not dest.is_dir():
            return JSONResponse({"error": f"Destination folder does not exist: {dest}"}, status_code=400)
        conn = get_db_connection(DEFAULT_DB_PATH)
        cursor = conn.cursor()
        for clip_id in copy_req.clip_ids:
            cursor.execute("SELECT filename, path FROM clips WHERE id = ?", (clip_id,))
            row = cursor.fetchone()
            if not row or not row[1]:
                results[str(clip_id)] = "error: missing path"
                continue
            src = Path(row[1])
            if not src.exists():
                results[row[0]] = f"error: source not found ({src})"
                continue
            try:
                shutil.copy2(src, dest / src.name)
                results[row[0]] = "ok"
            except Exception as e:
                results[row[0]] = f"error: {e}"
        return JSONResponse({"results": results})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

# TODO: Add API endpoints for clips, tagging, starring, etc.
# TODO: Add video playback route 