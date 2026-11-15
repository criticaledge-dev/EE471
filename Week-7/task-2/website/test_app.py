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

OUTPUT = {"class": "cat", "score": .5, "top3": {"cat": .5, "dog": .3, "bird": .1}}


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
            self.assertEqual(response.json["status"], "succeeded")
            self.assertEqual(response.json["results"]["baseline"]["output"], OUTPUT)
            self.assertEqual(self.cog.call_count, 2)
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

    def test_rejects_non_32x32_images(self):
        for size in ((33, 32), (32, 33), (31, 32)):
            with self.subTest(size=size):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", Image.DecompressionBombWarning)
                    self.assertEqual(self.upload(picture(size=size)).status_code, 400)
        self.cog.assert_not_called()

    def test_http_200_failed_not_success_or_raw_error_leak(self):
        self.cog.return_value = reply({"status": "failed", "output": None, "error": "INTERNAL data:image secret"})
        response = self.upload()
        self.assertEqual(response.json["status"], "failed")
        self.assertNotIn("INTERNAL", response.get_data(as_text=True))
        self.assertNotIn("output", response.json)

    def test_busy_not_ready_http_and_pending(self):
        for status in (409, 503):
            self.cog.return_value = reply({}, status)
            self.assertEqual(self.upload().json["status"], "failed")
        self.cog.return_value = reply({"status": "processing"})
        self.assertEqual(self.upload().json["status"], "failed")

    def test_service_http_error(self):
        self.cog.return_value = reply({}, 500)
        self.assertEqual(self.upload().json["status"], "failed")

    def test_timeout_and_connection_then_recovery(self):
        for error, status in ((requests.Timeout("secret"), 504),
                              (requests.ConnectionError("secret"), 503),
                              (requests.RequestException("secret"), 502)):
            self.cog.reset_mock()
            self.cog.side_effect = error
            response = self.upload()
            self.assertTrue(all(item["http_status"] == status for item in response.json["results"].values()))
            self.assertNotIn("secret", response.get_data(as_text=True))
            self.assertEqual(self.cog.call_count, 2)
        self.cog.side_effect = None
        self.assertEqual(self.upload().status_code, 200)

    def test_bad_schema_and_scores(self):
        for body in (None, [], {}, {"status": "succeeded", "output": {}},
                     {"status": "succeeded", "output": {"x": 2, "y": 0, "z": 0}},
                     {"status": "succeeded", "output": {"x": True, "y": 0, "z": 0}},
                     {"status": "succeeded", "output": {"x": float("nan"), "y": 0, "z": 0}}):
            with self.subTest(body=body):
                self.cog.return_value = reply(body)
                self.assertEqual(self.upload().json["status"], "failed")

    def test_invalid_json_and_response_size(self):
        for data in (b"not-json", b"x" * (website.MAX_COG_RESPONSE + 1)):
            self.cog.return_value = reply({})
            self.cog.return_value.iter_content.return_value = [data]
            self.assertEqual(self.upload().json["status"], "failed")

    def test_both_services_receive_same_image_once(self):
        response = self.upload()
        self.assertEqual(set(response.json["results"]), {"baseline", "optimized"})
        self.assertEqual(self.cog.call_count, 2)
        calls = self.cog.call_args_list
        self.assertEqual({c.args[1] for c in calls}, {website.app.config[key]+"/predictions" for key in ("BASELINE_URL", "OPTIMIZED_URL")})
        self.assertEqual(calls[0].kwargs["json"], calls[1].kwargs["json"])

    def test_partial_failure_preserves_other_output_and_recovers(self):
        for failed in ("BASELINE_URL", "OPTIMIZED_URL"):
            def respond(_client, url, **kwargs):
                if url.startswith(website.app.config[failed]):
                    raise requests.ConnectionError("private detail")
                return reply({"status": "succeeded", "output": OUTPUT})
            self.cog.side_effect = respond
            response = self.upload()
            self.assertEqual(response.json["status"], "partial")
            for name in ("baseline", "optimized"):
                result = response.json["results"][name]
                self.assertEqual(result["status"], "failed" if name.upper()+"_URL" == failed else "succeeded")
                if result["status"] == "succeeded": self.assertEqual(result["output"], OUTPUT)
            self.assertNotIn("private detail", response.get_data(as_text=True))
        self.cog.side_effect = None
        self.assertEqual(self.upload().json["status"], "succeeded")

    def test_metrics_come_from_recorded_files(self):
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("51.41%", page)
        self.assertIn("54.24%", page)

    def test_rejects_inconsistent_or_invalid_top_prediction(self):
        payloads = [
            {"class": "dog", "score": .5, "top3": OUTPUT["top3"]},
            {"class": "cat", "score": True, "top3": OUTPUT["top3"]},
            {"class": "cat", "score": .5, "top3": {"cat": .5, "unknown": .3, "dog": .1}},
            {"class": "cat", "score": .5, "top3": {"cat": .5, "dog": float("nan"), "bird": .1}},
            {"class": "cat", "score": .5, "top3": {"cat": .5, "dog": True, "bird": .1}},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                self.cog.return_value = reply({"status": "succeeded", "output": payload})
                self.assertEqual(self.upload().json["status"], "failed")

    def test_scores_preserved_without_renormalization(self):
        output = {"class": "cat", "score": .7, "top3": {"cat": .7, "dog": .2, "bird": .05}}
        self.cog.return_value = reply({"status": "succeeded", "output": output})
        self.assertEqual(self.upload().json["results"]["baseline"]["output"], output)


if __name__ == "__main__":
    unittest.main()
