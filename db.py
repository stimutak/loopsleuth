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
