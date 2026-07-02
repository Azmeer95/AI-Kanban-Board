import unittest

from fastapi.testclient import TestClient

from backend.app.main import create_app


class AiApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_ai_health_endpoint(self) -> None:
        response = self.client.get("/api/ai/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ok", response.json()["status"])


if __name__ == "__main__":
    unittest.main()
