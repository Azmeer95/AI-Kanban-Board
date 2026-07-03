import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import (
    _apply_board_actions,
    _create_card_id,
    _parse_ai_response,
    create_app,
)


class AiApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_ai_health_endpoint(self) -> None:
        response = self.client.get("/api/ai/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ok", response.json()["status"])


class ParseAiResponseTests(unittest.TestCase):
    def test_plain_text_returns_no_actions(self) -> None:
        reply, actions = _parse_ai_response("Hello, how can I help?")
        self.assertIsNone(reply)
        self.assertEqual(actions, [])

    def test_json_with_reply_only(self) -> None:
        reply, actions = _parse_ai_response('{"reply": "Done!"}')
        self.assertEqual(reply, "Done!")
        self.assertEqual(actions, [])

    def test_json_with_actions(self) -> None:
        content = '{"reply": "Added a card", "actions": [{"type": "add_card", "column_id": "col-backlog", "title": "Test"}]}'
        reply, actions = _parse_ai_response(content)
        self.assertEqual(reply, "Added a card")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "add_card")

    def test_json_in_code_fence(self) -> None:
        content = '```json\n{"reply": "Moved card", "actions": [{"type": "move_card", "card_id": "card-1", "to_column": "col-progress"}]}\n```'
        reply, actions = _parse_ai_response(content)
        self.assertEqual(reply, "Moved card")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "move_card")

    def test_json_in_code_fence_no_lang(self) -> None:
        content = '```\n{"reply": "Deleted card", "actions": [{"type": "delete_card", "card_id": "card-5"}]}\n```'
        reply, actions = _parse_ai_response(content)
        self.assertEqual(reply, "Deleted card")
        self.assertEqual(len(actions), 1)

    def test_invalid_json_returns_empty(self) -> None:
        reply, actions = _parse_ai_response("Not json { broken")
        self.assertIsNone(reply)
        self.assertEqual(actions, [])


class ApplyBoardActionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.board = {
            "columns": [
                {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]},
                {"id": "col-progress", "title": "In Progress", "cardIds": []},
                {"id": "col-done", "title": "Done", "cardIds": ["card-2"]},
            ],
            "cards": {
                "card-1": {"id": "card-1", "title": "Task 1", "details": "Details 1"},
                "card-2": {"id": "card-2", "title": "Task 2", "details": "Details 2"},
            },
        }

    def test_add_card(self) -> None:
        actions = [{"type": "add_card", "column_id": "col-backlog", "title": "New task", "details": "New details"}]
        result = _apply_board_actions(self.board, actions)
        new_card_ids = [cid for cid in result["columns"][0]["cardIds"] if cid not in ["card-1"]]
        self.assertEqual(len(new_card_ids), 1)
        card_id = new_card_ids[0]
        self.assertEqual(result["cards"][card_id]["title"], "New task")
        self.assertEqual(result["cards"][card_id]["details"], "New details")

    def test_move_card(self) -> None:
        actions = [{"type": "move_card", "card_id": "card-1", "to_column": "col-progress"}]
        result = _apply_board_actions(self.board, actions)
        self.assertNotIn("card-1", result["columns"][0]["cardIds"])
        self.assertIn("card-1", result["columns"][1]["cardIds"])

    def test_edit_card(self) -> None:
        actions = [{"type": "edit_card", "card_id": "card-1", "title": "Updated title", "details": "Updated details"}]
        result = _apply_board_actions(self.board, actions)
        self.assertEqual(result["cards"]["card-1"]["title"], "Updated title")
        self.assertEqual(result["cards"]["card-1"]["details"], "Updated details")

    def test_delete_card(self) -> None:
        actions = [{"type": "delete_card", "card_id": "card-1"}]
        result = _apply_board_actions(self.board, actions)
        self.assertNotIn("card-1", result["cards"])
        self.assertNotIn("card-1", result["columns"][0]["cardIds"])

    def test_unknown_action_type_is_ignored(self) -> None:
        actions = [{"type": "unknown", "card_id": "card-1"}]
        result = _apply_board_actions(self.board, actions)
        self.assertEqual(len(result["cards"]), 2)

    def test_multiple_actions(self) -> None:
        actions = [
            {"type": "add_card", "column_id": "col-backlog", "title": "New"},
            {"type": "move_card", "card_id": "card-2", "to_column": "col-progress"},
        ]
        result = _apply_board_actions(self.board, actions)
        card_count = len(result["cards"])
        self.assertEqual(card_count, 3)
        self.assertIn("card-2", result["columns"][1]["cardIds"])
        backlog_card_ids = result["columns"][0]["cardIds"]
        new_cards = [cid for cid in backlog_card_ids if cid not in ["card-1"]]
        self.assertEqual(len(new_cards), 1)


class CreateCardIdTests(unittest.TestCase):
    def test_generates_unique_ids(self) -> None:
        ids = {_create_card_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_starts_with_card_prefix(self) -> None:
        card_id = _create_card_id()
        self.assertTrue(card_id.startswith("card-"))


if __name__ == "__main__":
    unittest.main()
