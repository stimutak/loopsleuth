"""Perceptual hashing (pHash) for generated thumbnails."""

import sys
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

# Adjust import path
SCRIPTS_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPTS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from PIL import Image, UnidentifiedImageError
import imagehash

from loopsleuth.db import get_db_connection, get_default_db_path

class HasherError(Exception):
    """Custom exception for errors during hashing."""
    pass

def calculate_phash(image_path: Path) -> Optional[str]:
    """
    Calculates the perceptual hash (pHash) for an image file.

    Args:
        image_path: Path to the input image file (e.g., a thumbnail).

    Returns:
        The pHash as a hexadecimal string, or None if hashing failed.

    Raises:
        HasherError: If Pillow fails to open the image or imagehash fails.
        FileNotFoundError: If the image file does not exist.
    """
    if not image_path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with Image.open(image_path) as img:
            # Calculate pHash (perceptual hash)
            # hash_size can be adjusted (default 8 -> 64-bit hash)
            # higher hash_size increases precision but also sensitivity to noise
            hash_val = imagehash.phash(img, hash_size=16) # Use 16 for more bits (256)
            return str(hash_val)
    except UnidentifiedImageError as e:
        raise HasherError(f"Pillow could not identify image file: {image_path}. Error: {e}") from e
    except Exception as e:
        # Catch potential errors from imagehash or other Pillow issues
        raise HasherError(f"Failed to calculate pHash for {image_path}. Error: {e}") from e

def process_hashes(
    db_path: Path = get_default_db_path(),
    limit: Optional[int] = None,
    force_regenerate: bool = False,
) -> Tuple[int, int]:
    """
    Finds clips missing pHash in the database and calculates/stores them.
    Requires thumbnails to exist.

    Args:
        db_path: Path to the SQLite database.
        limit: Maximum number of hashes to generate in one run (optional).
        force_regenerate: If True, regenerate hashes even if they exist (optional).

    Returns:
        A tuple containing (success_count, error_count).
    """
    conn = None
    success_count = 0
    error_count = 0
    project_root = db_path.parent # Assume DB is in project root

    print(f"Processing missing perceptual hashes (DB: {db_path})...")

    try:
        conn = get_db_connection(db_path)
        conn.isolation_level = None # Autocommit mode for updates
        read_cursor = conn.cursor()
        update_cursor = conn.cursor()

        # Select clips that have a thumbnail path but maybe no phash
        query = """
            SELECT id, thumbnail_path
            FROM clips
            WHERE thumbnail_path IS NOT NULL
        """
        if not force_regenerate:
            query += " AND phash IS NULL"

        if limit is not None and limit > 0:
            query += f" LIMIT {limit}"

        read_cursor.execute(query)

        row = read_cursor.fetchone()
        while row is not None:
            clip_id, thumb_path_rel = row['id'], row['thumbnail_path']
            thumbnail_path = (project_root / thumb_path_rel).resolve()
            print(f"- Processing hash for clip ID {clip_id} (Thumb: {thumb_path_rel})")

            if not thumbnail_path.exists():
                print(f"  Warning: Thumbnail file not found: {thumbnail_path}. Skipping.", file=sys.stderr)
                error_count += 1
                row = read_cursor.fetchone() # Move to next row
                continue

            try:
                phash_str = calculate_phash(thumbnail_path)

                if phash_str:
                    try:
                        # Use explicit transaction for update
                        update_cursor.execute("BEGIN")
                        update_cursor.execute(
                            "UPDATE clips SET phash = ? WHERE id = ?",
                            (phash_str, clip_id)
                        )
                        update_cursor.execute("COMMIT")
                        success_count += 1
                        # print(f"  Success: {phash_str}")
                    except sqlite3.Error as db_err:
                        print(f"  Error updating database for clip ID {clip_id}: {db_err}", file=sys.stderr)
                        update_cursor.execute("ROLLBACK")
                        error_count += 1
                else:
                    # Should not happen with current calculate_phash unless exception
                    print(f"  Warning: Hash calculation returned None for clip ID {clip_id}.", file=sys.stderr)
                    error_count += 1

            except (HasherError, FileNotFoundError) as e:
                print(f"  Error generating hash for clip ID {clip_id}: {e}", file=sys.stderr)
                error_count += 1
            except Exception as e:
                 print(f"  Unexpected error hashing for clip ID {clip_id}: {e}", file=sys.stderr)
                 error_count += 1

            # Fetch next row
            row = read_cursor.fetchone()

    except sqlite3.Error as e:
        print(f"Database error during hash processing: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred during hashing: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

    print(f"\nHash processing complete. Success: {success_count}, Errors: {error_count}")
    return success_count, error_count

# --- Example Usage ---
if __name__ == '__main__':
    import time
    # This example assumes the thumbnailer example ran first and created
    # a test DB (temp_thumb_test.db) with at least one clip and its thumbnail.

    test_db_path = Path("./temp_thumb_test.db") # Use the DB from thumbnailer example

    print("--- Hasher Example ---")
    if not test_db_path.exists():
        print(f"!!! Error: Test database '{test_db_path}' not found.")
        print("!!! Please run the thumbnailer.py example first to create it.")
        sys.exit(1)

    # Check if there are entries ready for hashing
    conn_check = None
    clip_to_hash_id = None
    try:
        conn_check = get_db_connection(test_db_path)
        cursor_check = conn_check.cursor()
        cursor_check.execute("SELECT id FROM clips WHERE thumbnail_path IS NOT NULL AND phash IS NULL LIMIT 1")
        result = cursor_check.fetchone()
        if result:
            clip_to_hash_id = result['id']
            print(f"Found clip ID {clip_to_hash_id} ready for hashing.")
        else:
            print("No clips found requiring hashing in the test DB.")
            # Optionally, run thumbnailer again or force regenerate hash?
            # For now, just exit if nothing to do.
            sys.exit(0)
    except sqlite3.Error as e:
        print(f"Error checking database before hashing: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn_check: conn_check.close()


    # Process Hashes
    print("\nAttempting to calculate missing hashes...")
    start_time = time.time()

    success, errors = process_hashes(db_path=test_db_path)

    end_time = time.time()
    print(f"process_hashes finished in {end_time - start_time:.2f}s")

    # Verification
    if success > 0 and clip_to_hash_id:
        conn_verify = None
        try:
            conn_verify = get_db_connection(test_db_path)
            cursor_verify = conn_verify.cursor()
            cursor_verify.execute("SELECT phash FROM clips WHERE id = ?", (clip_to_hash_id,))
            result = cursor_verify.fetchone()
            if result and result['phash']:
                print(f"Verification successful: DB record {clip_to_hash_id} has pHash: {result['phash']}")
            else:
                print("Verification failed: DB record not updated or pHash is NULL.")
        except sqlite3.Error as e:
            print(f"Error verifying DB after hash processing: {e}", file=sys.stderr)
        finally:
            if conn_verify: conn_verify.close()
    else:
        print("No hashes were successfully generated or verified.")

    # Note: Cleanup of the test DB and thumbnails should be handled externally or manually.
    # Removed automatic cleanup.
    print("--- Example Done ---") 