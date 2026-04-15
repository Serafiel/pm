import pytest


@pytest.fixture
def auth_client(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    return client


# GET /api/board

def test_get_board_requires_auth(client):
    assert client.get("/api/board").status_code == 401


def test_get_board_returns_board_data(auth_client):
    res = auth_client.get("/api/board")
    assert res.status_code == 200
    data = res.json()
    assert len(data["columns"]) == 5
    assert len(data["cards"]) == 8
    assert all("cardIds" in col for col in data["columns"])


# PUT /api/board/columns/{id}

def test_rename_column_requires_auth(client):
    assert client.put("/api/board/columns/1", json={"title": "X"}).status_code == 401


def test_rename_column(auth_client):
    board = auth_client.get("/api/board").json()
    col_id = board["columns"][0]["id"]
    assert auth_client.put(f"/api/board/columns/{col_id}", json={"title": "Sprint"}).status_code == 200
    board2 = auth_client.get("/api/board").json()
    assert board2["columns"][0]["title"] == "Sprint"


def test_rename_column_not_found(auth_client):
    assert auth_client.put("/api/board/columns/99999", json={"title": "X"}).status_code == 404


# POST /api/board/cards

def test_create_card_requires_auth(client):
    assert client.post("/api/board/cards", json={"column_id": 1, "title": "T", "details": ""}).status_code == 401


def test_create_card(auth_client):
    board = auth_client.get("/api/board").json()
    col_id = int(board["columns"][0]["id"])
    initial_count = len(board["columns"][0]["cardIds"])

    res = auth_client.post("/api/board/cards", json={"column_id": col_id, "title": "New card", "details": "Detail"})
    assert res.status_code == 201
    card = res.json()
    assert card["title"] == "New card"

    board2 = auth_client.get("/api/board").json()
    assert len(board2["columns"][0]["cardIds"]) == initial_count + 1


def test_create_card_column_not_found(auth_client):
    assert auth_client.post("/api/board/cards", json={"column_id": 99999, "title": "T", "details": ""}).status_code == 404


# DELETE /api/board/cards/{id}

def test_delete_card_requires_auth(client):
    assert client.delete("/api/board/cards/1").status_code == 401


def test_delete_card(auth_client):
    board = auth_client.get("/api/board").json()
    card_id = board["columns"][0]["cardIds"][0]

    assert auth_client.delete(f"/api/board/cards/{card_id}").status_code == 200

    board2 = auth_client.get("/api/board").json()
    assert card_id not in board2["columns"][0]["cardIds"]


def test_delete_card_not_found(auth_client):
    assert auth_client.delete("/api/board/cards/99999").status_code == 404


# PATCH /api/board/cards/{id}/move

def test_move_card_requires_auth(client):
    assert client.patch("/api/board/cards/1/move", json={"column_id": 1, "position": 0}).status_code == 401


def test_move_card_cross_column(auth_client):
    board = auth_client.get("/api/board").json()
    src_col = board["columns"][0]
    dst_col = board["columns"][4]
    card_id = src_col["cardIds"][0]

    res = auth_client.patch(
        f"/api/board/cards/{card_id}/move",
        json={"column_id": int(dst_col["id"]), "position": 0},
    )
    assert res.status_code == 200

    board2 = auth_client.get("/api/board").json()
    assert card_id not in board2["columns"][0]["cardIds"]
    assert board2["columns"][4]["cardIds"][0] == card_id


def test_move_card_same_column(auth_client):
    board = auth_client.get("/api/board").json()
    col = board["columns"][0]
    card_id = col["cardIds"][0]
    second_card_id = col["cardIds"][1]

    auth_client.patch(
        f"/api/board/cards/{card_id}/move",
        json={"column_id": int(col["id"]), "position": 1},
    )

    board2 = auth_client.get("/api/board").json()
    assert board2["columns"][0]["cardIds"][0] == second_card_id
    assert board2["columns"][0]["cardIds"][1] == card_id


def test_move_card_not_found(auth_client):
    board = auth_client.get("/api/board").json()
    col_id = int(board["columns"][0]["id"])
    assert auth_client.patch("/api/board/cards/99999/move", json={"column_id": col_id, "position": 0}).status_code == 404
