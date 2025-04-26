import pytest
from pathlib import Path

from loopsleuth.metadata import get_video_duration, get_video_metadata, FFprobeError

def test_get_video_duration_missing():
    with pytest.raises(FileNotFoundError):
        get_video_duration(Path("nofile.mp4"))
def test_get_video_duration_bad_file(tmp_path):
    f = tmp_path / "bad.txt"
    f.write_text("nonsense")
    with pytest.raises(FFprobeError):
        get_video_duration(f)

def test_get_video_metadata_missing():
    with pytest.raises(FileNotFoundError):
        get_video_metadata(Path("nofile.mp4"))