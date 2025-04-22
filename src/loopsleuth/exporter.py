"""Handles exporting data from the LoopSleuth database."""

import sqlite3
from pathlib import Path
import sys

# Adjust import path if needed for standalone execution or testing
# (Assuming db.py is in the same directory or Python path is set correctly)
try:
    from .db import get_db_connection
except ImportError:
    # Allow running/testing directly if needed, adjust as necessary
    SCRIPTS_DIR = Path(__file__).parent.resolve()
    SRC_DIR = SCRIPTS_DIR.parent
    if str(SRC_DIR) not in sys.path:
        sys.path.append(str(SRC_DIR))
    from loopsleuth.db import get_db_connection

def export_starred_clips(db_path: Path, output_file: Path) -> tuple[bool, str]:
    """
    Queries the database for starred clips and writes their full paths to a text file.

    Args:
        db_path: Path to the SQLite database file.
        output_file: Path to the text file where starred clip paths will be written.

    Returns:
        A tuple containing:
        - bool: True if export was successful, False otherwise.
        - str: A message indicating success (with count) or the error encountered.
    """
    conn = None
    starred_clips_count = 0
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT path FROM clips WHERE starred = 1 ORDER BY path ASC
        """)
        starred_paths = [row['path'] for row in cursor.fetchall()]
        starred_clips_count = len(starred_paths)

        # Ensure the output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for path in starred_paths:
                f.write(f"{path}\n")

        return True, f"Exported {starred_clips_count} starred clip paths to {output_file.name}"

    except sqlite3.Error as e:
        return False, f"Database error during export: {e}"
    except OSError as e:
        return False, f"File system error writing export file: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred during export: {e}"
    finally:
        if conn:
            conn.close()

# Example usage (for testing the exporter directly)
if __name__ == '__main__':
    print("Testing exporter...")
    # Assume the test DB exists in the parent directory relative to this script
    test_db = Path(__file__).parent.parent / 'temp_thumb_test.db'
    output = Path(__file__).parent.parent / 'keepers_test.txt'

    if not test_db.exists():
        print(f"Test database not found at: {test_db}")
        print("Please run the TUI once (python -m src.loopsleuth.tui) to generate it.")
    else:
        # Add a starred item for testing if none exist
        conn_test = None
        try:
            conn_test = get_db_connection(test_db)
            cur_test = conn_test.cursor()
            cur_test.execute("SELECT 1 FROM clips WHERE starred = 1")
            if cur_test.fetchone() is None:
                print("No starred clips found, starring the first clip for testing export...")
                cur_test.execute("UPDATE clips SET starred = 1 WHERE id = (SELECT MIN(id) FROM clips)")
                conn_test.commit()
                print("Starred the first clip.")
        except sqlite3.Error as e:
            print(f"DB error while checking/starring clip for test: {e}")
        finally:
            if conn_test: conn_test.close()

        print(f"Exporting starred clips from {test_db.name} to {output.name}...")
        success, message = export_starred_clips(test_db, output)
        print(message)
        if success:
            try:
                with open(output, 'r', encoding='utf-8') as f:
                    print("--- File Content ---")
                    print(f.read())
                    print("--------------------")
            except Exception as e:
                print(f"Error reading back export file: {e}") 