# AI Integration

## Endpoint

`POST /api/ai/chat` — requires authentication.

### Request

```json
{
  "message": "Move the first card to Done",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

### Response

```json
{
  "reply": "Done — I moved 'Align roadmap themes' to the Done column.",
  "board_updated": true
}
```

---

## System Prompt

The system prompt is constructed at request time. It contains:

1. The user's full board state as JSON (columns with cardIds, cards with id/title/details).
2. Instructions on when and how to use `board_update`.

```
You are a project management assistant. The user's current Kanban board is:

{board_json}

You may optionally include board mutations in board_update. Available operations:
- create: add a card (column_id, title, details)
- move: move a card (card_id, column_id, position — 0-based index within the target column)
- delete: remove a card (card_id)
- rename_column: rename a column (column_id, title)

Only include board_update when the user explicitly asks you to change the board. Set it to null otherwise.
Positions are 0-based. Use the board JSON above to reason about current card order and exact target positions.
```

---

## Structured Output Schema

The model responds with a JSON object matching this schema. The `openai` Python SDK's
`beta.chat.completions.parse` handles serialization automatically via Pydantic.

```json
{
  "reply": "string",
  "board_update": [
    { "op": "create", "column_id": "string", "title": "string", "details": "string" },
    { "op": "move", "card_id": "string", "column_id": "string", "position": 0 },
    { "op": "delete", "card_id": "string" },
    { "op": "rename_column", "column_id": "string", "title": "string" }
  ]
}
```

`board_update` is `null` when no mutations are needed.

Operations are applied sequentially. If any operation references an unknown ID the request
fails immediately with 404 and no further operations are applied.

All IDs are strings matching the board JSON (e.g. `"3"`, not `3`).
