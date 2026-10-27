"""Speech translation mock tests: never read .env or call Azure."""

import io
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as web
import speech_service as service
from test_stt import wav_bytes
from continuous_mock import wire_continuous


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.dotenv = patch.object(service, "load_dotenv").start()
        patch.dict(os.environ, {"SPEECH_KEY": "test-placeholder", "SPEECH_REGION": "eastus"}, clear=True).start()
        self.config = patch.object(service.speechsdk.translation, "SpeechTranslationConfig").start()
        self.recognizer = patch.object(service.speechsdk.translation, "TranslationRecognizer").start()
        self.stream = patch.object(service.speechsdk.audio, "PushAudioInputStream").start()
        self.audio_format = patch.object(service.speechsdk.audio, "AudioStreamFormat").start()
        self.audio_config = patch.object(service.speechsdk.audio, "AudioConfig").start()
        self.result = SimpleNamespace(reason=service.speechsdk.ResultReason.TranslatedSpeech,
                                      text="Hello", translations={"tr": "Merhaba", "en": "Hello"})
        wire_continuous(self.recognizer.return_value, self.stream.return_value, lambda: self.result, kind="translate")
        self.client = web.app.test_client()
        self.wav = wav_bytes()

    def post(self, audio=None, source="en-US", target="tr", filename="sample.wav"):
        return self.client.post("/api/translate", data={
            "audio": (io.BytesIO(self.wav if audio is None else audio), filename),
            "source_language": source, "target_language": target,
        })

    def test_success_both_directions_and_sdk_contract(self):
        for source, target in service.TRANSLATION_PAIRS.items():
            with self.subTest(source=source):
                response = self.post(source=source, target=target)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json, {
                    "recognized_text": "Hello", "translated_text": self.result.translations[target],
                    "source_language": source, "target_language": target,
                })
                self.config.assert_called_with(subscription="test-placeholder", region="eastus")
                self.assertEqual(self.config.return_value.speech_recognition_language, source)
                self.config.return_value.add_target_language.assert_called_with(target)
                self.audio_format.assert_called_with(samples_per_second=16000, bits_per_sample=16, channels=1)
                self.audio_config.assert_called_with(stream=self.stream.return_value)
                self.recognizer.assert_called_with(translation_config=self.config.return_value,
                                                   audio_config=self.audio_config.return_value)
                self.recognizer.return_value.start_continuous_recognition_async.assert_called_with()
                self.recognizer.return_value.stop_continuous_recognition_async.assert_called_with()
                self.stream.return_value.write.assert_called_with(self.wav[44:])
                self.stream.return_value.close.assert_called()
                self.dotenv.assert_called_with(dotenv_path=service.ENV_PATH, override=False)

    def test_invalid_language_pairs(self):
        for source, target in [("en-US", "en"), ("tr-TR", "tr"), ("en", "tr"),
                               ("de-DE", "tr"), ("en-US", "tr-TR"), ("", "tr"), ("en-US", "")]:
            self.assertEqual(self.post(source=source, target=target).status_code, 400)
        self.dotenv.assert_not_called()
        self.recognizer.assert_not_called()

    def test_invalid_audio_and_limits(self):
        for audio in [b"", b"not wav", self.wav[:-1], wav_bytes(channels=2),
                      wav_bytes(width=1), wav_bytes(rate=24000), wav_bytes(seconds=30.01)]:
            self.assertEqual(self.post(audio=audio).status_code, 400)
        for size in [service.MAX_FILE_BYTES + 1, web.app.config["MAX_CONTENT_LENGTH"] + 1]:
            response = self.post(audio=b"x" * size)
            self.assertEqual(response.status_code, 413)
            self.assertIn("error", response.json)
        self.dotenv.assert_not_called()
        self.recognizer.assert_not_called()

    def test_missing_file_and_wrong_content_type(self):
        response = self.client.post("/api/translate", data={"source_language": "en-US", "target_language": "tr"},
                                    content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.post(filename="").status_code, 400)
        self.assertEqual(self.client.post("/api/translate", json={}).status_code, 400)
        self.recognizer.assert_not_called()

    def test_no_match_and_empty_original_text(self):
        for reason, text in [(service.speechsdk.ResultReason.NoMatch, ""),
                             (service.speechsdk.ResultReason.TranslatedSpeech, " \n")]:
            self.result.reason, self.result.text = reason, text
            response = self.post()
            self.assertEqual(response.status_code, 422)
            self.assertIn("error", response.json)
            self.assertNotIn("translated_text", response.json)

    def test_missing_translation_is_not_success(self):
        for translations in [{}, {"tr": ""}, {"tr": " \n"}, {"en": "wrong target"}]:
            self.result.translations = translations
            response = self.post()
            self.assertEqual(response.status_code, 502)
            self.assertIn("çeviri", response.json["error"])
        self.result.reason = service.speechsdk.ResultReason.RecognizedSpeech
        self.assertEqual(self.post().status_code, 502)

    def test_cancellation_and_exceptions_are_sanitized(self):
        codes = service.speechsdk.CancellationErrorCode
        self.result.reason = service.speechsdk.ResultReason.Canceled
        for code, message in [(codes.AuthenticationFailure, "kimlik"), (codes.TooManyRequests, "kota"),
                              (codes.ConnectionFailure, "bağlantı"), (codes.ServiceTimeout, "zaman"),
                              (codes.ServiceError, "hata")]:
            self.result.cancellation_details = SimpleNamespace(error_code=code, error_details="private-sdk-detail")
            response = self.post()
            self.assertEqual(response.status_code, 502)
            self.assertIn(message, response.json["error"])
            self.assertNotIn("private-sdk-detail", response.get_data(as_text=True))
        self.recognizer.side_effect = RuntimeError("private-sdk-detail test-placeholder")
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("test-placeholder", response.get_data(as_text=True))
        self.assertNotIn("private-sdk-detail", response.get_data(as_text=True))

    def test_missing_configuration(self):
        for key, region in [("", "eastus"), ("test-placeholder", "")]:
            with patch.dict(os.environ, {"SPEECH_KEY": key, "SPEECH_REGION": region}, clear=True):
                self.assertEqual(self.post().status_code, 503)
        self.recognizer.assert_not_called()

    def test_stream_cleanup_on_write_failure_and_lock_release(self):
        self.stream.return_value.write.side_effect = RuntimeError("private-sdk-detail")
        self.assertEqual(self.post().status_code, 502)
        self.stream.return_value.close.assert_called_once()
        acquired = service._speech_lock.acquire(blocking=False)
        if acquired:
            service._speech_lock.release()
        self.assertTrue(acquired)

    def test_translation_enters_the_common_lock(self):
        from unittest.mock import MagicMock
        lock = MagicMock()
        with patch.object(service, "_speech_lock", lock):
            self.assertEqual(self.post().status_code, 200)
        lock.__enter__.assert_called_once()
        lock.__exit__.assert_called_once()

    def test_unexpected_error_is_sanitized(self):
        with patch.object(web, "translate_pcm", side_effect=RuntimeError("private-detail")):
            response = self.post()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-detail", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
