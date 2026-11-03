"""Event-driven SDK mock wiring; never invokes real Azure operations."""

from types import SimpleNamespace
from unittest.mock import create_autospec
import speech_service as service


class Signal:
    def __init__(self):
        self.handlers = []
        self.sdk = create_autospec(service.speechsdk.EventSignal, instance=True, spec_set=True)
        self.sdk.connect.side_effect = self.handlers.append
        self.sdk.disconnect_all.side_effect = self.handlers.clear

    def __getattr__(self, name):
        # SDK methods/signatures only; .emit/.handlers are test instrumentation.
        return getattr(self.sdk, name)

    def emit(self, event=None):
        for callback in list(self.handlers):
            callback(event or SimpleNamespace())


def result_event(kind, reason, text="", translations=None):
    sdk = service.speechsdk
    result_type = (sdk.translation.TranslationRecognitionResult if kind == "translate"
                   else sdk.SpeechRecognitionResult)
    event_type = (sdk.translation.TranslationRecognitionEventArgs if kind == "translate"
                  else sdk.SpeechRecognitionEventArgs)
    result = create_autospec(result_type, instance=True, spec_set=True)
    result.reason, result.text = reason, text
    if kind == "translate":
        result.translations = translations or {}
    event = create_autospec(event_type, instance=True, spec_set=True)
    event.result = result
    return event


def cancellation_event(kind, reason, code=None):
    sdk = service.speechsdk
    event_type = (sdk.translation.TranslationRecognitionCanceledEventArgs if kind == "translate"
                  else sdk.SpeechRecognitionCanceledEventArgs)
    event = create_autospec(event_type, instance=True, spec_set=True)
    details = create_autospec(sdk.CancellationDetails, instance=True, spec_set=True)
    details.reason = reason
    details.code = code if code is not None else sdk.CancellationErrorCode.NoError
    event.cancellation_details = details
    if kind == "translate":
        event.reason, event.error_code = details.reason, details.code
    return event


def emit_result(recognizer, result, kind):
    if result.reason == service.speechsdk.ResultReason.Canceled:
        recognizer.canceled.emit(cancellation_event(
            kind, service.speechsdk.CancellationReason.Error,
            result.cancellation_details.error_code,
        ))
    else:
        recognizer.recognized.emit(result_event(
            kind, result.reason, result.text, getattr(result, "translations", None)))


def wire_continuous(recognizer, stream, get_result, kind="stt"):
    for name in ["recognized", "recognizing", "session_stopped", "speech_end_detected", "canceled"]:
        setattr(recognizer, name, Signal())
    state = {"started": False, "in_callback": False}

    def start():
        state["started"] = True

    def emit():
        state["in_callback"] = True
        try:
            emit_result(recognizer, get_result(), kind)
            recognizer.session_stopped.emit()
        finally:
            state["in_callback"] = False

    def stop():
        assert not state["in_callback"], "Stop must not block inside an SDK callback"

    recognizer.start_continuous_recognition_async.return_value.get.side_effect = start
    recognizer.stop_continuous_recognition_async.return_value.get.side_effect = stop
    stream.close.side_effect = emit
    return state
