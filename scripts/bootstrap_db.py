#!/usr/bin/env python3
"""Create a local SQLite database from the schema and seed SQL files."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "collingham-archive-catalogue.sqlite"
SCHEMA = ROOT / "schema" / "001_initial.sql"
SEED = ROOT / "seed" / "001_sample_data.sql"


def bootstrap(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.executescript(SEED.read_text(encoding="utf-8"))
        conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to the SQLite database to create.",
    )
    args = parser.parse_args()

    if args.db.exists():
        raise SystemExit(f"Refusing to overwrite existing database: {args.db}")

    bootstrap(args.db)
    print(f"Created SQLite database at {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

