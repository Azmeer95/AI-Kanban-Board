import os
import sqlite3
import tempfile
import unittest

from backend.app.storage import BoardStore


class BoardStoreTests(unittest.TestCase):
    def test_save_and_load_board(self) -> None:
        temp_dir = tempfile.mkdtemp(prefix="kanban-test-", dir=".")
        db_path = os.path.join(temp_dir, "kanban.db")
        try:
            store = BoardStore(db_path=db_path)
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
                if os.path.exists(db_path):
                    os.remove(db_path)
            except PermissionError:
                pass
            if os.path.isdir(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()
