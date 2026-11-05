import os
import tempfile
from pathlib import Path

os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", "sqlite:///" + str(Path(tempfile.mkdtemp()) / "test.db")
)
if os.getenv("TEST_DATABASE_URL") and not os.getenv("TEST_DATABASE_URL").rsplit("/", 1)[
    -1
].endswith("_test"):
    raise RuntimeError(
        "TEST_DATABASE_URL must name an isolated database ending in _test"
    )
os.environ["AI_ENABLED"] = "false"
os.environ["ALLOWED_HOSTS"] = "testserver,localhost,127.0.0.1"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
import pytest
from fastapi.testclient import TestClient
from backend.main import app, rates, seed
from backend.db import Base, engine


@pytest.fixture
def client():
    rates.clear()
    Base.metadata.drop_all(engine)
    seed()
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/auth/login",
            json={"username": "author", "password": "Aegis-author-2026!"},
        )
        assert r.status_code == 200
        c.headers["x-csrf-token"] = r.json()["csrf"]
        yield c
