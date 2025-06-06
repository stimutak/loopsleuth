"""
LoopSleuth Web Frontend (FastAPI)

- Serves the main grid view of clips (with thumbnails)
- Will support video playback, tagging, starring, and export
- Uses Jinja2 templates and static files
"""
from fastapi import FastAPI, Request, HTTPException, Form, Body, status, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys
sys.path.append(str((Path(__file__).parent.parent.parent).resolve()))  # Ensure src/ is importable
from loopsleuth.db import get_db_connection, get_default_db_path
from urllib.parse import unquote
from loopsleuth.scanner import ingest_directory
import mimetypes  # <-- Add this import
from pydantic import BaseModel
from typing import List, Dict, Optional
import tempfile
import os
import shutil
import platform
import subprocess
import json
from datetime import datetime, timedelta
import re
import io

def get_db_path_from_request(request: Request) -> Path:
    """
    Returns the database path for this request, using the 'db' query parameter if present,
    otherwise falling back to LOOPSLEUTH_DB_PATH or the default.
    """
    db_param = request.query_params.get('db') if hasattr(request, 'query_params') else None
    if db_param:
        return Path(db_param)
    return Path(os.environ.get("LOOPSLEUTH_DB_PATH", "loopsleuth.db"))

# --- App setup ---
# Use the main production database by default
app = FastAPI(title="LoopSleuth Web")

# Mount static files (for thumbnails, CSS, JS, etc.)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# --- Custom Jinja2 filter for file size formatting ---
def filesizeformat(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return "?"
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.1f} {unit}" if unit != "bytes" else f"{value} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"

templates.env.filters["filesizeformat"] = filesizeformat

THUMB_DIR = Path(".loopsleuth_data/thumbnails")
STATIC_DIR = Path(__file__).parent / "static" # Define static dir for placeholder check

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
def grid(request: Request):
    """
    Main grid view: shows all clips with thumbnails and info. Now paginated.
    Supports filtering by playlist_id (if provided as a query param).
    """
    db_path = get_db_path_from_request(request)
    default_scan_folder = "E:/Downloads"
    sort = request.query_params.get("sort", "filename")
    order = request.query_params.get("order", "asc")
    starred_first = request.query_params.get("starred_first", "0") == "1"
    playlist_id = request.query_params.get("playlist_id")
    try:
        page = int(request.query_params.get("page", 1))
        if page < 1:
            page = 1
    except Exception:
        page = 1
    try:
        per_page = int(request.query_params.get("per_page", 100))
        if per_page < 1:
            per_page = 100
    except Exception:
        per_page = 100
    offset = (page - 1) * per_page
    if starred_first:
        order_by = f"starred DESC, {sort} {order.upper()}"
    else:
        order_by = f"{sort} {order.upper()}"
    conn = None
    clips = []
    total_clips = 0
    has_duplicates = False
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        # Check for flagged duplicates
        cursor.execute("SELECT 1 FROM clips WHERE needs_review = 1 LIMIT 1")
        if cursor.fetchone():
            has_duplicates = True
        # Get the latest scan_id
        cursor.execute("SELECT id FROM scans ORDER BY scanned_at DESC LIMIT 1")
        row = cursor.fetchone()
        latest_scan_id = row[0] if row else None
        if latest_scan_id is not None:
            if playlist_id:
                # Filter by playlist membership
                cursor.execute("""
                    SELECT COUNT(*) FROM playlist_clips pc
                    JOIN clips c ON pc.clip_id = c.id
                    WHERE pc.playlist_id = ? AND c.scan_id = ?
                """, (playlist_id, latest_scan_id))
                total_clips = cursor.fetchone()[0]
                cursor.execute(f"""
                    SELECT c.id, c.filename, c.path, c.duration, c.thumbnail_path, c.starred, c.size, c.modified_at
                    FROM playlist_clips pc
                    JOIN clips c ON pc.clip_id = c.id
                    WHERE pc.playlist_id = ? AND c.scan_id = ?
                    ORDER BY pc.position ASC, c.id ASC
                    LIMIT ? OFFSET ?
                """, (playlist_id, latest_scan_id, per_page, offset))
            else:
                cursor.execute("SELECT COUNT(*) FROM clips WHERE scan_id = ?", (latest_scan_id,))
                total_clips = cursor.fetchone()[0]
                cursor.execute(f"""
                    SELECT id, filename, path, duration, thumbnail_path, starred, size, modified_at
                    FROM clips
                    WHERE scan_id = ?
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                """, (latest_scan_id, per_page, offset))
        else:
            total_clips = 0
            cursor.execute("SELECT id, filename, path, duration, thumbnail_path, starred, size, modified_at FROM clips WHERE 0")
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
            # --- Fetch playlists for this clip ---
            cursor.execute("""
                SELECT p.id, p.name FROM playlist_clips pc
                JOIN playlists p ON pc.playlist_id = p.id
                WHERE pc.clip_id = ?
                ORDER BY p.name ASC
            """, (clip['id'],))
            clip['playlists'] = [dict(id=r[0], name=r[1]) for r in cursor.fetchall()]
            clips.append(clip)
    except Exception as e:
        print(f"[Error] Could not load clips: {e}")
    finally:
        if conn:
            conn.close()
    return templates.TemplateResponse(
        "grid.html", {
            "request": request,
            "clips": clips,
            "default_scan_folder": default_scan_folder,
            "sort": sort,
            "order": order,
            "starred_first": starred_first,
            "page": page,
            "per_page": per_page,
            "total_clips": total_clips,
            "has_duplicates": has_duplicates
        }
    )

@app.get("/clip/{clip_id}", response_class=HTMLResponse)
def clip_detail(request: Request, clip_id: int):
    """
    Detail page for a single clip: video playback and metadata.
    """
    db_path = get_db_path_from_request(request)
    conn = None
    clip = None
    video_mime = "video/mp4"  # Default
    all_playlists = []
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, path, thumbnail_path, starred, width, height, size, codec_name
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
            # Fetch all playlists and annotate membership
            cursor.execute("SELECT id, name FROM playlists ORDER BY name ASC")
            playlists = [dict(id=r[0], name=r[1]) for r in cursor.fetchall()]
            # Fetch playlist IDs for this clip
            cursor.execute("SELECT playlist_id FROM playlist_clips WHERE clip_id = ?", (clip['id'],))
            member_ids = set(r[0] for r in cursor.fetchall())
            for pl in playlists:
                pl['is_member'] = pl['id'] in member_ids
            all_playlists = playlists
        else:
            # Return a custom 404 page if the clip is not found
            return templates.TemplateResponse(
                "404.html", {"request": request, "message": f"Clip with ID {clip_id} not found."}, status_code=404
            )
    except Exception as e:
        print(f"[Error] Could not load clip {clip_id}: {e}")
        # Return a user-friendly error page
        return templates.TemplateResponse(
            "error.html", {"request": request, "message": f"An error occurred while loading the clip: {e}"}, status_code=500
        )
    finally:
        if conn:
            conn.close()
    return templates.TemplateResponse(
        "clip_detail.html", {"request": request, "clip": clip, "video_mime": video_mime, "all_playlists": all_playlists}
    )

@app.get("/thumbs/{filename}")
def serve_thumbnail(filename: str):
    # Basic security: prevent path traversal
    if ".." in filename or filename.startswith("/"):
        print(f"[Serve Thumbnail] Invalid filename attempt: {filename}")
        raise HTTPException(status_code=400, detail="Invalid filename.")

    print(f"[Serve Thumbnail] Requested filename: {filename}") # Log requested filename

    if filename == "missing.jpg":
        print(f"[Serve Thumbnail] Explicitly asked for missing.jpg. This is unusual.")
        # Let's try to serve the actual placeholder if this happens, to avoid deeper errors
        # This is a temporary diagnostic measure.
        placeholder_path = STATIC_DIR / "placeholder.png" # Assuming you have this
        if placeholder_path.is_file():
            print(f"[Serve Thumbnail] Serving actual placeholder.png for missing.jpg request: {placeholder_path}")
            return FileResponse(placeholder_path)
        else:
            print(f"[Serve Thumbnail] Actual placeholder.png not found at {placeholder_path} when missing.jpg was requested.")
            raise HTTPException(status_code=404, detail="Fallback placeholder missing.jpg and actual placeholder.png not found.")

    thumb_path = THUMB_DIR / filename
    print(f"[Serve Thumbnail] Attempting to serve: {thumb_path}") # Log full path

    if not thumb_path.is_file():
        print(f"[Serve Thumbnail] File not found at path: {thumb_path}")
        # If an _anim.gif is not found, let's try to serve its static .jpg counterpart
        # This is a more graceful fallback than a generic 404 for the animation
        if filename.endswith("_anim.gif"):
            static_filename = filename.replace("_anim.gif", ".jpg")
            static_thumb_path = THUMB_DIR / static_filename
            print(f"[Serve Thumbnail] Animated GIF {filename} not found, trying static fallback: {static_thumb_path}")
            if static_thumb_path.is_file():
                print(f"[Serve Thumbnail] Serving static fallback {static_filename} for missing animated GIF.")
                return FileResponse(static_thumb_path)
            else:
                print(f"[Serve Thumbnail] Static fallback {static_filename} also not found.")
        # If still not found (or wasn't an anim.gif request), raise 404 for the original request
        raise HTTPException(status_code=404, detail=f"Thumbnail {filename} not found, and no suitable fallback available.")
    
    print(f"[Serve Thumbnail] Serving file: {thumb_path}")
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
def scan_folder(request: Request, folder_path: str = Form(...), force_rescan: bool = Form(False), db_path: Optional[str] = Form(None), db_path_manual: Optional[str] = Form(None), background_tasks: BackgroundTasks = None):
    """
    Scan the given folder for videos and ingest them into the DB.
    Accepts an optional db_path (from dropdown or manual entry). If not provided, auto-generates a DB name based on the folder.
    Validates all inputs and returns clear error messages for any failure.
    """
    lock_path = Path(".loopsleuth_data/scan.lock")
    # --- Validation: scan folder must exist and be a directory ---
    scan_folder_path = Path(folder_path).expanduser().resolve()
    if not scan_folder_path.exists() or not scan_folder_path.is_dir():
        return JSONResponse({"error": f"Scan folder does not exist or is not a directory: {scan_folder_path}"}, status_code=400)
    if not os.access(scan_folder_path, os.R_OK):
        return JSONResponse({"error": f"Scan folder is not readable: {scan_folder_path}"}, status_code=400)

    # --- Database path resolution and validation ---
    db_path_final = None
    forbidden_chars = r'[<>:"/\\|?*]'  # Windows forbidden chars, also avoid slashes
    reserved_names = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
    if db_path_manual and db_path_manual.strip():
        db_path_final = Path(db_path_manual.strip())
    elif db_path and db_path.strip():
        db_path_final = Path(db_path.strip())
    else:
        # Auto-generate DB name from folder name
        safe_name = scan_folder_path.name or "scanned"
        db_path_final = Path(f"{safe_name}.db")
    # Validate DB path: must not be a directory, must not contain forbidden chars, must not be reserved, must end with .db
    db_name = db_path_final.name
    if db_path_final.is_dir():
        return JSONResponse({"error": f"Database path cannot be a directory: {db_path_final}"}, status_code=400)
    if re.search(forbidden_chars, db_name):
        return JSONResponse({"error": f"Database name contains forbidden characters: {db_name}"}, status_code=400)
    if db_name.split(".")[0].upper() in reserved_names:
        return JSONResponse({"error": f"Database name is a reserved system name: {db_name}"}, status_code=400)
    if not db_name.lower().endswith(".db"):
        return JSONResponse({"error": f"Database name must end with .db: {db_name}"}, status_code=400)
    if not db_name or db_name.strip() == "":
        return JSONResponse({"error": "Database name cannot be empty."}, status_code=400)
    # Optionally: check for write permission in the target directory
    db_dir = db_path_final.parent.resolve()
    if not db_dir.exists():
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return JSONResponse({"error": f"Could not create database directory: {db_dir}. Error: {e}"}, status_code=400)
    if not os.access(db_dir, os.W_OK):
        return JSONResponse({"error": f"Database directory is not writable: {db_dir}"}, status_code=400)

    # --- Scan lock: prevent overlapping scans ---
    if lock_path.exists():
        mtime = datetime.fromtimestamp(lock_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            return JSONResponse({"error": "A scan is already in progress."}, status_code=409)
        else:
            # Stale lock, remove it
            lock_path.unlink()
    # Create lock
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(datetime.now()))

    def wrapped_ingest(*args, **kwargs):
        try:
            ingest_directory(*args, **kwargs)
        except Exception as e:
            # Log error and remove lock
            print(f"[Scan Error] {e}")
            if lock_path.exists():
                lock_path.unlink()
        finally:
            if lock_path.exists():
                lock_path.unlink()

    try:
        if background_tasks is not None:
            background_tasks.add_task(
                wrapped_ingest,
                scan_folder_path,
                db_path=db_path_final,
                force_rescan=force_rescan
            )
        else:
            wrapped_ingest(
                scan_folder_path,
                db_path=db_path_final,
                force_rescan=force_rescan
            )
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        if lock_path.exists():
            lock_path.unlink()
        return JSONResponse({"error": f"Scan failed: {e}"}, status_code=500)

@app.post("/star/{clip_id}")
def toggle_star(request: Request, clip_id: int):
    """Toggle the 'starred' flag for a clip and return the new state as JSON."""
    db_path = get_db_path_from_request(request)
    conn = None
    try:
        conn = get_db_connection(db_path)
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
def update_tags(request: Request, clip_id: int, tag_update: TagUpdate = Body(...)):
    """
    Update the tags for a clip. Accepts JSON {"tags": ["tag1", "tag2", ...]}.
    Updates the tags and clip_tags tables. Returns the new tag list as JSON.
    """
    print(f"[DEBUG] Received tag update for clip {clip_id}: {tag_update}")
    tags = [t.strip() for t in tag_update.tags if t.strip()]
    db_path = get_db_path_from_request(request)
    conn = None
    try:
        conn = get_db_connection(db_path)
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
def get_all_tags(request: Request, q: str = None):
    """Return a list of all tag names for autocomplete/suggestions. If 'q' is provided, return only tags starting with the prefix (case-insensitive)."""
    db_path = get_db_path_from_request(request)
    conn = None
    try:
        conn = get_db_connection(db_path)
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
def batch_tag_update(request: Request, batch_update: BatchTagUpdate = Body(...)):
    """
    Batch tag editing endpoint. Accepts JSON with:
      - clip_ids: list of clip IDs
      - add_tags: tags to add (optional)
      - remove_tags: tags to remove (optional)
      - clear: if true, remove all tags from selected clips
    Returns: {clip_id: [updated tags, ...], ...}
    """
    db_path = get_db_path_from_request(request)
    conn = None
    try:
        conn = get_db_connection(db_path)
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
    db_path = get_db_path_from_request(request)
    conn = None
    try:
        conn = get_db_connection(db_path)
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
    db_path = get_db_path_from_request(request)
    conn = None
    results = {}
    try:
        dest = Path(copy_req.dest_folder)
        if not dest.exists() or not dest.is_dir():
            return JSONResponse({"error": f"Destination folder does not exist: {dest}"}, status_code=400)
        conn = get_db_connection(db_path)
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

# --- Playlist Management Models ---
class PlaylistCreateRequest(BaseModel):
    name: str

class PlaylistRenameRequest(BaseModel):
    name: str

class PlaylistClipUpdateRequest(BaseModel):
    clip_ids: List[int]

class PlaylistReorderRequest(BaseModel):
    clip_ids: List[int]  # New order for this playlist

class PlaylistExportFormat(str):
    pass  # For future: enum for 'txt', 'zip', 'tox'

class MultiPlaylistClipUpdateRequest(BaseModel):
    clip_ids: List[int]
    playlist_ids: List[int]

# --- Playlist Endpoints ---
@app.post("/playlists")
async def create_playlist(request: Request):
    """Create a new playlist with a unique name and set its order to the next available value."""
    db_path = get_db_path_from_request(request)
    data = await request.json()
    name = data.get("name")
    if not name or not name.strip():
        return JSONResponse({"error": "Playlist name required"}, status_code=400)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    # Determine next order value
    cursor.execute("SELECT MAX(\"order\") FROM playlists")
    row = cursor.fetchone()
    next_order = (row[0] + 1) if row and row[0] is not None else 0
    cursor.execute("INSERT INTO playlists (name, \"order\") VALUES (?, ?)", (name.strip(), next_order))
    conn.commit()
    playlist_id = cursor.lastrowid
    cursor.execute("SELECT id, name, created_at, \"order\" FROM playlists WHERE id = ?", (playlist_id,))
    playlist = cursor.fetchone()
    conn.close()
    return {"id": playlist[0], "name": playlist[1], "created_at": playlist[2], "order": playlist[3]}

@app.patch("/playlists/{playlist_id}")
def rename_playlist(playlist_id: int, req: PlaylistRenameRequest):
    """Rename a playlist."""
    conn = None
    try:
        conn = get_db_connection(get_default_db_path())
        cursor = conn.cursor()
        cursor.execute("UPDATE playlists SET name = ? WHERE id = ?", (req.name, playlist_id))
        if cursor.rowcount == 0:
            return JSONResponse({"error": "Playlist not found"}, status_code=404)
        conn.commit()
        return {"id": playlist_id, "name": req.name}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: int):
    """Delete a playlist and its associations."""
    conn = None
    try:
        conn = get_db_connection(get_default_db_path())
        cursor = conn.cursor()
        cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        if cursor.rowcount == 0:
            return JSONResponse({"error": "Playlist not found"}, status_code=404)
        conn.commit()
        return {"id": playlist_id, "deleted": True}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.get("/playlists")
def list_playlists(request: Request):
    """List all playlists (id, name, created_at, order) for the selected DB, ordered by 'order' if present."""
    db_path = get_db_path_from_request(request)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    # Try to order by 'order', fallback to created_at
    try:
        cursor.execute("SELECT id, name, created_at, \"order\" FROM playlists ORDER BY \"order\" ASC, created_at DESC")
    except Exception:
        cursor.execute("SELECT id, name, created_at FROM playlists ORDER BY created_at DESC")
    playlists = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"playlists": playlists}

@app.get("/playlists/{playlist_id}")
def get_playlist(request: Request, playlist_id: int):
    """Get playlist details: id, name, created_at, and ordered clips for the selected DB."""
    db_path = get_db_path_from_request(request)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, created_at FROM playlists WHERE id = ?", (playlist_id,))
    playlist = cursor.fetchone()
    if not playlist:
        return JSONResponse({"error": "Playlist not found"}, status_code=404)
    cursor.execute("""
        SELECT c.id, c.filename, c.thumbnail_path, c.duration, pc.position
        FROM playlist_clips pc
        JOIN clips c ON pc.clip_id = c.id
        WHERE pc.playlist_id = ?
        ORDER BY pc.position ASC
    """, (playlist_id,))
    clips = [dict(row) for row in cursor.fetchall()]
    return {"id": playlist[0], "name": playlist[1], "created_at": playlist[2], "clips": clips}

@app.post("/playlists/clips")
def add_clips_to_multiple_playlists(req: MultiPlaylistClipUpdateRequest):
    """Add one or more clips to one or more playlists (multi-playlist support)."""
    conn = None
    summary = {}
    try:
        conn = get_db_connection(get_default_db_path())
        cursor = conn.cursor()
        for playlist_id in req.playlist_ids:
            # Get current max position for this playlist
            cursor.execute("SELECT MAX(position) FROM playlist_clips WHERE playlist_id = ?", (playlist_id,))
            row = cursor.fetchone()
            start_pos = (row[0] + 1) if row and row[0] is not None else 0
            added = []
            for i, clip_id in enumerate(req.clip_ids):
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO playlist_clips (playlist_id, clip_id, position)
                    VALUES (?, ?, ?)
                    """,
                    (playlist_id, clip_id, start_pos + i)
                )
                if cursor.rowcount > 0:
                    added.append(clip_id)
            summary[playlist_id] = added
        conn.commit()
        return {"added": summary}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.post("/playlists/{playlist_id}/clips/remove")
def remove_clips_from_playlist(playlist_id: int, req: PlaylistClipUpdateRequest):
    """Remove one or more clips from a playlist (POST for batch remove)."""
    conn = None
    try:
        conn = get_db_connection(get_default_db_path())
        cursor = conn.cursor()
        for clip_id in req.clip_ids:
            cursor.execute("DELETE FROM playlist_clips WHERE playlist_id = ? AND clip_id = ?", (playlist_id, clip_id))
        conn.commit()
        return {"playlist_id": playlist_id, "removed": req.clip_ids}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.patch("/playlists/{playlist_id}/reorder")
def reorder_playlist_clips(playlist_id: int, req: PlaylistReorderRequest):
    """Reorder clips in a playlist. Accepts new clip_id order."""
    conn = None
    try:
        conn = get_db_connection(get_default_db_path())
        cursor = conn.cursor()
        for pos, clip_id in enumerate(req.clip_ids):
            cursor.execute("""
                UPDATE playlist_clips SET position = ?
                WHERE playlist_id = ? AND clip_id = ?
            """, (pos, playlist_id, clip_id))
        conn.commit()
        return {"playlist_id": playlist_id, "order": req.clip_ids}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.get("/playlists/{playlist_id}/export")
def export_playlist(playlist_id: int, format: str = "txt"):
    """Export playlist in the requested format (txt, zip, tox)."""
    if format not in ("txt", "zip", "tox"):
        return JSONResponse({"error": f"Unsupported export format: {format}"}, status_code=400)
    conn = None
    try:
        conn = get_db_connection(get_default_db_path())
        cursor = conn.cursor()
        # Get playlist name (for filename)
        cursor.execute("SELECT name FROM playlists WHERE id = ?", (playlist_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({"error": "Playlist not found"}, status_code=404)
        playlist_name = row[0]
        # Get all clip paths in order
        cursor.execute("""
            SELECT c.path FROM playlist_clips pc
            JOIN clips c ON pc.clip_id = c.id
            WHERE pc.playlist_id = ?
            ORDER BY pc.position ASC
        """, (playlist_id,))
        paths = [r[0] for r in cursor.fetchall()]
        if format == "txt":
            if not paths:
                return JSONResponse({"error": "Playlist is empty."}, status_code=400)
            # Build text content
            content = "\n".join(paths) + "\n"
            filename = f"playlist_{playlist_name}.txt" # Use playlist_name for filename
            # Use StreamingResponse for download
            return StreamingResponse(
                io.BytesIO(content.encode("utf-8")),
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        elif format == "zip":
            # TODO: Implement zip export
            return JSONResponse({"error": "ZIP export not yet implemented."}, status_code=501)
        elif format == "tox":
            # TODO: Implement TouchDesigner .tox export
            return JSONResponse({"error": ".tox export not yet implemented."}, status_code=501)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.post("/open_in_system/{clip_id}")
def open_in_system(clip_id: int):
    """
    Open the folder containing the video file in the system's file explorer, selecting the file if possible.
    """
    conn = None
    try:
        conn = get_db_connection(get_default_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT path FROM clips WHERE id = ?", (clip_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({"detail": "Clip not found"}, status_code=status.HTTP_404_NOT_FOUND)
        file_path = Path(row[0])
        if not file_path.exists():
            return JSONResponse({"detail": "File not found"}, status_code=status.HTTP_404_NOT_FOUND)
        folder = file_path.parent
        system = platform.system()
        try:
            if system == "Windows":
                # Select the file in Explorer
                subprocess.Popen(["explorer", "/select,", str(file_path)])
            elif system == "Darwin":
                # Reveal the file in Finder
                subprocess.Popen(["open", "-R", str(file_path)])
            else:
                # Linux: just open the folder
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as e:
            return JSONResponse({"detail": f"Failed to open folder: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return JSONResponse({"detail": "Opened in system file explorer"})
    except Exception as e:
        return JSONResponse({"detail": f"Error: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if conn:
            conn.close()

@app.get("/scan_progress")
def scan_progress():
    """
    Returns the current scan/ingest progress for the frontend progress bar.
    Reads .loopsleuth_data/scan_progress.json. If missing, returns status: idle.
    """
    progress_path = Path(".loopsleuth_data/scan_progress.json")
    if not progress_path.exists():
        return JSONResponse({"status": "idle"})
    try:
        with progress_path.open("r") as f:
            data = json.load(f)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

@app.get("/api/clips")
def api_clips(request: Request, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    """
    Returns a window of clips for virtualized/infinite scrolling.
    Uses the selected DB from the request for multi-library support.
    Supports filtering by playlist_id (if provided as a query param).
    Now supports sorting by sort/order/starred_first params (matches main grid route).
    """
    db_path = get_db_path_from_request(request)
    playlist_id = request.query_params.get("playlist_id")
    # --- Sorting params ---
    sort = request.query_params.get("sort", "filename")
    order = request.query_params.get("order", "asc")
    starred_first = request.query_params.get("starred_first", "0") == "1"
    valid_sorts = {"filename", "modified_at", "size", "duration", "starred"}
    valid_orders = {"asc", "desc"}
    if sort not in valid_sorts:
        sort = "filename"
    if order not in valid_orders:
        order = "asc"
    if starred_first:
        order_by = f"starred DESC, {sort} {order.upper()}"
    else:
        order_by = f"{sort} {order.upper()}"
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if playlist_id:
        # Filter by playlist membership, keep playlist order
        cursor.execute("""
            SELECT COUNT(*) FROM playlist_clips pc
            JOIN clips c ON pc.clip_id = c.id
            WHERE pc.playlist_id = ?
        """, (playlist_id,))
        total = cursor.fetchone()[0]
        cursor.execute("""
            SELECT c.id, c.filename, c.path, c.thumbnail_path, c.duration, c.size, c.starred, c.modified_at
            FROM playlist_clips pc
            JOIN clips c ON pc.clip_id = c.id
            WHERE pc.playlist_id = ?
            ORDER BY pc.position ASC, c.id ASC
            LIMIT ? OFFSET ?
        """, (playlist_id, limit, offset))
    else:
        cursor.execute("SELECT COUNT(*) FROM clips")
        total = cursor.fetchone()[0]
        cursor.execute(f"""
            SELECT id, filename, path, thumbnail_path, duration, size, starred, modified_at
            FROM clips
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """, (limit, offset))
    clips = []
    for row in cursor.fetchall():
        clip_id = row[0]
        # Fetch playlist memberships for this clip
        cursor.execute("""
            SELECT p.id, p.name FROM playlist_clips pc
            JOIN playlists p ON pc.playlist_id = p.id
            WHERE pc.clip_id = ?
            ORDER BY p.name ASC
        """, (clip_id,))
        playlists = [ {"id": r[0], "name": r[1]} for r in cursor.fetchall() ]
        # Fetch tags for this clip
        cursor.execute("""
            SELECT t.name FROM tags t
            JOIN clip_tags ct ON t.id = ct.tag_id
            WHERE ct.clip_id = ?
            ORDER BY t.name ASC
        """, (clip_id,))
        tags = [r[0] for r in cursor.fetchall()]
        clip = {
            "id": row[0],
            "filename": row[1],
            "path": row[2],
            "thumb_url": f"/thumbs/{os.path.basename(row[3])}" if row[3] else None,
            "duration": row[4],
            "size": row[5],
            "starred": row[6],
            "modified_at": row[7],
            "playlists": playlists,
            "tags": tags,
        }
        clips.append(clip)
    # Debug: print the first 2 clips for verification
    print("[api_clips] Returning sample clips:", clips[:2])
    conn.close()
    return JSONResponse({"clips": clips, "total": total})

@app.get("/api/duplicates")
def api_duplicates(request: Request):
    """
    Returns all clips flagged for duplicate review (needs_review=1), grouped by canonical (duplicate_of).
    Uses the selected DB from the request for multi-library support.
    """
    try:
        db_path = get_db_path_from_request(request)
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        # Find all clips needing review
        cursor.execute("SELECT * FROM clips WHERE needs_review = 1")
        dup_rows = cursor.fetchall()
        # Group by duplicate_of (canonical id)
        groups = {}
        for row in dup_rows:
            canonical_id = row['duplicate_of'] if isinstance(row, dict) or hasattr(row, '__getitem__') else None
            if canonical_id is None:
                print(f"[api_duplicates] Warning: needs_review=1 but duplicate_of is NULL for clip id {row['id'] if 'id' in row.keys() else '?'}")
                continue  # Defensive: should always be set if needs_review=1
            if canonical_id not in groups:
                try:
                    canonical_size = row['size']
                except (KeyError, IndexError):
                    canonical_size = None
                groups[canonical_id] = {
                    'canonical': {
                        'id': row['id'],
                        'filename': row['filename'],
                        'path': row['path'],
                        'phash': row['phash'],
                        'thumbnail_path': row['thumbnail_path'],
                        'duration': row['duration'],
                        'size': canonical_size,
                    },
                    'duplicates': []
                }
            try:
                row_size = row['size']
            except (KeyError, IndexError):
                row_size = None
            groups[canonical_id]['duplicates'].append({
                'id': row['id'],
                'filename': row['filename'],
                'path': row['path'],
                'phash': row['phash'],
                'thumbnail_path': row['thumbnail_path'],
                'duration': row['duration'],
                'size': row_size,
            })
        # Return as list of groups
        result = list(groups.values())
        conn.close()
        return {"duplicate_groups": result}
    except Exception as e:
        import traceback
        print("[api_duplicates] Exception:", e)
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/duplicates", response_class=HTMLResponse)
def duplicates_review(request: Request):
    """
    Render the batch duplicate review UI. Fetches duplicate groups via JS from /api/duplicates.
    """
    return templates.TemplateResponse("duplicates.html", {"request": request})

@app.post("/api/duplicate_action")
async def duplicate_action(request: Request):
    """
    Handle actions for duplicate review: keep, delete, ignore.
    Expects JSON: {"dup_id": int, "action": "keep"|"delete"|"ignore", "canonical_id": int}
    """
    try:
        data = await request.json()
    except Exception:
        data = None
    if not data:
        return JSONResponse({"error": "Missing or invalid JSON."}, status_code=400)
    dup_id = data.get("dup_id")
    action = data.get("action")
    canonical_id = data.get("canonical_id")
    if not dup_id or not action:
        return JSONResponse({"error": "Missing dup_id or action."}, status_code=400)
    conn = get_db_connection(get_default_db_path())
    cursor = conn.cursor()
    try:
        if action == "keep":
            # Clear needs_review and duplicate_of
            cursor.execute("UPDATE clips SET needs_review = 0, duplicate_of = NULL WHERE id = ?", (dup_id,))
            conn.commit()
            return {"status": "kept", "dup_id": dup_id}
        elif action == "delete":
            # Delete tags, clip_tags, and the clip itself
            cursor.execute("DELETE FROM clip_tags WHERE clip_id = ?", (dup_id,))
            cursor.execute("DELETE FROM playlist_clips WHERE clip_id = ?", (dup_id,))
            cursor.execute("DELETE FROM clips WHERE id = ?", (dup_id,))
            conn.commit()
            return {"status": "deleted", "dup_id": dup_id}
        elif action == "ignore":
            # Clear needs_review but leave duplicate_of
            cursor.execute("UPDATE clips SET needs_review = 0 WHERE id = ?", (dup_id,))
            conn.commit()
            return {"status": "ignored", "dup_id": dup_id}
        elif action == "merge":
            # --- Merge tags ---
            # Get all tag_ids for canonical and duplicate
            cursor.execute("SELECT tag_id FROM clip_tags WHERE clip_id = ?", (canonical_id,))
            canonical_tags = set(row[0] for row in cursor.fetchall())
            cursor.execute("SELECT tag_id FROM clip_tags WHERE clip_id = ?", (dup_id,))
            dup_tags = set(row[0] for row in cursor.fetchall())
            tags_to_add = dup_tags - canonical_tags
            for tag_id in tags_to_add:
                cursor.execute("INSERT OR IGNORE INTO clip_tags (clip_id, tag_id) VALUES (?, ?)", (canonical_id, tag_id))
            # --- Merge playlist memberships ---
            cursor.execute("SELECT playlist_id FROM playlist_clips WHERE clip_id = ?", (canonical_id,))
            canonical_playlists = set(row[0] for row in cursor.fetchall())
            cursor.execute("SELECT playlist_id FROM playlist_clips WHERE clip_id = ?", (dup_id,))
            dup_playlists = set(row[0] for row in cursor.fetchall())
            playlists_to_add = dup_playlists - canonical_playlists
            for playlist_id in playlists_to_add:
                # Add to end of playlist (max position + 1)
                cursor.execute("SELECT MAX(position) FROM playlist_clips WHERE playlist_id = ?", (playlist_id,))
                row = cursor.fetchone()
                pos = (row[0] + 1) if row and row[0] is not None else 0
                cursor.execute("INSERT OR IGNORE INTO playlist_clips (playlist_id, clip_id, position) VALUES (?, ?, ?)", (playlist_id, canonical_id, pos))
            # --- Delete duplicate ---
            cursor.execute("DELETE FROM clip_tags WHERE clip_id = ?", (dup_id,))
            cursor.execute("DELETE FROM playlist_clips WHERE clip_id = ?", (dup_id,))
            cursor.execute("DELETE FROM clips WHERE id = ?", (dup_id,))
            conn.commit()
            return {"status": "merged", "dup_id": dup_id, "canonical_id": canonical_id, "tags_merged": list(tags_to_add), "playlists_merged": list(playlists_to_add)}
        else:
            return JSONResponse({"error": f"Unknown action: {action}"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()

@app.get("/api/tag_suggestions")
def api_tag_suggestions(request: Request, q: str = None):
    """Return a list of tag suggestions for autocomplete. If 'q' is provided, return only tags starting with the prefix (case-insensitive)."""
    db_path = get_db_path_from_request(request)
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        if q:
            # Use parameterized LIKE for case-insensitive prefix search
            cursor.execute("SELECT name FROM tags WHERE LOWER(name) LIKE ? ORDER BY name ASC", (q.lower() + '%',))
        else:
            cursor.execute("SELECT name FROM tags ORDER BY name ASC")
        tags = [row[0] for row in cursor.fetchall()]
        return JSONResponse({"suggestions": tags})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()

# TODO: Add API endpoints for clips, tagging, starring, etc.
# TODO: Add video playback route 