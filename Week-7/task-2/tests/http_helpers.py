"""Ubuntu: real local Python/Cog/website checks; does not retrain or stop services."""
import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def command(*args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=120)
    if result.returncode:
        print(result.stdout + result.stderr, file=sys.stderr)
        result.check_returncode()
    return result.stdout + result.stderr


def request(port, path, data=None, mime="application/json"):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data,
                                 headers={"Content-Type": mime})
    try:
        with urllib.request.urlopen(req, timeout=80) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as response:
        return response.code, json.load(response)


def upload(data):
    boundary = "EE471FashionBoundary"
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="untrusted.txt"\r\n'
            'Content-Type: text/plain\r\n\r\n').encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return request(5074, "/api/classify", body, f"multipart/form-data; boundary={boundary}")


def same_scores(left, right):
    assert set(left) == set(right), "Class labels disagree"
    assert all(abs(left[label] - right[label]) <= 1e-7 for label in left), "Scores disagree"


