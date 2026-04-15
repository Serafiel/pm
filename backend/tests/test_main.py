import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def static_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("STATIC_DIR", str(tmp_path))
    (tmp_path / "index.html").write_text("<html><body>Kanban</body></html>")
    (tmp_path / "_next").mkdir()
    return tmp_path


@pytest.fixture
def client(static_dir):
    import main
    importlib.reload(main)
    return TestClient(main.app)


def test_ping(client):
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_serves_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Kanban" in response.text


def test_catch_all_serves_index(client):
    response = client.get("/some/deep/path")
    assert response.status_code == 200
    assert "Kanban" in response.text
