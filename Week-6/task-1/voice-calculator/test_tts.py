"""Offline Azure SDK-spec TTS tests; dotenv and native SDK calls are mocked."""
import os
import unittest
from unittest.mock import create_autospec, patch
import speech_service as s
from app import app
from test_voice import wav


class TtsTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.addCleanup(patch.stopall)
        self.dotenv = patch.object(s, "load_dotenv").start()
        patch.dict(os.environ, {"SPEECH_KEY": "test-placeholder", "SPEECH_REGION": "eastus"}).start()
        self.config = patch.object(s.speechsdk, "SpeechConfig", autospec=True).start()
        self.synth = create_autospec(s.speechsdk.SpeechSynthesizer, instance=True, spec_set=True)
        self.factory = patch.object(s.speechsdk, "SpeechSynthesizer", return_value=self.synth).start()
        self.result = create_autospec(s.speechsdk.SpeechSynthesisResult, instance=True, spec_set=True)
        self.result.reason = s.speechsdk.ResultReason.SynthesizingAudioCompleted
        self.result.audio_data = wav()
        self.synth.speak_text_async.return_value.get.return_value = self.result

    def assert_unlocked(self):
        self.assertTrue(s._speech_lock.acquire(blocking=False))
        s._speech_lock.release()

    def test_wav_output_and_sdk_configuration(self):
        response = self.client.post("/api/tts", json={"text": "is eight"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/wav")
        self.assertEqual(response.data, wav())
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.factory.assert_called_once_with(speech_config=self.config.return_value, audio_config=None)
        self.config.return_value.set_speech_synthesis_output_format.assert_called_once_with(
            s.speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
        self.assertEqual(self.config.return_value.speech_synthesis_voice_name, "en-US-JennyNeural")
        self.synth.speak_text_async.assert_called_once_with("is eight")
        self.dotenv.assert_called_once_with(dotenv_path=s.ENV_PATH, override=False)
        self.assert_unlocked()

    def test_invalid_requests(self):
        for data in (None, [], {}, {"text": 5}, {"text": " "}, {"text": "x" * 501}):
            self.assertEqual(self.client.post("/api/tts", json=data).status_code, 400)
        self.assertEqual(self.client.post("/api/tts", data="{", content_type="application/json").status_code, 400)
        self.dotenv.assert_not_called()

    def test_missing_settings(self):
        with patch.dict(os.environ, {"SPEECH_KEY": "", "SPEECH_REGION": ""}):
            self.assertEqual(self.client.post("/api/tts", json={"text": "one"}).status_code, 503)
            self.assertEqual(self.client.get("/").status_code, 200)
        self.assert_unlocked()

    def test_cancellations_and_native_errors_are_safe(self):
        self.result.reason = s.speechsdk.ResultReason.Canceled
        details = create_autospec(s.speechsdk.SpeechSynthesisCancellationDetails, instance=True, spec_set=True)
        self.result.cancellation_details = details
        for code in (s.speechsdk.CancellationErrorCode.AuthenticationFailure,
                     s.speechsdk.CancellationErrorCode.TooManyRequests,
                     s.speechsdk.CancellationErrorCode.ConnectionFailure):
            details.error_code = code
            response = self.client.post("/api/tts", json={"text": "one"})
            self.assertEqual(response.status_code, 502)
            self.assert_unlocked()
        self.synth.speak_text_async.side_effect = RuntimeError("private-native-detail")
        response = self.client.post("/api/tts", json={"text": "one"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private-native-detail", response.get_data(as_text=True))
        self.assert_unlocked()

    def test_invalid_audio_and_recovery(self):
        self.result.audio_data = b"bad"
        self.assertEqual(self.client.post("/api/tts", json={"text": "one"}).status_code, 502)
        self.assert_unlocked()
        self.result.audio_data = wav()
        self.assertEqual(self.client.post("/api/tts", json={"text": "one"}).status_code, 200)

    def test_speech_busy_does_not_affect_calculator(self):
        with s._speech_lock:
            self.assertEqual(self.client.post("/api/tts", json={"text": "one"}).status_code, 502)
            self.assertEqual(self.client.post("/api/calculate", json={"operation": "add", "x": 5, "y": 3}).json, {"result": 8})
