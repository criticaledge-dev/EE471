"""Azure TTS synthesis in memory; no speaker or shared output file."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
VOICES = {"en-US": "en-US-JennyNeural", "tr-TR": "tr-TR-EmelNeural"}


class ConfigurationError(Exception):
    """Required server settings are missing."""


class SpeechServiceError(Exception):
    """Only fixed, safe messages may be passed to this exception."""

    def __init__(self, public_message):
        super().__init__(public_message)
        self.public_message = public_message


@dataclass(frozen=True)
class SpeechSettings:
    key: str = field(repr=False)
    region: str

    def validate(self):
        if not self.key or not self.region:
            raise ConfigurationError("SPEECH_KEY ve SPEECH_REGION gereklidir.")


def load_speech_settings():
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    return SpeechSettings(
        key=os.getenv("SPEECH_KEY", "").strip(),
        region=os.getenv("SPEECH_REGION", "").strip(),
    )


def synthesize_speech(text, language):
    """Return RIFF PCM WAV bytes, or a safe configuration/service error."""
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:
        raise ValueError("Geçersiz metin.")
    if not isinstance(language, str) or language not in VOICES:
        raise ValueError("Desteklenmeyen dil.")
    settings = load_speech_settings()
    settings.validate()
    try:
        config = speechsdk.SpeechConfig(subscription=settings.key, region=settings.region)
        config.speech_synthesis_voice_name = VOICES[language]
        config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
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
