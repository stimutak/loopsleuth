"""Textual User Interface for LoopSleuth."""

import sys
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# Adjust import path
SCRIPTS_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPTS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive

# Import database functions and default path
from loopsleuth.db import get_db_connection, DEFAULT_DB_PATH


class ClipCard(Static):
    """Widget to display information about a single video clip."""

    # Store the raw clip data dictionary
    clip_data = reactive[Optional[Dict[str, Any]]](None)

    DEFAULT_CSS = """
    ClipCard {
        border: round $primary;
        height: auto;
        padding: 1;
        margin: 1; /* Margin around each card */
        width: 1fr; /* Take up available grid width */
    }
    ClipCard:focus {
        border: thick $accent;
        background: $accent-darken-1;
    }
    """

    def __init__(self, clip_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        # Set clip_data only after super().__init__ to trigger reactive update
        self.clip_data = clip_data
        self.can_focus = True # Make cards focusable

    def render(self) -> str:
        """Render the clip card content based on clip_data."""
        if not self.clip_data:
            return "[b]Error:[/b] No data."

        # Safely get data with defaults
        clip_id = self.clip_data.get('id', 'N/A')
        filename = self.clip_data.get('filename', 'Unknown')
        thumb_path = self.clip_data.get('thumbnail_path', '')
        starred = self.clip_data.get('starred', False)
        tags = self.clip_data.get('tags', '')

        star_icon = "[b green]★[/]" if starred else "[dim]☆[/]"
        thumb_display = f"Thumb: {thumb_path}" if thumb_path else "Thumb: --"
        tags_display = f"Tags: {tags}" if tags else "Tags: --"

        # Simple multi-line layout
        return (
            f"[b]{filename}[/b]\n"
            f"{star_icon} ID: {clip_id}\n"
            f"{thumb_display}\n"
            f"{tags_display}"
        )


class ClipGrid(VerticalScroll):
    """A scrollable container displaying ClipCards in a grid layout."""

    DEFAULT_CSS = """
    ClipGrid {
        layout: grid;
        grid-size: 3; /* Number of columns */
        grid-gutter: 1 2; /* Vertical and horizontal spacing */
        padding: 1; /* Padding around the grid itself */
    }
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

    def on_mount(self) -> None:
        """Load clips when the widget is mounted."""
        self.load_clips()

    def load_clips(self):
        """Query the database and mount ClipCard widgets."""
        self.remove_children() # Clear previous cards

        clips: List[Dict[str, Any]] = []
        conn = None
        try:
            conn = get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, thumbnail_path, starred, tags
                FROM clips
                ORDER BY filename ASC
            """)
            clips = [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            self.mount(Static(f"[b red]Database Error:[/b red]\n{e}"))
            print(f"Database error loading clips: {e}", file=sys.stderr)
        except Exception as e:
            self.mount(Static(f"[b red]Unexpected Error:[/b red]\n{e}"))
            print(f"Unexpected error loading clips: {e}", file=sys.stderr)
        finally:
            if conn:
                conn.close()

        if clips:
            self.mount_all(ClipCard(clip_data=clip) for clip in clips)
        else:
            self.mount(Static("No clips found in the database."))


class LoopSleuthApp(App[None]):
    """The main Textual application for LoopSleuth."""

    # Embed all necessary CSS directly
    CSS = """
    Screen {
        /* Add global screen styles if needed */
    }
    Container#main-container {
        height: 1fr; /* Ensure container fills space */
    }
    """ + ClipGrid.DEFAULT_CSS + ClipCard.DEFAULT_CSS

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("r", "refresh_grid", "Refresh Grid"),
    ]

    # Store DB path for the app instance
    db_path: Path = DEFAULT_DB_PATH

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(ClipGrid(db_path=self.db_path, id="clip-grid"), id="main-container")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark

    def action_refresh_grid(self) -> None:
        """Reload clips in the grid."""
        try:
            grid = self.query_one(ClipGrid)
            grid.load_clips()
            self.notify("Clip grid refreshed.")
        except Exception as e:
            self.notify(f"Error refreshing grid: {e}", severity="error")
            print(f"Error refreshing grid: {e}", file=sys.stderr)


# --- Main execution block for testing --- #

def run_prerequisites():
    """Runs thumbnailer and hasher examples to ensure test data exists."""
    try:
        print("Running thumbnailer example to ensure test data...")
        # Use capture_output=False if you want to see their print statements
        subprocess.run([sys.executable, "-m", "src.loopsleuth.thumbnailer"], check=True, text=True, capture_output=True)
        print("Thumbnailer example completed.")

        print("\nRunning hasher example to ensure test data...")
        subprocess.run([sys.executable, "-m", "src.loopsleuth.hasher"], check=True, text=True, capture_output=True)
        print("Hasher example completed.")
        return True
    except FileNotFoundError as e:
        print(f"[Error] Prerequisite script components not found or Python can't find modules ({e})")
        print("        Make sure you are running from the project root directory (loopsleuth/).")
    except subprocess.CalledProcessError as e:
        print(f"[Error] Running prerequisite script failed:")
        print(f"  Command: {' '.join(e.cmd)}")
        print(f"  Return Code: {e.returncode}")
        # Print stderr first as it often contains the useful error message
        if e.stderr:
             print(f"  Stderr:\n{e.stderr}")
        if e.stdout:
            print(f"  Stdout:\n{e.stdout}")
        print("        Ensure FFmpeg/FFprobe are installed and ./temp_thumb_test/test_clip.mp4 exists.")
    except Exception as e:
        print(f"[Error] An unexpected error occurred running prerequisite scripts: {e}")
    return False

if __name__ == "__main__":
    # Define the path to the test database used by the examples
    TEST_DB = Path("./temp_thumb_test.db")

    # Ensure prerequisite data exists
    print("--- Setting up Test Environment --- ")
    if not run_prerequisites():
        print("\n[Error] Could not set up test environment. Aborting TUI launch.")
        sys.exit(1)
    print("-----------------------------------")

    print("\n--- Starting TUI --- ")
    # Create an app instance specifically for testing, pointing to the test DB
    test_app = LoopSleuthApp()
    test_app.db_path = TEST_DB # Override the default DB path for this instance
    test_app.run()
    print("--------------------") 