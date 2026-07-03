import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.app.storage import BoardStore


class BoardStoreTests(unittest.TestCase):
    def test_save_and_load_board(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="kanban-test-"))
        db_path = temp_dir / "kanban.db"
        try:
            store = BoardStore(db_path=str(db_path))
            board = {
                "columns": [{"id": "col-1", "title": "Backlog", "cardIds": []}],
                "cards": {},
            }

            store.save_board("user", board)
            loaded = store.get_board("user")

            self.assertEqual(loaded, board)

            with sqlite3.connect(db_path) as conn:
                row = conn.execute("SELECT payload FROM boards WHERE username = ?", ("user",)).fetchone()
                self.assertIsNotNone(row)
        finally:
            try:
                if db_path.exists():
                    db_path.unlink()
            except PermissionError:
                pass
            try:
                temp_dir.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
