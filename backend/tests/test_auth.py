
def test_login_success(client):
    res = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert res.status_code == 200
    assert "session" in res.cookies


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"username": "user", "password": "wrong"})
    assert res.status_code == 401


def test_login_wrong_username(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "password"})
    assert res.status_code == 401


def test_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_authenticated(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json() == {"username": "user"}


def test_logout_clears_session(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
