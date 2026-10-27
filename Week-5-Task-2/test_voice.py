"""Offline API/lifecycle tests. No real .env load or Azure request."""
import io
import os
import struct
import unittest
import wave
from unittest.mock import create_autospec, patch

import speech_service as s
from app import app


def wav(seconds=0.01, rate=16000, channels=1, width=2):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(width)
        audio.setframerate(rate)
        audio.writeframes(b"\0" * int(seconds * rate) * channels * width)
    return output.getvalue()


class Signal:
    def __init__(self):
        self.handlers = []
        self.sdk = create_autospec(s.speechsdk.EventSignal, instance=True, spec_set=True)
        self.sdk.connect.side_effect = self.handlers.append
        self.sdk.disconnect_all.side_effect = self.handlers.clear

    def emit(self, event=None):
        for handler in list(self.handlers):
            handler(event)


def result(text, reason=None):
    event = create_autospec(s.speechsdk.SpeechRecognitionEventArgs, instance=True, spec_set=True)
    value = create_autospec(s.speechsdk.SpeechRecognitionResult, instance=True, spec_set=True)
    value.reason = reason or s.speechsdk.ResultReason.RecognizedSpeech
    value.text = text
    event.result = value
    return event


def canceled(reason, code=None):
    event = create_autospec(s.speechsdk.SpeechRecognitionCanceledEventArgs, instance=True, spec_set=True)
    details = create_autospec(s.speechsdk.CancellationDetails, instance=True, spec_set=True)
    details.reason = reason
    details.code = code or s.speechsdk.CancellationErrorCode.NoError
    event.cancellation_details = details
    return event


class VoiceTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.dotenv = patch.object(s, "load_dotenv").start()
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {"SPEECH_KEY": "test-placeholder", "SPEECH_REGION": "eastus"}).start()
        self.config = patch.object(s.speechsdk, "SpeechConfig", autospec=True).start()
        self.recognizer = create_autospec(s.speechsdk.SpeechRecognizer, instance=True, spec_set=True)
        self.signals = {name: Signal() for name in ("recognized", "canceled", "session_stopped", "recognizing")}
        for name, signal in self.signals.items():
            setattr(self.recognizer, name, signal.sdk)
        patch.object(s.speechsdk, "SpeechRecognizer", return_value=self.recognizer).start()
        self.stream = create_autospec(s.speechsdk.audio.PushAudioInputStream, instance=True, spec_set=True)
        patch.object(s.speechsdk.audio, "PushAudioInputStream", return_value=self.stream).start()
        patch.object(s.speechsdk.audio, "AudioConfig", autospec=True).start()
        patch.object(s.speechsdk.audio, "AudioStreamFormat", autospec=True).start()

    def emit(self, items, stopped=True):
        def close():
            for signal, event in items:
                self.signals[signal].emit(event)
            if stopped:
                self.signals["session_stopped"].emit()
        self.stream.close.side_effect = close

    def post(self, data=None):
        return self.client.post("/api/voice-input", data={"audio": (io.BytesIO(wav() if data is None else data), "command.wav")})

    def assert_reusable(self):
        self.assertTrue(s._speech_lock.acquire(blocking=False))
        s._speech_lock.release()
        for name in ("recognized", "canceled", "session_stopped"):
            self.signals[name].sdk.disconnect_all.assert_called()
        self.recognizer.stop_continuous_recognition_async.assert_called()

    def test_final_segments_and_eof(self):
        self.emit([("recognizing", result("ignored")), ("recognized", result("Five plus")),
                   ("recognized", result("two is.")),
                   ("canceled", canceled(s.speechsdk.CancellationReason.EndOfStream))])
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"text": "Five plus two is.", "language": "en-US"})
        self.assertEqual(self.config.return_value.speech_recognition_language, "en-US")
        self.dotenv.assert_called_once_with(dotenv_path=s.ENV_PATH, override=False)
        self.stream.write.assert_called_once_with(s.validate_wav(wav()))
        self.assert_reusable()

    def test_partial_result_then_service_error_is_not_success(self):
        self.emit([("recognized", result("five")), ("canceled", canceled(
            s.speechsdk.CancellationReason.Error, s.speechsdk.CancellationErrorCode.AuthenticationFailure))])
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("text", response.json)
        self.assert_reusable()
        self.emit([("recognized", result("two plus two is"))])
        self.assertEqual(self.post().status_code, 200)

    def test_silence(self):
        self.emit([("recognized", result("", s.speechsdk.ResultReason.NoMatch))])
        self.assertEqual(self.post().status_code, 422)
        self.assert_reusable()

    def test_unmatched_segment_cannot_silently_change_command(self):
        self.emit([("recognized", result("five plus two is")),
                   ("recognized", result("", s.speechsdk.ResultReason.NoMatch))])
        self.assertEqual(self.post().status_code, 422)
        self.assert_reusable()

    def test_timeout_and_cancel(self):
        self.emit([("recognized", result("five"))], stopped=False)
        with patch.object(s, "RECOGNITION_TIMEOUT_SECONDS", 0.01):
            self.assertEqual(self.post().status_code, 502)
        self.assert_reusable()
        self.emit([("canceled", canceled(s.speechsdk.CancellationReason.CancelledByUser))])
        self.assertEqual(self.post().status_code, 502)
        self.assert_reusable()

    def test_callback_and_cleanup_errors(self):
        self.emit([("recognized", object())])
        self.assertEqual(self.post().status_code, 502)
        self.assert_reusable()
        self.emit([("recognized", result("five plus two is"))])
        self.signals["recognized"].sdk.disconnect_all.side_effect = RuntimeError("private-native-detail")
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private-native-detail", response.get_data(as_text=True))
        self.assert_reusable()

    def test_start_failure_cleanup(self):
        self.recognizer.start_continuous_recognition_async.return_value.get.side_effect = RuntimeError("private")
        self.assertEqual(self.post().status_code, 502)
        self.assert_reusable()

    def test_missing_configuration_without_dotenv_read(self):
        with patch.dict(os.environ, {"SPEECH_KEY": "", "SPEECH_REGION": ""}):
            self.assertEqual(self.post().status_code, 503)
            self.assertEqual(self.client.get("/").status_code, 200)
        self.assertTrue(s._speech_lock.acquire(blocking=False))
        s._speech_lock.release()

    def test_wav_limits_and_format(self):
        self.assertEqual(len(s.validate_wav(wav(15))), 480000)
        bad = [b"", b"fake", wav(15.01), wav(rate=24000), wav(channels=2), wav(width=1), wav()[:-1],
               b"0" * (s.MAX_FILE_BYTES + 1)]
        malformed = bytearray(wav())
        struct.pack_into("<I", malformed, 28, 123)
        bad.append(bytes(malformed))
        for audio in bad:
            with self.subTest(length=len(audio)):
                self.assertEqual(self.post(audio).status_code, 400)
        self.config.assert_not_called()
        self.assertEqual(self.client.post("/api/voice-input").status_code, 400)
        huge = self.client.post("/api/voice-input", data=b"0" * (s.MAX_FILE_BYTES + 65537), content_type="multipart/form-data")
        self.assertEqual(huge.status_code, 413)

    def test_new_assets_and_controls(self):
        page = self.client.get("/").get_data(as_text=True)
        for control in ("voice-start", "voice-stop", "voice-transcript", "voice-command"):
            self.assertIn(f'id="{control}"', page)
        for file in ("voice-input.mjs", "voice-command.mjs", "voice-worklet.mjs", "pcm-resampler.mjs", "voice-audio.mjs"):
            response = self.client.get("/static/" + file)
            self.assertEqual(response.status_code, 200)
            self.assertIn("javascript", response.content_type)
        self.dotenv.assert_not_called()

    def test_required_voice_operands_use_real_calculator(self):
        for operation, x, y, expected in (("add", 5, 2, 7), ("subtract", 7, 3, 4), ("subtract", 6, 2, 4),
                                         ("multiply", 3, 2, 6), ("divide", 9, 3, 3),
                                         ("add", 1.5, 2, 3.5)):
            with self.subTest(operation=operation, x=x):
                response = self.client.post("/api/calculate", json={"operation": operation, "x": x, "y": y})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json, {"result": expected})


if __name__ == "__main__":
    unittest.main()
