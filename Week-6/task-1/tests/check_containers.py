"""Ubuntu Docker checks. Never reads a real .env or calls Azure.

Run from task-1 with python3 tests/check_containers.py after building both images.
Only this task's temporary Compose services are removed in finally.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.request
from ws_transport import Client

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ["docker", "compose", "--env-file", "/dev/null", "-f", "compose.yaml",
           "-f", "tests/compose.offline.yaml"]


def command(*args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=180)
    if result.returncode:
        print(result.stdout + result.stderr, file=sys.stderr)
        result.check_returncode()
    return result.stdout + result.stderr


def bind(source, target):
    return ["--mount", f"type=bind,source={source},target={target},readonly"]


def task2_ids():
    return command("docker", "ps", "--filter", "label=com.docker.compose.project=ee471-week6-task2",
                   "--format", "{{.ID}} {{.Names}}").strip()


def get(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as response:
        return response.status, response.read(), response.headers.get_content_type()


def post(port, path, data):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as response:
        return response.code, json.load(response)


def main():
    previous_task2 = task2_ids()
    counts = {}
    for folder, image in (("speech-studio", "ee471-week6-speech-studio"),
                          ("voice-calculator", "ee471-week6-voice-calculator")):
        print(command("docker", "run", "--rm", "--network", "none",
                      *bind(ROOT / "tests", "/checks"),
                      image, "python", "-B", "/checks/native_probe.py"))
        if folder == "speech-studio":
            mounts = bind(ROOT / folder / "tests", "/app/tests")
            discovery = ["-s", "tests"]
        else:
            mounts = [part for file in (ROOT / folder).glob("test_*.py")
                      for part in bind(file, "/app/" + file.name)]
            discovery = []
        report = command("docker", "run", "--rm", "--network", "none", *mounts, image,
                         "python", "-B", "-m", "unittest", "discover", *discovery, "-v")
        print(report)
        counts[folder] = int(re.search(r"Ran (\d+) tests", report)[1])
    print(command("docker", "run", "--rm", "--network", "none",
                  *bind(ROOT / "speech-studio/tests", "/app/tests"),
                  *bind(ROOT / "tests", "/checks"),
                  "ee471-week6-speech-studio", "python", "-B", "/checks/probe_websocket.py"))
    try:
        print(command(*COMPOSE, "up", "-d", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "90"))
        for folder, port in (("speech-studio", 5081), ("voice-calculator", 5062)):
            code, html, _ = get(port, "/")
            assert code == 200
            assert b"SPEECH_KEY" not in html and b"offline-test" not in html
            for file in (ROOT / folder / "static").iterdir():
                if file.suffix not in (".js", ".mjs", ".css"):
                    continue
                code, content, mime = get(port, "/static/" + file.name)
                assert code == 200 and content == file.read_bytes(), file.name
                if file.suffix in (".js", ".mjs"):
                    assert mime in ("text/javascript", "application/javascript"), (file.name, mime)
            code, error = post(port, "/api/tts", {"text": "Offline fixture", "language": "en-US"})
            assert code == 503 and "error" in error, (folder, code)
        code, result = post(5062, "/api/calculate", {"operation": "multiply", "x": 4, "y": 6})
        assert code == 200 and result == {"result": 24}
        code, result = post(5062, "/api/calculate", {"operation": "divide", "x": 4, "y": 0})
        assert code == 400 and "error" in result
        # Browser-style WebSocket handshake against the actual published port,
        # missing settings must produce a safe error without contacting Azure.
        socket = Client("localhost", 5081, "http://localhost:5081")
        try:
            socket.send('{"type":"start","language":"en-US"}')
            error = json.loads(socket.receive())
            assert error["type"] == "error" and "SPEECH_KEY" in error["error"]
        finally:
            socket.close()
        print("Published localhost:5081 WebSocket missing-settings error/close passed (no Azure call)")
        print("REAL_HTTP: home/static/JS MIME on 5081+5062; calculate=24; divide-by-zero; missing Azure=503 passed")
    finally:
        print(command(*COMPOSE, "down"))
        assert task2_ids() == previous_task2, "Task 2 container state changed"
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs/container-checks.json").write_text(json.dumps({
        "python_tests": counts, "native_sdk": True, "websocket_mock_transport": True,
        "http_ports": [5081, 5062], "task2_preserved": True, "real_azure": False,
        "task1_test_containers_removed": True
    }, indent=2) + "\n")
    print("CHECKS_PASSED", json.dumps(counts), "Task 1 test services removed; Task 2 unchanged")


if __name__ == "__main__":
    main()
