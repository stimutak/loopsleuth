"""Textual User Interface for LoopSleuth."""

import sys
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import os

# Adjust import path
SCRIPTS_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPTS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static, Input
from textual.reactive import reactive
from textual.events import Key
from textual.screen import ModalScreen

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

        # --- Add Logging --- 
        self.log(f"ClipGrid loaded {len(clips)} clips from DB.")
        # --- End Logging ---
        if clips:
            # Mount all cards first
            yielded_cards = [ClipCard(clip_data=clip) for clip in clips]
            self.mount_all(yielded_cards)
        else:
            self.mount(Static("No clips found in the database."))


class EditTagsScreen(ModalScreen[str]):
    """A modal screen for editing clip tags."""

    # Store the clip ID and original widget to update later
    clip_id: int
    original_widget: ClipCard

    DEFAULT_CSS = """
    EditTagsScreen {
        align: center middle;
    }

    #edit-tags-container {
        width: 80%;
        height: auto;
        border: thick $primary;
        background: $surface;
    }

    #tags-input {
        margin: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel_edit", "Cancel"),
        # ("enter", "submit_edit", "Submit") # Input handles enter by default
    ]

    def __init__(self, clip_id: int, current_tags: str, original_widget: ClipCard, **kwargs):
        super().__init__(**kwargs)
        self.clip_id = clip_id
        self.current_tags = current_tags
        self.original_widget = original_widget

    def compose(self) -> ComposeResult:
        with Container(id="edit-tags-container"):
            yield Static("Edit tags (comma-separated), press Enter to submit, Escape to cancel:")
            yield Input(
                value=self.current_tags,
                placeholder="tag1, tag2, ...",
                id="tags-input"
            )

    def on_mount(self) -> None:
        """Focus the input field when the screen is mounted."""
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle the submission of the input field."""
        new_tags = event.value.strip() # Get the entered value
        # Optional: normalize tags (e.g., lowercase, remove extra spaces)
        new_tags = ", ".join(t.strip() for t in new_tags.split(",") if t.strip())
        self.dismiss(new_tags) # Dismiss the screen and return the new tags

    def action_cancel_edit(self) -> None:
        """Handle cancellation."""
        self.dismiss(self.current_tags) # Dismiss and return original tags


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
    """ + ClipGrid.DEFAULT_CSS + ClipCard.DEFAULT_CSS + EditTagsScreen.DEFAULT_CSS

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("r", "refresh_grid", "Refresh Grid"),
        ("space", "toggle_star", "Toggle Star"),
        ("t", "edit_tags", "Edit Tags"),
    ]

    # Store DB path for the app instance
    db_path: Path

    def __init__(self, db_path: Path = DEFAULT_DB_PATH, **kwargs):
        """Initialize the app, ensuring base class init and setting DB path."""
        super().__init__(**kwargs)
        self.db_path = db_path

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(ClipGrid(db_path=self.db_path, id="clip-grid"), id="main-container")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """Toggle dark mode (Currently may be unstable in v3.1.0)."""
        # Attempt to toggle dark mode, but catch potential errors
        try:
            self.dark = not self.dark
        except Exception as e:
            # Log if possible, notify user
            try:
                self.log.error(f"Failed to toggle dark mode: {e}")
            except Exception:
                pass # Logging might also fail
            self.notify(f"Error toggling dark mode: {e}", severity="error")

    def action_refresh_grid(self) -> None:
        """Reload clips in the grid."""
        try:
            grid = self.query_one(ClipGrid)
            grid.load_clips()
            self.notify("Clip grid refreshed.")
        except Exception as e:
            self.notify(f"Error refreshing grid: {e}", severity="error")
            print(f"Error refreshing grid: {e}", file=sys.stderr)

    def action_toggle_star(self) -> None:
        """Toggle the starred status of the currently focused clip."""
        focused_widget = self.focused
        if isinstance(focused_widget, ClipCard) and focused_widget.clip_data:
            clip_id = focused_widget.clip_data.get('id')
            current_starred = focused_widget.clip_data.get('starred', False)
            new_starred = not current_starred

            if clip_id is None:
                self.notify("Cannot star clip: Missing ID.", severity="error")
                return

            conn = None
            try:
                conn = get_db_connection(self.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE clips SET starred = ? WHERE id = ?", (new_starred, clip_id))
                conn.commit()

                # Update the widget's reactive data to refresh display
                # Create a copy, modify, and reassign to trigger reactivity
                updated_data = focused_widget.clip_data.copy()
                updated_data['starred'] = new_starred
                focused_widget.clip_data = updated_data

                status = "Starred" if new_starred else "Unstarred"
                self.notify(f"{status}: {focused_widget.clip_data.get('filename', '?')}")

            except sqlite3.Error as e:
                self.notify(f"Database error toggling star: {e}", severity="error")
                print(f"Database error toggling star for ID {clip_id}: {e}", file=sys.stderr)
            except Exception as e:
                self.notify(f"Error toggling star: {e}", severity="error")
                print(f"Error toggling star for ID {clip_id}: {e}", file=sys.stderr)
            finally:
                if conn:
                    conn.close()
        elif focused_widget:
             self.notify(f"Cannot star: Focused item is not a ClipCard ({type(focused_widget).__name__})")
        else:
             self.notify("Cannot star: No clip selected.")

    def action_edit_tags(self) -> None:
        """Open the modal screen to edit tags for the focused clip."""
        focused_widget = self.focused
        if isinstance(focused_widget, ClipCard) and focused_widget.clip_data:
            clip_id = focused_widget.clip_data.get('id')
            current_tags = focused_widget.clip_data.get('tags', '')

            if clip_id is None:
                self.notify("Cannot edit tags: Clip missing ID.", severity="error")
                return

            def check_edit_result(new_tags: str):
                """Callback function to handle the result from EditTagsScreen."""
                if new_tags != current_tags: # Only update if changed
                    self.update_tags_in_db(clip_id, new_tags, focused_widget)

            # Push the modal screen, passing necessary data and the callback
            self.push_screen(
                EditTagsScreen(
                    clip_id=clip_id,
                    current_tags=current_tags,
                    original_widget=focused_widget
                ),
                check_edit_result # Pass the callback function
            )
        elif focused_widget:
             self.notify(f"Cannot edit tags: Focused item is not a ClipCard ({type(focused_widget).__name__})")
        else:
             self.notify("Cannot edit tags: No clip selected.")

    def update_tags_in_db(self, clip_id: int, new_tags: str, widget_to_update: ClipCard):
        """Update the tags for a given clip ID in the database and refresh the widget."""
        conn = None
        try:
            conn = get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE clips SET tags = ? WHERE id = ?", (new_tags, clip_id))
            conn.commit()

            # Update the widget's reactive data
            if widget_to_update.clip_data:
                updated_data = widget_to_update.clip_data.copy()
                updated_data['tags'] = new_tags
                widget_to_update.clip_data = updated_data
                self.notify(f"Tags updated for clip ID {clip_id}")
            else:
                 self.notify(f"DB updated for {clip_id}, but widget data missing?", severity="warning")

        except sqlite3.Error as e:
            self.notify(f"Database error updating tags: {e}", severity="error")
            print(f"Database error updating tags for ID {clip_id}: {e}", file=sys.stderr)
        except Exception as e:
            self.notify(f"Error updating tags: {e}", severity="error")
            print(f"Error updating tags for ID {clip_id}: {e}", file=sys.stderr)
        finally:
            if conn:
                conn.close()


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
    prereqs_ok = run_prerequisites()
    if not prereqs_ok:
        print("\n[Error] Could not set up test environment. Aborting TUI launch.")
        sys.exit(1)

    # --- Manually add a second clip for testing navigation --- 
    # Assuming prerequisites ran and created the first clip & thumb/hash
    # Assumes you copied 'test_clip.mp4' to 'test_clip_copy.mp4' in temp_thumb_test/
    second_clip_name = "test_clip_copy.mp4"
    second_clip_path = Path("./temp_thumb_test") / second_clip_name
    if second_clip_path.exists():
        conn_add = None
        try:
            conn_add = get_db_connection(TEST_DB)
            cursor_add = conn_add.cursor()
            # Check if it already exists (to avoid duplicate entries on re-runs)
            cursor_add.execute("SELECT 1 FROM clips WHERE filename = ?", (second_clip_name,))
            if cursor_add.fetchone() is None:
                # Use metadata from the first clip for simplicity, only change path/filename
                cursor_add.execute("SELECT duration, thumbnail_path, phash FROM clips LIMIT 1")
                first_clip_meta = cursor_add.fetchone()
                if first_clip_meta:
                    cursor_add.execute("""
                        INSERT INTO clips (path, filename, duration, thumbnail_path, phash)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(second_clip_path.resolve()),
                        second_clip_name,
                        first_clip_meta['duration'],
                        first_clip_meta['thumbnail_path'], # Reuse thumb for simplicity
                        first_clip_meta['phash'] # Reuse hash for simplicity
                    ))
                    conn_add.commit()
                    print(f"Manually added second clip '{second_clip_name}' to test DB for UI testing.")
                else:
                    print("Warning: Could not find first clip's metadata to copy for second clip.")
            # else: Already exists, do nothing
        except sqlite3.Error as e:
            print(f"Warning: Database error adding second clip for testing: {e}")
        except Exception as e:
             print(f"Warning: Error adding second clip for testing: {e}")
        finally:
            if conn_add:
                conn_add.close()
    else:
        print(f"Warning: Second test clip '{second_clip_path}' not found. Cannot add to DB for UI testing.")
    # --- End manual clip addition --- 

    print("-----------------------------------")

    print("\n--- Starting TUI --- ")
    # Instantiate the app directly, passing the test DB path
    test_app = LoopSleuthApp(db_path=TEST_DB)
    test_app.run()
    print("--------------------") 