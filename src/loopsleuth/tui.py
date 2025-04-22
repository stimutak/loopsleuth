"""Textual User Interface for LoopSleuth."""

import sys
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os

# Adjust import path
SCRIPTS_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPTS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button
from textual.reactive import reactive
from textual.events import Key
from textual.screen import ModalScreen
from textual import events # Import events
from textual.geometry import Region # Import Region

# Import database functions and default path
from loopsleuth.db import get_db_connection, DEFAULT_DB_PATH
# Import the exporter function
from loopsleuth.exporter import export_starred_clips


class ClipCard(Static):
    """Widget to display information about a single video clip."""

    # Store the raw clip data dictionary
    clip_data = reactive[Optional[Dict[str, Any]]](None)

    DEFAULT_CSS = """
    ClipCard {
        border: round $primary;
        /* Fixed height is important for scroll calculation */
        height: 12; # Reduced height as there's no image placeholder needed now
        layout: vertical;
        padding: 1;
        margin: 1;
        width: 1fr;
        /* Add transition for smoother loading appearance */
        transition: opacity 300ms linear;
    }
    ClipCard > Static#info-text { /* Style the text part */
        height: auto;
        width: 100%;
    }
    ClipCard:focus {
        border: thick $accent;
        background: $accent-darken-1;
    }
    """

    def __init__(self, clip_id: int, clip_data: Dict[str, Any], **kwargs):
        # Assign a unique ID for easier querying
        super().__init__(id=f"clip-card-{clip_id}", **kwargs)
        # Set clip_data only after super().__init__ to trigger reactive update
        self.clip_data = clip_data
        self.can_focus = True # Make cards focusable

    def compose(self) -> ComposeResult:
        """Compose the clip card with text info."""
        if not self.clip_data:
            yield Static("[b]Error:[/b] No data.")
            return # Stop composing if no data

        # Safely get data
        clip_id = self.clip_data.get('id', 'N/A')
        filename = self.clip_data.get('filename', 'Unknown')
        starred = self.clip_data.get('starred', False)
        tags = self.clip_data.get('tags', '')

        star_icon = "[b green]★[/]" if starred else "[dim]☆[/]"
        tags_display = f"Tags: {tags}" if tags else "Tags: --"

        # Just yield the text information
        yield Static(
            f"[b]{filename}[/b]\n"
            f"{star_icon} ID: {clip_id}\n"
            f"{tags_display}",
            id="info-text" # Add ID for clarity
        )

    def update_display(self):
        """Updates the text info part of the card."""
        # Find the info Static widget and update its content
        info_static = self.query_one("#info-text", Static)

        # Rebuild the text content based on potentially updated self.clip_data
        if self.clip_data:
            clip_id = self.clip_data.get('id', 'N/A')
            filename = self.clip_data.get('filename', 'Unknown')
            starred = self.clip_data.get('starred', False)
            tags = self.clip_data.get('tags', '')
            star_icon = "[b green]★[/]" if starred else "[dim]☆[/]"
            tags_display = f"Tags: {tags}" if tags else "Tags: --"

            info_static.update(
                f"[b]{filename}[/b]\n"
                f"{star_icon} ID: {clip_id}\n"
                f"{tags_display}"
            )
        else:
            info_static.update("[b]Error:[/b] No data.")


class ClipGrid(VerticalScroll):
    """A scrollable container displaying ClipCards in a grid layout."""

    DEFAULT_CSS = """
    ClipGrid {
        layout: grid;
        grid-size: 3; /* Number of columns */
        grid-gutter: 1 2; /* Vertical and horizontal spacing */
        padding: 1;
    }
    """
    # Store all clip data separately from mounted widgets
    all_clips_data: List[Dict[str, Any]] = []
    # Store grid geometry - Assume fixed for now, could be dynamic
    grid_cols: int = 3
    card_height: int = 14 # Approx. height (ClipCard height 12 + margin 1*2)

    def __init__(self, db_path: Path = DEFAULT_DB_PATH, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

    def on_mount(self) -> None:
        """Load metadata and mount placeholder cards when the widget is mounted."""
        self.load_clips_metadata()
        self.mount_all_cards_unloaded()

    def load_clips_metadata(self):
        """Query the database for clip metadata only."""
        self.all_clips_data = [] # Clear previous data
        conn = None
        try:
            conn = get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, thumbnail_path, starred, tags
                FROM clips
                ORDER BY filename ASC
            """)
            # Fetch all rows as dictionaries
            keys = [description[0] for description in cursor.description]
            self.all_clips_data = [dict(zip(keys, row)) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            self.app.push_screen(ErrorScreen(f"Database Error loading metadata:\n{e}"))
            print(f"Database error loading clips: {e}", file=sys.stderr)
        except Exception as e:
            self.app.push_screen(ErrorScreen(f"Unexpected Error loading metadata:\n{e}"))
            print(f"Unexpected error loading clips: {e}", file=sys.stderr)
        finally:
            if conn:
                conn.close()

    def mount_all_cards_unloaded(self):
        """Mount ClipCard widgets for all clips, but without loading images."""
        self.remove_children() # Clear any existing widgets (like error messages)
        if self.all_clips_data:
            cards = [
                ClipCard(clip_id=clip['id'], clip_data=clip)
                for clip in self.all_clips_data
            ]
            self.mount(*cards) # Mount all cards
        else:
            self.mount(Static("No clips found in the database."))

    def on_resize(self, event: events.Resize) -> None:
        """Handles resize events."""
        # Future: could dynamically adjust grid_cols here
        pass # No action needed currently as image loading removed


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


class ConfirmDeleteScreen(ModalScreen[bool]):
    """A modal screen to confirm deletion."""

    # Store info about the clip to be deleted
    clip_id: int
    clip_filename: str
    clip_widget: ClipCard # Keep track of the widget to remove

    DEFAULT_CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }
    #confirm-delete-container {
        width: 60; /* Set a fixed width */
        max-width: 80%; /* But don't allow it to exceed 80% screen width */
        height: auto;
        padding: 1 2;
        border: thick $error;
        background: $surface;
    }
    #confirm-delete-buttons {
        width: 100%;
        align-horizontal: right;
        padding-top: 1;
    }
    Button {
        margin-left: 2;
    }
    """

    def __init__(self, clip_id: int, clip_filename: str, clip_widget: ClipCard, **kwargs):
        super().__init__(**kwargs)
        self.clip_id = clip_id
        self.clip_filename = clip_filename
        self.clip_widget = clip_widget

    def compose(self) -> ComposeResult:
        with Container(id="confirm-delete-container"):
            yield Static(f"Permanently delete clip \'{self.clip_filename}\' (ID: {self.clip_id})?")
            yield Static("This will delete the database record, video file, and thumbnail.")
            with Horizontal(id="confirm-delete-buttons"):
                yield Button("Yes, Delete", variant="error", id="confirm-delete-yes")
                yield Button("No, Cancel", variant="primary", id="confirm-delete-no")

    def on_mount(self) -> None:
        """Focus the 'No' button by default."""
        self.query_one("#confirm-delete-no").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "confirm-delete-yes":
            self.dismiss(True) # Return True to confirm deletion
        else:
            self.dismiss(False) # Return False to cancel


class ErrorScreen(ModalScreen[None]):
    """Modal screen to display errors."""
    def __init__(self, error_message: str, **kwargs):
        super().__init__(**kwargs)
        self.error_message = error_message

    DEFAULT_CSS = """
    ErrorScreen {
        align: center middle;
    }
    #error-container {
        width: auto;
        max-width: 80%;
        height: auto;
        max-height: 80%;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    #error-message { margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"[b red]Error[/]:", id="error-title"),
            Static(self.error_message, id="error-message"),
            Button("OK", variant="primary", id="error-ok"),
            id="error-container"
        )

    def on_mount(self) -> None:
        self.query_one("#error-ok", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


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
    """ + ClipGrid.DEFAULT_CSS + ClipCard.DEFAULT_CSS + EditTagsScreen.DEFAULT_CSS + ConfirmDeleteScreen.DEFAULT_CSS + ErrorScreen.DEFAULT_CSS

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "request_delete", "Delete Clip"),
        ("r", "refresh_grid", "Refresh Grid"),
        ("space", "toggle_star", "Toggle Star"),
        ("t", "edit_tags", "Edit Tags"),
        ("e", "export_starred", "Export Starred"),
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
        yield Container(
            ClipGrid(db_path=self.db_path), # Pass db_path
            id="main-container"
        )
        yield Footer()

    def action_refresh_grid(self) -> None:
        """Refreshes the grid by reloading metadata and remounting cards."""
        self.log("Refreshing grid...") # Add log
        grid = self.query_one(ClipGrid)
        # Clear focus first to avoid issues if focused element is removed
        self.screen.set_focus(None)
        grid.load_clips_metadata()
        grid.mount_all_cards_unloaded()
        # Try focusing the grid itself after refresh
        self.set_timer(0.1, lambda: self.screen.set_focus(grid))

    def action_toggle_star(self) -> None:
        """Toggle the starred status of the currently focused clip."""
        try:
            focused_widget = self.query_one("ClipCard:focus")
            if focused_widget and isinstance(focused_widget, ClipCard):
                clip_id = focused_widget.clip_data.get('id')
                current_star_status = focused_widget.clip_data.get('starred', False)
                if clip_id is not None:
                    # Optimistically update UI first
                    new_star_status = not current_star_status
                    # Create a *copy* of the data and update it
                    updated_data = focused_widget.clip_data.copy()
                    updated_data['starred'] = new_star_status
                    # Assign the new dictionary back to trigger reactive update
                    focused_widget.clip_data = updated_data
                    # Explicitly tell the card to update its text display
                    focused_widget.update_display()

                    # Then, update the database
                    self.update_star_in_db(clip_id, new_star_status, focused_widget)
            else:
                self.log("No ClipCard focused to toggle star.")
        except Exception as e:
            self.log(f"Error toggling star: {e}")
            self.app.push_screen(ErrorScreen(f"Error toggling star:\n{e}"))

    def action_edit_tags(self) -> None:
        """Open the modal screen to edit tags for the focused clip."""
        try:
            focused_widget = self.query_one("ClipCard:focus")
            if focused_widget and isinstance(focused_widget, ClipCard):
                clip_id = focused_widget.clip_data.get('id')
                current_tags = focused_widget.clip_data.get('tags', '')
                if clip_id is not None:
                    # Define callback to handle result from modal
                    def check_edit_result(new_tags: str):
                        if new_tags is not None: # Check if submit vs cancel
                            self.log(f"Updating tags for clip {clip_id} to: {new_tags}")
                            # Update DB and the original widget's data
                            self.update_tags_in_db(clip_id, new_tags, focused_widget)

                    # Push the modal screen
                    self.push_screen(
                        EditTagsScreen(clip_id, current_tags, focused_widget),
                        check_edit_result
                    )
            else:
                self.log("No ClipCard focused to edit tags.")
        except Exception as e:
            self.log(f"Error initiating tag edit: {e}")
            self.app.push_screen(ErrorScreen(f"Error initiating tag edit:\n{e}"))

    def action_request_delete(self) -> None:
        """Request confirmation to delete the focused clip."""
        try:
            focused_widget = self.query_one("ClipCard:focus")
            if focused_widget and isinstance(focused_widget, ClipCard):
                clip_id = focused_widget.clip_data.get('id')
                clip_filename = focused_widget.clip_data.get('filename', 'Unknown')
                if clip_id is not None:
                    # Define callback
                    def handle_delete_confirmation(confirmed: bool):
                        if confirmed:
                            self.log(f"Confirmed deletion for clip {clip_id}")
                            self.delete_clip(clip_id, focused_widget)
                        else:
                            self.log("Deletion cancelled.")

                    # Push confirmation screen
                    self.push_screen(
                        ConfirmDeleteScreen(clip_id, clip_filename, focused_widget),
                        handle_delete_confirmation
                    )
            else:
                self.log("No ClipCard focused to delete.")
        except Exception as e:
            self.log(f"Error initiating delete request: {e}")
            self.app.push_screen(ErrorScreen(f"Error initiating delete request:\n{e}"))

    def action_export_starred(self) -> None:
        """Export starred clip paths to a file."""
        try:
            output_file = Path("keepers.txt") # Or make configurable
            export_starred_clips(self.db_path, output_file)
            self.log(f"Exported starred clips to {output_file}")
            # Maybe show a notification? Textual doesn't have built-in popups easily
            # For now, log is sufficient. Could add a temporary status message.
            self.bell() # Simple notification
        except Exception as e:
            self.log(f"Error exporting starred clips: {e}")
            self.app.push_screen(ErrorScreen(f"Error exporting starred clips:\n{e}"))

    async def delete_clip(self, clip_id: int, clip_widget: ClipCard):
        """Deletes a clip from the database and filesystem, then removes its card."""
        conn = None
        clip_path_str = None
        thumb_path_str = None

        # --- 1. Get paths from the widget's data before deleting from DB ---
        if clip_widget.clip_data:
             # Use .get() for safety
            clip_path_str = clip_widget.clip_data.get("filepath") # Assuming 'filepath' is stored
            thumb_path_str = clip_widget.clip_data.get("thumbnail_path")

        # --- If filepath wasn't in the widget data, query the DB ---
        if not clip_path_str:
            try:
                conn = get_db_connection(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT filepath, thumbnail_path FROM clips WHERE id = ?", (clip_id,))
                result = cursor.fetchone()
                if result:
                    clip_path_str = result["filepath"]
                    thumb_path_str = result["thumbnail_path"]
                else:
                    self.log(f"Could not find clip {clip_id} in DB to get filepath.")
                    # Optionally show error, but proceed to delete DB entry anyway
            except sqlite3.Error as e:
                self.log(f"Database error fetching clip path for deletion: {e}")
                self.app.push_screen(ErrorScreen(f"DB Error getting path for delete:\n{e}"))
                # Decide if we should stop here or try to continue
                if conn: conn.close() # Ensure connection closed on error
                return # Stop deletion if we can't confirm paths
            finally:
                if conn and not conn.in_transaction: # Avoid closing if in transaction (shouldn't be here)
                    conn.close()
                    conn = None # Reset conn


        # --- 2. Delete from Database ---
        conn = None # Reset conn for the delete operation
        deleted_from_db = False
        try:
            conn = get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
            conn.commit()
            if cursor.rowcount > 0:
                self.log(f"Deleted clip {clip_id} from database.")
                deleted_from_db = True
            else:
                 self.log(f"Clip {clip_id} not found in database for deletion.")
                 # Treat as success if goal is removal, but log it.

        except sqlite3.Error as e:
            self.log(f"Database error deleting clip {clip_id}: {e}")
            self.app.push_screen(ErrorScreen(f"Database error deleting clip:\n{e}"))
            # Decide whether to proceed with file deletion if DB failed
        finally:
            if conn:
                conn.close()

        # --- 3. Delete Files (only if DB delete was attempted or successful) ---
        # Delete video file
        if clip_path_str:
            try:
                clip_path = Path(clip_path_str)
                if clip_path.exists():
                    clip_path.unlink()
                    self.log(f"Deleted video file: {clip_path}")
                else:
                    self.log(f"Video file not found, skipping deletion: {clip_path}")
            except OSError as e:
                self.log(f"Error deleting video file {clip_path}: {e}")
                self.app.push_screen(ErrorScreen(f"OS Error deleting video file:\n{e}"))
            except Exception as e: # Catch any other unexpected errors
                 self.log(f"Unexpected error deleting video file {clip_path}: {e}")
                 self.app.push_screen(ErrorScreen(f"Error deleting video file:\n{e}"))

        # Delete thumbnail file
        if thumb_path_str:
            try:
                thumb_path = Path(thumb_path_str)
                if thumb_path.exists():
                    thumb_path.unlink()
                    self.log(f"Deleted thumbnail file: {thumb_path}")
                else:
                    self.log(f"Thumbnail file not found, skipping deletion: {thumb_path}")
            except OSError as e:
                self.log(f"Error deleting thumbnail file {thumb_path}: {e}")
                self.app.push_screen(ErrorScreen(f"OS Error deleting thumbnail:\n{e}"))
            except Exception as e: # Catch any other unexpected errors
                 self.log(f"Unexpected error deleting thumbnail {thumb_path}: {e}")
                 self.app.push_screen(ErrorScreen(f"Error deleting thumbnail:\n{e}"))


        # --- 4. Remove the widget from the UI ---
        try:
            # Find the grid to update its internal list
            grid = self.query_one(ClipGrid)
            # Remove the clip from the grid's internal data list
            grid.all_clips_data = [c for c in grid.all_clips_data if c.get('id') != clip_id]

            await clip_widget.remove() # Use await for async remove
            self.log(f"Removed ClipCard widget for clip {clip_id}.")
            # Optionally, refocus the grid or the next/previous element
            self.set_timer(0.1, lambda: self.screen.set_focus(grid))
        except Exception as e:
             self.log(f"Error removing clip widget {clip_id}: {e}")
             # The item might already be gone, or focus issues. Grid refresh might fix.

    def update_star_in_db(self, clip_id: int, new_star_status: bool, widget_to_update: ClipCard):
        """Updates the starred status for a clip in the database and refreshes the widget."""
        conn = None
        try:
            conn = get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE clips SET starred = ? WHERE id = ?", (new_star_status, clip_id))
            conn.commit()
            self.log(f"Updated star status for clip {clip_id} to {new_star_status} in DB.")
            # Update the widget's internal data *after* successful DB commit
            # Create a new dict to ensure reactivity works
            updated_data = widget_to_update.clip_data.copy()
            updated_data['starred'] = new_star_status
            widget_to_update.clip_data = updated_data
            # Explicitly tell the card to update its display text
            widget_to_update.update_display()

        except sqlite3.Error as e:
            self.log(f"Database error updating star status for clip {clip_id}: {e}")
            self.app.push_screen(ErrorScreen(f"Database error updating star:\n{e}"))
            # Revert optimistic UI update on failure
            # Create a new dict to ensure reactivity works
            reverted_data = widget_to_update.clip_data.copy()
            reverted_data['starred'] = not new_star_status # Set back to original
            widget_to_update.clip_data = reverted_data
            widget_to_update.update_display() # Update display back
        finally:
            if conn:
                conn.close()

    def update_tags_in_db(self, clip_id: int, new_tags: str, widget_to_update: ClipCard):
        """Updates tags for a clip in the database and refreshes the widget."""
        conn = None
        original_tags = widget_to_update.clip_data.get('tags', '') # Store original for revert
        try:
            conn = get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE clips SET tags = ? WHERE id = ?", (new_tags, clip_id))
            conn.commit()
            self.log(f"Updated tags for clip {clip_id} to '{new_tags}' in DB.")
            # Update the widget's internal data *after* successful DB commit
            # Create a new dict to ensure reactivity works
            updated_data = widget_to_update.clip_data.copy()
            updated_data['tags'] = new_tags
            widget_to_update.clip_data = updated_data
            # Explicitly tell the card to update its display text
            widget_to_update.update_display()

        except sqlite3.Error as e:
            self.log(f"Database error updating tags for clip {clip_id}: {e}")
            self.app.push_screen(ErrorScreen(f"Database error updating tags:\n{e}"))
            # Revert optimistic UI update on failure (though we didn't do one here)
            # It's good practice to ensure the widget reflects DB state if possible
            # If the update failed, the widget should ideally show original_tags
            # Create a new dict to ensure reactivity works
            reverted_data = widget_to_update.clip_data.copy()
            reverted_data['tags'] = original_tags # Revert to original tags visually
            widget_to_update.clip_data = reverted_data
            widget_to_update.update_display()
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
                cursor_add.execute("SELECT duration, thumbnail_path, phash, path FROM clips LIMIT 1") # Added path
                first_clip_meta = cursor_add.fetchone()
                if first_clip_meta:
                    # Construct a plausible unique path for the copy
                    original_path = Path(first_clip_meta['path'])
                    new_path = original_path.parent / second_clip_name # Use the new filename
                    
                    # Use a different thumbnail path to avoid deleting the same one twice
                    original_thumb_rel = first_clip_meta['thumbnail_path']
                    new_thumb_rel = None
                    if original_thumb_rel:
                        thumb_p = Path(original_thumb_rel)
                        new_thumb_rel = str(thumb_p.with_stem(f"{thumb_p.stem}_copy"))
                    
                    cursor_add.execute("""
                        INSERT INTO clips (path, filename, duration, thumbnail_path, phash)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(new_path.resolve()), # Use constructed new path
                        second_clip_name,
                        first_clip_meta['duration'],
                        new_thumb_rel, # Use new thumb path if available
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