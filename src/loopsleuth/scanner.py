"""Directory scanning and ingestion into the database."""

import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterable, List, Set, Optional
import json

# Add tqdm for progress bar if available
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Adjust import path assuming this script might be run directly
# or as part of the package
SCRIPTS_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPTS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from loopsleuth.db import get_db_connection, get_default_db_path
from loopsleuth.metadata import get_video_duration, FFprobeError, get_video_metadata
from loopsleuth.thumbnailer import generate_thumbnail, ThumbnailError

# Common video file extensions
# TODO: Make this configurable
DEFAULT_VIDEO_EXTENSIONS: Set[str] = {
    ".mov",
    ".mp4",
    ".avi",
    ".mkv",
    # Add more as needed, e.g., .mpeg, .mpg, .wmv
    # DXV is often in a .mov container, so it should be covered.
}

def _scan_directory_internal(
    start_path: Path,
    extensions: Set[str] = DEFAULT_VIDEO_EXTENSIONS,
) -> Iterable[Path]:
    """Internal helper to yield video file paths."""
    # TODO: Add tqdm progress bar here for large directories
    for item in start_path.rglob("*"): # Recursively glob for all files
        if item.is_file() and item.suffix.lower() in extensions:
            yield item.resolve() # Yield absolute path

def ingest_directory(
    start_path: Path,
    db_path: Path = get_default_db_path(),
    extensions: Set[str] = DEFAULT_VIDEO_EXTENSIONS,
    force_rescan: bool = False,
) -> None:
    """
    Scans a directory for video files, extracts metadata (duration),
    and saves the information to the database.
    Now writes progress to .loopsleuth_data/scan_progress.json for UI polling.

    Args:
        start_path: The directory path to start scanning from.
        db_path: Path to the SQLite database file.
        extensions: A set of lowercase file extensions to look for.
        force_rescan: If True, update duration and regenerate thumbnail for all files, even if they already exist.
    """
    if not start_path.is_dir():
        print(f"Error: Invalid start path '{start_path}' is not a directory.", file=sys.stderr)
        return

    progress_path = Path(".loopsleuth_data/scan_progress.json")
    try:
        progress_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    print(f"Scanning {start_path} for video files ({', '.join(extensions)})...")

    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        # --- Insert new scan row ---
        cursor.execute("INSERT INTO scans (folder_path) VALUES (?)", (str(start_path),))
        scan_id = cursor.lastrowid

        processed_count = 0
        skipped_count = 0
        error_count = 0

        # Collect all video files first for progress bar
        video_files = list(_scan_directory_internal(start_path, extensions))
        total_files = len(video_files)
        # Write initial progress
        with progress_path.open("w") as f:
            json.dump({"total": total_files, "done": 0, "status": "scanning"}, f)

        iterator = tqdm(video_files, desc="Scanning", unit="file") if tqdm else video_files

        for idx, video_path in enumerate(iterator):
            try:
                path_str = str(video_path)
                filename = video_path.name

                # Check if path already exists
                cursor.execute("SELECT id FROM clips WHERE path = ?", (path_str,))
                existing = cursor.fetchone()
                if existing and not force_rescan:
                    skipped_count += 1
                    # Update progress for skipped
                    with progress_path.open("w") as f:
                        json.dump({"total": total_files, "done": idx + 1, "status": "scanning"}, f)
                    continue

                print(f"Processing: {filename}")
                # --- Extract metadata ---
                try:
                    meta = get_video_metadata(video_path)
                except FFprobeError as e:
                    print(f"  Warning: Could not get metadata for {filename}. Error: {e}", file=sys.stderr)
                    error_count += 1
                    # Update progress for error
                    with progress_path.open("w") as f:
                        json.dump({"total": total_files, "done": idx + 1, "status": "scanning"}, f)
                    continue
                except FileNotFoundError as e:
                    print(f"  Error: {e}", file=sys.stderr)
                    print("  Aborting scan due to missing ffprobe.", file=sys.stderr)
                    error_count += 1
                    # Set error status and exit
                    with progress_path.open("w") as f:
                        json.dump({"total": total_files, "done": idx, "status": "error", "error": str(e)}, f)
                    break
                duration = meta.get("duration")
                width = meta.get("width")
                height = meta.get("height")
                size = meta.get("size")
                codec_name = meta.get("codec_name")
                print(f"  Metadata: duration={duration}, width={width}, height={height}, size={size}, codec={codec_name}")

                if existing and force_rescan:
                    clip_id = existing[0]
                    cursor.execute(
                        "UPDATE clips SET duration = ?, width = ?, height = ?, size = ?, codec_name = ?, scan_id = ? WHERE id = ?",
                        (duration, width, height, size, codec_name, scan_id, clip_id)
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO clips (path, filename, duration, width, height, size, codec_name, modified_at, scan_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                        """,
                        (path_str, filename, duration, width, height, size, codec_name, scan_id)
                    )
                    clip_id = cursor.lastrowid
                    processed_count += 1

                # --- Generate thumbnail immediately if possible ---
                if duration and duration > 0:
                    try:
                        from loopsleuth.thumbnailer import _get_thumbnail_dir
                        thumb_path = generate_thumbnail(
                            video_path=video_path,
                            duration=duration,
                            clip_id=clip_id,
                            output_dir=_get_thumbnail_dir()
                        )
                        if thumb_path:
                            try:
                                abs_thumb_path = thumb_path.resolve()
                                abs_project_root = Path.cwd().resolve()
                                relative_thumb_path = str(abs_thumb_path.relative_to(abs_project_root))
                            except ValueError:
                                relative_thumb_path = str(thumb_path.name)
                            cursor.execute(
                                "UPDATE clips SET thumbnail_path = ? WHERE id = ?",
                                (relative_thumb_path, clip_id)
                            )
                    except (ThumbnailError, Exception) as e:
                        print(f"  Error generating thumbnail for {filename}: {e}", file=sys.stderr)

                # Update progress after each file
                with progress_path.open("w") as f:
                    json.dump({"total": total_files, "done": idx + 1, "status": "scanning"}, f)

            except Exception as e:
                # Catch unexpected errors during processing of a single file
                print(f"  Error processing file {video_path}: {e}", file=sys.stderr)
                error_count += 1
                # Update progress for error
                with progress_path.open("w") as f:
                    json.dump({"total": total_files, "done": idx + 1, "status": "scanning"}, f)
                continue # Skip to the next file

        # --- Delete all clips not from this scan (true replace behavior) ---
        cursor.execute("DELETE FROM clips WHERE scan_id != ? OR scan_id IS NULL", (scan_id,))

        conn.commit()
        print("\nScan complete.")
        print(f"  Processed: {processed_count}")
        print(f"  Skipped (already exist): {skipped_count}")
        print(f"  Errors: {error_count}")

        # Set status to done
        with progress_path.open("w") as f:
            json.dump({"total": total_files, "done": total_files, "status": "done"}, f)

    except sqlite3.Error as e:
        print(f"Database error during scan: {e}", file=sys.stderr)
        # Set error status
        with progress_path.open("w") as f:
            json.dump({"total": 0, "done": 0, "status": "error", "error": str(e)}, f)
    except Exception as e:
        print(f"An unexpected error occurred during scan: {e}", file=sys.stderr)
        # Set error status
        with progress_path.open("w") as f:
            json.dump({"total": 0, "done": 0, "status": "error", "error": str(e)}, f)
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

# --- Example usage section --- #

def _setup_test_environment(test_dir: Path):
    """Creates dummy files and directories for testing."""
    test_dir.mkdir(exist_ok=True)
    (test_dir / "video1.mov").touch()
    (test_dir / "video2.mp4").touch()
    (test_dir / "subfolder").mkdir(exist_ok=True)
    (test_dir / "subfolder" / "video3.mkv").touch()
    (test_dir / "image.jpg").touch()
    (test_dir / "document.txt").touch()
    print(f"Created test environment in: {test_dir}")

def _cleanup_test_environment(test_dir: Path, db_path: Path):
    """Removes dummy files, directories, and the test database."""
    print("\nCleaning up test environment...")
    files_to_remove = [
        test_dir / "video1.mov",
        test_dir / "video2.mp4",
        test_dir / "subfolder" / "video3.mkv",
        test_dir / "image.jpg",
        test_dir / "document.txt"
    ]
    for f in files_to_remove:
        try:
            os.remove(f)
        except OSError:
            pass # Ignore if file doesn't exist

    dirs_to_remove = [test_dir / "subfolder", test_dir]
    for d in dirs_to_remove:
        try:
            os.rmdir(d)
        except OSError:
            pass # Ignore if dir doesn't exist or isn't empty

    try:
        if db_path.exists():
            os.remove(db_path)
            print(f"Removed test database: {db_path}")
    except OSError as e:
        print(f"Error removing test database {db_path}: {e}", file=sys.stderr)

    print("Cleanup complete.")

if __name__ == '__main__':
    test_dir = Path("./temp_scan_test")
    test_db = Path("./temp_test_loopsleuth.db")

    # Ensure clean state before test
    _cleanup_test_environment(test_dir, test_db)

    _setup_test_environment(test_dir)

    print("\nStarting ingestion process...")
    # Note: This will likely fail to get duration unless ffprobe is installed
    # and accessible. The errors will be printed.
    ingest_directory(test_dir, db_path=test_db)

    # Optional: Verify DB content (basic check)
    if test_db.exists():
        conn_check = None
        try:
            conn_check = sqlite3.connect(test_db)
            cursor_check = conn_check.cursor()
            cursor_check.execute("SELECT COUNT(*) FROM clips")
            count = cursor_check.fetchone()[0]
            print(f"\nVerification: Found {count} entries in the test database.")
            cursor_check.execute("SELECT path, filename, duration FROM clips")
            for row in cursor_check.fetchall():
                print(f"  - {row[1]} (Path: {row[0]}, Duration: {row[2]})")
        except sqlite3.Error as e:
            print(f"Error verifying test database: {e}", file=sys.stderr)
        finally:
            if conn_check:
                conn_check.close()

    # Clean up after test
    _cleanup_test_environment(test_dir, test_db) 