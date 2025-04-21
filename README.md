# LoopSleuth

A terminal‑first librarian for video loops.

## Why
- Thumbnail & metadata view for huge DXV/H.264 clip libraries
- ⭐ flag keepers, tag with free text, delete duds
- Export a `keepers.txt` list for a TouchDesigner Replicator

## MVP (v0.1)
1. **Scan**: walk folder → SQLite row per clip (`ffprobe`)
2. **Thumb**: grab frame @ 25 % duration → 256 px JPEG
3. **Hash**: perceptual pHash → find near‑dupes later
4. **TUI**: Textual grid  
   - <Space> toggle star  
   - `t` edit tags  
   - `d` delete
5. **Export**: write `keepers.txt` with starred clip paths

_Stretch_: duplicate‑collapse, CLIP auto‑tags, .tox export.

## Tech
Python ≥ 3.10, ffmpeg/ffprobe, SQLite, Pillow, imagehash, Textual, Typer.

