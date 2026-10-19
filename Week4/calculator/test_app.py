"""Run with: python -m unittest -v test_app.py"""

import unittest
from unittest.mock import patch

from app import app
from custom_classes import Calculator


class CalculatorApiTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_page_and_assets(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="display"', response.data)
        for path in ("/static/style.css", "/static/script.js"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_operations_use_calculator(self):
        for operation, x, y, expected in (
            ("add", 10, 5, 15),
            ("subtract", 2, 5, -3),
            ("multiply", -2, 0.5, -1),
            ("divide", 7, 2, 3.5),
            ("add", 0, 0, 0),
        ):
            with self.subTest(operation=operation, x=x):
                with patch.object(
                    Calculator, operation, autospec=True,
                    side_effect=getattr(Calculator, operation),
                ) as method:
                    response = self.client.post(
                        "/api/calculate", json={"operation": operation, "x": x, "y": y}
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.get_json(), {"result": expected})
                    method.assert_called_once()
                    self.assertEqual(method.call_args.args[1:], (x, y))

    def test_invalid_payloads(self):
        valid = {"operation": "add", "x": 10, "y": 5}
        payloads = [None, [], "text", 1, True, {}]
        payloads.extend({key: value for key, value in valid.items() if key != missing}
                        for missing in valid)
        for operation in ("power", "ADD", None, [], {}, 42, True):
            payloads.append({**valid, "operation": operation})
        for field in ("x", "y"):
            for value in (True, False, "10", None, [], {}, float("inf"), float("nan")):
                payloads.append({**valid, field: value})
        payloads.extend([
            {"operation": "divide", "x": 10, "y": 0},
            {"operation": "divide", "x": 10, "y": -0.0},
            {"operation": "multiply", "x": 1e308, "y": 1e308},
        ])
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/calculate", json=payload)
                self.assert_error(response)

    def test_malformed_json_and_content_type(self):
        for data, content_type in (
            ('{"operation":', "application/json"),
            ("", "application/json"),
            ('{"operation":"add","x":10,"y":5}', "text/plain"),
        ):
            with self.subTest(data=data, content_type=content_type):
                self.assert_error(self.client.post(
                    "/api/calculate", data=data, content_type=content_type
                ))

    def assert_error(self, response):
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.get_json()), {"error"})
        self.assertIsInstance(response.get_json()["error"], str)
        self.assertTrue(response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
