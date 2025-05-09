"""Database interaction for LoopSleuth."""

import sqlite3
from pathlib import Path
from typing import Optional
import os

def get_default_db_path():
    return Path(os.environ.get("LOOPSLEUTH_DB_PATH", "loopsleuth.db"))

def get_db_connection(db_path: Path = None) -> sqlite3.Connection:
    """
    Establishes a connection to the SQLite database and ensures the necessary
    table exists.

    Args:
        db_path: The path to the SQLite database file.

    Returns:
        An active SQLite database connection.
    """
    if db_path is None:
        db_path = get_default_db_path()
    conn = sqlite3.connect(db_path)
    # Defensive: Always set Row factory for dict-like access to columns
    conn.row_factory = sqlite3.Row
    print(f"[get_db_connection] row_factory set to: {conn.row_factory}")
    create_table(conn)
    migrate_clips_table(conn)
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
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Track file modification
            duplicate_of INTEGER,   -- If duplicate, points to canonical clip.id
            needs_review BOOLEAN DEFAULT 0 -- Flag for batch duplicate review
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

    # --- Playlist tables ---
    # playlists: stores playlist metadata (name, created_at, order)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            "order" INTEGER
        )
    """)
    # Add 'order' column if missing (for playlist sidebar reordering)
    try:
        cursor.execute("ALTER TABLE playlists ADD COLUMN \"order\" INTEGER")
    except Exception:
        pass  # Already exists
    # playlist_clips: join table for ordered clips in playlists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_clips (
            playlist_id INTEGER NOT NULL,
            clip_id INTEGER NOT NULL,
            position INTEGER NOT NULL, -- 0-based ordering in playlist
            PRIMARY KEY (playlist_id, clip_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE
        )
    """)

    # --- Scan tracking table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_path TEXT NOT NULL,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Add scan_id to clips if not present
    try:
        cursor.execute("ALTER TABLE clips ADD COLUMN scan_id INTEGER")
    except Exception:
        pass  # Already exists

    conn.commit()

def migrate_clips_table(conn):
    """Add width, height, size, codec_name, duplicate_of, and needs_review columns to the clips table if missing."""
    cursor = conn.cursor()
    # Check and add columns if they do not exist
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(clips)")]
    alter_stmts = []
    if 'width' not in columns:
        alter_stmts.append("ALTER TABLE clips ADD COLUMN width INTEGER")
    if 'height' not in columns:
        alter_stmts.append("ALTER TABLE clips ADD COLUMN height INTEGER")
    if 'size' not in columns:
        alter_stmts.append("ALTER TABLE clips ADD COLUMN size INTEGER")
    if 'codec_name' not in columns:
        alter_stmts.append("ALTER TABLE clips ADD COLUMN codec_name TEXT")
    if 'duplicate_of' not in columns:
        alter_stmts.append("ALTER TABLE clips ADD COLUMN duplicate_of INTEGER")
    if 'needs_review' not in columns:
        alter_stmts.append("ALTER TABLE clips ADD COLUMN needs_review BOOLEAN DEFAULT 0")
    for stmt in alter_stmts:
        cursor.execute(stmt)
    if alter_stmts:
        conn.commit()

# Example usage (optional, can be removed or moved to a main script)
if __name__ == '__main__':
    connection = get_db_connection()
    print(f"Database connection established to {get_default_db_path()}")
    print("'clips' table ensured.")
    connection.close() 