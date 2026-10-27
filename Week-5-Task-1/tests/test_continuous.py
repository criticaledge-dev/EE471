"""Whole-file lifecycle regression tests, with mocked SDK events only."""

import io
import threading
import traceback
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import app as web
import speech_service as service
from continuous_mock import Signal, cancellation_event, result_event, wire_continuous
from test_stt import wav_bytes


class ContinuousTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(service, "load_dotenv").start()
        patch.dict("os.environ", {"SPEECH_KEY": "test-placeholder", "SPEECH_REGION": "eastus"}, clear=True).start()
        patch.object(service, "RECOGNITION_TIMEOUT_SECONDS", 0.05).start()
        patch.object(service, "SDK_OPERATION_TIMEOUT_SECONDS", 0.2).start()
        patch.object(service.speechsdk, "SpeechConfig").start()
        patch.object(service.speechsdk.translation, "SpeechTranslationConfig").start()
        self.factory = patch.object(service.speechsdk, "SpeechRecognizer").start()
        patch.object(service.speechsdk.translation, "TranslationRecognizer", self.factory).start()
        self.recognizer = self.factory.return_value
        self.stream = patch.object(service.speechsdk.audio, "PushAudioInputStream").start().return_value
        patch.object(service.speechsdk.audio, "AudioStreamFormat").start()
        patch.object(service.speechsdk.audio, "AudioConfig").start()
        wire_continuous(self.recognizer, self.stream, lambda: None)
        self.wav = wav_bytes()
        self.scenario = lambda: self.recognizer.session_stopped.emit()
        self.stream.close.side_effect = lambda: self.scenario()
        self.client = web.app.test_client()

    def post(self, kind):
        fields = {"audio": (io.BytesIO(self.wav), "sample.wav")}
        fields.update({"source_language": "en-US", "target_language": "tr"} if kind == "translate"
                      else {"language": "en-US"})
        return self.client.post("/api/" + kind, data=fields)

    def final(self, kind, text, translated="Merhaba."):
        self.recognizer.recognized.emit(result_event(
            kind, (service.speechsdk.ResultReason.TranslatedSpeech if kind == "translate"
                   else service.speechsdk.ResultReason.RecognizedSpeech),
            text, {"tr": translated}))

    def assert_cleanup_and_unlocked(self):
        self.recognizer.stop_continuous_recognition_async.assert_called()
        self.stream.close.assert_called()
        for signal in [self.recognizer.recognized, self.recognizer.canceled, self.recognizer.session_stopped]:
            self.assertEqual(signal.handlers, [])
        acquired = service._speech_lock.acquire(blocking=False)
        if acquired:
            service._speech_lock.release()
        self.assertTrue(acquired)

    def test_two_finals_in_order_ignore_interim_and_speech_end(self):
        for kind in ["stt", "translate"]:
            def scenario():
                self.recognizer.recognizing.emit(NS(result=NS(text="Hello, the weather")))
                self.final(kind, "Hello, the weather is very nice today.", "Merhaba, bugün hava çok güzel.")
                self.recognizer.speech_end_detected.emit()
                self.recognizer.recognizing.emit(NS(result=NS(text="I'm going")))
                self.final(kind, "I'm going to the library.", "Kütüphaneye gidiyorum.")
                self.recognizer.session_stopped.emit()
            self.scenario = scenario
            response = self.post(kind)
            self.assertEqual(response.status_code, 200)
            expected = "Hello, the weather is very nice today. I'm going to the library."
            self.assertEqual(response.json["recognized_text" if kind == "translate" else "text"], expected)
            if kind == "translate":
                self.assertEqual(response.json["translated_text"], "Merhaba, bugün hava çok güzel. Kütüphaneye gidiyorum.")
            self.assert_cleanup_and_unlocked()

    def test_error_after_first_final_never_returns_partial_success_and_retry_works(self):
        for kind in ["stt", "translate"]:
            def scenario():
                self.final(kind, "First sentence.")
                self.recognizer.canceled.emit(cancellation_event(kind,
                    service.speechsdk.CancellationReason.Error,
                    service.speechsdk.CancellationErrorCode.ConnectionFailure))
                self.recognizer.session_stopped.emit()
            self.scenario = scenario
            response = self.post(kind)
            self.assertEqual(response.status_code, 502)
            self.assertNotIn("First sentence", response.get_data(as_text=True))
            self.assertNotIn("private-sdk-detail", response.get_data(as_text=True))
            self.assert_cleanup_and_unlocked()
            self.scenario = lambda: (self.final(kind, "Retry."), self.recognizer.session_stopped.emit())
            self.assertEqual(self.post(kind).status_code, 200)

    def test_silence_and_nomatch(self):
        for kind in ["stt", "translate"]:
            self.scenario = lambda: (
                self.recognizer.recognized.emit(NS(result=NS(reason=service.speechsdk.ResultReason.NoMatch))),
                self.recognizer.session_stopped.emit())
            self.assertEqual(self.post(kind).status_code, 422)
            self.assert_cleanup_and_unlocked()

    def test_partial_without_session_stopped_times_out(self):
        for kind in ["stt", "translate"]:
            self.scenario = lambda: self.final(kind, "Only the first sentence.")
            response = self.post(kind)
            self.assertEqual(response.status_code, 502)
            self.assertNotIn("Only the first", response.get_data(as_text=True))
            self.assert_cleanup_and_unlocked()

    def test_eof_cancellation_needs_session_stopped_user_cancellation_is_error(self):
        for kind in ["stt", "translate"]:
            def eof():
                self.final(kind, "Complete.")
                self.recognizer.canceled.emit(cancellation_event(kind, service.speechsdk.CancellationReason.EndOfStream))
            self.scenario = eof
            self.assertEqual(self.post(kind).status_code, 502)
            self.scenario = lambda: (eof(), self.recognizer.session_stopped.emit())
            self.assertEqual(self.post(kind).status_code, 200)
            self.scenario = lambda: self.recognizer.canceled.emit(
                cancellation_event(kind, service.speechsdk.CancellationReason.CancelledByUser))
            self.assertEqual(self.post(kind).status_code, 502)
            self.assert_cleanup_and_unlocked()

    def test_missing_second_translation_rejects_entire_response(self):
        self.scenario = lambda: (self.final("translate", "First."),
                                self.final("translate", "Second.", ""),
                                self.recognizer.session_stopped.emit())
        response = self.post("translate")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("recognized_text", response.json)
        self.assert_cleanup_and_unlocked()

    def test_callback_exception_propagates_and_stop_never_waits_in_callback(self):
        for kind in ["stt", "translate"]:
            def scenario():
                # SDK worker callback: malformed event must reach the request flow.
                self.recognizer.recognized.emit(NS())
            worker = None
            def spawn():
                nonlocal worker
                worker = threading.Thread(target=scenario, name="sdk-callback")
                worker.start()
            self.scenario = spawn
            self.recognizer.stop_continuous_recognition_async.side_effect = lambda: (
                self.assertNotEqual(threading.current_thread().name, "sdk-callback") or
                self.recognizer.stop_continuous_recognition_async.return_value)
            response = self.post(kind)
            worker.join(1)
            self.assertEqual(response.status_code, 502)
            self.assert_cleanup_and_unlocked()

    def test_start_and_stop_timeouts_are_bounded_and_do_not_report_success(self):
        self.scenario = lambda: (self.final("stt", "Complete."), self.recognizer.session_stopped.emit())
        for operation in ["start_continuous_recognition_async", "stop_continuous_recognition_async"]:
            with self.subTest(operation=operation):
                finished = threading.Event()
                future = getattr(self.recognizer, operation).return_value
                original = future.get.side_effect
                future.get.side_effect = lambda: finished.wait(1)
                try:
                    self.assertEqual(self.post("stt").status_code, 502)
                    self.assert_cleanup_and_unlocked()
                finally:
                    finished.set()
                    future.get.side_effect = original

    def test_signal_mock_matches_real_sdk_surface(self):
        signal = Signal()
        self.assertFalse(hasattr(service.speechsdk.EventSignal, "disconnect"))
        with self.assertRaises(AttributeError):
            signal.disconnect
        with self.assertRaises(TypeError):
            signal.disconnect_all(lambda: None)
        callback = lambda event: None
        signal.connect(callback)
        signal.disconnect_all()
        self.assertEqual(signal.handlers, [])

    def test_actual_sdk_signals_complete_multisentence_cleanup_offline(self):
        # Real EventSignal class, with no native recognizer/network connection.
        class Owner:
            _handle = None

        owner = Owner()
        for kind in ["stt", "translate"]:
            signals = [service.speechsdk.EventSignal(owner, lambda *_: None) for _ in range(3)]
            self.recognizer.recognized, self.recognizer.canceled, self.recognizer.session_stopped = signals

            def scenario():
                for text, translated in [("First sentence.", "İlk cümle."), ("Second sentence.", "İkinci cümle.")]:
                    signals[0].signal(NS(result=NS(
                        reason=(service.speechsdk.ResultReason.TranslatedSpeech if kind == "translate"
                                else service.speechsdk.ResultReason.RecognizedSpeech),
                        text=text, translations={"tr": translated})))
                signals[2].signal(NS())

            self.scenario = scenario
            response = self.post(kind)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["recognized_text" if kind == "translate" else "text"],
                             "First sentence. Second sentence.")
            self.assertTrue(all(not signal.is_connected() for signal in signals))
            acquired = service._speech_lock.acquire(blocking=False)
            if acquired:
                service._speech_lock.release()
            self.assertTrue(acquired)

    def test_cleanup_order_after_write_failure(self):
        order = []
        self.stream.write.side_effect = RuntimeError("private-write-detail")
        self.recognizer.stop_continuous_recognition_async.return_value.get.side_effect = lambda: order.append("stopped")
        for signal in [self.recognizer.recognized, self.recognizer.canceled, self.recognizer.session_stopped]:
            def disconnect(signal=signal):
                order.append("disconnect_all")
                signal.handlers.clear()
            signal.sdk.disconnect_all.side_effect = disconnect
        self.stream.close.side_effect = lambda: order.append("stream_closed")
        self.assertEqual(self.post("stt").status_code, 502)
        self.assertEqual(order, ["stopped", "disconnect_all", "disconnect_all", "disconnect_all", "stream_closed"])
        self.assert_cleanup_and_unlocked()

    def test_cleanup_failure_cannot_turn_success_into_200(self):
        self.scenario = lambda: (self.final("stt", "Complete."), self.recognizer.session_stopped.emit())
        signal = self.recognizer.recognized
        signal.sdk.disconnect_all.side_effect = RuntimeError("private-cleanup-detail")
        response = self.post("stt")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("Complete", response.get_data(as_text=True))
        self.assertNotIn("private-cleanup-detail", response.get_data(as_text=True))
        self.recognizer.stop_continuous_recognition_async.assert_called()
        acquired = service._speech_lock.acquire(blocking=False)
        if acquired:
            service._speech_lock.release()
        self.assertTrue(acquired)
        # Reset test instrumentation and confirm a later request can succeed.
        signal.handlers.clear()
        signal.sdk.disconnect_all.side_effect = signal.handlers.clear
        self.assertEqual(self.post("stt").status_code, 200)

    def test_primary_failure_and_traceback_survive_cleanup_failure(self):
        original = RuntimeError("private-write-detail")
        self.stream.write.side_effect = original
        self.recognizer.stop_continuous_recognition_async.return_value.get.side_effect = RuntimeError("private-stop-detail")
        try:
            service._continuous_pcm(object(), b"\0\0")
        except RuntimeError as caught:
            self.assertIs(caught, original)
            self.assertEqual(caught.cleanup_failures, (("stop", "SpeechServiceError"),))
            self.assertNotIn("private-stop-detail", str(caught.cleanup_failures))
            frames = traceback.extract_tb(caught.__traceback__)
            self.assertTrue(any(frame.name == "_continuous_pcm" and "stream.write" in frame.line for frame in frames))
        else:
            self.fail("The original write failure was masked")
        # Callback/session error is also primary even if stop subsequently fails.
        self.stream.write.side_effect = None
        self.scenario = lambda: self.recognizer.canceled.emit(cancellation_event("stt",
            service.speechsdk.CancellationReason.Error,
            service.speechsdk.CancellationErrorCode.AuthenticationFailure))
        with self.assertRaises(service.SpeechServiceError) as caught:
            service._continuous_pcm(object(), b"\0\0")
        self.assertIn("kimlik", caught.exception.public_message)
        self.assertEqual(caught.exception.cleanup_failures, (("stop", "SpeechServiceError"),))

    def test_partial_start_failure_cleans_owned_signals_and_stream(self):
        self.recognizer.start_continuous_recognition_async.return_value.get.side_effect = RuntimeError("private-start-detail")
        self.assertEqual(self.post("translate").status_code, 502)
        self.assert_cleanup_and_unlocked()
        self.recognizer.start_continuous_recognition_async.return_value.get.side_effect = None
        self.scenario = lambda: (self.final("translate", "Retry."), self.recognizer.session_stopped.emit())
        self.assertEqual(self.post("translate").status_code, 200)

    def test_partially_connected_signal_is_also_disconnected(self):
        signal = self.recognizer.recognized
        def partial_connect(handler):
            signal.handlers.append(handler)
            raise RuntimeError("private-connect-detail")
        signal.sdk.connect.side_effect = partial_connect
        self.assertEqual(self.post("stt").status_code, 502)
        self.assertEqual(signal.handlers, [])
        self.recognizer.stop_continuous_recognition_async.assert_called_once()
        self.stream.close.assert_called_once()

    def test_stt_and_translation_specs_have_distinct_result_and_cancellation_fields(self):
        stt = result_event("stt", service.speechsdk.ResultReason.RecognizedSpeech, "Fixture.")
        translation = result_event("translate", service.speechsdk.ResultReason.TranslatedSpeech,
                                   "Fixture.", {"tr": "Örnek."})
        with self.assertRaises(AttributeError):
            stt.result.translations
        self.assertEqual(translation.result.translations, {"tr": "Örnek."})
        canceled = cancellation_event("stt", service.speechsdk.CancellationReason.EndOfStream)
        with self.assertRaises(AttributeError):
            canceled.reason
        with self.assertRaises(AttributeError):
            canceled.error_code
        self.assertEqual(canceled.cancellation_details.reason, service.speechsdk.CancellationReason.EndOfStream)

    def test_multisentence_then_eof_with_distinct_sdk_specs_and_retry_after_error(self):
        for kind in ["stt", "translate"]:
            def success():
                self.final(kind, "First sentence.", "İlk cümle.")
                self.final(kind, "Second sentence.", "İkinci cümle.")
                self.recognizer.canceled.emit(cancellation_event(kind, service.speechsdk.CancellationReason.EndOfStream))
                self.recognizer.session_stopped.emit()

            self.scenario = success
            response = self.post(kind)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["recognized_text" if kind == "translate" else "text"],
                             "First sentence. Second sentence.")
            if kind == "translate":
                self.assertEqual(response.json["translated_text"], "İlk cümle. İkinci cümle.")
            self.assert_cleanup_and_unlocked()
            self.scenario = lambda: self.recognizer.canceled.emit(cancellation_event(kind,
                service.speechsdk.CancellationReason.Error,
                service.speechsdk.CancellationErrorCode.ConnectionFailure))
            response = self.post(kind)
            self.assertEqual(response.status_code, 502)
            self.assertIn("bağlantı", response.json["error"])
            self.assertNotIn("sonucu işlenemedi", response.json["error"])
            self.assert_cleanup_and_unlocked()
            self.scenario = success
            self.assertEqual(self.post(kind).status_code, 200)


if __name__ == "__main__":
    unittest.main()
