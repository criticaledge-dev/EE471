"""Offline pronunciation assessment tests: SDK specs and synthetic JSON only."""

import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as web
import speech_service as service
from continuous_mock import cancellation_event, result_event, wire_continuous
from test_stt import wav_bytes


def assessment_json():
    return {"NBest": [{"PronunciationAssessment": {
        "AccuracyScore": 91, "FluencyScore": 82, "CompletenessScore": 93, "PronScore": 86,
    }, "Words": [{"Word": "Hello", "PronunciationAssessment": {
        "AccuracyScore": 91, "ErrorType": "None",
    }}]}]}


class PronunciationTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.dotenv = patch.object(service, "load_dotenv").start()
        patch.dict(os.environ, {"SPEECH_KEY": "test-placeholder", "SPEECH_REGION": "eastus"}, clear=True).start()
        patch.object(service, "RECOGNITION_TIMEOUT_SECONDS", 0.05).start()
        patch.object(service, "SDK_OPERATION_TIMEOUT_SECONDS", 0.2).start()
        self.config = patch.object(service.speechsdk, "SpeechConfig", autospec=True, spec_set=True).start()
        self.assessment_config = patch.object(service.speechsdk, "PronunciationAssessmentConfig", autospec=True, spec_set=True).start()
        self.factory = patch.object(service.speechsdk, "SpeechRecognizer", autospec=True, spec_set=True).start()
        self.recognizer = self.factory.return_value
        self.stream = patch.object(service.speechsdk.audio, "PushAudioInputStream", autospec=True).start().return_value
        patch.object(service.speechsdk.audio, "AudioStreamFormat", autospec=True).start()
        patch.object(service.speechsdk.audio, "AudioConfig", autospec=True).start()
        wire_continuous(self.recognizer, self.stream, lambda: None)
        self.scenario = self.success
        self.stream.close.side_effect = lambda: self.scenario()
        self.client = web.app.test_client()
        self.wav = wav_bytes()

    def final(self, text="Hello.", payload=None):
        event = result_event("stt", service.speechsdk.ResultReason.RecognizedSpeech, text)
        # SpeechRecognitionResult.properties is a dict in SDK 1.53.0,
        # unlike SpeechConfig.properties (PropertyCollection).
        event.result.properties = {service.speechsdk.PropertyId.SpeechServiceResponse_JsonResult:
                                   json.dumps(assessment_json() if payload is None else payload)}
        self.recognizer.recognized.emit(event)

    def success(self):
        self.final()
        self.recognizer.session_stopped.emit()

    def post(self, audio=None, reference="Hello.", language="en-US", filename="sample.wav"):
        fields = {"audio": (io.BytesIO(self.wav if audio is None else audio), filename), "language": language}
        if reference is not None:
            fields["reference_text"] = reference
        return self.client.post("/api/pronunciation", data=fields)

    def assert_unlocked(self):
        acquired = service._speech_lock.acquire(blocking=False)
        if acquired:
            service._speech_lock.release()
        self.assertTrue(acquired)

    def test_single_segment_sdk_contract_and_real_score_fields(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        body = response.json
        self.assertTrue(body["session_complete"])
        self.assertTrue(body["assessment_complete"])
        self.assertEqual(body["scope"], "single_segment")
        self.assertEqual(body["score_scale"], 100)
        self.assertIsNone(body["overall_scores"])
        self.assertEqual(body["segments"][0]["scores"],
                         {"accuracy": 91, "fluency": 82, "completeness": 93, "pronunciation": 86})
        self.assertEqual(body["segments"][0]["words"], [{"word": "Hello", "accuracy": 91, "error_type": "None"}])
        self.assessment_config.assert_called_once_with(
            reference_text="Hello.", grading_system=service.speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=service.speechsdk.PronunciationAssessmentGranularity.Word, enable_miscue=False)
        self.assessment_config.return_value.apply_to.assert_called_once_with(self.recognizer)
        self.assessment_config.return_value.enable_prosody_assessment.assert_not_called()
        self.recognizer.start_continuous_recognition_async.assert_called_once()
        self.recognizer.recognize_once_async.assert_not_called()
        self.recognizer.stop_continuous_recognition_async.assert_called_once()
        self.assertEqual(self.recognizer.recognized.handlers, [])
        self.assert_unlocked()

    def test_configuration_applied_before_start(self):
        order = []
        self.assessment_config.return_value.apply_to.side_effect = lambda recognizer: order.append("apply_to")
        self.recognizer.start_continuous_recognition_async.return_value.get.side_effect = lambda: order.append("start")
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(order, ["apply_to", "start"])

    def test_multisegment_order_no_averaging_or_interim_duplicates(self):
        second = assessment_json()
        second["NBest"][0]["PronunciationAssessment"]["AccuracyScore"] = 63
        def scenario():
            self.recognizer.recognizing.emit(result_event("stt", service.speechsdk.ResultReason.RecognizingSpeech, "Partial"))
            self.final("First.")
            self.recognizer.speech_end_detected.emit()
            self.final("Second.", second)
            self.recognizer.session_stopped.emit()
        self.scenario = scenario
        response = self.post(reference="First. Second.")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["recognized_text"], "First. Second.")
        self.assertEqual(response.json["scope"], "segments_only")
        self.assertEqual([s["index"] for s in response.json["segments"]], [1, 2])
        self.assertEqual([s["scores"]["accuracy"] for s in response.json["segments"]], [91, 63])
        self.assertIsNone(response.json["overall_scores"])
        self.assert_unlocked()

    def test_missing_score_is_null_not_zero_and_scope_is_incomplete(self):
        payload = assessment_json()
        del payload["NBest"][0]["PronunciationAssessment"]["CompletenessScore"]
        del payload["NBest"][0]["Words"][0]["PronunciationAssessment"]["AccuracyScore"]
        self.scenario = lambda: (self.final(payload=payload), self.recognizer.session_stopped.emit())
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["assessment_complete"])
        self.assertIsNone(response.json["segments"][0]["scores"]["completeness"])
        self.assertIsNone(response.json["segments"][0]["words"][0]["accuracy"])
        self.assertTrue(response.json["warnings"])

    def test_real_zero_preserved_and_omission_word_score_not_used(self):
        payload = assessment_json()
        payload["NBest"][0]["PronunciationAssessment"]["AccuracyScore"] = 0
        payload["NBest"][0]["Words"][0]["PronunciationAssessment"]["ErrorType"] = "Omission"
        self.scenario = lambda: (self.final(payload=payload), self.recognizer.session_stopped.emit())
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["segments"][0]["scores"]["accuracy"], 0)
        self.assertIsNone(response.json["segments"][0]["words"][0]["accuracy"])

    def test_nomatch_segment_marks_partial_assessment(self):
        self.scenario = lambda: (self.final(), self.recognizer.recognized.emit(
            result_event("stt", service.speechsdk.ResultReason.NoMatch)), self.recognizer.session_stopped.emit())
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["assessment_complete"])
        self.assertEqual(response.json["unassessed_segments"], 1)

    def test_missing_malformed_or_invalid_assessment_is_error(self):
        for payload in [{}, {"NBest": []}, {"NBest": [{}]},
                        {"NBest": [{"PronunciationAssessment": {"AccuracyScore": -1}}]},
                        {"NBest": [{"PronunciationAssessment": {"AccuracyScore": "90"}}]}]:
            self.scenario = lambda payload=payload: (self.final(payload=payload), self.recognizer.session_stopped.emit())
            self.assertEqual(self.post().status_code, 502)
            self.assert_unlocked()

    def test_invalid_inputs_do_not_call_sdk(self):
        for reference in [None, "", " \n", "a" * 501]:
            self.assertEqual(self.post(reference=reference).status_code, 400)
        for language in ["", "tr-TR", "en"]:
            self.assertEqual(self.post(language=language).status_code, 400)
        for audio in [b"", b"invalid", self.wav[:-1], wav_bytes(channels=2),
                      wav_bytes(rate=24000), wav_bytes(width=1), wav_bytes(seconds=30.01)]:
            self.assertEqual(self.post(audio=audio).status_code, 400)
        self.assertEqual(self.post(audio=b"x" * (service.MAX_FILE_BYTES + 1)).status_code, 413)
        self.assertEqual(self.post(filename="").status_code, 400)
        self.assertEqual(self.client.post("/api/pronunciation", json={}).status_code, 400)
        self.dotenv.assert_not_called()
        self.factory.assert_not_called()

    def test_maximum_reference_length_accepted_and_missing_settings_fail(self):
        self.assertEqual(self.post(reference="a" * 500).status_code, 200)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.post().status_code, 503)

    def test_silence_timeout_and_cancellation_no_partial_success(self):
        self.scenario = lambda: self.recognizer.session_stopped.emit()
        self.assertEqual(self.post().status_code, 422)
        self.scenario = lambda: self.final()
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("segments", response.json)
        self.scenario = lambda: self.recognizer.canceled.emit(cancellation_event("stt",
            service.speechsdk.CancellationReason.CancelledByUser))
        self.assertEqual(self.post().status_code, 502)
        self.assert_unlocked()

    def test_service_error_after_first_segment_and_retry(self):
        self.scenario = lambda: (self.final(), self.recognizer.canceled.emit(cancellation_event("stt",
            service.speechsdk.CancellationReason.Error, service.speechsdk.CancellationErrorCode.ConnectionFailure)))
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("segments", response.json)
        self.assert_unlocked()
        self.scenario = self.success
        self.assertEqual(self.post().status_code, 200)

    def test_apply_callback_and_cleanup_failures_never_return_success(self):
        self.assessment_config.return_value.apply_to.side_effect = RuntimeError("private-detail")
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private-detail", response.get_data(as_text=True))
        self.recognizer.stop_continuous_recognition_async.assert_called()
        self.assert_unlocked()
        self.assessment_config.return_value.apply_to.side_effect = None
        self.recognizer.stop_continuous_recognition_async.return_value.get.side_effect = RuntimeError("private-detail")
        self.assertEqual(self.post().status_code, 502)
        self.assert_unlocked()

    def test_home_has_pronunciation_without_loading_settings(self):
        self.assertIn("Pronunciation Assessment", self.client.get("/").get_data(as_text=True))
        self.dotenv.assert_not_called()


if __name__ == "__main__":
    unittest.main()
