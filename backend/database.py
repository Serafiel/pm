import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", "data/kanban.db"))

_db: sqlite3.Connection | None = None


def db() -> sqlite3.Connection:
    global _db
    if _db is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _db.row_factory = sqlite3.Row
        _db.execute("PRAGMA foreign_keys = ON")
    return _db


def init_db() -> None:
    conn = db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS boards (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title   TEXT    NOT NULL DEFAULT 'My Board'
        );
        CREATE TABLE IF NOT EXISTS columns (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL REFERENCES boards(id),
            title    TEXT    NOT NULL,
            position INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cards (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL REFERENCES columns(id),
            title     TEXT    NOT NULL,
            details   TEXT    NOT NULL DEFAULT '',
            position  INTEGER NOT NULL
        );
    """)
    _seed_if_empty(conn)


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        return

    with conn:
        conn.execute("INSERT INTO users (username) VALUES ('user')")
        user_id = conn.execute("SELECT id FROM users WHERE username='user'").fetchone()["id"]
        conn.execute("INSERT INTO boards (user_id) VALUES (?)", (user_id,))
        board_id = conn.execute("SELECT id FROM boards WHERE user_id=?", (user_id,)).fetchone()["id"]

        for pos, title in enumerate(["Backlog", "Discovery", "In Progress", "Review", "Done"]):
            conn.execute(
                "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
                (board_id, title, pos),
            )

        col_ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM columns WHERE board_id=? ORDER BY position", (board_id,)
            ).fetchall()
        ]

        seed_cards = [
            (0, "Align roadmap themes", "Draft quarterly themes with impact statements and metrics.", 0),
            (0, "Gather customer signals", "Review support tags, sales notes, and churn feedback.", 1),
            (1, "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs.", 0),
            (2, "Refine status language", "Standardize column labels and tone across the board.", 0),
            (2, "Design card layout", "Add hierarchy and spacing for scanning dense lists.", 1),
            (3, "QA micro-interactions", "Verify hover, focus, and loading states.", 0),
            (4, "Ship marketing page", "Final copy approved and asset pack delivered.", 0),
            (4, "Close onboarding sprint", "Document release notes and share internally.", 1),
        ]
        for col_idx, title, details, pos in seed_cards:
            conn.execute(
                "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
                (col_ids[col_idx], title, details, pos),
            )


def get_user_id(username: str) -> int | None:
    row = db().execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    return row["id"] if row else None


def get_board_data(user_id: int) -> dict:
    conn = db()
    board_row = conn.execute("SELECT id FROM boards WHERE user_id=?", (user_id,)).fetchone()
    if not board_row:
        return {"columns": [], "cards": {}}
    board_id = board_row["id"]

    col_rows = conn.execute(
        "SELECT id, title FROM columns WHERE board_id=? ORDER BY position", (board_id,)
    ).fetchall()

    columns = []
    for col in col_rows:
        card_rows = conn.execute(
            "SELECT id FROM cards WHERE column_id=? ORDER BY position", (col["id"],)
        ).fetchall()
        columns.append({
            "id": str(col["id"]),
            "title": col["title"],
            "cardIds": [str(c["id"]) for c in card_rows],
        })

    all_cards = conn.execute(
        """
        SELECT cards.id, cards.title, cards.details
        FROM cards
        JOIN columns ON cards.column_id = columns.id
        WHERE columns.board_id = ?
        """,
        (board_id,),
    ).fetchall()

    cards = {
        str(c["id"]): {"id": str(c["id"]), "title": c["title"], "details": c["details"]}
        for c in all_cards
    }

    return {"columns": columns, "cards": cards}


def get_column_for_user(column_id: int, user_id: int) -> sqlite3.Row | None:
    return db().execute(
        """
        SELECT columns.id, columns.position
        FROM columns
        JOIN boards ON columns.board_id = boards.id
        WHERE columns.id = ? AND boards.user_id = ?
        """,
        (column_id, user_id),
    ).fetchone()


def get_card_for_user(card_id: int, user_id: int) -> sqlite3.Row | None:
    return db().execute(
        """
        SELECT cards.id, cards.column_id, cards.position
        FROM cards
        JOIN columns ON cards.column_id = columns.id
        JOIN boards ON columns.board_id = boards.id
        WHERE cards.id = ? AND boards.user_id = ?
        """,
        (card_id, user_id),
    ).fetchone()


def rename_column(column_id: int, title: str) -> None:
    with db() as conn:
        conn.execute("UPDATE columns SET title=? WHERE id=?", (title, column_id))


def create_card(column_id: int, title: str, details: str) -> int:
    conn = db()
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), -1) FROM cards WHERE column_id=?", (column_id,)
    ).fetchone()[0]
    with conn:
        cursor = conn.execute(
            "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
            (column_id, title, details, max_pos + 1),
        )
    return cursor.lastrowid


def delete_card(card_id: int, column_id: int, position: int) -> None:
    with db() as conn:
        conn.execute("DELETE FROM cards WHERE id=?", (card_id,))
        conn.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id=? AND position > ?",
            (column_id, position),
        )


def move_card(card_id: int, src_col: int, src_pos: int, dst_col: int, dst_pos: int) -> None:
    with db() as conn:
        if src_col == dst_col:
            if src_pos < dst_pos:
                conn.execute(
                    "UPDATE cards SET position = position - 1 WHERE column_id=? AND position > ? AND position <= ?",
                    (src_col, src_pos, dst_pos),
                )
            elif src_pos > dst_pos:
                conn.execute(
                    "UPDATE cards SET position = position + 1 WHERE column_id=? AND position >= ? AND position < ?",
                    (src_col, dst_pos, src_pos),
                )
            conn.execute("UPDATE cards SET position=? WHERE id=?", (dst_pos, card_id))
        else:
            conn.execute(
                "UPDATE cards SET position = position - 1 WHERE column_id=? AND position > ?",
                (src_col, src_pos),
            )
            conn.execute(
                "UPDATE cards SET position = position + 1 WHERE column_id=? AND position >= ?",
                (dst_col, dst_pos),
            )
            conn.execute(
                "UPDATE cards SET column_id=?, position=? WHERE id=?",
                (dst_col, dst_pos, card_id),
            )
