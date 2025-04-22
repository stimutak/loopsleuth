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
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button
from textual.reactive import reactive
from textual.events import Key
from textual.screen import ModalScreen

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
    """ + ClipGrid.DEFAULT_CSS + ClipCard.DEFAULT_CSS + EditTagsScreen.DEFAULT_CSS + ConfirmDeleteScreen.DEFAULT_CSS

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
        yield Container(ClipGrid(db_path=self.db_path, id="clip-grid"), id="main-container")
        yield Footer()

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

    def action_request_delete(self) -> None:
        """Request confirmation to delete the focused clip."""
        focused_widget = self.focused
        if isinstance(focused_widget, ClipCard) and focused_widget.clip_data:
            clip_id = focused_widget.clip_data.get('id')
            filename = focused_widget.clip_data.get('filename', '?')

            if clip_id is None:
                self.notify("Cannot delete clip: Missing ID.", severity="error")
                return

            def handle_delete_confirmation(confirmed: bool):
                """Callback for the delete confirmation modal."""
                if confirmed:
                    self.log(f"Deletion confirmed for clip ID {clip_id}")
                    self.delete_clip(clip_id, focused_widget)
                else:
                    self.log(f"Deletion cancelled for clip ID {clip_id}")
                    self.notify("Deletion cancelled.")

            # Push the confirmation screen
            self.push_screen(
                ConfirmDeleteScreen(
                    clip_id=clip_id,
                    clip_filename=filename,
                    clip_widget=focused_widget
                ),
                handle_delete_confirmation
            )

        elif focused_widget:
            self.notify(f"Cannot delete: Focused item is not a ClipCard ({type(focused_widget).__name__})")
        else:
            self.notify("Cannot delete: No clip selected.")

    def action_export_starred(self) -> None:
        """Export starred clip paths to a file."""
        # Define output file path (e.g., in the current directory)
        output_filename = "keepers.txt"
        # For the test environment, write next to the test DB
        output_path = self.db_path.parent / output_filename 
        # For a real install, you might want CWD: output_path = Path.cwd() / output_filename

        self.log(f"Attempting export to {output_path}")
        success, message = export_starred_clips(self.db_path, output_path)

        if success:
            self.notify(message, title="Export Complete", severity="information")
        else:
            self.notify(message, title="Export Failed", severity="error")
            print(f"Export Error: {message}", file=sys.stderr)

    def delete_clip(self, clip_id: int, clip_widget: ClipCard):
        """Deletes the clip record, video file, and thumbnail file."""
        if not clip_widget.clip_data:
            self.notify(f"Cannot delete clip {clip_id}: Widget data missing.", severity="error")
            return

        # We need the video file path and thumbnail path
        path_str = None
        thumb_path_rel = clip_widget.clip_data.get('thumbnail_path')

        conn_get_path = None
        try:
            # Get full video path from DB as it might not be in clip_data
            conn_get_path = get_db_connection(self.db_path)
            cursor_get_path = conn_get_path.cursor()
            cursor_get_path.execute("SELECT path FROM clips WHERE id = ?", (clip_id,))
            result = cursor_get_path.fetchone()
            if result:
                path_str = result['path']
            else:
                self.notify(f"Cannot find DB record for clip ID {clip_id} to get path.", severity="error")
                return
        except sqlite3.Error as e:
            self.notify(f"DB error getting path for clip {clip_id}: {e}", severity="error")
            return
        finally:
            if conn_get_path: conn_get_path.close()

        if not path_str:
            self.notify(f"Cannot delete clip {clip_id}: Video path not found.", severity="error")
            return

        video_file = Path(path_str)
        thumb_file = None
        if thumb_path_rel:
            # Thumbnails stored relative to DB file's parent directory
            thumb_file = self.db_path.parent / thumb_path_rel

        # --- Perform Deletions --- 
        errors = []
        # 1. Delete video file
        try:
            if video_file.exists():
                video_file.unlink()
                self.log(f"Deleted video file: {video_file}")
            else:
                self.log.warning(f"Video file not found for deletion: {video_file}")
        except OSError as e:
            errors.append(f"Error deleting video file {video_file}: {e}")
            self.log.error(f"Error deleting video file: {e}")

        # 2. Delete thumbnail file
        if thumb_file:
            try:
                if thumb_file.exists():
                    thumb_file.unlink()
                    self.log(f"Deleted thumbnail file: {thumb_file}")
                else:
                     self.log.warning(f"Thumbnail file not found for deletion: {thumb_file}")
            except OSError as e:
                errors.append(f"Error deleting thumbnail file {thumb_file}: {e}")
                self.log.error(f"Error deleting thumbnail file: {e}")

        # 3. Delete database record
        conn_delete = None
        try:
            conn_delete = get_db_connection(self.db_path)
            cursor_delete = conn_delete.cursor()
            cursor_delete.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
            conn_delete.commit()
            self.log(f"Deleted DB record for clip ID {clip_id}")
        except sqlite3.Error as e:
            errors.append(f"Error deleting DB record for clip ID {clip_id}: {e}")
            self.log.error(f"Error deleting DB record: {e}")
        finally:
            if conn_delete: conn_delete.close()

        # --- Update UI --- 
        try:
             clip_widget.remove()
             self.notify(f"Removed clip {clip_id} from view.")
        except Exception as e:
             errors.append(f"Error removing widget for clip {clip_id}: {e}")
             self.log.error(f"Error removing widget: {e}")

        # --- Report outcome --- 
        if not errors:
             self.notify(f"Successfully deleted clip {clip_id} ({clip_widget.clip_data.get('filename', '?')}).", title="Deletion Complete")
        else:
             self.notify("Deletion completed with errors. See log/console.", title="Deletion Error", severity="error")
             print("[Delete Errors]:\n" + "\n".join(errors), file=sys.stderr)

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