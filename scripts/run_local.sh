#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
DB="$ROOT/data/collingham-archive-catalogue.sqlite"

if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"

python -m pip install -r "$ROOT/requirements.txt"

if [ ! -f "$DB" ]; then
    echo "Database not found; bootstrapping..."
    python "$ROOT/scripts/bootstrap_db.py"
else
    echo "Using existing database: $DB"
fi

exec python "$ROOT/run_app.py"
