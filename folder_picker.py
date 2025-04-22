#!/usr/bin/env python3
"""
Folder Picker Utility for LoopSleuth
- Opens a native folder picker dialog
- Copies the selected folder path to the clipboard (requires pyperclip)
- Prints the path to the terminal as a fallback

Usage:
    python folder_picker.py

If pyperclip is not installed, run:
    pip install pyperclip
"""
import sys
import tkinter as tk
from tkinter import filedialog

try:
    import pyperclip
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False

root = tk.Tk()
root.withdraw()
folder = filedialog.askdirectory(title="Select a folder to scan with LoopSleuth")
if folder:
    if HAS_CLIP:
        pyperclip.copy(folder)
        print(f"[LoopSleuth] Folder path copied to clipboard:\n{folder}")
    else:
        print(f"[LoopSleuth] Folder path (install pyperclip for clipboard support):\n{folder}")
else:
    print("[LoopSleuth] No folder selected.") 