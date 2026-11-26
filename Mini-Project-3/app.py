"""Flask app for transcription, local chat and image generation."""
import io
import mimetypes

from flask import Flask, jsonify, render_template, request, send_file

from generation import Generation

mimetypes.add_type("text/javascript", ".mjs")


def create_app(engine=None, speech_backend=None):
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=1024 * 1024 + 64 * 1024)
    engine = engine if engine is not None else Generation()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="Gönderilen dosya veya metin çok büyük."), 413

    @app.post("/api/voice-input")
    def transcribe():
        if request.form.get("language", "en-US") != "en-US":
            return jsonify(error="Bu demo İngilizce ses girişini destekliyor."), 400
        if not (audio := request.files.get("audio")):
            return jsonify(error="Bir WAV kaydı gönder."), 400
        if speech_backend is None:
            import speech_service as speech
        else:
            speech = speech_backend
        try:
            pcm = speech.validate_wav(audio.read(speech.MAX_FILE_BYTES + 1))
            return jsonify(text=speech.transcribe_pcm(pcm), language="en-US")
        except speech.ConfigurationError as exc:
            return jsonify(error=str(exc) or "Ses tanıma ayarları eksik."), 503
        except speech.InvalidAudioError as exc:
            return jsonify(error=str(exc)), 400
        except speech.NoSpeechError:
            return jsonify(error="Konuşma algılanmadı. Tekrar dene."), 422
        except speech.SpeechServiceError as exc:
            return jsonify(error=exc.public_message), 502

    @app.post("/api/chat")
    def chat():
        payload = request.get_json(silent=True)
        messages = payload.get("messages") if isinstance(payload, dict) else None
        if not isinstance(messages, list) or not 1 <= len(messages) <= 9 or len(messages) % 2 != 1:
            return jsonify(error="Geçerli bir sohbet mesajı gönder."), 400
        clean = []
        for index, message in enumerate(messages):
            role = "assistant" if index % 2 else "user"
            if not isinstance(message, dict) or message.get("role") != role:
                return jsonify(error="Sohbet sırası geçersiz."), 400
            content = message.get("content")
            if not isinstance(content, str) or not 1 <= len(content.strip()) <= 2000:
                return jsonify(error="Her mesaj 1–2000 karakter olmalı."), 400
            clean.append({"role": role, "content": content.strip()})
        try:
            return jsonify(reply=engine.reply(clean))
        except (OSError, RuntimeError, ValueError, ImportError):
            app.logger.exception("Chat generation failed")
            return jsonify(error="Sohbet modeli çalışmadı. Sunucu terminalini kontrol et."), 503

    @app.post("/api/image")
    def image():
        payload = request.get_json(silent=True)
        prompt = payload.get("prompt") if isinstance(payload, dict) else None
        if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 1000:
            return jsonify(error="Görsel açıklaması 1–1000 karakter olmalı."), 400
        try:
            output = io.BytesIO()
            engine.render(prompt.strip()).save(output, "PNG")
            output.seek(0)
            return send_file(output, mimetype="image/png", max_age=0)
        except (OSError, RuntimeError, ValueError, ImportError):
            app.logger.exception("Image generation failed")
            return jsonify(error="Görsel üretilemedi. Sunucu terminalini kontrol et."), 503

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5003)
