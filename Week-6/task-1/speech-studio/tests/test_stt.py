"""Offline tests: no real Azure calls and no real dotenv reads."""

import io
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as web
import speech_service as service
from continuous_mock import wire_continuous


def wav_bytes(seconds=1, channels=1, width=2, rate=16000):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(rate)
        wav.writeframes(b"\x00" * int(seconds * rate * channels * width))
    return buffer.getvalue()


def replace_u32(data, offset, value):
    result = bytearray(data)
    struct.pack_into("<I", result, offset, value)
    return bytes(result)


class STTTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        web.app.config.update(TESTING=True)
        self.client = web.app.test_client()
        self.dotenv = patch.object(service, "load_dotenv").start()
        patch.dict(os.environ, {"SPEECH_KEY": "test-placeholder", "SPEECH_REGION": "eastus"}, clear=True).start()
        self.config_factory = patch.object(service.speechsdk, "SpeechConfig").start()
        self.format_factory = patch.object(service.speechsdk.audio, "AudioStreamFormat").start()
        self.stream_factory = patch.object(service.speechsdk.audio, "PushAudioInputStream").start()
        self.audio_factory = patch.object(service.speechsdk.audio, "AudioConfig").start()
        self.recognizer_factory = patch.object(service.speechsdk, "SpeechRecognizer").start()
        self.recognizer = self.recognizer_factory.return_value
        self.result = SimpleNamespace(reason=service.speechsdk.ResultReason.RecognizedSpeech, text="Merhaba dünya.")
        wire_continuous(self.recognizer, self.stream_factory.return_value, lambda: self.result)
        self.wav = wav_bytes()

    def post(self, audio=None, language="en-US", filename="sample.wav"):
        return self.client.post("/api/stt", data={
            "audio": (io.BytesIO(self.wav if audio is None else audio), filename),
            "language": language,
        }, content_type="multipart/form-data")

    def test_success_for_both_languages_and_sdk_stream_contract(self):
        for language in ["en-US", "tr-TR"]:
            with self.subTest(language=language):
                response = self.post(language=language)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json, {"text": "Merhaba dünya."})
                self.config_factory.assert_called_with(subscription="test-placeholder", region="eastus")
                self.assertEqual(self.config_factory.return_value.speech_recognition_language, language)
                self.format_factory.assert_called_with(samples_per_second=16000, bits_per_sample=16, channels=1)
                self.audio_factory.assert_called_with(stream=self.stream_factory.return_value)
                self.stream_factory.return_value.write.assert_called_with(self.wav[44:])
                self.stream_factory.return_value.close.assert_called()
                self.recognizer.start_continuous_recognition_async.assert_called_with()
                self.recognizer.stop_continuous_recognition_async.assert_called_with()
                self.dotenv.assert_called_with(dotenv_path=service.ENV_PATH, override=False)
                self.assertEqual(service.ENV_PATH, Path(service.__file__).resolve().parent / ".env")

    def test_no_match_and_empty_recognition_are_not_success(self):
        for reason, text in [(service.speechsdk.ResultReason.NoMatch, ""),
                             (service.speechsdk.ResultReason.RecognizedSpeech, " \n")]:
            self.result.reason, self.result.text = reason, text
            response = self.post()
            self.assertEqual(response.status_code, 422)
            self.assertIn("error", response.json)
            self.assertNotIn("text", response.json)

    def test_cancellation_errors_are_sanitized(self):
        codes = service.speechsdk.CancellationErrorCode
        for code, message in [(codes.AuthenticationFailure, "kimlik"),
                              (codes.TooManyRequests, "kota"),
                              (codes.ConnectionFailure, "bağlantı"),
                              (codes.ServiceTimeout, "zaman"),
                              (codes.ServiceError, "hata")]:
            with self.subTest(code=code):
                self.result.reason = service.speechsdk.ResultReason.Canceled
                self.result.cancellation_details = SimpleNamespace(error_code=code, error_details="private-sdk-detail")
                response = self.post()
                self.assertEqual(response.status_code, 502)
                self.assertIn(message, response.json["error"])
                self.assertNotIn("private-sdk-detail", response.get_data(as_text=True))

    def test_sdk_exception_and_stream_cleanup(self):
        self.stream_factory.return_value.write.side_effect = RuntimeError("private-sdk-detail")
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private-sdk-detail", response.get_data(as_text=True))
        self.assertNotIn("test-placeholder", response.get_data(as_text=True))
        self.stream_factory.return_value.close.assert_called_once()

    def test_unexpected_result_is_not_success(self):
        self.result.reason = service.speechsdk.ResultReason.RecognizingSpeech
        self.assertEqual(self.post().status_code, 502)

    def test_missing_configuration(self):
        for key, region in [("", ""), ("", "eastus"), ("test-placeholder", "")]:
            with patch.dict(os.environ, {"SPEECH_KEY": key, "SPEECH_REGION": region}, clear=True):
                response = self.post()
                self.assertEqual(response.status_code, 503)
                self.assertIn("SPEECH_KEY", response.json["error"])
        self.recognizer_factory.assert_not_called()

    def test_missing_file_language_or_wrong_request_type(self):
        responses = [
            self.client.post("/api/stt", json={"language": "en-US"}),
            self.client.post("/api/stt", data={"language": "en-US"}, content_type="multipart/form-data"),
            self.post(language="de-DE"), self.post(language=""), self.post(filename=""),
        ]
        for response in responses:
            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.json)
        self.dotenv.assert_not_called()
        self.recognizer_factory.assert_not_called()

    def test_invalid_wav_and_formats_do_not_call_azure(self):
        compressed = bytearray(self.wav)
        struct.pack_into("<H", compressed, 20, 3)  # IEEE float, not PCM
        bad_alignment = bytearray(self.wav)
        struct.pack_into("<H", bad_alignment, 32, 4)
        invalid = [b"", b"not a wav", self.wav[:-1], self.wav + b"extra",
                   bytes(compressed), bytes(bad_alignment),
                   wav_bytes(channels=2), wav_bytes(width=1),
                   wav_bytes(rate=24000), wav_bytes(rate=44100),
                   wav_bytes(seconds=0), wav_bytes(seconds=30.01)]
        for audio in invalid:
            with self.subTest(length=len(audio)):
                response = self.post(audio=audio)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json)
        self.dotenv.assert_not_called()
        self.recognizer_factory.assert_not_called()

    def test_chunk_boundaries_and_declared_duration_are_validated(self):
        # A header claiming many samples cannot make a truncated WAV valid.
        for audio in [replace_u32(self.wav, 40, 960000),
                      replace_u32(self.wav, 16, 0xffffffff),
                      replace_u32(self.wav, 40, 31999)]:
            with self.assertRaises(service.InvalidAudioError):
                service.validate_wav(audio)
        # Unknown RIFF chunks are valid only when their sizes/padding are valid.
        with_chunk = self.wav[:12] + b"JUNK\x02\x00\x00\x00xx" + self.wav[12:]
        with_chunk = replace_u32(with_chunk, 4, len(with_chunk) - 8)
        self.assertEqual(service.validate_wav(with_chunk), self.wav[44:])

    def test_file_and_request_size_limits(self):
        for audio in [b"x" * (service.MAX_FILE_BYTES + 1),
                      b"x" * (web.app.config["MAX_CONTENT_LENGTH"] + 1)]:
            response = self.post(audio=audio)
            self.assertEqual(response.status_code, 413)
            self.assertIn("error", response.json)
        self.recognizer_factory.assert_not_called()

    def test_exact_30_seconds_and_valid_header_without_wav_extension(self):
        self.assertEqual(self.post(audio=wav_bytes(seconds=30), filename="upload.bin").status_code, 200)

    def test_each_request_gets_its_own_stream(self):
        from unittest.mock import MagicMock
        streams = [MagicMock(), MagicMock()]
        self.stream_factory.side_effect = streams
        for stream in streams:
            wire_continuous(self.recognizer, stream, lambda: self.result)
        for _ in range(2):
            self.assertEqual(self.post().status_code, 200)
        for stream in streams:
            stream.write.assert_called_once_with(self.wav[44:])
            stream.close.assert_called_once()

    def test_unexpected_error_is_sanitized(self):
        with patch.object(web, "transcribe_pcm", side_effect=RuntimeError("private-detail")):
            response = self.post()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-detail", response.get_data(as_text=True))

    def test_home_and_static_files_without_settings(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get("/")
            self.assertEqual(response.status_code, 200)
            self.assertIn("Speech Studio", response.get_data(as_text=True))
            self.assertIn("Speech to Text", response.get_data(as_text=True))
            self.assertIn("Text to Speech", response.get_data(as_text=True))
            for path in ["/static/style.css", "/static/script.js"]:
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code, 200)
        self.dotenv.assert_not_called()
        self.recognizer_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
