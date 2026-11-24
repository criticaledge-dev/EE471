"""Local Gradio Blocks frontend for EE471 Week 9 Task 3."""
import argparse
from functools import wraps
import os
from pathlib import Path
import wave

HERE = Path(__file__).resolve().parent
SAMPLES = HERE.parents[1] / "Week-8" / "samples"
HOST = "127.0.0.1"
PORT = 7860

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ.setdefault("GRADIO_TEMP_DIR", str(HERE / "output" / "gradio-cache"))

import gradio as gr
from inference import TransformerDemos, demo


def user_errors(method):
    @wraps(method)
    def run(*args):
        try:
            return method(*args)
        except (OSError, RuntimeError, ValueError, wave.Error) as error:
            raise gr.Error(str(error)) from error
    return run


def bind(name, method, inputs, output):
    gr.Button("Çalıştır", variant="primary", elem_id=f"{name}-run").click(
        user_errors(method), inputs, output, api_name=name,
        concurrency_id="cpu-inference", concurrency_limit=1,
    )


def build_app(photo=None, wav=None):
    models = TransformerDemos()
    with gr.Blocks(title="EE471 Week 9 · Task 3") as app:
        gr.Markdown("# EE471 Week 9 · Task 3")
        with gr.Tab("Metin"):
            with gr.Tab("Sentiment"):
                text = gr.Textbox(label="İki cümle · her satıra bir cümle",
                                  value="\n".join(demo.SENTENCES), lines=3)
                bind("sentiment", models.sentiment, text, gr.JSON(label="Etiket ve skor", elem_id="sentiment-result"))
            with gr.Tab("Zero-shot"):
                text = gr.Textbox(label="Metin", value=demo.ZERO_TEXT)
                labels = gr.Textbox(label="Aday etiketler · virgülle ayırın", value=", ".join(demo.LABELS))
                bind("zero_shot", models.zero_shot, [text, labels], gr.JSON(label="Sıralı skorlar", elem_id="zero_shot-result"))
            with gr.Tab("Generation"):
                text = gr.Textbox(label="Cümle başlangıcı", value=demo.PROMPT, lines=2)
                bind("text_generation", models.text_generation, text,
                     gr.JSON(label="İki tamamlanmış cümle ve kelime sayısı", elem_id="text_generation-result"))
            with gr.Tab("Fill-mask"):
                text = gr.Textbox(label="Bir […] içeren cümle", value=demo.MASKED)
                bind("fill_mask", models.fill_mask, text, gr.JSON(label="Doldurulmuş öneri", elem_id="fill_mask-result"))
            with gr.Tab("NER"):
                text = gr.Textbox(label="Metin", value=demo.CONTEXT, lines=4)
                bind("ner", models.ner, text, gr.JSON(label="Varlıklar ve konumları", elem_id="ner-result"))
            with gr.Tab("QA"):
                context = gr.Textbox(label="Bağlam", value=demo.CONTEXT, lines=4)
                questions = gr.Textbox(label="Sorular · her satıra bir soru",
                                       value="\n".join(demo.QUESTIONS.values()), lines=3)
                bind("qa", models.qa, [context, questions], gr.JSON(label="Bağlamdan çıkarılan cevaplar", elem_id="qa-result"))
            with gr.Tab("Summarization"):
                text = gr.Textbox(label="Özgün metin", value=demo.SUMMARY, lines=6)
                bind("summarization", models.summarization, text, gr.JSON(label="Özgün metin ve özet", elem_id="summarization-result"))
            with gr.Tab("Translation"):
                text = gr.Textbox(label="Fransızca", value=demo.TRANSLATION, lines=2)
                bind("translation", models.translation, text,
                     gr.Textbox(label="İngilizce", interactive=False, elem_id="translation-result"))
        with gr.Tab("Görsel"):
            image = gr.Image(label="JPG / PNG fotoğraf", value=str(photo) if photo else None,
                             type="filepath", sources=["upload"], format="png", elem_id="photo-input")
            bind("image_classification", models.image_classification, image,
                 gr.JSON(label="ViT · İlk üç etiket ve skor", elem_id="image_classification-result"))
        with gr.Tab("Ses"):
            audio = gr.Audio(label="İngilizce PCM16 WAV · en fazla 30 saniye",
                             value=str(wav) if wav else None, type="filepath",
                             sources=["upload"], elem_id="audio-input")
            bind("asr", models.asr, audio,
                 gr.Textbox(label="Whisper Large V3 · Transkript", interactive=False, elem_id="asr-result"))
    return app.queue(default_concurrency_limit=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photo", type=Path, help="Yerel JPG/PNG örneği")
    parser.add_argument("--wav", type=Path, help="Yerel PCM16 WAV örneği")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    if any(path is not None and not path.is_file() for path in (args.photo, args.wav)):
        parser.error("Verilen fotoğraf veya WAV bulunamadı.")
    photo = args.photo or SAMPLES / "cat_and_dog.jpg"
    wav = args.wav or SAMPLES / "speech_16000_hz_mono.wav"
    app = build_app(photo.resolve() if photo.is_file() else None, wav.resolve() if wav.is_file() else None)
    app.launch(server_name=HOST, server_port=args.port, share=False, max_file_size="20mb")


if __name__ == "__main__":
    main()
