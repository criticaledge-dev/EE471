"""Shared configuration, serialized Azure TTS/STT and strict WAV validation."""

import os
import json
import math
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
import struct
from threading import Event, Lock, Thread

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
VOICES = {"en-US": "en-US-JennyNeural", "tr-TR": "tr-TR-EmelNeural"}
LANGUAGES = set(VOICES)
TRANSLATION_PAIRS = {"en-US": "tr", "tr-TR": "en"}
MAX_FILE_BYTES = 1024 * 1024
MAX_SECONDS = 30
SAMPLE_RATE = 16000
RECOGNITION_TIMEOUT_SECONDS = 60
SDK_OPERATION_TIMEOUT_SECONDS = 5

# Shared across all clients and both operations in this server process.
_speech_lock = Lock()
_live_session_active = Event()


def serialized_speech(operation):
    @wraps(operation)
    def run(*args, **kwargs):
        if _live_session_active.is_set():
            raise SpeechBusyError()
        with _speech_lock:
            if _live_session_active.is_set():
                raise SpeechBusyError()
            return operation(*args, **kwargs)
    return run


class InvalidAudioError(ValueError):
    """Invalid upload; messages contain no user-provided data."""


class ConfigurationError(Exception):
    """Required server settings are missing."""


class NoSpeechError(Exception):
    """No recognized speech; never a successful transcript."""


class MissingTranslationError(Exception):
    """Azure returned no usable translation for the requested target."""


class SpeechServiceError(Exception):
    """Only fixed, safe messages may be passed to this exception."""

    def __init__(self, public_message):
        super().__init__(public_message)
        self.public_message = public_message


class SpeechBusyError(SpeechServiceError):
    def __init__(self):
        super().__init__("Konuşma servisi meşgul. Canlı mikrofon oturumunu durdurup tekrar deneyin.")


@dataclass(frozen=True)
class SpeechSettings:
    key: str = field(repr=False)
    region: str

    def validate(self):
        if not self.key or not self.region:
            raise ConfigurationError("SPEECH_KEY ve SPEECH_REGION gereklidir.")


def load_speech_settings():
    """Load and validate only on a speech request, never on page rendering."""
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    settings = SpeechSettings(
        key=os.getenv("SPEECH_KEY", "").strip(),
        region=os.getenv("SPEECH_REGION", "").strip(),
    )
    settings.validate()
    return settings


def validate_wav(data):
    """Return raw PCM after checking RIFF size, chunks, format and duration.

    Only classic little-endian PCM (format tag 1) is supported. Filenames and
    MIME types are intentionally not trusted. All chunks must fit the upload.
    """
    if not data:
        raise InvalidAudioError("Ses dosyası boş.")
    if len(data) > MAX_FILE_BYTES:
        raise InvalidAudioError("WAV dosyası en fazla 1 MiB olabilir.")
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise InvalidAudioError("Geçerli bir RIFF/WAVE dosyası yükleyin.")
    if struct.unpack_from("<I", data, 4)[0] + 8 != len(data):
        raise InvalidAudioError("WAV başlığındaki dosya boyutu geçersiz; dosya eksik veya bozuk.")
    offset = 12
    fmt = None
    pcm = None
    while offset < len(data):
        if offset + 8 > len(data):
            raise InvalidAudioError("WAV bölüm başlığı eksik veya bozuk.")
        kind, size = struct.unpack_from("<4sI", data, offset)
        start = offset + 8
        end = start + size
        if end + (size % 2) > len(data):
            raise InvalidAudioError("WAV bölümü eksik veya bozuk.")
        if kind == b"fmt ":
            if fmt is not None or size < 16:
                raise InvalidAudioError("WAV biçim başlığı geçersiz.")
            fmt = struct.unpack_from("<HHIIHH", data, start)
        elif kind == b"data":
            if pcm is not None or fmt is None:
                raise InvalidAudioError("WAV ses bölümü geçersiz.")
            pcm = data[start:end]
        offset = end + (size % 2)
    if fmt is None or pcm is None:
        raise InvalidAudioError("WAV dosyasında biçim veya ses bölümü eksik.")
    tag, channels, rate, byte_rate, alignment, bits = fmt
    if (tag, channels, rate, bits) != (1, 1, SAMPLE_RATE, 16):
        raise InvalidAudioError("Yalnızca sıkıştırılmamış PCM WAV, 16-bit, mono, 16 kHz desteklenir.")
    if alignment != 2 or byte_rate != SAMPLE_RATE * 2 or len(pcm) % 2:
        raise InvalidAudioError("WAV PCM örnek boyutları geçersiz.")
    if not pcm:
        raise InvalidAudioError("WAV dosyası ses örneği içermiyor.")
    if len(pcm) > MAX_SECONDS * SAMPLE_RATE * 2:
        raise InvalidAudioError("Kayıt en fazla 30 saniye olabilir.")
    return pcm


@serialized_speech
def synthesize_speech(text, language):
    """Return RIFF PCM WAV bytes, or a safe configuration/service error."""
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:
        raise ValueError("Geçersiz metin.")
    if not isinstance(language, str) or language not in VOICES:
        raise ValueError("Desteklenmeyen dil.")
    settings = load_speech_settings()
    try:
        config = speechsdk.SpeechConfig(subscription=settings.key, region=settings.region)
        config.speech_synthesis_voice_name = VOICES[language]
        config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
        )
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.Canceled:
            code = result.cancellation_details.error_code
            messages = {
                speechsdk.CancellationErrorCode.AuthenticationFailure:
                    "Azure kimlik doğrulaması başarısız. Sunucudaki anahtar ve bölge ayarlarını kontrol edin.",
                speechsdk.CancellationErrorCode.TooManyRequests:
                    "Azure istek sınırına veya kotasına ulaşıldı. Kotayı kontrol edip daha sonra deneyin.",
                speechsdk.CancellationErrorCode.ConnectionFailure:
                    "Azure bağlantısı kurulamadı. Ağ bağlantısını kontrol edip tekrar deneyin.",
                speechsdk.CancellationErrorCode.ServiceTimeout:
                    "Azure yanıtı zaman aşımına uğradı. Daha sonra tekrar deneyin.",
            }
            raise SpeechServiceError(messages.get(code, "Azure ses üretimini iptal etti. Daha sonra tekrar deneyin."))
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            raise SpeechServiceError("Azure ses üretimini tamamlayamadı.")
        audio = bytes(result.audio_data)
        if len(audio) <= 44 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
            raise SpeechServiceError("Azure geçerli bir WAV ses yanıtı döndürmedi.")
        return audio
    except SpeechServiceError:
        raise
    except Exception:
        raise SpeechServiceError("Azure ses servisine erişilemedi. Ayarları ve bağlantıyı kontrol edip tekrar deneyin.") from None


def _wait_sdk_operation(operation):
    """Bound SDK future.get() waits, which have no Python timeout argument.

    Only the request flow calls this helper; SDK event callbacks never wait
    for start/stop. A stuck native future cannot block the request forever.
    """
    finished = Event()
    errors = []

    def run():
        try:
            operation().get()
        except Exception as error:
            errors.append(error)
        finally:
            finished.set()

    Thread(target=run, daemon=True).start()
    if not finished.wait(SDK_OPERATION_TIMEOUT_SECONDS):
        raise SpeechServiceError("Azure tanıma işlemi zaman aşımına uğradı; sonuç tamamlanamadı.")
    if errors:
        raise SpeechServiceError("Azure tanıma işlemi başlatılamadı veya durdurulamadı.") from None


def _continuous_pcm(config, pcm, target_language=None, *, configure_recognizer=None, on_final=None, on_no_match=None):
    """Collect final segments until session_stopped; never return partial success."""
    done = Event()
    state_lock = Lock()
    texts, translations, errors = [], [], []
    session_finished = False
    accepting = True
    stream = recognizer = None
    stream_closed = False
    connections = []
    primary_error = None

    def guarded(callback):
        def handle(event):
            with state_lock:
                if not accepting:
                    return
                try:
                    callback(event)
                except (NoSpeechError, MissingTranslationError, SpeechServiceError) as error:
                    errors.append(error)
                    done.set()
                except Exception:
                    errors.append(SpeechServiceError("Azure tanıma sonucu işlenemedi; kayıt tamamlanamadı."))
                    done.set()
        return handle

    def recognized(event):
        result = event.result
        if result.reason == speechsdk.ResultReason.NoMatch:
            if on_no_match is not None:
                on_no_match()
            return  # Silence between utterances is not the end of the file.
        expected = (speechsdk.ResultReason.TranslatedSpeech if target_language
                    else speechsdk.ResultReason.RecognizedSpeech)
        if target_language and result.reason == speechsdk.ResultReason.RecognizedSpeech:
            raise MissingTranslationError()
        if result.reason != expected:
            raise SpeechServiceError("Azure kaydın tamamını işleyemedi.")
        if not isinstance(result.text, str) or not result.text.strip():
            if on_no_match is not None:
                on_no_match()
            return
        if target_language:
            translated = result.translations.get(target_language)
            if not isinstance(translated, str) or not translated.strip():
                raise MissingTranslationError()
            translations.append(translated.strip())
        if on_final is not None:
            on_final(result)
        texts.append(result.text.strip())

    def canceled(event):
        # Both SDK event types expose CancellationDetails. STT does not expose
        # TranslationRecognitionCanceledEventArgs.reason/error_code shortcuts.
        details = event.cancellation_details
        if details.reason == speechsdk.CancellationReason.EndOfStream:
            return  # Normal EOF still requires session_stopped, not early success.
        if details.reason == speechsdk.CancellationReason.Error:
            codes = speechsdk.CancellationErrorCode
            messages = {
                codes.AuthenticationFailure: "Azure kimlik doğrulaması başarısız. Sunucudaki anahtar ve bölgeyi kontrol edin.",
                codes.TooManyRequests: "Azure istek sınırına veya kotasına ulaşıldı. Daha sonra tekrar deneyin.",
                codes.ConnectionFailure: "Azure bağlantısı kesildi; kaydın tamamı işlenemedi.",
                codes.ServiceTimeout: "Azure yanıtı zaman aşımına uğradı; kayıt tamamlanamadı.",
            }
            raise SpeechServiceError(messages.get(details.code, "Azure servisi kaydı işlerken hata verdi."))
        raise SpeechServiceError("Azure tanıma işlemi iptal edildi; kaydın tamamı işlenemedi.")

    def stopped(_event):
        nonlocal session_finished
        session_finished = True
        done.set()

    try:
        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=SAMPLE_RATE, bits_per_sample=16, channels=1
        )
        stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        if target_language:
            recognizer = speechsdk.translation.TranslationRecognizer(
                translation_config=config, audio_config=audio_config)
        else:
            recognizer = speechsdk.SpeechRecognizer(speech_config=config, audio_config=audio_config)
        if configure_recognizer is not None:
            configure_recognizer(recognizer)
        # No recognizing or speech_end_detected handlers: neither is a final result/EOF.
        for signal, callback in [(recognizer.recognized, recognized),
                                 (recognizer.canceled, canceled),
                                 (recognizer.session_stopped, stopped)]:
            handler = guarded(callback)
            # Track before connect: even a partially attached callback must be removed.
            connections.append(signal)
            signal.connect(handler)
        _wait_sdk_operation(recognizer.start_continuous_recognition_async)
        stream.write(pcm)
        stream.close()  # EOF is sent only after all validated samples were supplied.
        stream_closed = True
        if not done.wait(RECOGNITION_TIMEOUT_SECONDS):
            raise SpeechServiceError("Kaydın tamamı zamanında işlenemedi; kısmi sonuç döndürülmedi.")
        if errors:
            raise errors[0]
        if not session_finished:
            raise SpeechServiceError("Azure tanıma oturumu tamamlanmadı.")
        if not texts:
            raise NoSpeechError()
    except BaseException as error:
        primary_error = error
        raise
    finally:
        with state_lock:
            accepting = False
        cleanup_failures = []
        if recognizer is not None:
            try:
                # Initiated by the request flow, never by an SDK callback.
                _wait_sdk_operation(recognizer.stop_continuous_recognition_async)
            except Exception as error:
                cleanup_failures.append(("stop", type(error).__name__))
        for signal in connections:
            try:
                # This request owns its recognizer and all of these subscriptions.
                signal.disconnect_all()
            except Exception as error:
                cleanup_failures.append(("disconnect_all", type(error).__name__))
        if stream is not None and not stream_closed:
            try:
                stream.close()
            except Exception as error:
                cleanup_failures.append(("stream.close", type(error).__name__))
        if cleanup_failures:
            # Keep only safe stage/type diagnostics, never raw SDK messages/locals.
            # A cleanup failure must not replace the original failure or its traceback.
            if primary_error is not None:
                primary_error.cleanup_failures = tuple(cleanup_failures)
            else:
                error = SpeechServiceError("Azure tanıma işlemi güvenle tamamlanamadı; tekrar deneyin.")
                error.cleanup_failures = tuple(cleanup_failures)
                raise error from None
    return " ".join(texts), " ".join(translations)


@serialized_speech
def transcribe_pcm(pcm, language):
    """Recognize every finalized utterance in a validated WAV's PCM samples."""
    if language not in LANGUAGES:
        raise InvalidAudioError("Desteklenen diller: en-US ve tr-TR.")
    settings = load_speech_settings()
    try:
        config = speechsdk.SpeechConfig(subscription=settings.key, region=settings.region)
        config.speech_recognition_language = language
        text, _ = _continuous_pcm(config, pcm)
        return text
    except (NoSpeechError, SpeechServiceError):
        raise
    except Exception:
        raise SpeechServiceError("Azure ses servisine erişilemedi. Ayarları ve bağlantıyı kontrol edip tekrar deneyin.") from None


@serialized_speech
def translate_pcm(pcm, source_language, target_language):
    """Translate every finalized utterance using the shared Speech resource."""
    if (not isinstance(source_language, str)
            or TRANSLATION_PAIRS.get(source_language) != target_language):
        raise InvalidAudioError("Desteklenen çeviriler: en-US → tr ve tr-TR → en.")
    settings = load_speech_settings()
    try:
        config = speechsdk.translation.SpeechTranslationConfig(
            subscription=settings.key, region=settings.region)
        config.speech_recognition_language = source_language
        config.add_target_language(target_language)
        text, translated = _continuous_pcm(config, pcm, target_language)
        return {"recognized_text": text, "translated_text": translated,
                "source_language": source_language, "target_language": target_language}
    except (NoSpeechError, MissingTranslationError, SpeechServiceError):
        raise
    except Exception:
        raise SpeechServiceError("Azure konuşma çevirisine erişilemedi. Ayarları ve bağlantıyı kontrol edip tekrar deneyin.") from None


def _azure_score(data, key):
    """Missing Azure scores stay null; never substitute SDK defaults or estimates."""
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
        raise SpeechServiceError("Azure geçerli bir değerlendirme puanı döndürmedi.")
    return value


def _assessment_segment(result):
    # The official Python sample reads this exact SDK property / NBest schema.
    # Parse presence explicitly: missing scores must not turn into fabricated zeros.
    raw = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
    if not isinstance(raw, str) or not raw:
        raise SpeechServiceError("Azure telaffuz değerlendirmesi döndürmedi.")
    data = json.loads(raw)
    best = data["NBest"][0]
    assessment = best.get("PronunciationAssessment")
    if not isinstance(assessment, dict) or not assessment:
        raise SpeechServiceError("Azure telaffuz değerlendirmesi eksik.")
    scores = {name: _azure_score(assessment, key) for name, key in {
        "accuracy": "AccuracyScore", "fluency": "FluencyScore",
        "completeness": "CompletenessScore", "pronunciation": "PronScore",
    }.items()}
    if all(value is None for value in scores.values()):
        raise SpeechServiceError("Azure kullanılabilir telaffuz puanı döndürmedi.")
    words = []
    for word in best.get("Words", []):
        if not isinstance(word.get("Word"), str):
            raise SpeechServiceError("Azure kelime değerlendirmesi geçersiz.")
        detail = word.get("PronunciationAssessment", {})
        error_type = detail.get("ErrorType")
        words.append({
            "word": word["Word"],
            "accuracy": None if error_type == "Omission" else _azure_score(detail, "AccuracyScore"),
            "error_type": error_type if isinstance(error_type, str) else None,
        })
    return {"text": result.text, "scores": scores, "words": words,
            "assessment_complete": all(value is not None for value in scores.values())}


@serialized_speech
def assess_pronunciation(pcm, reference_text, language):
    """Continuous scripted en-US assessment; keep segment scores, no invented total."""
    if language != "en-US":
        raise InvalidAudioError("Telaffuz değerlendirmesi yalnızca en-US destekler.")
    if not isinstance(reference_text, str) or not reference_text.strip() or len(reference_text) > 500:
        raise InvalidAudioError("Referans metin boş olmayan, en fazla 500 karakterlik bir string olmalıdır.")
    settings = load_speech_settings()
    try:
        config = speechsdk.SpeechConfig(subscription=settings.key, region=settings.region)
        config.speech_recognition_language = language
        assessment = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Word,
            enable_miscue=False,
        )
        segments = []
        unassessed_segments = 0

        def collect(result):
            segment = _assessment_segment(result)
            segment["index"] = len(segments) + 1
            segments.append(segment)

        def unassessed():
            nonlocal unassessed_segments
            unassessed_segments += 1

        text, _ = _continuous_pcm(config, pcm, configure_recognizer=assessment.apply_to,
                                  on_final=collect, on_no_match=unassessed)
        complete = not unassessed_segments and all(segment["assessment_complete"] for segment in segments)
        warnings = ["Puanlar Azure'un kesinleşmiş segment sonuçlarıdır; tüm kayıt/referans için toplam puan hesaplanmaz."]
        if not complete:
            warnings.append("Bazı bölümler veya puanlar değerlendirilemedi; eksik puanlar null olarak gösterilir.")
        return {
            "language": language, "reference_text": reference_text, "recognized_text": text,
            "score_scale": 100, "session_complete": True, "assessment_complete": complete,
            "unassessed_segments": unassessed_segments,
            "scope": "single_segment" if len(segments) == 1 else "segments_only",
            "overall_scores": None, "segments": segments, "warnings": warnings,
        }
    except (NoSpeechError, SpeechServiceError):
        raise
    except Exception:
        raise SpeechServiceError("Azure telaffuz değerlendirmesi tamamlanamadı. Ayarları ve bağlantıyı kontrol edin.") from None
