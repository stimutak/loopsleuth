"""Video metadata extraction using ffprobe."""

import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple

FFPROBE_COMMAND = "ffprobe" # Assumes ffprobe is in PATH

class FFprobeError(Exception):
    """Custom exception for errors during ffprobe execution or parsing."""
    pass

def get_video_duration(video_path: Path) -> Optional[float]:
    """
    Retrieves the duration of a video file using ffprobe.

    Args:
        video_path: The path to the video file.

    Returns:
        The duration in seconds as a float, or None if duration cannot be determined.

    Raises:
        FFprobeError: If ffprobe command fails or returns invalid data.
        FileNotFoundError: If ffprobe executable is not found.
    """
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    command = [
        FFPROBE_COMMAND,
        "-v", "quiet",            # Suppress logging info
        "-print_format", "json", # Output in JSON format
        "-show_format",         # Request format information (contains duration)
        str(video_path)         # Input file path
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True, # Raise CalledProcessError on non-zero exit
            encoding='utf-8'
        )
        metadata = json.loads(result.stdout)

        duration_str = metadata.get("format", {}).get("duration")
        if duration_str:
            return float(duration_str)
        else:
            # Handle cases where duration might be missing (e.g., corrupted file)
            # print(f"Warning: Could not find duration for {video_path}")
            return None

    except FileNotFoundError:
        # This occurs if FFPROBE_COMMAND is not found in PATH
        raise FileNotFoundError(
            f"'{FFPROBE_COMMAND}' command not found. "
            f"Ensure FFmpeg is installed and '{FFPROBE_COMMAND}' is in your PATH."
        )
    except subprocess.CalledProcessError as e:
        # ffprobe exited with an error (e.g., invalid file format)
        raise FFprobeError(
            f"ffprobe failed for {video_path}. Error: {e.stderr or e}"
        ) from e
    except json.JSONDecodeError as e:
        # Could not parse ffprobe's JSON output
        raise FFprobeError(
            f"Failed to parse ffprobe JSON output for {video_path}. Error: {e}"
        ) from e
    except Exception as e:
        # Catch any other unexpected errors
        raise FFprobeError(
            f"An unexpected error occurred while processing {video_path}: {e}"
        ) from e

def get_video_metadata(video_path: Path) -> dict:
    """
    Retrieves video metadata (duration, width, height, codec_name, size) using ffprobe.

    Args:
        video_path: The path to the video file.

    Returns:
        A dict with keys: duration (float), width (int), height (int), codec_name (str), size (int)
        Any missing value will be None.

    Raises:
        FFprobeError: If ffprobe command fails or returns invalid data.
        FileNotFoundError: If ffprobe executable is not found.
    """
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    command = [
        FFPROBE_COMMAND,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path)
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        metadata = json.loads(result.stdout)
        # Duration and size from format
        fmt = metadata.get("format", {})
        duration = float(fmt.get("duration")) if fmt.get("duration") else None
        size = int(fmt.get("size")) if fmt.get("size") else None
        # First video stream for width/height/codec_name
        width = height = codec_name = None
        for stream in metadata.get("streams", []):
            if stream.get("codec_type") == "video":
                width = stream.get("width")
                height = stream.get("height")
                codec_name = stream.get("codec_name")
                break
        return {
            "duration": duration,
            "width": width,
            "height": height,
            "codec_name": codec_name,
            "size": size
        }
    except FileNotFoundError:
        raise FileNotFoundError(
            f"'{FFPROBE_COMMAND}' command not found. "
            f"Ensure FFmpeg is installed and '{FFPROBE_COMMAND}' is in your PATH."
        )
    except subprocess.CalledProcessError as e:
        raise FFprobeError(
            f"ffprobe failed for {video_path}. Error: {e.stderr or e}"
        ) from e
    except json.JSONDecodeError as e:
        raise FFprobeError(
            f"Failed to parse ffprobe JSON output for {video_path}. Error: {e}"
        ) from e
    except Exception as e:
        raise FFprobeError(
            f"An unexpected error occurred while processing {video_path}: {e}"
        ) from e

# Example Usage (requires a real video file and ffprobe installed)
if __name__ == '__main__':
    # Replace with a path to an actual video file on your system for testing
    # test_video = Path("/path/to/your/test/video.mp4")
    test_video = Path("dummy_video_for_testing.mp4") # Placeholder

    print(f"Attempting to get duration for: {test_video}")

    # Create a dummy file just to test the file existence check
    test_video.touch()

    try:
        duration = get_video_duration(test_video)
        if duration is not None:
            print(f"Duration: {duration:.2f} seconds")
        else:
            print("Could not determine duration (ffprobe might have run but found no duration field).")
    except FileNotFoundError as e:
        print(f"Error: {e}") # Specifically catch ffprobe not found
    except FFprobeError as e:
        print(f"Error: {e}") # Catch errors from ffprobe execution/parsing
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Clean up dummy file
        if test_video.exists():
            test_video.unlink()
            print(f"Cleaned up dummy file: {test_video}") 