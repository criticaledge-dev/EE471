"""Real local Flask-Sock transport; SDK callbacks mocked with SDK specs.

Run in the studio image with --network none, tests mounted at /app/tests.
No microphone, Azure, or actual .env access. Exercises the real route/Origin.
"""
import json
import sys
from threading import Thread
import time
import urllib.error
import urllib.request

from ws_transport import Client
from werkzeug.serving import WSGIRequestHandler, make_server

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/tests")
from test_diarization import LiveTests
import app as web
import speech_service as shared


class QuietHandler(WSGIRequestHandler):
    def log(self, *_args, **_kwargs):
        pass


fixture = LiveTests("test_interim_final_unknown_timing_and_final_during_stop")
fixture.setUp()
server = make_server("0.0.0.0", 5081, web.app, threaded=True, request_handler=QuietHandler)
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()


def unlocked():
    for _ in range(100):
        acquired = shared._speech_lock.acquire(blocking=False)
        if acquired:
            shared._speech_lock.release()
            assert not shared._live_session_active.is_set()
            return
        time.sleep(.01)
    raise AssertionError("Live lock not released")


def connect(origin="http://127.0.0.1:5081", hostname="127.0.0.1"):
    return Client(hostname, 5081, origin)


def receive(ws):
    payload = ws.receive(timeout=3)
    assert payload is not None, "WebSocket response timeout"
    return json.loads(payload)


try:
    fixture.stream.write.side_effect = lambda _pcm: fixture.transcriber.transcribed.emit(fixture.event("First"))
    fixture.transcriber.stop_transcribing_async.return_value.get.side_effect = lambda: fixture.transcriber.transcribed.emit(
        fixture.event("Tail", "Guest-2", "two"))
    ws = connect("http://localhost:5081", "localhost")
    ws.send(json.dumps({"type": "start", "language": "en-US"}))
    assert receive(ws)["type"] == "ready"
    # The same process must serve HTTP while WebSocket owns the speech lock.
    with urllib.request.urlopen("http://127.0.0.1:5081/", timeout=2) as response:
        assert response.status == 200
    req = urllib.request.Request("http://127.0.0.1:5081/api/tts",
        data=b'{"text":"Offline fixture","language":"en-US"}', headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=2)
        raise AssertionError("Expected busy HTTP response")
    except urllib.error.HTTPError as error:
        assert error.code == 409
    ws.send(b"\0\0")
    ws.send('{"type":"stop"}')
    messages = []
    for _ in range(12):
        message = receive(ws)
        messages.append(message)
        if message["type"] in ("completed", "error"):
            break
    assert messages[-1]["type"] == "completed", messages
    assert [m["text"] for m in messages if m["type"] == "final"] == ["First", "Tail"]
    ws.close()
    unlocked()
    print("Real WebSocket upgrade on Origin port 5081; concurrent HTTP/busy; ordered final/tail/completed; cleanup passed")

    ws = connect()
    ws.send('{"type":"start","language":"en-US"}')
    assert receive(ws)["type"] == "ready"
    ws.close()
    unlocked()
    print("Disconnect releases stream/listeners/lock; next session remains usable")
    fixture.transcriber.stop_transcribing_async.assert_called()
    assert not fixture.transcriber.transcribed.handlers

    for origin in ("http://localhost:5062", "http://localhost:5061", "http://127.0.0.1:5000", "http://example.com:5081"):
        try:
            denied = connect(origin)
        except Exception as error:
            assert getattr(error, "status_code", None) == 403, type(error).__name__
        else:
            denied.close()
            raise AssertionError("Cross-origin WebSocket accepted")
    assert web.allowed_origin("http://localhost:5081", "localhost:5081")
    print("Wrong Origin hostname/port denied with 403; localhost:5081 accepted")
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)
    fixture.doCleanups()
