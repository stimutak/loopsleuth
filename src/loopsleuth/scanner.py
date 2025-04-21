"""Directory scanning functionality for finding video clips."""

import os
from pathlib import Path
from typing import Iterable, List, Set

# Common video file extensions
# TODO: Make this configurable
DEFAULT_VIDEO_EXTENSIONS: Set[str] = {
    ".mov",
    ".mp4",
    ".avi",
    ".mkv",
    # Add more as needed, e.g., .mpeg, .mpg, .wmv
    # DXV is often in a .mov container, so it should be covered.
}

def scan_directory(
    start_path: Path,
    extensions: Set[str] = DEFAULT_VIDEO_EXTENSIONS,
) -> Iterable[Path]:
    """
    Recursively scans a directory for video files with specified extensions.

    Args:
        start_path: The directory path to start scanning from.
        extensions: A set of lowercase file extensions to look for (including the dot).

    Yields:
        Path objects for found video files.
    """
    if not start_path.is_dir():
        raise ValueError(f"Invalid start path: {start_path} is not a directory.")

    print(f"Scanning {start_path} for video files ({', '.join(extensions)})...")
    # TODO: Add tqdm progress bar here for large directories

    for item in start_path.rglob("*"): # Recursively glob for all files
        if item.is_file() and item.suffix.lower() in extensions:
            yield item.resolve() # Yield absolute path

# Example usage for testing
if __name__ == '__main__':
    # Create dummy files for testing
    test_dir = Path("./temp_scan_test")
    test_dir.mkdir(exist_ok=True)
    (test_dir / "video1.mov").touch()
    (test_dir / "video2.mp4").touch()
    (test_dir / "subfolder").mkdir(exist_ok=True)
    (test_dir / "subfolder" / "video3.mkv").touch()
    (test_dir / "image.jpg").touch()
    (test_dir / "document.txt").touch()

    print("Starting scan...")
    found_files: List[Path] = list(scan_directory(test_dir))

    print("\nFound video files:")
    if found_files:
        for f in found_files:
            print(f" - {f}")
    else:
        print("No video files found in the test directory.")

    # Clean up dummy files
    print("\nCleaning up test files...")
    os.remove(test_dir / "video1.mov")
    os.remove(test_dir / "video2.mp4")
    os.remove(test_dir / "subfolder" / "video3.mkv")
    os.remove(test_dir / "image.jpg")
    os.remove(test_dir / "document.txt")
    os.rmdir(test_dir / "subfolder")
    os.rmdir(test_dir)
    print("Cleanup complete.") 