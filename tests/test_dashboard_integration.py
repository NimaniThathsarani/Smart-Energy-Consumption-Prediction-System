from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from tests.mock_dashboard_server import create_server


class DashboardIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get(self, path: str):
        with urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as response:
            return response.status, response.headers.get_content_type(), response.read()

    def test_dashboard_assets_are_served(self) -> None:
        status, content_type, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "text/html")
        self.assertIn(b"Smart recommendations", body)
        for asset in ("/app.js", "/api.mjs", "/core.mjs", "/styles.css"):
            self.assertEqual(self.get(asset)[0], 200)

    def test_all_required_api_routes_return_non_empty_json(self) -> None:
        for route in ("/forecast?limit=24", "/peak", "/anomalies", "/clusters", "/recommendations", "/model-performance"):
            with self.subTest(route=route):
                status, content_type, body = self.get(route)
                self.assertEqual(status, 200)
                self.assertEqual(content_type, "application/json")
                self.assertTrue(next(iter(json.loads(body).values())))

    def test_forecast_limit_is_validated(self) -> None:
        with self.assertRaises(HTTPError) as context:
            self.get("/forecast?limit=invalid")
        self.assertEqual(context.exception.code, 400)
        context.exception.close()

    def test_path_traversal_is_rejected(self) -> None:
        with self.assertRaises(HTTPError) as context:
            self.get("/%2e%2e/requirements.txt")
        self.assertIn(context.exception.code, (403, 404))
        context.exception.close()


if __name__ == "__main__":
    unittest.main()
