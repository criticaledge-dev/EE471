"""Mock Cog HTTP responses; these tests do not prove real model inference."""
import io
import json
import unittest
import warnings
from contextlib import closing
from unittest.mock import MagicMock, patch

from PIL import Image
import requests
import app as website
from werkzeug.test import EnvironBuilder

OUTPUT = {"tiger cat": .5, "tabby": .3, "Egyptian cat": .1}


def picture(kind="PNG", size=(32, 32)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (40, 80, 120)).save(buffer, format=kind)
    return buffer.getvalue()


def reply(body, status=200):
    response = MagicMock(spec=requests.Response)
    response.status_code = status
    response.iter_content.return_value = [json.dumps(body).encode()]
    response.__enter__.return_value = response
    return response


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.client = website.app.test_client()
        self.post = patch.object(requests.Session, "post", autospec=True)
        self.cog = self.post.start()
        self.addCleanup(self.post.stop)
        self.cog.return_value = reply({"status": "succeeded", "output": OUTPUT})

    def upload(self, data=None, name="image.png", mime="image/png"):
        with io.BytesIO(picture() if data is None else data) as file:
            with closing(EnvironBuilder(path="/api/classify", method="POST", data={"image": (file, name, mime)})) as builder:
                environment = builder.get_environ()
                try:
                    response = self.client.open(environment)
                finally:
                    environment["wsgi.input"].close()
        response.get_data()
        response.close()
        return response

    def test_home_and_static(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        for path in ("/static/script.js", "/static/style.css", "/healthz"):
            with self.subTest(path=path):
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code, 200)
        self.cog.assert_not_called()

    def test_png_and_jpeg_ignore_filename_and_mime(self):
        for kind, mime in (("PNG", "image/png"), ("JPEG", "image/jpeg")):
            self.cog.reset_mock()
            data = picture(kind)
            response = self.upload(data, "../../evil.txt", "text/plain")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {"status": "succeeded", "output": OUTPUT})
            self.cog.assert_called_once()
            args, kwargs = self.cog.call_args
            self.assertTrue(args[1].endswith("/predictions"))
            self.assertTrue(kwargs["json"]["input"]["image"].startswith(f"data:{mime};base64,"))
            self.assertNotIn("files", kwargs)
            self.assertEqual(kwargs["timeout"], (3, 60))
            self.assertFalse(args[0].trust_env)

    def test_missing_empty_and_corrupt(self):
        self.assertEqual(self.client.post("/api/classify").status_code, 400)
        for data in (b"", b"bad", picture()[:30]):
            with self.subTest(data_length=len(data)):
                self.assertEqual(self.upload(data).status_code, 400)
        self.cog.assert_not_called()

    def test_other_format(self):
        self.assertEqual(self.upload(picture("GIF")).status_code, 400)
        self.cog.assert_not_called()

    def test_file_size(self):
        self.assertEqual(self.upload(b"x" * (website.MAX_FILE_BYTES + 1)).status_code, 413)
        self.cog.assert_not_called()

    def test_request_size(self):
        response = self.client.post("/api/classify", data=b"x" * (website.MAX_FILE_BYTES + 100_000))
        self.assertEqual(response.status_code, 413)
        self.assertIn("error", response.json)
        self.cog.assert_not_called()

    def test_dimension_and_pixel_limits(self):
        for size in ((6001, 1), (4000, 3001)):
            with self.subTest(size=size):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", Image.DecompressionBombWarning)
                    self.assertEqual(self.upload(picture(size=size)).status_code, 400)
        self.cog.assert_not_called()

    def test_http_200_failed_not_success_or_raw_error_leak(self):
        self.cog.return_value = reply({"status": "failed", "output": None, "error": "INTERNAL data:image secret"})
        response = self.upload()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("INTERNAL", response.get_data(as_text=True))
        self.assertNotIn("output", response.json)

    def test_busy_not_ready_http_and_pending(self):
        for status in (409, 503):
            self.cog.return_value = reply({}, status)
            self.assertEqual(self.upload().status_code, 503)
        self.cog.return_value = reply({"status": "processing"})
        self.assertEqual(self.upload().status_code, 503)

    def test_service_http_error(self):
        self.cog.return_value = reply({}, 500)
        self.assertEqual(self.upload().status_code, 502)

    def test_timeout_and_connection_then_recovery(self):
        for error, status in ((requests.Timeout("secret"), 504),
                              (requests.ConnectionError("secret"), 503),
                              (requests.RequestException("secret"), 502)):
            self.cog.reset_mock()
            self.cog.side_effect = error
            response = self.upload()
            self.assertEqual(response.status_code, status)
            self.assertNotIn("secret", response.get_data(as_text=True))
            self.cog.assert_called_once()
        self.cog.side_effect = None
        self.assertEqual(self.upload().status_code, 200)

    def test_bad_schema_and_scores(self):
        for body in (None, [], {}, {"status": "succeeded", "output": {}},
                     {"status": "succeeded", "output": {"x": 2, "y": 0, "z": 0}},
                     {"status": "succeeded", "output": {"x": True, "y": 0, "z": 0}},
                     {"status": "succeeded", "output": {"x": float("nan"), "y": 0, "z": 0}}):
            with self.subTest(body=body):
                self.cog.return_value = reply(body)
                self.assertEqual(self.upload().status_code, 502)

    def test_invalid_json_and_response_size(self):
        for data in (b"not-json", b"x" * (website.MAX_COG_RESPONSE + 1)):
            self.cog.return_value = reply({})
            self.cog.return_value.iter_content.return_value = [data]
            self.assertEqual(self.upload().status_code, 502)

    def test_not_forced_to_cat(self):
        output = {"school bus": .7, "minibus": .2, "trolleybus": .05}
        self.cog.return_value = reply({"status": "succeeded", "output": output})
        self.assertEqual(self.upload().json["output"], output)


if __name__ == "__main__":
    unittest.main()
