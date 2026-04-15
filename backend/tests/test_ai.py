from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def auth_client(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    return client


def _mock_completion(content: str):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def test_ai_ping_requires_auth(client):
    assert client.post("/api/ai/ping").status_code == 401


def test_ai_ping_returns_response(auth_client):
    with patch("main._ai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion("The answer is 4.")
        res = auth_client.post("/api/ai/ping")
    assert res.status_code == 200
    assert "4" in res.json()["response"]


def test_ai_ping_returns_500_on_api_error(auth_client):
    with patch("main._ai_client") as mock_client:
        mock_client.chat.completions.create.side_effect = Exception("connection refused")
        res = auth_client.post("/api/ai/ping")
    assert res.status_code == 500
    assert "AI request failed" in res.json()["detail"]
