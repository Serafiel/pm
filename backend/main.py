import json
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import database
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from models import (
    AIChatResponse,
    CardCreateOp,
    CardDeleteOp,
    CardMoveOp,
    ChatRequest,
    ColumnRenameOp,
)
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

STATIC_DIR = Path(os.environ.get("STATIC_DIR", "/app/static"))

# token → user_id
_sessions: dict[str, int] = {}

_ai_client: OpenAI | None = None


@asynccontextmanager
async def lifespan(app):
    global _ai_client
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set")
    _ai_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    database.init_db()
    yield


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_user(session: str | None = Cookie(default=None)) -> int:
    if not session or session not in _sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _sessions[session]


@app.post("/api/auth/login")
async def login(body: LoginRequest, response: Response):
    if body.username != "user" or body.password != "password":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_id = database.get_user_id("user")
    token = secrets.token_hex(32)
    _sessions[token] = user_id
    response.set_cookie("session", token, httponly=True, samesite="lax")
    return {"ok": True}


@app.post("/api/auth/logout")
async def logout(response: Response, session: str | None = Cookie(default=None)):
    if session:
        _sessions.pop(session, None)
    response.delete_cookie("session")
    return {"ok": True}


@app.get("/api/auth/me")
async def me(user_id: int = Depends(get_current_user)):
    return {"username": "user"}


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

@app.get("/api/board")
async def get_board(user_id: int = Depends(get_current_user)):
    return database.get_board_data(user_id)


class RenameColumnRequest(BaseModel):
    title: str


@app.put("/api/board/columns/{column_id}")
async def rename_column(
    column_id: int,
    body: RenameColumnRequest,
    user_id: int = Depends(get_current_user),
):
    if not database.get_column_for_user(column_id, user_id):
        raise HTTPException(status_code=404, detail="Column not found")
    database.rename_column(column_id, body.title)
    return {"ok": True}


class CreateCardRequest(BaseModel):
    column_id: int
    title: str
    details: str = ""


@app.post("/api/board/cards", status_code=201)
async def create_card(body: CreateCardRequest, user_id: int = Depends(get_current_user)):
    if not database.get_column_for_user(body.column_id, user_id):
        raise HTTPException(status_code=404, detail="Column not found")
    card_id = database.create_card(body.column_id, body.title, body.details)
    return {"id": str(card_id), "title": body.title, "details": body.details}


@app.delete("/api/board/cards/{card_id}")
async def delete_card(card_id: int, user_id: int = Depends(get_current_user)):
    card = database.get_card_for_user(card_id, user_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    database.delete_card(card_id, card["column_id"], card["position"])
    return {"ok": True}


class MoveCardRequest(BaseModel):
    column_id: int
    position: int


@app.patch("/api/board/cards/{card_id}/move")
async def move_card_route(
    card_id: int,
    body: MoveCardRequest,
    user_id: int = Depends(get_current_user),
):
    card = database.get_card_for_user(card_id, user_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if not database.get_column_for_user(body.column_id, user_id):
        raise HTTPException(status_code=404, detail="Column not found")
    database.move_card(card_id, card["column_id"], card["position"], body.column_id, body.position)
    return {"ok": True}


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------

def _apply_board_update(operations: list, user_id: int) -> None:
    for op in operations:
        if isinstance(op, CardCreateOp):
            col_id = int(op.column_id)
            if not database.get_column_for_user(col_id, user_id):
                raise HTTPException(status_code=404, detail=f"Column {op.column_id} not found")
            database.create_card(col_id, op.title, op.details)
        elif isinstance(op, CardMoveOp):
            card_id = int(op.card_id)
            card = database.get_card_for_user(card_id, user_id)
            if not card:
                raise HTTPException(status_code=404, detail=f"Card {op.card_id} not found")
            col_id = int(op.column_id)
            if not database.get_column_for_user(col_id, user_id):
                raise HTTPException(status_code=404, detail=f"Column {op.column_id} not found")
            database.move_card(card_id, card["column_id"], card["position"], col_id, op.position)
        elif isinstance(op, CardDeleteOp):
            card_id = int(op.card_id)
            card = database.get_card_for_user(card_id, user_id)
            if not card:
                raise HTTPException(status_code=404, detail=f"Card {op.card_id} not found")
            database.delete_card(card_id, card["column_id"], card["position"])
        elif isinstance(op, ColumnRenameOp):
            col_id = int(op.column_id)
            if not database.get_column_for_user(col_id, user_id):
                raise HTTPException(status_code=404, detail=f"Column {op.column_id} not found")
            database.rename_column(col_id, op.title)


@app.post("/api/ai/chat")
async def ai_chat(body: ChatRequest, user_id: int = Depends(get_current_user)):
    board = database.get_board_data(user_id)
    board_json = json.dumps(board, indent=2)

    system_prompt = f"""You are a project management assistant. The user's current Kanban board is:

{board_json}

You may optionally include board mutations in board_update. Available operations:
- create: add a card (column_id, title, details)
- move: move a card (card_id, column_id, position — 0-based index within the target column)
- delete: remove a card (card_id)
- rename_column: rename a column (column_id, title)

Only include board_update when the user explicitly asks you to change the board. Set it to null otherwise.
Positions are 0-based. Use the board JSON above to reason about current card order and exact target positions."""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in body.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": body.message})

    try:
        completion = _ai_client.beta.chat.completions.parse(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format=AIChatResponse,
        )
        result = completion.choices[0].message.parsed
    except Exception as e:
        logger.error("OpenRouter request failed: %s", e)
        raise HTTPException(status_code=500, detail=f"AI request failed: {e}")

    board_updated = False
    if result.board_update:
        try:
            _apply_board_update(result.board_update, user_id)
            board_updated = True
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to apply board update: %s", e)
            raise HTTPException(status_code=500, detail=f"Failed to apply board update: {e}")

    return {"reply": result.reply, "board_updated": board_updated}


@app.post("/api/ai/ping")
async def ai_ping(user_id: int = Depends(get_current_user)):
    try:
        completion = _ai_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "What is 2+2?"}],
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        logger.error("OpenRouter request failed: %s", e)
        raise HTTPException(status_code=500, detail=f"AI request failed: {e}")


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

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
