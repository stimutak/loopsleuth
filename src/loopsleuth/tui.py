"""Textual User Interface for LoopSleuth."""

import sys
from pathlib import Path

# Adjust import path
SCRIPTS_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPTS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static, Placeholder

# from loopsleuth.db import get_db_connection, DEFAULT_DB_PATH

class LoopSleuthApp(App):
    """The main Textual application for LoopSleuth."""

    CSS_PATH = "tui.css" # We'll create this file next
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        # Add other global bindings here (e.g., scan, process thumbs/hashes)
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        # Main content area - will hold the grid view later
        yield Container(
            Placeholder("Clip Grid Area") # Placeholder for now
        )
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    # Create a dummy DB for testing if it doesn't exist
    # from loopsleuth.db import get_db_connection, DEFAULT_DB_PATH
    # conn = get_db_connection(DEFAULT_DB_PATH)
    # conn.close()
    # print(f"Ensured database exists at {DEFAULT_DB_PATH}")

    app = LoopSleuthApp()
    app.run() 