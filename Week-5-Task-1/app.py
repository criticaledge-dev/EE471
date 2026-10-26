"""Speech Studio STT HTTP interface."""

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from speech_service import (
    ConfigurationError, InvalidAudioError, LANGUAGES, MAX_FILE_BYTES,
    NoSpeechError, SpeechServiceError, transcribe_pcm, validate_wav,
)

app = Flask(__name__)
# Allow multipart headers in addition to the file limit.
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES + 64 * 1024


@app.get("/")
def index():
    return render_template("index.html")


@app.errorhandler(RequestEntityTooLarge)
def oversized_request(_error):
    return jsonify(error="Yükleme çok büyük. WAV dosyası en fazla 1 MiB olabilir."), 413


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
        return jsonify(error="Konuşma tanınamadı. Seçilen dilde, net ve tek ifadeli bir kayıt deneyin."), 422
    except SpeechServiceError as error:
        return jsonify(error=error.public_message), 502
    except Exception:
        # Neither log nor return raw exceptions, credentials or user content.
        return jsonify(error="Ses işlenemedi. Lütfen daha sonra tekrar deneyin."), 500
    return jsonify(text=text)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
