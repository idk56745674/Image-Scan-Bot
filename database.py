import os
import sqlite3

import numpy as np

import config

_connections: dict[int, sqlite3.Connection] = {}

SCHEMA = """
CREATE TABLE IF NOT EXISTS image_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url TEXT,
    description TEXT,
    author TEXT,
    jump_url TEXT,
    content_hash TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS image_tags (
    image_id INTEGER NOT NULL REFERENCES image_store(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (image_id, tag)
);
CREATE INDEX IF NOT EXISTS idx_image_tags_tag ON image_tags(tag);
CREATE TABLE IF NOT EXISTS tag_vectors (
    tag TEXT PRIMARY KEY,
    vector BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def get_db(guild_id: int) -> sqlite3.Connection:
    conn = _connections.get(guild_id)
    if conn is None:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(os.path.join(config.DATA_DIR, f"guild_{guild_id}.db"))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        conn.commit()
        _connections[guild_id] = conn
    return conn


def is_scan_enabled(guild_id: int) -> bool:
    row = get_db(guild_id).execute(
        "SELECT value FROM settings WHERE key = 'scan_enabled'"
    ).fetchone()
    return bool(row and row[0] == "1")


def set_scan_enabled(guild_id: int, enabled: bool) -> None:
    conn = get_db(guild_id)
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('scan_enabled', ?)",
        ("1" if enabled else "0",),
    )
    conn.commit()



def image_exists(guild_id: int, content_hash: str) -> bool:
    row = get_db(guild_id).execute(
        "SELECT 1 FROM image_store WHERE content_hash = ?", (content_hash,)
    ).fetchone()
    return row is not None


def add_image(guild_id, image_url, tags, author, jump_url, content_hash) -> bool:
    """Returns False if an identical image (same bytes) is already stored."""
    conn = get_db(guild_id)
    cur = conn.execute(
        "INSERT OR IGNORE INTO image_store "
        "(image_url, description, author, jump_url, content_hash) VALUES (?, ?, ?, ?, ?)",
        (image_url, ", ".join(tags), author, jump_url, content_hash),
    )
    if cur.rowcount == 0:
        conn.commit()
        return False
    conn.executemany(
        "INSERT OR IGNORE INTO image_tags (image_id, tag) VALUES (?, ?)",
        [(cur.lastrowid, t) for t in tags],
    )
    conn.commit()
    return True


def all_tags(guild_id: int) -> list[str]:
    rows = get_db(guild_id).execute("SELECT DISTINCT tag FROM image_tags").fetchall()
    return [r[0] for r in rows]


def images_for_tags(guild_id: int, tags: list[str]) -> list[tuple[int, str]]:
    if not tags:
        return []
    marks = ",".join("?" * len(tags))
    return get_db(guild_id).execute(
        f"SELECT image_id, tag FROM image_tags WHERE tag IN ({marks})", tags
    ).fetchall()


def get_images(guild_id: int, ids: list[int]) -> dict[int, tuple]:
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    rows = get_db(guild_id).execute(
        f"SELECT id, image_url, description, author, jump_url "
        f"FROM image_store WHERE id IN ({marks})",
        ids,
    ).fetchall()
    return {r[0]: r[1:] for r in rows}


def tags_missing_vectors(guild_id: int) -> list[str]:
    rows = get_db(guild_id).execute(
        "SELECT DISTINCT tag FROM image_tags WHERE tag NOT IN (SELECT tag FROM tag_vectors)"
    ).fetchall()
    return [r[0] for r in rows]


def save_vectors(guild_id: int, tags: list[str], vectors: np.ndarray) -> None:
    conn = get_db(guild_id)
    conn.executemany(
        "INSERT OR REPLACE INTO tag_vectors (tag, vector) VALUES (?, ?)",
        [(t, v.astype(np.float32).tobytes()) for t, v in zip(tags, vectors)],
    )
    conn.commit()


def load_vectors(guild_id: int) -> tuple[list[str], np.ndarray]:
    rows = get_db(guild_id).execute("SELECT tag, vector FROM tag_vectors").fetchall()
    if not rows:
        return [], np.empty((0, 0), dtype=np.float32)
    tags = [r[0] for r in rows]
    matrix = np.vstack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    return tags, matrix
