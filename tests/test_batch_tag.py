import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import shutil
import sqlite3
import uuid
import sys
from loopsleuth.web.app import app
from loopsleuth.db import get_db_connection, get_default_db_path

@pytest.fixture
def test_db_path(tmp_path, monkeypatch):
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    # Create minimal schema matching production (including NOT NULL path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE clips (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            path TEXT NOT NULL,
            duration REAL,
            thumbnail_path TEXT,
            starred INTEGER DEFAULT 0,
            phash TEXT
        )
    """)
    c.execute("CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
    c.execute("CREATE TABLE clip_tags (clip_id INTEGER, tag_id INTEGER, PRIMARY KEY (clip_id, tag_id))")
    conn.commit()
    conn.close()
    monkeypatch.setenv("LOOPSLEUTH_DB_PATH", str(db_path))
    return db_path

@pytest.fixture
def client(test_db_path):
    return TestClient(app)

def seed_clips_and_tags(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO clips (id, filename, path, duration, thumbnail_path, starred, phash) VALUES (1, 'a.mp4', '/a.mp4', 1.0, '', 0, 'hash1')")
    c.execute("INSERT INTO clips (id, filename, path, duration, thumbnail_path, starred, phash) VALUES (2, 'b.mp4', '/b.mp4', 1.0, '', 0, 'hash2')")
    c.execute("INSERT INTO tags (id, name) VALUES (1, 'foo')")
    c.execute("INSERT INTO tags (id, name) VALUES (2, 'bar')")
    c.execute("INSERT INTO clip_tags (clip_id, tag_id) VALUES (1, 1)")
    c.execute("INSERT INTO clip_tags (clip_id, tag_id) VALUES (2, 2)")
    conn.commit()
    conn.close()

def get_tags_for_clip(db_path, clip_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT t.name FROM tags t JOIN clip_tags ct ON t.id = ct.tag_id WHERE ct.clip_id = ? ORDER BY t.name", (clip_id,))
    tags = [row[0] for row in c.fetchall()]
    conn.close()
    return tags

def test_batch_add_tags(client, test_db_path):
    seed_clips_and_tags(test_db_path)
    resp = client.post("/batch_tag", json={"clip_ids": [1,2], "add_tags": ["baz"]})
    if resp.status_code != 200:
        print('Response:', resp.status_code, resp.text)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["1"]) == {"foo", "baz"}
    assert set(data["2"]) == {"bar", "baz"}
    assert "baz" in get_tags_for_clip(test_db_path, 1)
    assert "baz" in get_tags_for_clip(test_db_path, 2)

def test_batch_remove_tags(client, test_db_path):
    seed_clips_and_tags(test_db_path)
    client.post("/batch_tag", json={"clip_ids": [1,2], "add_tags": ["baz"]})
    resp = client.post("/batch_tag", json={"clip_ids": [1,2], "remove_tags": ["baz"]})
    if resp.status_code != 200:
        print('Response:', resp.status_code, resp.text)
    assert resp.status_code == 200
    data = resp.json()
    assert "baz" not in data["1"]
    assert "baz" not in data["2"]
    assert "baz" not in get_tags_for_clip(test_db_path, 1)
    assert "baz" not in get_tags_for_clip(test_db_path, 2)

def test_batch_clear_tags(client, test_db_path):
    seed_clips_and_tags(test_db_path)
    resp = client.post("/batch_tag", json={"clip_ids": [1,2], "clear": True})
    if resp.status_code != 200:
        print('Response:', resp.status_code, resp.text)
    assert resp.status_code == 200
    data = resp.json()
    assert data["1"] == []
    assert data["2"] == []
    assert get_tags_for_clip(test_db_path, 1) == []
    assert get_tags_for_clip(test_db_path, 2) == [] 