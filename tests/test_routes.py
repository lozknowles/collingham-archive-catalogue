from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.web import create_app


def test_routes_smoke():
    app = create_app()
    client = app.test_client()
    assert client.get("/records").status_code == 200
    assert client.get("/review-queue").status_code == 200
    assert client.get("/lexicon").status_code == 200
    assert client.get("/records/1").status_code == 200
