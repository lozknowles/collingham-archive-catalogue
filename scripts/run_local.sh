#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"

if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
fi

"$PIP" install -r "$ROOT/requirements.txt"
"$PYTHON" "$ROOT/scripts/bootstrap_db.py"
exec "$PYTHON" "$ROOT/run_app.py"

