from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class CardCreateOp(BaseModel):
    op: Literal["create"]
    column_id: str
    title: str
    details: str = ""


class CardMoveOp(BaseModel):
    op: Literal["move"]
    card_id: str
    column_id: str
    position: int


class CardDeleteOp(BaseModel):
    op: Literal["delete"]
    card_id: str


class ColumnRenameOp(BaseModel):
    op: Literal["rename_column"]
    column_id: str
    title: str


BoardOperation = Annotated[
    Union[CardCreateOp, CardMoveOp, CardDeleteOp, ColumnRenameOp],
    Field(discriminator="op"),
]


class AIChatResponse(BaseModel):
    reply: str
    board_update: list[BoardOperation] | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
