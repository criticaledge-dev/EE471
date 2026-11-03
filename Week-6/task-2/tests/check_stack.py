"""Run in Ubuntu from task-2. Real Docker/HTTP checks; no Postman automation."""
import base64
import json
import re
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent


def command(*args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        print(result.stdout, result.stderr, file=sys.stderr)
        result.check_returncode()
    return result.stdout + result.stderr


def request(path, data=None, mime="application/json", port=5063):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data,
                                 headers={"Content-Type": mime})
    try:
        with urllib.request.urlopen(req, timeout=80) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as response:
        return response.code, json.load(response)


def upload(data=None):
    boundary = "EE471ImageBoundary"
    if data is None:
        body = f"--{boundary}--\r\n".encode()
    else:
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="untrusted-name.txt"\r\n'
                f'Content-Type: text/plain\r\n\r\n').encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return request("/api/classify", body, f"multipart/form-data; boundary={boundary}")


def ready():
    for _ in range(60):
        try:
            if request("/health-check", port=5064)[1].get("status") == "READY":
                return
        except OSError:
            pass
        time.sleep(1)
    raise AssertionError("Classifier not READY")


def main():
    unit_file = ROOT / "website/test_app.py"
    unit_result = command("docker", "run", "--rm", "--network", "none", "--mount",
                  f"type=bind,source={unit_file},target=/app/test_app.py,readonly",
                  "ee471-week6-website", "python", "-B", "-m", "unittest", "-v", "test_app")
    print(unit_result)
    test_count = int(re.search(r"Ran (\d+) tests", unit_result)[1])
    print(f"MOCK_WEBSITE_TESTS: {test_count} passed (no network)")
    command(sys.executable, "postman/make_request.py", "classifier/test-data/input.jpg")
    collection = json.loads((ROOT / "postman/classifier.postman_collection.json").read_text())
    assert collection["item"][0]["request"]["url"] == "{{cog_url}}/predictions"
    payload = (ROOT / "outputs/postman-request.json").read_bytes()
    environment = json.loads((ROOT / "outputs/postman-environment.json").read_text())
    assert json.loads(environment["values"][0]["value"]) == json.loads(payload)
    ready()
    code, direct = request("/predictions", payload, port=5064)
    assert code == 200 and direct["status"] == "succeeded"
    # Record only safe schema information, never the response's input payload.
    print("DIRECT_COG", code, "keys", sorted(direct), "output", direct["output"])
    before = command("docker", "compose", "exec", "-T", "classifier", "cat", "/var/log/ee471/classifier.log")
    image = (ROOT / "classifier/test-data/input.jpg").read_bytes()
    code, website = upload(image)
    assert code == 200 and website["output"] == direct["output"], (code, website)
    after = command("docker", "compose", "exec", "-T", "classifier", "cat", "/var/log/ee471/classifier.log")
    assert after.count("Prediction completed") == before.count("Prediction completed") + 1
    assert "data:image" not in after and "base64" not in after
    for data, expected in ((None, 400), (b"not a picture", 400), (b"x" * (5 * 1024 * 1024 + 1), 413)):
        code, error = upload(data)
        assert code == expected and "error" in error and "output" not in error
    print("REAL_WEBSITE: matching output, one new model log; missing/corrupt/oversized rejected")
    command("docker", "compose", "stop", "classifier")
    try:
        code, failure = upload(image)
        assert code == 503 and "connect" in failure["error"].lower(), (code, failure)
        print("REAL_CONNECTION_FAILURE", code, failure["error"])
    finally:
        command("docker", "compose", "start", "classifier")
    ready()
    code, recovered = upload(image)
    assert code == 200 and recovered["output"] == direct["output"]
    print("REAL_RECOVERY: succeeded; both Compose services left running")
    (ROOT / "outputs/stack-result.json").write_text(json.dumps({
        "status": "succeeded", "output": direct["output"], "mock_tests": test_count,
        "real_website": True, "direct_cog": True, "connection_recovery": True,
        "postman_application_used": False
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
