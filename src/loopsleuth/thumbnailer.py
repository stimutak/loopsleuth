"""Thumbnail generation for video clips using ffmpeg and Pillow."""

import subprocess
import sys
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple

# Adjust import path
SCRIPTS_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPTS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from PIL import Image, UnidentifiedImageError

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

# --- Example Usage ---
# Note: This requires a real video file, ffmpeg installed, and ideally
# a database entry created by the scanner to have duration and ID.

if __name__ == '__main__':
    from io import BytesIO # Needed for example usage with BytesIO
    from loopsleuth.db import get_db_connection, DEFAULT_DB_PATH
    import time

    # --- Test Setup ---
    test_video_dir = Path("./temp_thumb_test")
    test_video_dir.mkdir(exist_ok=True)
    # We need a *real* small video file for ffmpeg to process
    # Creating a dummy one won't work here.
    # Please manually place a small video file named 'test_clip.mp4'
    # in the 'temp_thumb_test' directory for this example to run.
    sample_video_path = test_video_dir / "test_clip.mp4"
    test_db_path = Path("./temp_thumb_test.db")
    thumb_dir = _get_thumbnail_dir(test_video_dir) # Place thumbs inside test dir

    clip_id_in_db = None
    sample_duration = None

    print("--- Thumbnailer Example ---")
    if not sample_video_path.exists():
        print(f"!!! WARNING: Test video '{sample_video_path}' not found.")
        print("!!! Please place a small MP4 file there to run the example.")
        sys.exit(1)

    # 1. (Simulate) Get duration and add to DB (if not already done by scanner)
    conn = None
    try:
        if test_db_path.exists(): test_db_path.unlink() # Clean previous test DB
        conn = get_db_connection(test_db_path)
        cursor = conn.cursor()

        # Get duration first
        from loopsleuth.metadata import get_video_duration, FFprobeError
        try:
            sample_duration = get_video_duration(sample_video_path)
            if sample_duration is None:
                print("Error: Could not get duration for test video via ffprobe.", file=sys.stderr)
                sys.exit(1)

            print(f"Test video duration: {sample_duration:.2f}s")

            # Add to DB
            path_str = str(sample_video_path.resolve())
            filename = sample_video_path.name
            cursor.execute("INSERT INTO clips (path, filename, duration) VALUES (?, ?, ?)",
                           (path_str, filename, sample_duration))
            clip_id_in_db = cursor.lastrowid # Get the ID we just inserted
            conn.commit()
            print(f"Added test video to temporary DB (ID: {clip_id_in_db}): {test_db_path}")

        except (FFprobeError, FileNotFoundError) as e:
             print(f"Error getting duration for test video: {e}", file=sys.stderr)
             print("Ensure ffprobe is installed and in PATH.", file=sys.stderr)
             sys.exit(1)

    except sqlite3.Error as e:
        print(f"Database error during setup: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn: conn.close()

    # 2. Generate Thumbnail
    generated_thumb_path = None
    if sample_duration and clip_id_in_db:
        print(f"\nAttempting to generate thumbnail for ID {clip_id_in_db}...")
        start_time = time.time()
        try:
            generated_thumb_path = generate_thumbnail(
                video_path=sample_video_path,
                duration=sample_duration,
                clip_id=clip_id_in_db,
                output_dir=thumb_dir
            )
            end_time = time.time()
            if generated_thumb_path:
                print(f"Successfully generated thumbnail: {generated_thumb_path}")
                print(f"Time taken: {end_time - start_time:.2f}s")

                # 3. (Simulate) Update DB with thumbnail path
                conn_update = None
                try:
                    conn_update = get_db_connection(test_db_path)
                    cursor_update = conn_update.cursor()
                    thumb_path_str = str(generated_thumb_path.relative_to(Path('.'))) # Store relative path
                    cursor_update.execute("UPDATE clips SET thumbnail_path = ? WHERE id = ?",
                                         (thumb_path_str, clip_id_in_db))
                    conn_update.commit()
                    print(f"Updated DB record {clip_id_in_db} with thumbnail path: {thumb_path_str}")

                     # Verification
                    cursor_update.execute("SELECT thumbnail_path FROM clips WHERE id = ?", (clip_id_in_db,))
                    db_thumb_path = cursor_update.fetchone()[0]
                    print(f"Verification: DB thumbnail_path = {db_thumb_path}")

                except sqlite3.Error as e:
                     print(f"Database error updating thumbnail path: {e}", file=sys.stderr)
                finally:
                    if conn_update: conn_update.close()

            else:
                print("Thumbnail generation returned None (failed).")

        except (ThumbnailError, FileNotFoundError, ValueError) as e:
            print(f"Error generating thumbnail: {e}")
        except Exception as e:
             print(f"An unexpected error occurred: {e}")

    # --- Cleanup ---
    print("\nCleaning up test environment...")
    if generated_thumb_path and generated_thumb_path.exists():
        generated_thumb_path.unlink()
        print(f"- Removed: {generated_thumb_path}")
    if thumb_dir.exists():
        try:
            # Only remove if empty
            os.rmdir(thumb_dir)
            # Try removing parent if empty
            os.rmdir(thumb_dir.parent)
            print(f"- Removed empty thumbnail dirs")
        except OSError:
            print(f"- Thumbnail dir not empty, left as is: {thumb_dir}")
            pass # Not empty, leave it
    if test_db_path.exists():
        test_db_path.unlink()
        print(f"- Removed: {test_db_path}")
    # Keep the dummy video file for next run if needed, or remove manually
    # if sample_video_path.exists():
    #     sample_video_path.unlink()
    #     print(f"- Removed: {sample_video_path}")
    if test_video_dir.exists():
         try:
             os.rmdir(test_video_dir)
             print(f"- Removed: {test_video_dir}")
         except OSError:
             print(f"- Test dir not empty, left as is: {test_video_dir}")
             pass

    print("--- Example Done ---")

# """ 