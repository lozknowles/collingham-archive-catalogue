#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.web import create_app


def main() -> int:
    app = create_app()
    client = app.test_client()
    checks = [
        ("/records", 200),
        ("/review-queue", 200),
        ("/lexicon", 200),
        ("/records/1", 200),
    ]
    for path, expected in checks:
        resp = client.get(path)
        if resp.status_code != expected:
            raise SystemExit(f"{path} returned {resp.status_code}, expected {expected}")
    print("Route check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
