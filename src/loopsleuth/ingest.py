import json
import subprocess
from pathlib import Path
from typing import Dict, Any

class ProbeError(Exception):
    """Custom exception for ffprobe errors."""
    pass

def probe_video(video_path: Path) -> Dict[str, Any]:
    """
    Probes a video file using ffprobe and returns basic metadata.

    Returns a dict with keys:
      - width (int)
      - height (int)
      - fps (float)
      - duration (float)
      - codec (str)

    Raises:
      FileNotFoundError: If the video file does not exist.
      ProbeError: If ffprobe fails or returns invalid data.
    """
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except FileNotFoundError as e:
        raise FileNotFoundError("ffprobe not found. Please install FFmpeg.") from e
    except subprocess.CalledProcessError as e:
        raise ProbeError(f"ffprobe error for {video_path}: {e.stderr or e}") from e
    except json.JSONDecodeError as e:
        raise ProbeError(f"Failed to parse ffprobe output: {e}") from e

    fmt = data.get("format", {})
    duration = None
    if fmt.get("duration"):
        try:
            duration = float(fmt["duration"])
        except (TypeError, ValueError):
            pass

    width = height = fps = None
    codec = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            width = stream.get("width")
            height = stream.get("height")
            codec = stream.get("codec_name")
            rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
            if rate and "/" in rate:
                try:
                    n, d = rate.split("/")
                    fps = float(n) / float(d)
                except (ValueError, ZeroDivisionError):
                    pass
            else:
                try:
                    fps = float(rate)
                except (TypeError, ValueError):
                    pass
            break

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "codec": codec,
    }