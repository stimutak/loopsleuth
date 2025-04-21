def test_probe_video_returns_expected_keys(tmp_path):
    """ffprobe must at least return width, height, fps, duration, codec."""
    from loopsleuth.ingest import probe_video
    sample = tmp_path / "sample.mp4"
    # create a 1‑sec blank video w/ ffmpeg for the test ...
    out = probe_video(sample)
    assert {"width", "height", "fps", "duration", "codec"} <= out.keys()
