from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from scripts.bootstrap_db import DEFAULT_DB, SCHEMA, SEED


def resolve_db_path(db_path: str | Path | None = None) -> Path:
    if db_path is None:
        return DEFAULT_DB
    return Path(db_path).expanduser().resolve()


def ensure_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        seeded = conn.execute("SELECT COUNT(*) FROM catalogue_records").fetchone()[0]
        if seeded == 0:
            conn.executescript(SEED.read_text(encoding="utf-8"))
        conn.commit()


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = resolve_db_path(db_path)
    ensure_database(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def fetch_all(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(query, params).fetchall())


def fetch_one(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(query, params).fetchone()


def to_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def from_text_list(value: str) -> str:
    items = [part.strip() for part in value.splitlines() if part.strip()]
    return json.dumps(items, ensure_ascii=False)
