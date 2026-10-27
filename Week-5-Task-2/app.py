"""Flask interface for the existing Calculator class."""

import math
import mimetypes

from flask import Flask, jsonify, render_template, request

from custom_classes import Calculator
from speech_service import (MAX_FILE_BYTES, ConfigurationError, InvalidAudioError,
                            NoSpeechError, SpeechServiceError, transcribe_pcm, validate_wav, synthesize_speech)


mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("text/javascript", ".js")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES + 64 * 1024


@app.errorhandler(413)
def oversized_request(_error):
    return jsonify(error="Ses yüklemesi çok büyük; en fazla 1 MiB WAV yükleyin."), 413


@app.post("/api/voice-input")
def voice_input():
    audio = request.files.get("audio")
    if audio is None:
        return jsonify(error="audio alanında WAV dosyası gönderin."), 400
    try:
        pcm = validate_wav(audio.read(MAX_FILE_BYTES + 1))
        return jsonify(text=transcribe_pcm(pcm), language="en-US")
    except InvalidAudioError as error:
        return jsonify(error=str(error)), 400
    except ConfigurationError:
        return jsonify(error="Sunucuda SPEECH_KEY ve SPEECH_REGION ayarlanmalıdır."), 503
    except NoSpeechError:
        return jsonify(error="Konuşma tanınamadı. İngilizce komutu tekrar söyleyin."), 422
    except SpeechServiceError as error:
        return jsonify(error=error.public_message), 502
    except Exception:
        return jsonify(error="Ses kaydı işlenemedi; tekrar deneyin."), 500


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/tts")
def text_to_speech():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Geçerli bir JSON nesnesi gönderin."), 400
    try:
        audio = synthesize_speech(data.get("text"))
        return app.response_class(audio, mimetype="audio/wav", headers={"Cache-Control": "no-store"})
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except ConfigurationError:
        return jsonify(error="Sunucuda SPEECH_KEY ve SPEECH_REGION ayarlanmalıdır."), 503
    except SpeechServiceError as error:
        return jsonify(error=error.public_message), 502
    except Exception:
        return jsonify(error="Seslendirme tamamlanamadı; tekrar deneyin."), 500


@app.post("/api/calculate")
def calculate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Geçerli bir JSON nesnesi gönderin."), 400

    if not all(field in data for field in ("operation", "x", "y")):
        return jsonify(error="operation, x ve y alanları zorunludur."), 400

    calculator = Calculator()
    operations = {
        "add": calculator.add,
        "subtract": calculator.subtract,
        "multiply": calculator.multiply,
        "divide": calculator.divide,
    }
    operation = data["operation"]
    if not isinstance(operation, str) or operation not in operations:
        return jsonify(error="Geçersiz işlem. add, subtract, multiply veya divide kullanın."), 400

    x, y = data["x"], data["y"]
    for value in (x, y):
        if type(value) not in (int, float):
            return jsonify(error="x ve y sayı olmalıdır; boolean kabul edilmez."), 400
        if isinstance(value, float) and not math.isfinite(value):
            return jsonify(error="x ve y sonlu sayılar olmalıdır."), 400

    try:
        result = operations[operation](x, y)
    except ValueError:
        return jsonify(error="Sıfıra bölme yapılamaz."), 400
    except OverflowError:
        return jsonify(error="Sayılar hesaplanabilir aralığın dışında."), 400

    if isinstance(result, float) and not math.isfinite(result):
        return jsonify(error="Sonuç sonlu bir sayı olmalıdır."), 400
    return jsonify(result=result), 200


if __name__ == "__main__":
    app.run()
