"""HTTP contract tests using isolated in-memory model collections."""

import contextlib
import io
import json
import runpy
import unittest
from pathlib import Path
from unittest.mock import patch

import app as library_app
from custom_classes import Book, DVD, LibraryCollection


class LibraryApiTests(unittest.TestCase):
    def setUp(self):
        self.original_collection = library_app.collection
        self.collection = LibraryCollection()
        self.book = Book("Book", "Writer", 100)
        self.dvd = DVD("Film", "Director", 90)
        self.collection.add_item(self.book)
        self.collection.add_item(self.dvd)
        self.collection.add_item(Book("Second book", "Second writer", 200))
        replacement = patch.object(library_app, "collection", self.collection)
        replacement.start()
        self.addCleanup(replacement.stop)
        library_app.app.config["TESTING"] = True
        self.client = library_app.app.test_client()

    def assert_error(self, response, status):
        self.assertEqual(response.status_code, status)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(set(data), {"error"})
        self.assertIsInstance(data["error"], str)
        self.assertTrue(data["error"])

    def test_initial_data_and_persistence_between_requests(self):
        initial = self.original_collection.list_items()
        self.assertGreaterEqual(len(initial), 3)
        self.assertTrue(any(isinstance(item, Book) for item in initial))
        self.assertTrue(any(isinstance(item, DVD) for item in initial))
        response = self.client.post("/api/items", json={
            "type": "book", "title": "New", "author": "Author", "page_count": 50,
        })
        self.assertEqual(response.status_code, 201)
        item_id = response.get_json()["id"]
        self.assertEqual(self.client.get(f"/api/items/{item_id}").get_json(), response.get_json())
        self.assertEqual(len(self.client.get("/api/items").get_json()), 4)

    def test_create_both_types_delegates_to_model(self):
        for item_type, field in (("book", "page_count"), ("dvd", "duration")):
            data = {"type": item_type, "title": "New", "author": "Author", field: 50}
            with self.subTest(item_type=item_type):
                with patch.object(self.collection, "create_item",
                                  wraps=self.collection.create_item) as create:
                    response = self.client.post("/api/items", json=data)
                    create.assert_called_once_with(data)
                self.assertEqual(response.status_code, 201)
                result = response.get_json()
                self.assertEqual(result, {**data, "id": result["id"], "is_available": True})

    def test_create_rejects_missing_unknown_wrong_type_and_invalid_values(self):
        for item_type, field, wrong in (("book", "page_count", "duration"),
                                       ("dvd", "duration", "page_count")):
            valid = {"type": item_type, "title": "New", "author": "Author", field: 50}
            invalid = [{key: value for key, value in valid.items() if key != missing}
                       for missing in valid]
            for name in ("id", "is_available", "unknown", "item_id", wrong):
                invalid.append({**valid, name: 1})
            for value in (None, True, "media", "BOOK", [], {}):
                invalid.append({**valid, "type": value})
            for name in ("title", "author"):
                for value in ("", "  ", None, 42, False):
                    invalid.append({**valid, name: value})
            for value in (True, False, 0, -1, 1.5, "50", None):
                invalid.append({**valid, field: value})
            for data in invalid:
                with self.subTest(data=data):
                    self.assert_error(self.client.post("/api/items", json=data), 400)
        self.assertEqual(len(self.collection.list_items()), 3)
        self.assertEqual(self.collection.add_item(Book("Next", "Author", 1)), 4)

    def test_json_object_contract_for_create_put_and_patch(self):
        cases = [
            ("{", "application/json"), ("", "application/json"),
            ('{"title":"New"}', "text/plain"),
            ('{"title":"New"}', None),
        ]
        cases += [(json.dumps(value), "application/json")
                  for value in (None, [], "text", 1, True)]
        before = [item.to_dict() for item in self.collection.list_items()]
        for method, path in (("POST", "/api/items"), ("PUT", "/api/items/1"),
                             ("PATCH", "/api/items/1")):
            for data, content_type in cases:
                with self.subTest(method=method, data=data, content_type=content_type):
                    response = self.client.open(path, method=method, data=data,
                                                content_type=content_type)
                    self.assert_error(response, 400)
        self.assertEqual([item.to_dict() for item in self.collection.list_items()], before)

    def test_get_item_and_all_missing_item_endpoints(self):
        response = self.client.get("/api/items/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), self.book.to_dict())
        for method, suffix, data in (
            ("GET", "", None), ("DELETE", "", None),
            ("PUT", "", {"title": "New", "author": "Author", "page_count": 10}),
            ("PATCH", "", {"title": "New"}),
            ("POST", "/checkout", None), ("POST", "/return", None),
        ):
            with self.subTest(method=method, suffix=suffix):
                self.assert_error(self.client.open(
                    "/api/items/999" + suffix, method=method, json=data
                ), 404)

    def test_list_filters_work_together_and_delegate(self):
        self.dvd.checkout()
        for available in (None, True, False):
            for item_type in (None, "book", "dvd"):
                query = {}
                if available is not None:
                    query["available"] = str(available).lower()
                if item_type is not None:
                    query["type"] = item_type
                expected = [item.to_dict() for item in
                            self.collection.list_items(available, item_type)]
                with self.subTest(query=query):
                    with patch.object(self.collection, "list_items",
                                      wraps=self.collection.list_items) as listing:
                        response = self.client.get("/api/items", query_string=query)
                        listing.assert_called_once_with(available=available, item_type=item_type)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.get_json(), expected)

    def test_invalid_filters(self):
        for name, values in (("available", ("", "True", "1", "null", "yes")),
                             ("type", ("", "BOOK", "media", "unknown"))):
            for value in values:
                with self.subTest(name=name, value=value):
                    self.assert_error(self.client.get(
                        "/api/items", query_string={name: value}
                    ), 400)

    def test_put_requires_complete_fields_but_patch_accepts_partial(self):
        for item, field in ((self.book, "page_count"), (self.dvd, "duration")):
            url = f"/api/items/{item.id}"
            before = item.to_dict()
            full = {"title": "Updated", "author": "New author", field: 50}
            for missing in full:
                partial = {key: value for key, value in full.items() if key != missing}
                self.assert_error(self.client.put(url, json=partial), 400)
                self.assertEqual(item.to_dict(), before)
            with patch.object(self.collection, "replace_item",
                              wraps=self.collection.replace_item) as replace:
                response = self.client.put(url, json=full)
                replace.assert_called_once_with(item.id, full)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {**before, **full})
            with patch.object(self.collection, "patch_item",
                              wraps=self.collection.patch_item) as partial_update:
                response = self.client.patch(url, json={field: 75})
                partial_update.assert_called_once_with(item.id, {field: 75})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()[field], 75)
            self.assertEqual(response.get_json()["title"], "Updated")

    def test_updates_reject_forbidden_fields_and_remain_atomic(self):
        for item, field, wrong in ((self.book, "page_count", "duration"),
                                   (self.dvd, "duration", "page_count")):
            full = {"title": "Must not change", "author": "New", field: 50}
            invalid = [{name: value} for name, value in (
                ("id", 100), ("type", "book"), ("is_available", False),
                ("unknown", 1), ("item_id", 1), (wrong, 50),
                (field, True), (field, 0), (field, 1.5), ("author", " "),
                ("title", None),
            )]
            for method in ("PUT", "PATCH"):
                for fields in invalid + [{}]:
                    data = {**full, **fields} if fields and method == "PUT" else fields
                    if method == "PATCH" and fields:
                        data = {"title": "Must not change", **fields}
                    before = item.to_dict()
                    with self.subTest(method=method, data=data):
                        self.assert_error(self.client.open(
                            f"/api/items/{item.id}", method=method, json=data
                        ), 400)
                        self.assertEqual(item.to_dict(), before)

    def test_checkout_and_return_preserve_model_messages_and_errors(self):
        for item in (self.book, self.dvd):
            url = f"/api/items/{item.id}"
            self.assert_error(self.client.post(url + "/return"), 409)
            with patch.object(item, "checkout", wraps=item.checkout) as checkout:
                response = self.client.post(url + "/checkout")
                checkout.assert_called_once_with()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["item"], item.to_dict())
            self.assertFalse(response.get_json()["item"]["is_available"])
            if isinstance(item, DVD):
                self.assertIn("Handle with care", response.get_json()["message"])
            self.assert_error(self.client.post(url + "/checkout"), 409)
            self.assert_error(self.client.delete(url), 409)
            self.assertIs(self.collection.get_item(item.id), item)
            with patch.object(item, "return_item", wraps=item.return_item) as returning:
                response = self.client.post(url + "/return")
                returning.assert_called_once_with()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {
                "message": "Successful return", "item": item.to_dict(),
            })
            self.assertTrue(response.get_json()["item"]["is_available"])

    def test_custom_success_messages_are_not_hardcoded_in_routes(self):
        for suffix, method in (("checkout", "checkout"), ("return", "return_item")):
            with patch.object(self.book, method, return_value="Message from model"):
                response = self.client.post(f"/api/items/1/{suffix}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["message"], "Message from model")

    def test_delete_is_204_with_no_body_and_ids_are_not_reused(self):
        with patch.object(self.collection, "remove_item",
                          wraps=self.collection.remove_item) as remove:
            response = self.client.delete("/api/items/3")
            remove.assert_called_once_with(3)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")
        self.assertIsNone(response.get_json(silent=True))
        self.assert_error(self.client.get("/api/items/3"), 404)
        self.assert_error(self.client.delete("/api/items/3"), 404)
        response = self.client.post("/api/items", json={
            "type": "dvd", "title": "New", "author": "Creator", "duration": 60,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["id"], 4)

    def test_routing_errors_are_json_and_preserve_allow_header(self):
        self.assert_error(self.client.get("/missing"), 404)
        self.assert_error(self.client.get("/api/items/not-an-integer"), 404)
        response = self.client.put("/api/items")
        self.assert_error(response, 405)
        self.assertIn("GET", response.headers["Allow"])

    def test_import_does_not_start_server(self):
        with patch("flask.Flask.run") as run, contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(Path(library_app.__file__)), run_name="import_check")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
