# Database Schema

SQLite database, created automatically on first run. All tables use `CREATE TABLE IF NOT EXISTS` so startup is always safe.

---

## Tables

### `users`

```sql
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT    UNIQUE NOT NULL
);
```

One row per user. The MVP seeds a single `user` row on startup if it doesn't exist.

---

### `boards`

```sql
CREATE TABLE IF NOT EXISTS boards (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title   TEXT    NOT NULL DEFAULT 'My Board'
);
```

One board per user for the MVP. The schema supports multiple boards per user for the future.

---

### `columns`

```sql
CREATE TABLE IF NOT EXISTS columns (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL REFERENCES boards(id),
    title    TEXT    NOT NULL,
    position INTEGER NOT NULL
);
```

`position` is a non-negative integer. Columns are read with `ORDER BY position ASC`. When a column is renamed, only `title` is updated. Column order is fixed in the MVP (no drag-to-reorder columns).

---

### `cards`

```sql
CREATE TABLE IF NOT EXISTS cards (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    column_id INTEGER NOT NULL REFERENCES columns(id),
    title     TEXT    NOT NULL,
    details   TEXT    NOT NULL DEFAULT '',
    position  INTEGER NOT NULL
);
```

`position` is a non-negative integer within the column. Cards are read with `ORDER BY position ASC`. When a card is moved, the positions of affected cards are updated.

---

## Relationships

```
users ──< boards ──< columns ──< cards
```

- One user → many boards (MVP: one)
- One board → many columns (MVP: five fixed columns)
- One column → many cards

---

## Ordering

Both `columns` and `cards` use a `position` integer column. Positions are sequential integers starting at 0 (`0, 1, 2, …`). On reorder, all affected rows in the column are updated. This keeps queries simple (`ORDER BY position`) at the cost of a small multi-row update on move.

---

## Startup behaviour

On FastAPI startup:

1. Connect to `data/kanban.db` (created if missing).
2. Run `CREATE TABLE IF NOT EXISTS` for all four tables.
3. If no `user` row exists, insert one and create their default board with five columns and eight seed cards (matching the current frontend `initialData`).
