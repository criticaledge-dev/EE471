"""Small upload proxy for the existing Cog classifier; no model duplication."""
import base64
import io
import json
import math
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from PIL import Image, UnidentifiedImageError
import requests
from werkzeug.exceptions import RequestEntityTooLarge

MAX_FILE_BYTES = 1024 * 1024
MAX_COG_RESPONSE = 64 * 1024

app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=MAX_FILE_BYTES + 64 * 1024,
                  BASELINE_URL=os.environ.get("BASELINE_URL", "http://127.0.0.1:5072").rstrip("/"),
                  OPTIMIZED_URL=os.environ.get("OPTIMIZED_URL", "http://127.0.0.1:5073").rstrip("/"))


class ClassificationError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def image_data_url(data):
    if not data:
        raise ClassificationError("Choose a non-empty JPEG or PNG image.", 400)
    if len(data) > MAX_FILE_BYTES:
        raise ClassificationError("Image exceeds the 1 MiB file limit.", 413)
    try:
        with Image.open(io.BytesIO(data)) as image:
            image_format = image.format
            if image_format not in ("JPEG", "PNG"):
                raise ClassificationError("Only JPEG and PNG images are supported.", 400)
            if image.size != (28, 28):
                raise ClassificationError("Expected a 28x28 image. Choose a FashionMNIST demo PNG; no resize is applied.", 400)
            image.verify()
        # verify() checks structure; decoding also rejects truncated pixel data.
        with Image.open(io.BytesIO(data)) as image:
            image.load()
    except ClassificationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombError):
        raise ClassificationError("Invalid or damaged JPEG/PNG image.", 400) from None
    mime = "image/jpeg" if image_format == "JPEG" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def classify_with_cog(data_url, model="baseline"):
    try:
        # No proxy/environment credentials or automatic retry are needed locally.
        with requests.Session() as client:
            client.trust_env = False
            with client.post(app.config[model.upper() + "_URL"] + "/predictions",
                             json={"input": {"image": data_url}},
                             timeout=(3, 60), stream=True) as response:
                if response.status_code in (409, 503):
                    raise ClassificationError("Classifier is busy or not ready. Please try again later.", 503)
                if response.status_code != 200:
                    raise ClassificationError("Classifier service returned an error.")
                chunks, size = [], 0
                for chunk in response.iter_content(chunk_size=8192):
                    size += len(chunk)
                    if size > MAX_COG_RESPONSE:
                        raise ClassificationError("Classifier returned an invalid response.")
                    chunks.append(chunk)
                result = json.loads(b"".join(chunks))
    except requests.Timeout:
        raise ClassificationError("Classifier timed out. Please try again later.", 504) from None
    except requests.ConnectionError:
        raise ClassificationError("Cannot connect to the classifier. Check that it is running.", 503) from None
    except requests.RequestException:
        raise ClassificationError("Classifier connection failed. Please try again later.") from None
    except (ValueError, UnicodeError):
        raise ClassificationError("Classifier returned an invalid response.") from None

    if not isinstance(result, dict):
        raise ClassificationError("Classifier returned an invalid response.")
    if result.get("status") == "failed":
        # Raw Cog errors can contain internal details; never forward them.
        raise ClassificationError("Classifier could not process this image. Try another valid image.")
    if result.get("status") in ("starting", "processing"):
        raise ClassificationError("Classifier has not completed the prediction. Please try again later.", 503)
    if result.get("status") != "succeeded":
        raise ClassificationError("Classifier returned an invalid prediction status.")
    output = result.get("output")
    if not isinstance(output, dict) or len(output) != 3 or any(
        not isinstance(label, str) or not label.strip() or len(label) > 200
        or isinstance(score, bool) or not isinstance(score, (int, float))
        or not math.isfinite(score) or not 0 <= score <= 1
        for label, score in output.items()
    ):
        raise ClassificationError("Classifier returned invalid class scores.")
    return output


@app.get("/")
def index():
    metrics = {name: json.loads((Path(__file__).parent / f"{name}_metrics.json").read_text(encoding="utf-8"))
               for name in ("baseline", "optimized")}
    return render_template("index.html", metrics=metrics)


@app.get("/healthz")
def health():
    return jsonify(status="ok")


@app.errorhandler(RequestEntityTooLarge)
def too_large(_error):
    return jsonify(error="Upload is too large. Maximum image size is 1 MiB."), 413


@app.post("/api/classify")
def classify():
    upload = request.files.get("image")
    if upload is None:
        return jsonify(error="Choose a JPEG or PNG image."), 400
    try:
        data_url = image_data_url(upload.read(MAX_FILE_BYTES + 1))
    except ClassificationError as error:
        return jsonify(error=str(error)), error.status
    def predict(name):
        try:
            return {"status": "succeeded", "output": classify_with_cog(data_url, name)}
        except ClassificationError as error:
            return {"status": "failed", "error": str(error), "http_status": error.status}
    # Two bounded independent requests; each gets the identical validated image.
    # A failed service cannot discard the successful service's output.
    names = ("baseline", "optimized")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = dict(zip(names, pool.map(predict, names)))
    succeeded = sum(item["status"] == "succeeded" for item in results.values())
    return jsonify(status="succeeded" if succeeded == 2 else "partial" if succeeded else "failed",
                   results=results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
