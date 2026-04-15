import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    static_path = tmp_path / "static"
    static_path.mkdir()
    (static_path / "index.html").write_text("<html><body>Kanban</body></html>")
    (static_path / "_next").mkdir()

    monkeypatch.setenv("STATIC_DIR", str(static_path))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    import database
    import main
    importlib.reload(database)
    importlib.reload(main)

    database.init_db()

    return TestClient(main.app)
