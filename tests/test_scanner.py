import pytest
from pathlib import Path

import src.loopsleuth.scanner as scanner
from loopsleuth.db import get_db_connection, get_default_db_path

def test_scan_directory_internal(tmp_path):
    v1 = tmp_path / "v1.mp4"
    v2 = tmp_path / "v2.mov" 
    other = tmp_path / "skip.txt"
    
    v1.write_bytes(b"")
    v2.write_bytes(b"")
    other.write_text("no")
    results = list(scanner._scan_directory_internal(tmp_path, extensions={".mp4", ".mov"}))
    assert v1.resolve() in results
    assert v2.resolve() in results
    assert all(str(p).lower().endswith(('.mp4', '.mov')) for p in results)

def test_ingest_directory(monkeypatch, tmp_path):
    # Prepare a fake folder with two clips + one noise file
    d = tmp_path / "videos"
    d.mkdir()
    (d / "a.mp4").write_bytes(b"")
    (d / "b.mov").write_bytes(b"") 
    (d / "c.txt").write_text("no")
    # Stub out metadata and thumbnail generation
    monkeypatch.setattr(scanner, "get_video_metadata",
                       lambda p: {"duration": 1.0, "width": 10, "height": 10, "size": 100, "codec_name": "h264"})
    fake_thumb = tmp_path / "thumb.jpg"
    fake_thumb.write_bytes(b"dummy")
    monkeypatch.setattr(scanner, "generate_thumbnail",
                                lambda video_path, duration, clip_id, output_dir: fake_thumb)
    
    db_path = tmp_path / "scan_test.db"
    scanner.ingest_directory(start_path=d, db_path=db_path, force_rescan=False)

    conn = get_db_connection(db_path)
    rows = conn.execute("SELECT filename, thumbnail_path FROM clips ORDER BY filename").fetchall()
    conn.close()

    assert len(rows) == 2
    assert {r[0] for r in rows} == {"a.mp4", "b.mov"}
    assert all(Path(r[1]).name == fake_thumb.name for r in rows)

