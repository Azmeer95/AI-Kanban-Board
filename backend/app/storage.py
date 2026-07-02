from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


class BoardStore:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or os.getenv("KANBAN_DB_PATH", "backend/data/kanban.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists() and self.db_path.stat().st_size == 0:
            self.db_path.unlink()
        self._initialize()

    def _initialize(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS boards (
                    username TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def get_board(self, username: str) -> dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT payload FROM boards WHERE username = ?",
                (username,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return self._default_board()

        return json.loads(row[0])

    def save_board(self, username: str, board: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(board)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO boards(username, payload) VALUES(?, ?) ON CONFLICT(username) DO UPDATE SET payload = excluded.payload",
                (username, payload),
            )
            conn.commit()
        finally:
            conn.close()
        return board

    def _default_board(self) -> dict[str, Any]:
        return {
            "columns": [
                {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
                {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
                {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
                {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
                {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
            ],
            "cards": {
                "card-1": {"id": "card-1", "title": "Align roadmap themes", "details": "Draft quarterly themes with impact statements and metrics."},
                "card-2": {"id": "card-2", "title": "Gather customer signals", "details": "Review support tags, sales notes, and churn feedback."},
                "card-3": {"id": "card-3", "title": "Prototype analytics view", "details": "Sketch initial dashboard layout and key drill-downs."},
                "card-4": {"id": "card-4", "title": "Refine status language", "details": "Standardize column labels and tone across the board."},
                "card-5": {"id": "card-5", "title": "Design card layout", "details": "Add hierarchy and spacing for scanning dense lists."},
                "card-6": {"id": "card-6", "title": "QA micro-interactions", "details": "Verify hover, focus, and loading states."},
                "card-7": {"id": "card-7", "title": "Ship marketing page", "details": "Final copy approved and asset pack delivered."},
                "card-8": {"id": "card-8", "title": "Close onboarding sprint", "details": "Document release notes and share internally."},
            },
        }
