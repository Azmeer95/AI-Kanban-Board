import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import create_app


class KanbanApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_root_returns_frontend_index(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<html", response.text.lower())

    def test_ai_returns_fallback_when_api_key_missing(self) -> None:
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            login_response = self.client.post(
                "/api/login",
                json={"username": "user", "password": "password"},
            )
            self.assertEqual(login_response.status_code, 200)
            token = login_response.json()["access_token"]

            response = self.client.post(
                "/api/ai/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "hello"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("configured without an API key", response.json()["reply"])

    def test_login_and_board_round_trip(self) -> None:
        login_response = self.client.post(
            "/api/login",
            json={"username": "user", "password": "password"},
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["access_token"]

        board_response = self.client.get(
            "/api/board",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(board_response.status_code, 200)
        board = board_response.json()
        self.assertIn("columns", board)
        self.assertIn("cards", board)

        update_response = self.client.put(
            "/api/board",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "columns": board["columns"],
                "cards": {
                    **board["cards"],
                    "card-test": {
                        "id": "card-test",
                        "title": "Saved from API",
                        "details": "Persisted",
                    },
                },
            },
        )
        self.assertEqual(update_response.status_code, 200)

        reloaded = self.client.get(
            "/api/board",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(reloaded.status_code, 200)
        self.assertIn("card-test", reloaded.json()["cards"])


if __name__ == "__main__":
    unittest.main()
