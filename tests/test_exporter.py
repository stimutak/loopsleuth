from pathlib import Path
from loopsleuth.exporter import export_starred_clips
from loopsleuth.db import get_db_connection

def test_export_starred_clips(tmp_path):
    db_path = tmp_path / "exp.db"
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    # one starred, one not
    cur.execute(
        "INSERT INTO clips (path, filename, duration, thumbnail_path, phash, starred) VALUES (?, ?, ?, ?, ?, ?)",
        ("/tmp/a.mp4", "a.mp4", 1.0, "", "h1", True)
    )
    cur.execute(
        "INSERT INTO clips (path, filename, duration, thumbnail_path, phash, starred) VALUES (?, ?, ?, ?, ?, ?)",
        ("/tmp/b.mp4", "b.mp4", 1.0, "", "h2", False)
    )
    conn.commit()
    conn.close()

    out_file = tmp_path / "keepers.txt"
    success, msg = export_starred_clips(db_path, out_file)
    assert success is True
    assert "Exported 1" in msg
    assert out_file.read_text().splitlines() == ["/tmp/a.mp4"]