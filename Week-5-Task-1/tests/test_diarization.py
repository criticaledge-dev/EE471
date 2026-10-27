"""Offline live-WebSocket protocol tests, using real SDK method/event specs."""

from collections import deque
import io
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import create_autospec, patch

import app as web
import diarization_service as live
import speech_service as shared
from continuous_mock import Signal
from test_stt import wav_bytes


class Clock:
    def __init__(self):
        self.time = 0
        self.step = 0.1

    def __call__(self):
        self.time += self.step
        return self.time


class Socket:
    def __init__(self, inputs):
        self.inputs = deque(inputs)
        self.sent = []
        self.closed = False
        self.sender = threading.get_ident()
        self.on_send = lambda payload: None

    def receive(self, timeout=None):
        if not self.inputs:
            return None
        value = self.inputs.popleft()
        if isinstance(value, Exception):
            raise value
        return value

    def send(self, payload):
        assert threading.get_ident() == self.sender, "Only owner loop may send"
        payload = json.loads(payload)
        self.sent.append(payload)
        self.on_send(payload)

    def close(self):
        self.closed = True


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        shared._live_session_active.clear()
        patch.object(shared, "load_dotenv").start()
        patch.dict("os.environ", {"SPEECH_KEY": "test-placeholder", "SPEECH_REGION": "eastus"}, clear=True).start()
        self.config = patch.object(live.sdk, "SpeechConfig", autospec=True).start()
        patch.object(live.sdk.audio, "AudioStreamFormat", autospec=True).start()
        self.stream_type = live.sdk.audio.PushAudioInputStream
        self.stream = patch.object(live.sdk.audio, "PushAudioInputStream", autospec=True).start().return_value
        patch.object(live.sdk.audio, "AudioConfig", autospec=True).start()
        self.transcriber_type = live.sdk.transcription.ConversationTranscriber
        self.factory = patch.object(live.sdk.transcription, "ConversationTranscriber", autospec=True, spec_set=True).start()
        self.transcriber = self.factory.return_value
        self.signals(self.transcriber)
        self.transcriber.start_transcribing_async.return_value.get.side_effect = lambda: self.transcriber.session_started.emit()
        self.stream.close.side_effect = lambda: self.transcriber.session_stopped.emit()
        self.clock = Clock()
        patch.object(live, "monotonic", self.clock).start()
        patch.object(live, "READY_TIMEOUT", 0.02).start()
        patch.object(shared, "SDK_OPERATION_TIMEOUT_SECONDS", 0.1).start()

    def signals(self, transcriber):
        for name in ["transcribing", "transcribed", "canceled", "session_started", "session_stopped"]:
            setattr(transcriber, name, Signal())

    def event(self, text="Fixture", speaker="Guest-1", result_id="one", final=True, offset=10000000, duration=5000000):
        result = create_autospec(live.sdk.transcription.ConversationTranscriptionResult, instance=True, spec_set=True)
        result.text, result.speaker_id, result.result_id = text, speaker, result_id
        result.offset, result.duration = offset, duration
        result.reason = live.sdk.ResultReason.RecognizedSpeech if final else live.sdk.ResultReason.RecognizingSpeech
        event = create_autospec(live.sdk.transcription.ConversationTranscriptionEventArgs, instance=True, spec_set=True)
        event.result = result
        return event

    def cancellation(self, reason, code=None):
        event = create_autospec(live.sdk.transcription.ConversationTranscriptionCanceledEventArgs, instance=True, spec_set=True)
        details = create_autospec(live.sdk.CancellationDetails, instance=True, spec_set=True)
        details.reason = reason
        details.code = code or live.sdk.CancellationErrorCode.NoError
        event.cancellation_details = details
        return event

    def socket(self, *inputs):
        return Socket([json.dumps({"type": "start", "language": "en-US"}), *inputs])

    def assert_unlocked(self):
        self.assertFalse(shared._live_session_active.is_set())
        acquired = shared._speech_lock.acquire(blocking=False)
        if acquired:
            shared._speech_lock.release()
        self.assertTrue(acquired)

    def test_interim_final_unknown_timing_and_final_during_stop(self):
        writes = 0
        def write(_pcm):
            nonlocal writes
            writes += 1
            if writes == 1:
                self.transcriber.transcribing.emit(self.event("Partial", "Unknown", final=False))
            else:
                event = self.event("First", "Guest-1")
                self.transcriber.transcribed.emit(event)
                self.transcriber.transcribed.emit(event)  # duplicate must not be appended
        self.stream.write.side_effect = write
        self.transcriber.stop_transcribing_async.return_value.get.side_effect = lambda: self.transcriber.transcribed.emit(
            self.event("Tail", "Guest-2", "two", offset=20000000))
        ws = self.socket(b"\x00\x00" * 1600, b"\x01\x00" * 1600, '{"type":"stop"}')
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[0]["type"], "ready")
        self.assertTrue(any(item["type"] == "interim" and item["speaker_id"] == "Unknown" for item in ws.sent))
        finals = [item for item in ws.sent if item["type"] == "final"]
        self.assertEqual([item["text"] for item in finals], ["First", "Tail"])
        self.assertEqual(finals[0]["offset_ms"], 1000)
        self.assertEqual(finals[0]["duration_ms"], 500)
        self.assertEqual(ws.sent[-1]["type"], "completed")
        self.stream.write.assert_any_call(b"\x01\x00" * 1600)
        self.config.return_value.set_property.assert_called_once_with(
            live.sdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults, "true")
        self.transcriber.stop_transcribing_async.assert_called_once()
        self.assertTrue(all(not getattr(self.transcriber, signal).handlers for signal in
                            ["transcribing", "transcribed", "canceled", "session_started", "session_stopped"]))
        self.assert_unlocked()

    def test_input_constraints_and_session_byte_limit(self):
        session = live.LiveSession()
        session.stream = self.stream
        for pcm in [b"", b"x", b"x" * (live.MAX_CHUNK_BYTES + 2), "not bytes"]:
            with self.assertRaises(shared.InvalidAudioError):
                session.write(pcm)
        session.total_bytes = live.MAX_SESSION_BYTES
        with self.assertRaises(shared.InvalidAudioError):
            session.write(b"\0\0")
        self.stream.write.assert_not_called()

    def test_sixty_second_limit_requests_flush_and_can_finish(self):
        self.clock.step = 20
        self.stream.write.side_effect = lambda pcm: self.transcriber.transcribed.emit(self.event())
        ws = self.socket(b"\0\0")
        ws.on_send = lambda payload: ws.inputs.append('{"type":"stop"}') if payload["type"] == "stop_requested" else None
        live.serve_diarization(ws)
        self.assertTrue(any(item["type"] == "stop_requested" for item in ws.sent))
        self.assertEqual(ws.sent[-1]["type"], "completed")
        self.assert_unlocked()

    def test_duration_limit_without_client_flush_is_error(self):
        self.clock.step = 20
        ws = self.socket()
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        self.assertFalse(any(item["type"] == "completed" for item in ws.sent))
        self.assert_unlocked()

    def test_disconnect_drain_timeout_and_service_error_release_lock(self):
        ws = self.socket(live.ConnectionClosed())
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        self.assert_unlocked()
        self.stream.close.side_effect = None
        ws = self.socket('{"type":"stop"}')
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        self.assert_unlocked()
        self.stream.write.side_effect = lambda pcm: self.transcriber.canceled.emit(self.cancellation(
            live.sdk.CancellationReason.Error, live.sdk.CancellationErrorCode.ConnectionFailure))
        ws = self.socket(b"\0\0")
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        self.assertIn("bağlantı", ws.sent[-1]["error"])
        self.assert_unlocked()

    def test_start_cleanup_failure_and_queue_bounds(self):
        self.transcriber.start_transcribing_async.return_value.get.side_effect = RuntimeError("private-detail")
        ws = self.socket()
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        self.assertNotIn("private-detail", str(ws.sent))
        self.assert_unlocked()
        session = live.LiveSession()
        for index in range(live.MAX_EVENTS + 1):
            session._result(self.event(result_id=str(index)), True)
        self.assertEqual(session.events.qsize(), live.MAX_EVENTS)
        self.assertIsNotNone(session.error)

    def test_missing_settings_invalid_start_and_origin(self):
        with patch.dict("os.environ", {}, clear=True):
            ws = self.socket()
            live.serve_diarization(ws)
            self.assertEqual(ws.sent[-1]["type"], "error")
        self.assert_unlocked()
        ws = Socket(['{"type":"start","language":"tr-TR"}'])
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        client = web.app.test_client()
        for origin in ["https://evil.example", "http://localhost:9999", "null", ""]:
            self.assertEqual(client.get("/ws/diarization", headers={"Origin": origin}).status_code, 403)
        self.assertTrue(live.allowed_origin("http://localhost:5000", "localhost:5000"))
        self.assertTrue(live.allowed_origin("http://127.0.0.1:5000", "127.0.0.1:5000"))
        self.assertFalse(live.allowed_origin("http://localhost:5000", "evil.example:5000"))
        for path in ["/static/diarization.js", "/static/pcm-worklet.mjs", "/static/pcm-resampler.mjs"]:
            with client.get(path) as response:
                self.assertEqual(response.status_code, 200)
                self.assertIn(response.mimetype, {"text/javascript", "application/javascript"})

    def test_busy_http_and_second_live_session_do_not_wait(self):
        shared._live_session_active.set()
        client = web.app.test_client()
        try:
            self.assertEqual(client.post("/api/tts", json={"text": "Hello", "language": "en-US"}).status_code, 409)
            for path, fields in [("stt", {"language": "en-US"}),
                                 ("translate", {"source_language": "en-US", "target_language": "tr"}),
                                 ("pronunciation", {"language": "en-US", "reference_text": "Hello"})]:
                response = client.post("/api/" + path, data={**fields, "audio": (io.BytesIO(wav_bytes()), "sample.wav")})
                self.assertEqual(response.status_code, 409)
                self.assertIn("meşgul", response.json["error"])
        finally:
            shared._live_session_active.clear()
        shared._speech_lock.acquire()
        try:
            ws = self.socket()
            live.serve_diarization(ws)
            self.assertIn("meşgul", ws.sent[-1]["error"])
        finally:
            shared._speech_lock.release()
        self.assert_unlocked()

    def test_sdk_callback_thread_never_sends_on_socket(self):
        def write(pcm):
            thread = threading.Thread(target=lambda: self.transcriber.transcribed.emit(self.event()))
            thread.start()
            thread.join(1)
        self.stream.write.side_effect = write
        ws = self.socket(b"\0\0", '{"type":"stop"}')
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "completed")
        self.assert_unlocked()

    def test_each_session_owns_transcriber_stream_and_listeners(self):
        transcribers, streams = [], []
        for index in range(2):
            transcriber = create_autospec(self.transcriber_type, instance=True, spec_set=True)
            self.signals(transcriber)
            transcriber.start_transcribing_async.return_value.get.side_effect = lambda t=transcriber: t.session_started.emit()
            stream = create_autospec(self.stream_type, instance=True, spec_set=True)
            stream.write.side_effect = lambda pcm, t=transcriber: t.transcribed.emit(self.event())
            stream.close.side_effect = lambda t=transcriber: t.session_stopped.emit()
            transcribers.append(transcriber)
            streams.append(stream)
        self.factory.side_effect = transcribers
        live.sdk.audio.PushAudioInputStream.side_effect = streams
        for _ in range(2):
            ws = self.socket(b"\0\0", '{"type":"stop"}')
            live.serve_diarization(ws)
            self.assertEqual(ws.sent[-1]["type"], "completed")
            self.assert_unlocked()
        for transcriber, stream in zip(transcribers, streams):
            transcriber.stop_transcribing_async.assert_called_once()
            stream.close.assert_called_once()
            self.assertFalse(transcriber.transcribed.handlers)

    def test_not_ready_callback_and_cleanup_errors_never_complete(self):
        self.transcriber.start_transcribing_async.return_value.get.side_effect = None
        ws = self.socket()
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        self.assertFalse(any(item["type"] == "ready" for item in ws.sent))
        self.assert_unlocked()
        self.transcriber.start_transcribing_async.return_value.get.side_effect = lambda: self.transcriber.session_started.emit()
        self.stream.write.side_effect = lambda pcm: self.transcriber.transcribed.emit(SimpleNamespace())
        ws = self.socket(b"\0\0")
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        self.assert_unlocked()
        self.stream.write.side_effect = lambda pcm: self.transcriber.transcribed.emit(self.event())
        self.transcriber.stop_transcribing_async.return_value.get.side_effect = RuntimeError("private-stop-detail")
        ws = self.socket(b"\0\0", '{"type":"stop"}')
        live.serve_diarization(ws)
        self.assertEqual(ws.sent[-1]["type"], "error")
        self.assertFalse(any(item["type"] == "completed" for item in ws.sent))
        self.assert_unlocked()


if __name__ == "__main__":
    unittest.main()
