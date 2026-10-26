"""Validate PCM WAV uploads and recognize one utterance using Azure."""

import os
from pathlib import Path
import struct

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
LANGUAGES = {"en-US", "tr-TR"}
MAX_FILE_BYTES = 1024 * 1024
MAX_SECONDS = 30
SAMPLE_RATE = 16000


class InvalidAudioError(ValueError):
    """Invalid upload; messages contain no user-provided data."""


class ConfigurationError(Exception):
    """Missing server credentials."""


class NoSpeechError(Exception):
    """No recognized speech; never a successful transcript."""


class SpeechServiceError(Exception):
    def __init__(self, public_message):
        super().__init__(public_message)
        self.public_message = public_message


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
        raise InvalidAudioError("Kayıt en fazla 30 saniye olabilir; tek bir ifade yükleyin.")
    return pcm


def load_speech_settings():
    """Load only when recognition is requested, never during page rendering."""
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    key = os.getenv("SPEECH_KEY", "").strip()
    region = os.getenv("SPEECH_REGION", "").strip()
    if not key or not region:
        raise ConfigurationError("SPEECH_KEY ve SPEECH_REGION gereklidir.")
    return key, region


def transcribe_pcm(pcm, language):
    """Recognize a validated PCM buffer without a microphone or disk file."""
    if language not in LANGUAGES:
        raise InvalidAudioError("Desteklenen diller: en-US ve tr-TR.")
    key, region = load_speech_settings()
    stream = None
    stream_closed = False
    try:
        config = speechsdk.SpeechConfig(subscription=key, region=region)
        config.speech_recognition_language = language
        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=SAMPLE_RATE, bits_per_sample=16, channels=1
        )
        stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        recognizer = speechsdk.SpeechRecognizer(speech_config=config, audio_config=audio_config)
        future = recognizer.recognize_once_async()
        # Push only PCM samples: the WAV container has already been validated.
        stream.write(pcm)
        stream.close()
        stream_closed = True
        result = future.get()
        if result.reason == speechsdk.ResultReason.NoMatch:
            raise NoSpeechError()
        if result.reason == speechsdk.ResultReason.Canceled:
            code = result.cancellation_details.error_code
            errors = speechsdk.CancellationErrorCode
            messages = {
                errors.AuthenticationFailure: "Azure kimlik doğrulaması başarısız. Sunucudaki anahtar ve bölgeyi kontrol edin.",
                errors.TooManyRequests: "Azure istek sınırına veya kotasına ulaşıldı. Kotayı kontrol edip daha sonra deneyin.",
                errors.ConnectionFailure: "Azure bağlantısı kurulamadı. Ağ bağlantısını kontrol edip tekrar deneyin.",
                errors.ServiceTimeout: "Azure yanıtı zaman aşımına uğradı. Daha sonra tekrar deneyin.",
            }
            raise SpeechServiceError(messages.get(code, "Azure ses tanımayı iptal etti. Daha sonra tekrar deneyin."))
        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            raise SpeechServiceError("Azure ses tanımayı tamamlayamadı.")
        if not isinstance(result.text, str) or not result.text.strip():
            raise NoSpeechError()
        return result.text
    except (NoSpeechError, SpeechServiceError):
        raise
    except Exception:
        raise SpeechServiceError("Azure ses servisine erişilemedi. Ayarları ve bağlantıyı kontrol edip tekrar deneyin.") from None
    finally:
        if stream is not None and not stream_closed:
            try:
                stream.close()
            except Exception:
                pass
