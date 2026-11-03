"""Independent Task 2 WAV validation and bounded continuous en-US recognition."""
import os
import struct
from pathlib import Path
from threading import Event, Lock, Thread

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
MAX_FILE_BYTES = 1024 * 1024
MAX_SECONDS = 15
SAMPLE_RATE = 16000
RECOGNITION_TIMEOUT_SECONDS = 45
SDK_OPERATION_TIMEOUT_SECONDS = 5
_speech_lock = Lock()

class InvalidAudioError(ValueError):
    pass

class ConfigurationError(Exception):
    pass

class NoSpeechError(Exception):
    pass

class SpeechServiceError(Exception):
    """Fixed safe messages only; never expose native exception details."""
    def __init__(self, public_message):
        super().__init__(public_message)
        self.public_message = public_message


def transcribe_pcm(pcm):
    if not _speech_lock.acquire(blocking=False):
        raise SpeechServiceError("Konuşma servisi meşgul; tekrar deneyin.")
    try:
        key, region = load_speech_settings()
        try:
            config = speechsdk.SpeechConfig(subscription=key, region=region)
            config.speech_recognition_language = "en-US"
            return _continuous_pcm(config, pcm)
        except (NoSpeechError, SpeechServiceError):
            raise
        except Exception:
            raise SpeechServiceError("Azure ses servisine erişilemedi; ayarları ve bağlantıyı kontrol edin.") from None
    finally:
        _speech_lock.release()


def load_speech_settings():
    # Explicit Task 2 path; runtime speech requests only, never page rendering.
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    key = os.getenv("SPEECH_KEY", "").strip()
    region = os.getenv("SPEECH_REGION", "").strip()
    if not key or not region:
        raise ConfigurationError("Sunucuda SPEECH_KEY ve SPEECH_REGION ayarlanmalıdır.")
    return key, region


def synthesize_speech(text):
    """In-memory Azure WAV; never use the server's speaker or shared files."""
    if not isinstance(text, str) or not text.strip() or len(text) > 500:
        raise ValueError("Seslendirme metni boş olmayan, en fazla 500 karakterlik bir string olmalıdır.")
    if not _speech_lock.acquire(blocking=False):
        raise SpeechServiceError("Konuşma servisi meşgul; tekrar deneyin.")
    try:
        key, region = load_speech_settings()
        try:
            config = speechsdk.SpeechConfig(subscription=key, region=region)
            config.speech_synthesis_voice_name = "en-US-JennyNeural"
            config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
            result = synthesizer.speak_text_async(text).get()
            if result.reason == speechsdk.ResultReason.Canceled:
                code = result.cancellation_details.error_code
                messages = {
                    speechsdk.CancellationErrorCode.AuthenticationFailure: "Azure seslendirme kimlik doğrulaması başarısız; sunucu ayarlarını kontrol edin.",
                    speechsdk.CancellationErrorCode.TooManyRequests: "Azure seslendirme kotasına veya istek sınırına ulaşıldı.",
                    speechsdk.CancellationErrorCode.ConnectionFailure: "Azure seslendirme bağlantısı kurulamadı.",
                }
                raise SpeechServiceError(messages.get(code, "Azure seslendirmeyi tamamlayamadı; tekrar deneyin."))
            if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                raise SpeechServiceError("Azure seslendirmeyi tamamlayamadı.")
            audio = bytes(result.audio_data)
            if len(audio) <= 44 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
                raise SpeechServiceError("Azure geçerli bir WAV yanıtı döndürmedi.")
            return audio
        except SpeechServiceError:
            raise
        except Exception:
            raise SpeechServiceError("Azure seslendirme servisine erişilemedi; bağlantıyı ve ayarları kontrol edin.") from None
    finally:
        _speech_lock.release()


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
        raise InvalidAudioError("Kayıt en fazla 15 saniye olabilir.")
    return pcm


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


def _continuous_pcm(config, pcm):
    """Collect final segments until session_stopped; never return partial success."""
    done = Event()
    state_lock = Lock()
    texts, errors = [], []
    session_finished = False
    unmatched = False
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
                except (NoSpeechError, SpeechServiceError) as error:
                    errors.append(error)
                    done.set()
                except Exception:
                    errors.append(SpeechServiceError("Azure tanıma sonucu işlenemedi; kayıt tamamlanamadı."))
                    done.set()
        return handle

    def recognized(event):
        nonlocal unmatched
        result = event.result
        if result.reason == speechsdk.ResultReason.NoMatch:
            unmatched = True
            return
        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            raise SpeechServiceError("Azure kaydın tamamını işleyemedi.")
        if not isinstance(result.text, str) or not result.text.strip():
            return
        texts.append(result.text.strip())

    def canceled(event):
        # STT cancellation metadata is on cancellation_details, not direct event fields.
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
        recognizer = speechsdk.SpeechRecognizer(speech_config=config, audio_config=audio_config)
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
        if unmatched or not texts:
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
    return " ".join(texts)


