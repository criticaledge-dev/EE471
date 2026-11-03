"""Run inside either built image with --network none. No Azure operations."""
import ctypes
import gc
import importlib.metadata
from pathlib import Path
import runpy
import subprocess
import sys
from unittest.mock import patch

import azure.cognitiveservices.speech as sdk
sys.path.insert(0, "/app")
import app

assert importlib.metadata.version("azure-cognitiveservices-speech") == "1.53.0"
assert importlib.metadata.version("flask") == "3.1.3"
for library in ("libssl.so.3", "libcrypto.so.3", "libasound.so.2"):
    ctypes.CDLL(library)
package = Path(sdk.__file__).parent
libraries = list(package.glob("*.so"))
assert libraries, "No native Speech SDK libraries found"
for library in libraries:
    linked = subprocess.run(["ldd", str(library)], check=True, capture_output=True, text=True).stdout
    if library.name == "libMicrosoft.CognitiveServices.Speech.extension.codec.so":
        # Microsoft documents GStreamer for compressed audio. These apps accept
        # only raw PCM/WAV; the optional codec is neither loaded nor exercised.
        if "not found" in linked:
            missing = [line.split("=>")[0].strip() for line in linked.splitlines() if "not found" in line]
            assert set(missing) <= {"libgstreamer-1.0.so.0", "libgobject-2.0.so.0", "libglib-2.0.so.0", "libgstbase-1.0.so.0"}, missing
            print("Optional compressed-audio codec lacks GStreamer; PCM/WAV apps do not use it")
        continue
    assert "not found" not in linked, f"Missing runtime dependency for {library.name}"
print("Native SDK import, OpenSSL/ALSA load and required-library ldd checks passed")

# Explicit fake values, local constructors only. Never call start/recognize/speak.
config = sdk.SpeechConfig(subscription="offline-test-not-a-real-key", region="eastus")
config.set_speech_synthesis_output_format(sdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
stream = sdk.audio.PushAudioInputStream(stream_format=sdk.audio.AudioStreamFormat(
    samples_per_second=16000, bits_per_sample=16, channels=1))
audio = sdk.audio.AudioConfig(stream=stream)
recognizer = sdk.SpeechRecognizer(speech_config=config, audio_config=audio)
synthesizer = sdk.SpeechSynthesizer(speech_config=config, audio_config=None)
translation_config = sdk.translation.SpeechTranslationConfig(
    subscription="offline-test-not-a-real-key", region="eastus", speech_recognition_language="en-US")
translation_config.add_target_language("tr")
translator = sdk.translation.TranslationRecognizer(translation_config=translation_config, audio_config=audio)
transcriber = sdk.transcription.ConversationTranscriber(speech_config=config, audio_config=audio)
assessment = sdk.PronunciationAssessmentConfig(reference_text="Offline fixture",
    grading_system=sdk.PronunciationAssessmentGradingSystem.HundredMark)
assessment.apply_to(recognizer)
del recognizer, synthesizer, translator, transcriber, assessment
stream.close()
gc.collect()
print("SDK 1.53.0 local recognizer/TTS/translation/assessment/transcriber constructors passed; no service call")

with patch.object(app.app, "run") as run:
    runpy.run_path("container_server.py", run_name="__main__")
    run.assert_called_once_with(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
assert not app.app.debug
assert not Path("/app/.env").exists()
for forbidden in (".venv", ".test-deps", "node_modules", "tests", "outputs"):
    assert not Path("/app", forbidden).exists(), forbidden
print("Container startup binding/threading/debug flags and clean runtime filesystem passed")
