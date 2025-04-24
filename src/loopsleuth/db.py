"""Database interaction for LoopSleuth."""

import sqlite3
from pathlib import Path
from typing import Optional

# Define the default database path (e.g., in the user's data directory or project root)
# For simplicity during development, let's put it in the project root.
DEFAULT_DB_PATH = Path("loopsleuth.db")

def get_db_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Establishes a connection to the SQLite database and ensures the necessary
    table exists.

    Args:
        db_path: The path to the SQLite database file.

    Returns:
        An active SQLite database connection.
    """
    conn = sqlite3.connect(db_path)
    # Use Row factory for dict-like access to columns
    conn.row_factory = sqlite3.Row
    create_table(conn)
    return conn

def create_table(conn: sqlite3.Connection):
    """Creates the 'clips' table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL,
            duration REAL,          -- Duration in seconds (from ffprobe)
            thumbnail_path TEXT,    -- Path to the generated thumbnail JPEG
            phash TEXT,             -- Perceptual hash string
            starred BOOLEAN DEFAULT FALSE,
            tags TEXT,              -- Comma-separated string or JSON? Start with simple string.
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Track file modification
            -- Consider adding width, height, codec later if needed
        )
    """)
    # Add indexes for potentially queried columns
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clips_path ON clips (path)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clips_starred ON clips (starred)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clips_phash ON clips (phash)")

    # Create normalized tag tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clip_tags (
            clip_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (clip_id, tag_id),
            FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

# Example usage (optional, can be removed or moved to a main script)
if __name__ == '__main__':
    connection = get_db_connection()
    print(f"Database connection established to {DEFAULT_DB_PATH}")
    print("'clips' table ensured.")
    connection.close() 