"""Voice endpoint regressions and an opt-in real local Whisper check."""
import io
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch
import wave

from app import create_app
import speech_service
import whisper_service


def wav_bytes(pcm):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        wav.writeframes(pcm)
    return buffer.getvalue()


def post_wav(client, data, language="en-US"):
    return client.post(
        "/api/voice-input",
        data={"audio": (io.BytesIO(data), "speech.wav"), "language": language},
    )


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()
        self.enterContext(patch.dict(os.environ, clear=False))
        os.environ.pop("MP3_SPEECH_BACKEND", None)
        self.enterContext(patch.object(speech_service, "_whisper", None))
        self.settings = self.enterContext(patch.object(speech_service, "load_speech_settings"))

    def tearDown(self):
        self.settings.assert_not_called()

    def test_default_reuses_local_model_and_preserves_response(self):
        pcm = b"\x01\x00" * 160
        with (patch.object(whisper_service, "load_model", return_value=("processor", "model")) as load,
              patch.object(whisper_service, "transcribe", return_value="Hello.") as recognize):
            for _ in range(2):
                response = post_wav(self.client, wav_bytes(pcm))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json, {"text": "Hello.", "language": "en-US"})
            load.assert_called_once_with()
            self.assertEqual(recognize.call_count, 2)
            recognize.assert_called_with(pcm, 16000, "processor", "model")

    def test_malformed_wav_and_unsupported_language_are_rejected_before_model_load(self):
        with patch.object(whisper_service, "load_model") as load:
            self.assertEqual(post_wav(self.client, b"not a WAV").status_code, 400)
            self.assertEqual(post_wav(self.client, wav_bytes(b"\x01\x00"), "tr-TR").status_code, 400)
            load.assert_not_called()

    def test_digital_silence_returns_no_speech(self):
        with patch.object(whisper_service, "load_model") as load:
            self.assertEqual(post_wav(self.client, wav_bytes(b"\x00\x00" * 160)).status_code, 422)
            load.assert_not_called()

    def test_missing_model_reports_preparation_and_retries(self):
        with (patch.object(whisper_service, "load_model", side_effect=OSError) as load,
              self.assertLogs("speech_service", level="ERROR")):
            for _ in range(2):
                response = post_wav(self.client, wav_bytes(b"\x01\x00"))
                self.assertEqual(response.status_code, 503)
                self.assertIn("README", response.json["error"])
            self.assertEqual(load.call_count, 2)

    def test_explicit_azure_backend(self):
        os.environ["MP3_SPEECH_BACKEND"] = "azure"
        with (patch.object(speech_service, "_transcribe_azure", return_value="Azure test.") as azure,
              patch.object(whisper_service, "load_model") as load):
            response = post_wav(self.client, wav_bytes(b"\x01\x00"))
            self.assertEqual(response.json, {"text": "Azure test.", "language": "en-US"})
            azure.assert_called_once_with(b"\x01\x00")
            load.assert_not_called()

    @unittest.skipUnless(os.getenv("MP3_TEST_WAV"), "Set MP3_TEST_WAV to the Week 8 WAV for real inference.")
    def test_real_whisper_transcript(self):
        data = Path(os.environ["MP3_TEST_WAV"]).read_bytes()
        response = post_wav(self.client, data)
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json["language"], "en-US")
        normalize = lambda text: re.sub(r"[^a-z0-9]", "", text.casefold())
        self.assertEqual(normalize(response.json["text"]),
                         normalize("Send a text to Mike. I'll be home late tomorrow."))
        print(f"Whisper transcript: {response.json['text']}", flush=True)
