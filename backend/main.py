import os
import secrets
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

STATIC_DIR = Path(os.environ.get("STATIC_DIR", "/app/static"))

_sessions: set[str] = set()

app = FastAPI()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def login(body: LoginRequest, response: Response):
    if body.username != "user" or body.password != "password":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_hex(32)
    _sessions.add(token)
    response.set_cookie("session", token, httponly=True, samesite="lax")
    return {"ok": True}


@app.post("/api/auth/logout")
async def logout(response: Response, session: str | None = Cookie(default=None)):
    if session:
        _sessions.discard(session)
    response.delete_cookie("session")
    return {"ok": True}


@app.get("/api/auth/me")
async def me(session: str | None = Cookie(default=None)):
    if not session or session not in _sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"username": "user"}


@app.get("/api/ping")
async def ping():
    return {"status": "ok"}


app.mount("/_next", StaticFiles(directory=str(STATIC_DIR / "_next")), name="assets")


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if full_path:
        candidate = STATIC_DIR / f"{full_path}.html"
        if candidate.exists():
            return FileResponse(str(candidate))
    return FileResponse(str(STATIC_DIR / "index.html"))
