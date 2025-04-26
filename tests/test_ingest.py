def test_probe_video_returns_expected_keys(tmp_path):
    """ffprobe must at least return width, height, fps, duration, codec."""
    from loopsleuth.ingest import probe_video
    import subprocess, pytest

    sample = tmp_path / "sample.mp4"
    # create a 1-second black video via ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=1",
        "-c:v", "libx264", "-t", "1",
        str(sample),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pytest.skip("ffmpeg not installed, skipping probe test")
    except subprocess.CalledProcessError as e:
        pytest.skip(f"ffmpeg error ({e}), skipping probe test")

    out = probe_video(sample)
    assert {"width", "height", "fps", "duration", "codec"} <= set(out.keys())

