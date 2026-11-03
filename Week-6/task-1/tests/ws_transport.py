"""Bounded localhost WebSocket test client with a browser-style Host header.

Standard library only. Not application code; no audio device or Azure access.
"""
import base64
import hashlib
import os
import socket
import struct


class HandshakeError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"WebSocket handshake rejected: {status_code}")


class Client:
    def __init__(self, host, port, origin):
        self.socket = socket.create_connection((host, port), timeout=3)
        self.buffer = b""
        key = base64.b64encode(os.urandom(16)).decode()
        request = (f"GET /ws/diarization HTTP/1.1\r\nHost: {host}:{port}\r\n"
                   f"Origin: {origin}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                   f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        self.socket.sendall(request.encode())
        headers = b""
        while b"\r\n\r\n" not in headers:
            part = self.socket.recv(4096)
            if not part:
                self.socket.close()
                raise EOFError("WebSocket closed during handshake")
            headers += part
            if len(headers) > 16384:
                self.socket.close()
                raise AssertionError("Oversized WebSocket handshake")
        head, self.buffer = headers.split(b"\r\n\r\n", 1)
        status = int(head.split(b" ")[1])
        if status != 101:
            self.socket.close()
            raise HandshakeError(status)
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest())
        assert b"sec-websocket-accept: " + accept.lower() in head.lower()

    def _read(self, size):
        while len(self.buffer) < size:
            data = self.socket.recv(max(4096, size - len(self.buffer)))
            if not data:
                raise EOFError("WebSocket closed")
            self.buffer += data
        result, self.buffer = self.buffer[:size], self.buffer[size:]
        return result

    def _send(self, data, opcode):
        assert len(data) <= 65535
        mask = os.urandom(4)
        length = len(data)
        header = bytes([0x80 | opcode, 0x80 | (length if length < 126 else 126)])
        if length >= 126:
            header += struct.pack("!H", length)
        self.socket.sendall(header + mask + bytes(byte ^ mask[i % 4] for i, byte in enumerate(data)))

    def send(self, data):
        self._send(data if isinstance(data, bytes) else data.encode(), 2 if isinstance(data, bytes) else 1)

    def receive(self, timeout=3):
        self.socket.settimeout(timeout)
        for _ in range(8):
            first, second = self._read(2)
            assert first & 0x80, "Fragmented test response unsupported"
            length = second & 127
            if length == 126:
                length = struct.unpack("!H", self._read(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._read(8))[0]
            assert length <= 65536 and not second & 0x80
            data = self._read(length)
            opcode = first & 15
            if opcode == 1:
                return data.decode()
            if opcode == 8:
                raise EOFError("WebSocket closed")
            if opcode == 9:
                self._send(data, 10)
        raise AssertionError("Too many WebSocket control frames")

    def close(self):
        try:
            self._send(struct.pack("!H", 1000), 8)
        except OSError:
            pass
        self.socket.close()
