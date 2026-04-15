
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
