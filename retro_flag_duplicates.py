import sqlite3
from pathlib import Path
from collections import defaultdict

def hamming_distance(hash1: str, hash2: str) -> int:
    b1 = bin(int(hash1, 16))[2:].zfill(len(hash1)*4)
    b2 = bin(int(hash2, 16))[2:].zfill(len(hash2)*4)
    return sum(c1 != c2 for c1, c2 in zip(b1, b2))

DB_PATH = Path('loopsleuth.db')
THRESHOLD = 5  # Default threshold for near-duplicate

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch all clips with a pHash
    cur.execute("SELECT id, phash FROM clips WHERE phash IS NOT NULL")
    clips = cur.fetchall()
    print(f"Loaded {len(clips)} clips with pHash.")

    # Build groups of duplicates
    groups = []  # Each group is a list of ids
    seen = set()
    for i, clip in enumerate(clips):
        if clip['id'] in seen:
            continue
        group = [clip['id']]
        for j in range(i+1, len(clips)):
            other = clips[j]
            if other['id'] in seen:
                continue
            dist = hamming_distance(clip['phash'], other['phash'])
            if dist <= THRESHOLD:
                group.append(other['id'])
                seen.add(other['id'])
        if len(group) > 1:
            groups.append(group)
            seen.update(group)

    print(f"Found {len(groups)} duplicate groups.")

    # Reset all duplicate flags first (idempotent)
    cur.execute("UPDATE clips SET needs_review = 0, duplicate_of = NULL")
    conn.commit()

    # Flag duplicates
    for group in groups:
        canonical_id = min(group)  # Use lowest id as canonical
        for dup_id in group:
            if dup_id == canonical_id:
                continue
            cur.execute(
                "UPDATE clips SET needs_review = 1, duplicate_of = ? WHERE id = ?",
                (canonical_id, dup_id)
            )
            print(f"Flagged clip {dup_id} as duplicate of {canonical_id}")
    conn.commit()
    print("Retroactive duplicate flagging complete.")

if __name__ == "__main__":
    main() 