"""Read-only checks against running Studio; no .env, SDK calls or other services."""
import json
import urllib.request

from ws_transport import Client, HandshakeError


def main():
    with urllib.request.urlopen("http://127.0.0.1:5081/", timeout=5) as response:
        assert response.status == 200
        assert b"Speech Studio" in response.read()
    for host in ("127.0.0.1", "localhost"):
        client = Client(host, 5081, f"http://{host}:5081")
        try:
            # Reject before settings/recognizer creation; never start Azure.
            client.send('{"type":"start","language":"unsupported-test-language"}')
            result = json.loads(client.receive())
            assert result["type"] == "error"
        finally:
            client.close()
    for origin in ("http://127.0.0.1:5061", "http://127.0.0.1:5062", "http://example.com:5081"):
        try:
            client = Client("127.0.0.1", 5081, origin)
        except HandshakeError as error:
            assert error.status_code == 403
        else:
            client.close()
            raise AssertionError("Wrong Origin was accepted")
    print("HTTP 127.0.0.1:5081=200; localhost/127.0.0.1 WebSocket upgrade+close passed; wrong Origin=403. No Azure call.")


if __name__ == "__main__":
    main()
