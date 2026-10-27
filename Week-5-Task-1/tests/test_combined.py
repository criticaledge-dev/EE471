"""Combined app tests; SDK and dotenv are mocked, with no Azure access."""

import io
from html.parser import HTMLParser
from pathlib import Path
import sys
from threading import Event, Lock, Thread, current_thread
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as web
import speech_service as service
from continuous_mock import wire_continuous


def make_wav(seconds=1):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b"\0\0" * (16000 * seconds))
    return buffer.getvalue()


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.labels = []
        self.options = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "label":
            self.labels.append(attrs["for"])
        if tag == "option":
            self.options.append(attrs["value"])


class CombinedTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.dotenv = patch.object(service, "load_dotenv").start()
        patch.dict("os.environ", {"SPEECH_KEY": "test-placeholder", "SPEECH_REGION": "eastus"}, clear=True).start()
        self.config = patch.object(service.speechsdk, "SpeechConfig").start()
        self.synth = patch.object(service.speechsdk, "SpeechSynthesizer").start()
        self.recognizer = patch.object(service.speechsdk, "SpeechRecognizer").start()
        self.stream = patch.object(service.speechsdk.audio, "PushAudioInputStream").start()
        patch.object(service.speechsdk.audio, "AudioStreamFormat").start()
        patch.object(service.speechsdk.audio, "AudioConfig").start()
        self.wav = make_wav()
        self.synth.return_value.speak_text_async.return_value.get.return_value = SimpleNamespace(
            reason=service.speechsdk.ResultReason.SynthesizingAudioCompleted, audio_data=self.wav)
        result = SimpleNamespace(reason=service.speechsdk.ResultReason.RecognizedSpeech, text="Hello world")
        wire_continuous(self.recognizer.return_value, self.stream.return_value, lambda: result)
        self.client = web.app.test_client()

    def test_both_features_unique_ids_and_languages_without_configuration(self):
        with patch.dict("os.environ", {}, clear=True):
            page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        parser = PageParser()
        html = page.get_data(as_text=True)
        parser.feed(html)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertTrue(set(parser.labels).issubset(parser.ids))
        for element in ["tts-form", "stt-form", "tts-audio", "tts-download", "stt-copy", "stt-download"]:
            self.assertIn(element, parser.ids)
        self.assertEqual(parser.options.count("en-US"), 4)
        self.assertEqual(parser.options.count("tr-TR"), 3)
        self.assertIn("translation-form", parser.ids)
        self.assertIn("translation-original", parser.ids)
        self.assertIn("translation-text", parser.ids)
        self.assertIn("pronunciation-form", parser.ids)
        self.assertIn("pronunciation-reference", parser.ids)
        self.assertIn("pronunciation-result", parser.ids)
        self.assertIn("diarization-start", parser.ids)
        self.assertIn("diarization-finals", parser.ids)
        self.assertIn("30 saniye", html)
        self.dotenv.assert_not_called()

    def test_mock_tts_wav_can_be_uploaded_directly_to_stt(self):
        tts = self.client.post("/api/tts", json={"text": "Hello world", "language": "en-US"})
        self.assertEqual(tts.status_code, 200)
        with wave.open(io.BytesIO(tts.data)) as wav:
            self.assertEqual((wav.getframerate(), wav.getsampwidth(), wav.getnchannels(), wav.getcomptype()),
                             (16000, 2, 1, "NONE"))
        self.config.return_value.set_speech_synthesis_output_format.assert_called_once_with(
            service.speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
        response = self.client.post("/api/stt", data={
            "audio": (io.BytesIO(tts.data), "speech.wav"), "language": "en-US"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"text": "Hello world"})
        self.stream.return_value.write.assert_called_once_with(self.wav[44:])

    def test_long_tts_wav_still_rejected_by_stt(self):
        self.synth.return_value.speak_text_async.return_value.get.return_value.audio_data = make_wav(31)
        tts = self.client.post("/api/tts", json={"text": "Long text", "language": "en-US"})
        self.assertEqual(tts.status_code, 200)
        response = self.client.post("/api/stt", data={
            "audio": (io.BytesIO(tts.data), "long.wav"), "language": "en-US"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("30 saniye", response.json["error"])
        self.recognizer.assert_not_called()

    def test_tts_and_stt_share_server_lock(self):
        entered_tts, attempted_stt, release_tts = Event(), Event(), Event()
        lock = Lock()
        results, errors = {}, []

        class ObservedLock:
            def __enter__(self):
                if current_thread().name == "stt-test":
                    attempted_stt.set()
                lock.acquire()

            def __exit__(self, *args):
                lock.release()

        original_result = self.synth.return_value.speak_text_async.return_value.get.return_value

        def delayed_result():
            entered_tts.set()
            if not release_tts.wait(3):
                raise RuntimeError("Test timeout")
            return original_result

        def run(name, operation):
            try:
                results[name] = operation()
            except Exception as error:
                errors.append(error)

        self.synth.return_value.speak_text_async.return_value.get.side_effect = delayed_result
        tts_thread = Thread(target=run, args=("tts", lambda: service.synthesize_speech("Hello", "en-US")))
        stt_thread = Thread(name="stt-test", target=run,
                            args=("stt", lambda: service.transcribe_pcm(self.wav[44:], "en-US")))
        with patch.object(service, "_speech_lock", ObservedLock()):
            tts_thread.start()
            try:
                self.assertTrue(entered_tts.wait(2))
                stt_thread.start()
                self.assertTrue(attempted_stt.wait(2))
                self.recognizer.assert_not_called()
                self.assertEqual(self.config.call_count, 1)
            finally:
                release_tts.set()
                tts_thread.join(3)
                if stt_thread.ident is not None:
                    stt_thread.join(3)
        self.assertFalse(tts_thread.is_alive())
        self.assertFalse(stt_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(results, {"tts": self.wav, "stt": "Hello world"})

    def test_service_failure_releases_shared_lock(self):
        self.synth.side_effect = RuntimeError("private-sdk-detail")
        self.assertEqual(self.client.post("/api/tts", json={"text": "Hello", "language": "en-US"}).status_code, 502)
        acquired = service._speech_lock.acquire(blocking=False)
        if acquired:
            service._speech_lock.release()
        self.assertTrue(acquired)
        response = self.client.post("/api/stt", data={
            "audio": (io.BytesIO(self.wav), "speech.wav"), "language": "en-US"})
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
