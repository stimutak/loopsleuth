import sqlite3
from pathlib import Path
from collections import defaultdict

DB_PATH = Path("loopsleuth.db")

def migrate_tags(dry_run=True):
    """
    Migrates tags from the old comma-separated string in clips.tags
    to the normalized tags and clip_tags tables.
    If dry_run is True, prints actions without modifying the DB.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch all clips and their tags
    cursor.execute("SELECT id, tags FROM clips")
    clips = cursor.fetchall()

    # 2. Build a set of all unique tags
    tag_set = set()
    clip_to_tags = defaultdict(list)
    for row in clips:
        clip_id = row["id"]
        tags = row["tags"] or ""
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tag_list:
            tag_set.add(tag)
            clip_to_tags[clip_id].append(tag)

    print(f"Found {len(tag_set)} unique tags across {len(clips)} clips.")

    # 3. Insert unique tags into tags table
    tag_name_to_id = {}
    for tag in tag_set:
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
        row = cursor.fetchone()
        if row:
            tag_id = row["id"]
        else:
            if not dry_run:
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag,))
                tag_id = cursor.lastrowid
            else:
                tag_id = None
        tag_name_to_id[tag] = tag_id
        if dry_run:
            print(f"Would insert tag: '{tag}'")

    # 4. Insert into clip_tags join table
    for clip_id, tags in clip_to_tags.items():
        for tag in tags:
            tag_id = tag_name_to_id[tag]
            if not dry_run:
                # Get tag_id if not already set (for dry_run)
                if tag_id is None:
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                    tag_id = cursor.fetchone()["id"]
                cursor.execute(
                    "INSERT OR IGNORE INTO clip_tags (clip_id, tag_id) VALUES (?, ?)",
                    (clip_id, tag_id)
                )
            else:
                print(f"Would link clip {clip_id} to tag '{tag}'")

    if not dry_run:
        conn.commit()
        print("Migration committed.")
    else:
        print("Dry run complete. No changes made.")
    conn.close()

if __name__ == "__main__":
    import sys
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        dry_run = False
    migrate_tags(dry_run=dry_run) 