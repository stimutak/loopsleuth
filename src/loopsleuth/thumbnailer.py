"""Thumbnail generation for video clips using ffmpeg and Pillow."""

import subprocess
import sys
import os
import hashlib
import sqlite3 # Import top-level for exception handling
from io import BytesIO # Needed for Pillow processing
from pathlib import Path
from typing import Optional, Tuple

# Adjust import path
SCRIPTS_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPTS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from PIL import Image, UnidentifiedImageError
from loopsleuth.db import get_db_connection, DEFAULT_DB_PATH # Import top-level
from loopsleuth.metadata import get_video_duration, FFprobeError # Import top-level for example

# Constants
FFMPEG_COMMAND = "ffmpeg" # Assumes ffmpeg is in PATH
THUMBNAIL_DIR_NAME = ".loopsleuth_data/thumbnails"
THUMBNAIL_SIZE = (256, 256) # Target size (width, height) - keeping aspect ratio
THUMBNAIL_FORMAT = "JPEG"
THUMBNAIL_QUALITY = 85 # JPEG quality

class ThumbnailError(Exception):
    """Custom exception for errors during thumbnail generation."""
    pass

def _get_thumbnail_dir(base_dir: Path = Path('.')) -> Path:
    """Gets the thumbnail storage directory path, creating it if necessary."""
    thumb_dir = base_dir / THUMBNAIL_DIR_NAME
    thumb_dir.mkdir(parents=True, exist_ok=True)
    return thumb_dir

def _get_thumbnail_filename(video_path_str: str, clip_id: Optional[int] = None) -> str:
    """Generates a unique filename for the thumbnail."""
    if clip_id:
        # Prefer using DB ID if available
        return f"clip_{clip_id}.jpg"
    else:
        # Fallback to hash of path if ID is not provided
        path_hash = hashlib.sha1(video_path_str.encode('utf-8')).hexdigest()
        return f"path_{path_hash}.jpg"

def generate_thumbnail(
    video_path: Path,
    duration: Optional[float],
    clip_id: Optional[int] = None, # Pass DB ID for better filename
    output_dir: Optional[Path] = None,
    target_size: Tuple[int, int] = THUMBNAIL_SIZE,
    quality: int = THUMBNAIL_QUALITY,
    time_percent: float = 0.25 # Extract frame at 25% duration
) -> Optional[Path]:
    """
    Generates a resized thumbnail for a video file.

    Args:
        video_path: Path to the input video file.
        duration: Duration of the video in seconds (required to calculate time).
        clip_id: The primary key ID of the clip in the database (optional, for filename).
        output_dir: The directory to save thumbnails (defaults to THUMBNAIL_DIR_NAME).
        target_size: Desired thumbnail size (width, height), maintains aspect ratio.
        quality: JPEG quality (1-95).
        time_percent: Position in video duration (0.0 to 1.0) to grab frame from.

    Returns:
        The Path to the generated thumbnail file, or None if generation failed.

    Raises:
        ThumbnailError: If ffmpeg fails or Pillow encounters an issue.
        FileNotFoundError: If ffmpeg executable is not found.
        ValueError: If duration is None or invalid.
    """
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if duration is None or duration <= 0:
        raise ValueError(f"Invalid or missing duration ({duration}) for {video_path}. Cannot calculate timestamp.")

    # Ensure output directory exists
    if output_dir is None:
        output_dir = _get_thumbnail_dir()
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate timestamp (avoiding exactly 0 if possible for problematic videos)
    timestamp = max(0.01, duration * time_percent)
    timestamp_str = f"{timestamp:.4f}" # Format as seconds.milliseconds

    # Generate output path
    thumb_filename = _get_thumbnail_filename(str(video_path), clip_id)
    output_path = output_dir / thumb_filename

    # ffmpeg command to extract one frame
    # -ss: seek to position (input seeking is faster for some formats)
    # -i: input file
    # -vframes 1: extract only one frame
    # -vf scale='w=...': scale filter, -2 ensures aspect ratio is maintained based on width
    # -q:v 2: quality scale for MJPEG output (2-5 is often good)
    # -f image2pipe: output raw image data to stdout
    # -loglevel error: suppress verbose output
    ffmpeg_extract_command = [
        FFMPEG_COMMAND,
        "-ss", timestamp_str,
        "-i", str(video_path),
        "-vframes", "1",
        "-vf", f"scale={target_size[0]}:-2", # Scale width, auto height
        "-q:v", "2", # High quality intermediate frame
        "-f", "image2pipe",
        "-c:v", "mjpeg", # Output as motion jpeg (single frame)
        "-loglevel", "error",
        "-" # Output to stdout
    ]

    temp_frame_path = output_path.with_suffix(".tmp.jpg") # Temporary file for ffmpeg output if piping fails

    try:
        # Try piping directly first (more efficient)
        ffmpeg_process = subprocess.Popen(ffmpeg_extract_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = ffmpeg_process.communicate()

        if ffmpeg_process.returncode != 0:
            # If piping failed, maybe try writing to a temp file?
            # Sometimes specific codecs/videos cause issues with piping.
            # For now, raise error based on stderr.
            error_msg = stderr.decode('utf-8', errors='ignore').strip()
            raise ThumbnailError(
                f"ffmpeg failed to extract frame for {video_path} at {timestamp_str}s. "
                f"Return code: {ffmpeg_process.returncode}. Error: {error_msg or 'Unknown ffmpeg error'}"
            )

        if not stdout:
             raise ThumbnailError(f"ffmpeg produced no output for {video_path}.")

        # Process the image data from stdout with Pillow
        try:
            with Image.open(BytesIO(stdout)) as img:
                 # Pillow already did scaling via ffmpeg, just save
                 img.save(
                    output_path,
                    format=THUMBNAIL_FORMAT,
                    quality=quality,
                    optimize=True)
        except UnidentifiedImageError as e:
             raise ThumbnailError(f"Pillow could not identify image data from ffmpeg for {video_path}. Error: {e}") from e
        except Exception as e: # Catch other Pillow errors
            raise ThumbnailError(f"Pillow failed to save thumbnail for {video_path}. Error: {e}") from e

        # print(f"Generated thumbnail: {output_path}")
        return output_path

    except FileNotFoundError:
        # This occurs if FFMPEG_COMMAND is not found in PATH
        raise FileNotFoundError(
            f"'{FFMPEG_COMMAND}' command not found. "
            f"Ensure FFmpeg is installed and '{FFMPEG_COMMAND}' is in your PATH."
        )
    except Exception as e:
        # Catch other unexpected errors during the process
        # Ensure we don't leave partial temp files if something else went wrong
        if temp_frame_path.exists():
             try:
                 temp_frame_path.unlink()
             except OSError:
                 pass # Ignore cleanup error
        # Re-raise original error or a new ThumbnailError
        if isinstance(e, ThumbnailError) or isinstance(e, FileNotFoundError):
            raise # Re-raise specific errors
        else:
            raise ThumbnailError(f"An unexpected error occurred generating thumbnail for {video_path}: {e}") from e
    finally:
         # Final cleanup check for temp file
         if temp_frame_path.exists():
             try:
                 temp_frame_path.unlink()
             except OSError:
                 pass

def process_thumbnails(
    db_path: Path = DEFAULT_DB_PATH,
    limit: Optional[int] = None,
    force_regenerate: bool = False,
) -> Tuple[int, int]:
    """
    Finds clips missing thumbnails in the database and generates them.

    Args:
        db_path: Path to the SQLite database.
        limit: Maximum number of thumbnails to generate in one run (optional).
        force_regenerate: If True, regenerate thumbnails even if they exist (optional).

    Returns:
        A tuple containing (success_count, error_count).
    """
    conn = None
    success_count = 0
    error_count = 0
    base_output_dir = _get_thumbnail_dir(db_path.parent) # Store thumbs relative to DB location

    print(f"Processing missing thumbnails (DB: {db_path})...")

    try:
        conn = get_db_connection(db_path)
        # Use a separate cursor for updates within the loop
        conn.isolation_level = None # Autocommit mode for updates
        read_cursor = conn.cursor()
        update_cursor = conn.cursor()

        query = """
            SELECT id, path, duration
            FROM clips
            WHERE duration IS NOT NULL AND duration > 0
        """
        if not force_regenerate:
            query += " AND thumbnail_path IS NULL"

        if limit is not None and limit > 0:
            query += f" LIMIT {limit}"

        read_cursor.execute(query)

        row = read_cursor.fetchone()
        while row is not None:
            clip_id, path_str, duration = row['id'], row['path'], row['duration']
            video_path = Path(path_str)
            print(f"- Processing clip ID {clip_id}: {video_path.name}")

            if not video_path.exists():
                print(f"  Warning: Video file not found: {video_path}. Skipping.", file=sys.stderr)
                error_count += 1
                row = read_cursor.fetchone() # Move to next row
                continue

            try:
                thumb_path = generate_thumbnail(
                    video_path=video_path,
                    duration=duration,
                    clip_id=clip_id,
                    output_dir=base_output_dir
                )

                if thumb_path:
                    # Store path relative to the main project/db directory
                    relative_thumb_path = str(thumb_path.relative_to(db_path.parent))
                    try:
                        # Use explicit transaction for update
                        update_cursor.execute("BEGIN")
                        update_cursor.execute(
                            "UPDATE clips SET thumbnail_path = ? WHERE id = ?",
                            (relative_thumb_path, clip_id)
                        )
                        update_cursor.execute("COMMIT")
                        success_count += 1
                        # print(f"  Success: {relative_thumb_path}")
                    except sqlite3.Error as db_err:
                         print(f"  Error updating database for clip ID {clip_id}: {db_err}", file=sys.stderr)
                         update_cursor.execute("ROLLBACK")
                         error_count += 1
                         # Optionally delete the generated thumb if DB update failed?
                         # if thumb_path.exists(): thumb_path.unlink()
                else:
                    print(f"  Warning: Thumbnail generation failed for clip ID {clip_id}.", file=sys.stderr)
                    error_count += 1

            except (ThumbnailError, FileNotFoundError, ValueError) as e:
                print(f"  Error generating thumbnail for clip ID {clip_id}: {e}", file=sys.stderr)
                error_count += 1
            except Exception as e:
                 print(f"  Unexpected error for clip ID {clip_id}: {e}", file=sys.stderr)
                 error_count += 1

            # Fetch next row before potentially long processing
            row = read_cursor.fetchone()

    except sqlite3.Error as e:
        print(f"Database error during thumbnail processing: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

    print(f"\nThumbnail processing complete. Success: {success_count}, Errors: {error_count}")
    return success_count, error_count

# --- Example Usage ---
# Note: This requires a real video file, ffmpeg installed, and ideally
# a database entry created by the scanner to have duration and ID.

if __name__ == "__main__":
    from pathlib import Path
    import sys
    db_path = Path("temp_thumb_test.db")
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)
    print("Attempting to generate missing thumbnails for all clips...")
    success, error = process_thumbnails(db_path=db_path, force_regenerate=False)
    print(f"Thumbnail processing complete. Success: {success}, Errors: {error}")

# """ 