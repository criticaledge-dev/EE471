"""Regression tests for IDs, model validation and item state transitions."""

import contextlib
import importlib
import io
import unittest

from custom_classes import (
    Book, DVD, MediaItem, LibraryCollection, ItemNotFoundError, ItemStateError,
)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.library = LibraryCollection()
        self.book = Book("Book", "Author", 100)
        self.dvd = DVD("Film", "Director", 90)
        self.book_id = self.library.add_item(self.book)
        self.dvd_id = self.library.add_item(self.dvd)

    def test_ids_are_stable_and_never_reused(self):
        self.assertEqual((self.book_id, self.dvd_id), (1, 2))
        with self.assertRaises(ItemStateError):
            self.library.add_item(self.book)
        with self.assertRaises(ItemStateError):
            LibraryCollection().add_item(self.book)
        self.assertEqual(self.book.id, 1)
        self.assertEqual(len(self.library.items), 2)
        self.library.remove_item(self.dvd_id)
        with self.assertRaises(ItemStateError):
            self.library.add_item(self.dvd)
        self.assertEqual(self.dvd.id, 2)
        self.assertEqual(self.library.add_item(Book("New", "Writer", 1)), 3)
        with self.assertRaises(AttributeError):
            self.book.id = 99
        with self.assertRaises(ValueError):
            self.library.add_item("not an item")

    def test_serialization_and_base_item(self):
        self.assertEqual(self.book.to_dict(), {
            "id": 1, "type": "book", "title": "Book", "author": "Author",
            "is_available": True, "page_count": 100,
        })
        self.assertEqual(self.dvd.to_dict(), {
            "id": 2, "type": "dvd", "title": "Film", "author": "Director",
            "is_available": True, "duration": 90,
        })
        media = MediaItem("Media", "Creator")
        self.assertIsNone(media.id)
        self.assertEqual(self.library.add_item(media), 3)
        self.assertEqual(media.to_dict()["type"], "media")
        self.assertIn(media, self.library.list_items())
        self.assertEqual(str(self.book), "Book by Author [Available] - 100 pages")

    def test_checkout_return_and_dvd_warning(self):
        for item in (self.book, self.dvd):
            with self.subTest(item=item):
                with self.assertRaises(ItemStateError):
                    item.return_item()
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    message = item.checkout()
                self.assertEqual(output.getvalue(), "")
                self.assertIn("Successful checkout", message)
                if isinstance(item, DVD):
                    self.assertIn("Handle with care", message)
                self.assertFalse(item.is_available)
                with self.assertRaises(ItemStateError):
                    item.checkout()
                self.assertFalse(item.is_available)
                self.assertIn("Successful return", item.return_item())
                self.assertTrue(item.is_available)

    def test_filters_and_available_titles(self):
        self.dvd.checkout()
        self.assertEqual(self.library.list_items(), [self.book, self.dvd])
        self.assertEqual(self.library.list_available(), ["Book"])
        for available in (None, True, False):
            for item_type in (None, "book", "dvd"):
                with self.subTest(available=available, item_type=item_type):
                    expected = [item for item in (self.book, self.dvd)
                                if (available is None or item.is_available is available)
                                and (item_type is None or item.to_dict()["type"] == item_type)]
                    self.assertEqual(self.library.list_items(available, item_type), expected)
        for value in (0, 1, "true", [], {}):
            with self.subTest(available=value), self.assertRaises(ValueError):
                self.library.list_items(available=value)
        for value in ("media", "BOOK", "", True, 1, [], {}):
            with self.subTest(item_type=value), self.assertRaises(ValueError):
                self.library.list_items(item_type=value)

    def test_update_is_atomic_and_type_specific(self):
        for item in (self.book, self.dvd):
            specific = "page_count" if isinstance(item, Book) else "duration"
            wrong = "duration" if isinstance(item, Book) else "page_count"
            invalid_fields = [
                {"id": 9}, {"type": "book"}, {"is_available": False},
                {"unknown": 1}, {wrong: 50}, {specific: True}, {specific: 0},
                {specific: 1.5}, {"author": "  "}, {"title": None},
            ]
            for fields in invalid_fields:
                before = item.to_dict()
                # Put a valid change before the invalid field to detect partial writes.
                changes = {"title": "Must not change", **fields}
                with self.subTest(fields=fields), self.assertRaises(ValueError):
                    self.library.update_item(item.id, **changes)
                self.assertEqual(item.to_dict(), before)
            result = self.library.update_item(
                item.id, title="Updated", author="New author", **{specific: 50}
            )
            self.assertIs(result, item)
            self.assertEqual((item.title, item.author, getattr(item, specific)),
                             ("Updated", "New author", 50))

    def test_model_validation_at_creation_and_assignment(self):
        for field in ("title", "author"):
            for value in ("", "  \t", None, 7, True):
                arguments = {"title": "Title", "author": "Writer", field: value}
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        MediaItem(**arguments)
                    before = self.book.to_dict()
                    with self.assertRaises(ValueError):
                        setattr(self.book, field, value)
                    self.assertEqual(self.book.to_dict(), before)
        for value in (True, False, 0, -1, 1.5, "10", None):
            for model, field, item in ((Book, "page_count", self.book),
                                       (DVD, "duration", self.dvd)):
                with self.subTest(model=model, value=value):
                    with self.assertRaises(ValueError):
                        model("Title", "Creator", value)
                    before = item.to_dict()
                    with self.assertRaises(ValueError):
                        setattr(item, field, value)
                    self.assertEqual(item.to_dict(), before)

    def test_lookup_and_removal_errors_preserve_collection(self):
        self.assertIs(self.library.get_item(self.book_id), self.book)
        for item_id in (999, 0, -1, True, 1.0, "1", None):
            for action in (self.library.get_item, self.library.remove_item,
                           self.library.update_item):
                with self.subTest(item_id=item_id, action=action):
                    with self.assertRaises(ItemNotFoundError):
                        action(item_id)
        self.book.checkout()
        with self.assertRaises(ItemStateError):
            self.library.remove_item(self.book_id)
        self.assertIs(self.library.get_item(self.book_id), self.book)
        self.book.return_item()
        self.library.remove_item(self.book_id)
        with self.assertRaises(ItemNotFoundError):
            self.library.get_item(self.book_id)

    def test_importing_main_does_not_run_demo(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            importlib.import_module("main")
        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
