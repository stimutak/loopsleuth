"""
SQLite schema & helpers for LoopSleuth.

Tables
------
clips:
    path TEXT UNIQUE
    width INTEGER
    height INTEGER
    fps REAL
    duration REAL
    codec TEXT
    filesize INTEGER
    phash TEXT
    starred INTEGER DEFAULT 0
    tags TEXT DEFAULT ''          # comma‑separated

TODO
----
- migration helper if schema changes
- add 'created' timestamp
"""

if __name__ == "__main__":
    import sqlite3
    from pathlib import Path
    db_path = Path("temp_thumb_test.db")
    if not db_path.exists():
        print("Database not found.")
        exit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, filename, duration, thumbnail_path FROM clips ORDER BY id ASC LIMIT 20")
    rows = cur.fetchall()
    print(f"{'id':>4} | {'filename':<40} | {'duration':>8} | thumbnail_path")
    print("-"*100)
    for row in rows:
        print(f"{row['id']:>4} | {row['filename']:<40} | {row['duration']:>8} | {row['thumbnail_path']}")
    conn.close()
