import pytest
from pathlib import Path
import subprocess

from loopsleuth.thumbnailer import generate_thumbnail, ThumbnailError

def test_generate_thumbnail_file_not_found():
    with pytest.raises(FileNotFoundError):
        generate_thumbnail(Path("nofile.mp4"), duration=1.0)
def test_generate_thumbnail_invalid_duration(tmp_path):
    f = tmp_path / "vid.mp4"
    f.write_bytes(b"")
    with pytest.raises(ValueError):
        generate_thumbnail(f, duration=None)
def test_generate_thumbnail_ffmpeg_missing(monkeypatch, tmp_path):
    vid = tmp_path / "vid2.mp4"
    vid.write_bytes(b"")
    # Simulate missing ffmpeg
    monkeypatch.setattr(subprocess, "Popen",
                       lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
    with pytest.raises(FileNotFoundError):
                generate_thumbnail(vid, duration=1.0)