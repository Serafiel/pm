from unittest.mock import MagicMock, patch

import pytest

from models import AIChatResponse, CardCreateOp, CardDeleteOp, CardMoveOp, ColumnRenameOp


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


def _mock_parse(reply: str, board_update=None):
    parsed = AIChatResponse(reply=reply, board_update=board_update)
    message = MagicMock()
    message.parsed = parsed
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


# ---------------------------------------------------------------------------
# /api/ai/ping
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# /api/ai/chat
# ---------------------------------------------------------------------------

def test_ai_chat_requires_auth(client):
    assert client.post("/api/ai/chat", json={"message": "hello"}).status_code == 401


def test_ai_chat_returns_reply_no_update(auth_client):
    with patch("main._ai_client") as mock_client:
        mock_client.beta.chat.completions.parse.return_value = _mock_parse("Looking good!")
        res = auth_client.post("/api/ai/chat", json={"message": "How is the board?"})
    assert res.status_code == 200
    body = res.json()
    assert body["reply"] == "Looking good!"
    assert body["board_updated"] is False


def test_ai_chat_create_card(auth_client):
    board = auth_client.get("/api/board").json()
    col_id = board["columns"][0]["id"]
    initial_count = len(board["columns"][0]["cardIds"])

    op = CardCreateOp(op="create", column_id=col_id, title="AI card", details="From AI")
    with patch("main._ai_client") as mock_client:
        mock_client.beta.chat.completions.parse.return_value = _mock_parse(
            "Done.", board_update=[op]
        )
        res = auth_client.post("/api/ai/chat", json={"message": "Add a card"})

    assert res.status_code == 200
    assert res.json()["board_updated"] is True

    board2 = auth_client.get("/api/board").json()
    assert len(board2["columns"][0]["cardIds"]) == initial_count + 1


def test_ai_chat_move_card(auth_client):
    board = auth_client.get("/api/board").json()
    src_col = board["columns"][0]
    dst_col = board["columns"][4]
    card_id = src_col["cardIds"][0]

    op = CardMoveOp(op="move", card_id=card_id, column_id=dst_col["id"], position=0)
    with patch("main._ai_client") as mock_client:
        mock_client.beta.chat.completions.parse.return_value = _mock_parse(
            "Moved.", board_update=[op]
        )
        res = auth_client.post("/api/ai/chat", json={"message": "Move the card"})

    assert res.status_code == 200
    assert res.json()["board_updated"] is True

    board2 = auth_client.get("/api/board").json()
    assert card_id not in board2["columns"][0]["cardIds"]
    assert board2["columns"][4]["cardIds"][0] == card_id


def test_ai_chat_delete_card(auth_client):
    board = auth_client.get("/api/board").json()
    card_id = board["columns"][0]["cardIds"][0]

    op = CardDeleteOp(op="delete", card_id=card_id)
    with patch("main._ai_client") as mock_client:
        mock_client.beta.chat.completions.parse.return_value = _mock_parse(
            "Deleted.", board_update=[op]
        )
        res = auth_client.post("/api/ai/chat", json={"message": "Delete that card"})

    assert res.status_code == 200
    assert res.json()["board_updated"] is True

    board2 = auth_client.get("/api/board").json()
    assert card_id not in board2["columns"][0]["cardIds"]


def test_ai_chat_rename_column(auth_client):
    board = auth_client.get("/api/board").json()
    col_id = board["columns"][0]["id"]

    op = ColumnRenameOp(op="rename_column", column_id=col_id, title="Sprint")
    with patch("main._ai_client") as mock_client:
        mock_client.beta.chat.completions.parse.return_value = _mock_parse(
            "Renamed.", board_update=[op]
        )
        res = auth_client.post("/api/ai/chat", json={"message": "Rename the column"})

    assert res.status_code == 200
    assert res.json()["board_updated"] is True

    board2 = auth_client.get("/api/board").json()
    assert board2["columns"][0]["title"] == "Sprint"


def test_ai_chat_returns_500_on_api_error(auth_client):
    with patch("main._ai_client") as mock_client:
        mock_client.beta.chat.completions.parse.side_effect = Exception("network error")
        res = auth_client.post("/api/ai/chat", json={"message": "hello"})
    assert res.status_code == 500
    assert "AI request failed" in res.json()["detail"]


def test_ai_chat_returns_404_on_invalid_card_id(auth_client):
    op = CardDeleteOp(op="delete", card_id="99999")
    with patch("main._ai_client") as mock_client:
        mock_client.beta.chat.completions.parse.return_value = _mock_parse(
            "Done.", board_update=[op]
        )
        res = auth_client.post("/api/ai/chat", json={"message": "Delete a card"})
    assert res.status_code == 404
    assert "99999" in res.json()["detail"]
