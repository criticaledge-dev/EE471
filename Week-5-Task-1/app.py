"""Flask entry point for Speech Studio."""

from flask import Flask, Response, jsonify, render_template, request

from speech_service import ConfigurationError, SpeechServiceError, VOICES, synthesize_speech

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
