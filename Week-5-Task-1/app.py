"""Combined Speech Studio: TTS and STT routes."""

from flask import Flask, Response, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from speech_service import (
    ConfigurationError, InvalidAudioError, LANGUAGES, MAX_FILE_BYTES,
    MissingTranslationError, NoSpeechError, SpeechServiceError, VOICES,
    TRANSLATION_PAIRS, synthesize_speech, transcribe_pcm, translate_pcm, validate_wav,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES + 64 * 1024


@app.get("/")
def index():
    return render_template("index.html")


@app.errorhandler(RequestEntityTooLarge)
def oversized_request(_error):
    return jsonify(error="Yükleme çok büyük. WAV dosyası en fazla 1 MiB olabilir."), 413


@app.post("/api/tts")
def text_to_speech():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Geçerli bir JSON nesnesi gönderin."), 400
    text = data.get("text")
    language = data.get("language")
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:
        return jsonify(error="Metin boş olmayan ve en fazla 1000 karakter içeren bir string olmalıdır."), 400
    if not isinstance(language, str) or language not in VOICES:
        return jsonify(error="Desteklenen diller: en-US ve tr-TR."), 400
    try:
        audio = synthesize_speech(text, language)
    except ConfigurationError:
        return jsonify(error="Azure konuşma ayarları eksik. Sunucuda SPEECH_KEY ve SPEECH_REGION ayarlarını tamamlayın."), 503
    except SpeechServiceError as error:
        return jsonify(error=error.public_message), 502
    except Exception:
        # Do not expose or log exceptions that might contain credentials.
        return jsonify(error="Ses oluşturulamadı. Lütfen daha sonra tekrar deneyin."), 500
    return Response(audio, mimetype="audio/wav", headers={
        "Content-Disposition": 'attachment; filename="speech.wav"',
        "Cache-Control": "no-store",
    })


@app.post("/api/stt")
def speech_to_text():
    if request.mimetype != "multipart/form-data":
        return jsonify(error="audio dosyasını ve language alanını multipart/form-data olarak gönderin."), 400
    language = request.form.get("language", "")
    if language not in LANGUAGES:
        return jsonify(error="Desteklenen diller: en-US ve tr-TR."), 400
    upload = request.files.get("audio")
    if upload is None or not upload.filename:
        return jsonify(error="Bir WAV dosyası seçin (audio alanı)."), 400
    data = upload.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        return oversized_request(None)
    try:
        pcm = validate_wav(data)
        text = transcribe_pcm(pcm, language)
    except InvalidAudioError as error:
        return jsonify(error=str(error)), 400
    except ConfigurationError:
        return jsonify(error="Azure ayarları eksik. Sunucuda SPEECH_KEY ve SPEECH_REGION ayarlarını tamamlayın."), 503
    except NoSpeechError:
        return jsonify(error="Konuşma tanınamadı. Seçilen dilde net bir kayıt deneyin."), 422
    except SpeechServiceError as error:
        return jsonify(error=error.public_message), 502
    except Exception:
        # Neither log nor return raw exceptions, credentials or user content.
        return jsonify(error="Ses işlenemedi. Lütfen daha sonra tekrar deneyin."), 500
    return jsonify(text=text)


@app.post("/api/translate")
def speech_translation():
    if request.mimetype != "multipart/form-data":
        return jsonify(error="audio, source_language ve target_language alanlarını multipart/form-data olarak gönderin."), 400
    source = request.form.get("source_language", "")
    target = request.form.get("target_language", "")
    if source not in TRANSLATION_PAIRS or TRANSLATION_PAIRS[source] != target:
        return jsonify(error="Desteklenen çeviriler: en-US → tr ve tr-TR → en."), 400
    upload = request.files.get("audio")
    if upload is None or not upload.filename:
        return jsonify(error="Bir WAV dosyası seçin (audio alanı)."), 400
    data = upload.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        return oversized_request(None)
    try:
        pcm = validate_wav(data)
        result = translate_pcm(pcm, source, target)
    except InvalidAudioError as error:
        return jsonify(error=str(error)), 400
    except ConfigurationError:
        return jsonify(error="Azure ayarları eksik. Sunucuda SPEECH_KEY ve SPEECH_REGION ayarlarını tamamlayın."), 503
    except NoSpeechError:
        return jsonify(error="Konuşma tanınamadı. Kaynak dilde net bir kayıt deneyin."), 422
    except MissingTranslationError:
        return jsonify(error="Azure hedef dil için çeviri döndürmedi. Lütfen tekrar deneyin."), 502
    except SpeechServiceError as error:
        return jsonify(error=error.public_message), 502
    except Exception:
        return jsonify(error="Konuşma çevrilemedi. Lütfen daha sonra tekrar deneyin."), 500
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
