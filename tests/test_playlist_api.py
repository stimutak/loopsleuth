import os
import sys
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Ensure project root is in sys.path for src imports
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the FastAPI app
from loopsleuth.web.app import app, get_db_connection, get_default_db_path

@pytest.fixture(scope="function")
def temp_db(tmp_path):
    # Create a temp DB file and patch DEFAULT_DB_PATH
    db_path = tmp_path / "test_playlist.db"
    os.environ["LOOPSLEUTH_DB_PATH"] = str(db_path)
    # Patch the app's DEFAULT_DB_PATH if needed
    global DEFAULT_DB_PATH
    DEFAULT_DB_PATH = db_path
    # Ensure schema is created
    conn = get_db_connection(db_path)
    conn.close()
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()
    del os.environ["LOOPSLEUTH_DB_PATH"]

@pytest.fixture(scope="function")
def client(temp_db):
    return TestClient(app)

def test_playlist_crud_and_clips(client):
    # 1. Create playlist
    resp = client.post("/playlists", json={"name": "Test Playlist"})
    assert resp.status_code == 200
    playlist = resp.json()
    pid = playlist["id"]
    assert playlist["name"] == "Test Playlist"

    # 2. Rename playlist
    resp = client.patch(f"/playlists/{pid}", json={"name": "Renamed Playlist"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Playlist"

    # 3. List playlists
    resp = client.get("/playlists")
    assert resp.status_code == 200
    playlists = resp.json()["playlists"]
    assert any(p["id"] == pid for p in playlists)

    # 4. Add some clips to DB
    conn = get_db_connection(get_default_db_path())
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clips (path, filename) VALUES (?, ?)", ("/tmp/a.mp4", "a.mp4"))
    cid1 = cursor.lastrowid
    cursor.execute("INSERT INTO clips (path, filename) VALUES (?, ?)", ("/tmp/b.mp4", "b.mp4"))
    cid2 = cursor.lastrowid
    conn.commit()
    conn.close()

    # 5. Add clips to playlist
    resp = client.post(f"/playlists/{pid}/clips", json={"clip_ids": [cid1, cid2]})
    assert resp.status_code == 200
    assert set(resp.json()["added"]) == {cid1, cid2}

    # 6. Get playlist details (should include both clips, in order)
    resp = client.get(f"/playlists/{pid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == pid
    assert [c["id"] for c in data["clips"]] == [cid1, cid2]

    # 7. Reorder clips
    resp = client.patch(f"/playlists/{pid}/reorder", json={"clip_ids": [cid2, cid1]})
    assert resp.status_code == 200
    assert resp.json()["order"] == [cid2, cid1]
    # Confirm order
    resp = client.get(f"/playlists/{pid}")
    assert [c["id"] for c in resp.json()["clips"]] == [cid2, cid1]

    # 8. Remove a clip
    resp = client.post(f"/playlists/{pid}/clips/remove", json={"clip_ids": [cid1]})
    assert resp.status_code == 200
    assert cid1 in resp.json()["removed"]
    # Confirm only one clip left
    resp = client.get(f"/playlists/{pid}")
    assert [c["id"] for c in resp.json()["clips"]] == [cid2]

    # 9. Delete playlist
    resp = client.delete(f"/playlists/{pid}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
    # Confirm gone
    resp = client.get(f"/playlists/{pid}")
    assert resp.status_code == 404

def test_playlist_errors(client):
    # Non-existent playlist
    resp = client.get("/playlists/99999")
    assert resp.status_code == 404
    resp = client.patch("/playlists/99999", json={"name": "x"})
    assert resp.status_code == 404
    resp = client.delete("/playlists/99999")
    assert resp.status_code == 404
    resp = client.post("/playlists/99999/clips", json={"clip_ids": [1]})
    # Should not error, but nothing added
    assert resp.status_code == 200
    resp = client.post("/playlists/99999/clips/remove", json={"clip_ids": [1]})
    assert resp.status_code == 200
    resp = client.patch("/playlists/99999/reorder", json={"clip_ids": [1]})
    assert resp.status_code == 200

# --- Additional Playlist Tests ---
def test_playlist_export_stub(client):
    # Create a playlist
    resp = client.post("/playlists", json={"name": "ExportTest"})
    assert resp.status_code == 200
    pid = resp.json()["id"]
    # Export as txt (should be 501 Not Implemented)
    resp = client.get(f"/playlists/{pid}/export?format=txt")
    assert resp.status_code == 501
    assert "not yet implemented" in resp.json()["message"].lower()
    # Export as zip (should be 501)
    resp = client.get(f"/playlists/{pid}/export?format=zip")
    assert resp.status_code == 501
    # Export as tox (should be 501)
    resp = client.get(f"/playlists/{pid}/export?format=tox")
    assert resp.status_code == 501

def test_playlist_duplicate_and_edge_cases(client):
    # Create playlist and add a clip
    resp = client.post("/playlists", json={"name": "EdgeCase"})
    assert resp.status_code == 200
    pid = resp.json()["id"]
    # Add a clip to DB
    conn = get_db_connection(get_default_db_path())
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clips (path, filename) VALUES (?, ?)", ("/tmp/edge.mp4", "edge.mp4"))
    cid = cursor.lastrowid
    conn.commit()
    conn.close()
    # Add the same clip twice
    resp = client.post(f"/playlists/{pid}/clips", json={"clip_ids": [cid]})
    assert resp.status_code == 200
    resp = client.post(f"/playlists/{pid}/clips", json={"clip_ids": [cid]})
    assert resp.status_code == 200
    # Should only appear once in playlist
    resp = client.get(f"/playlists/{pid}")
    assert resp.status_code == 200
    clips = resp.json()["clips"]
    assert [c["id"] for c in clips].count(cid) == 1
    # Remove a non-existent clip (should not error)
    resp = client.post(f"/playlists/{pid}/clips/remove", json={"clip_ids": [99999]})
    assert resp.status_code == 200
    # Reorder with missing/extra IDs (should only reorder existing)
    resp = client.patch(f"/playlists/{pid}/reorder", json={"clip_ids": [cid, 99999]})
    assert resp.status_code == 200
    # Playlist should still have only the real clip
    resp = client.get(f"/playlists/{pid}")
    assert resp.status_code == 200
    clips = resp.json()["clips"]
    assert [c["id"] for c in clips] == [cid] 