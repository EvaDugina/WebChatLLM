from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class StoredMessage:
    id: int
    role: str
    text: str
    created_at: datetime


class SqliteStorage:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def init(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  role TEXT NOT NULL CHECK (role IN ('user','assistant')),
                  text TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);")

    def list_messages(self, limit: int = 500) -> list[StoredMessage]:
        with self._connect() as con:
            cur = con.execute(
                "SELECT id, role, text, created_at FROM messages ORDER BY id ASC LIMIT ?;",
                (limit,),
            )
            rows = cur.fetchall()
        return [
            StoredMessage(
                id=int(r[0]),
                role=str(r[1]),
                text=str(r[2]),
                created_at=datetime.fromisoformat(str(r[3])),
            )
            for r in rows
        ]

    def add_message(self, role: str, text: str) -> StoredMessage:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO messages(role, text, created_at) VALUES (?, ?, ?);",
                (role, text, created_at),
            )
            msg_id = int(cur.lastrowid)
        return StoredMessage(
            id=msg_id,
            role=role,
            text=text,
            created_at=datetime.fromisoformat(created_at),
        )

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._db_path, check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con

