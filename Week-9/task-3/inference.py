"""Object-oriented interface to the ten Task 1 inference functions."""
from functools import wraps
from pathlib import Path
import sys
from threading import Lock

TASK1 = Path(__file__).resolve().parents[1] / "task-1"
sys.path.insert(0, str(TASK1))
import demo


def serialized(method):
    @wraps(method)
    def run(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return run


def required(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} gerekli.")
    return value


class TransformerDemos:
    """Run one CPU inference at a time and retain no model between calls."""

    def __init__(self):
        self._lock = Lock()

    @serialized
    def sentiment(self, text):
        sentences = [line.strip() for line in text.splitlines() if line.strip()]
        if len(sentences) != 2:
            raise ValueError("İki cümleyi ayrı satırlara yazın.")
        return demo.sentiment_analysis(sentences)

    @serialized
    def zero_shot(self, text, candidates):
        labels = [label.strip() for label in candidates.split(",") if label.strip()]
        if len(labels) < 2 or len({label.casefold() for label in labels}) != len(labels):
            raise ValueError("Virgülle ayrılmış en az iki farklı aday etiket girin.")
        return demo.zero_shot_classification(required(text, "Metin"), labels)["ranking"]

    @serialized
    def text_generation(self, prompt):
        if len(required(prompt, "Cümle başlangıcı").split()) >= 35:
            raise ValueError("Cümle başlangıcı 35 kelimeden kısa olmalı.")
        return demo.text_generation(prompt)

    @serialized
    def fill_mask(self, text):
        if text.count("[…]") != 1:
            raise ValueError("Cümlede bir adet […] boşluğu kullanın.")
        return demo.fill_mask(text)

    @serialized
    def ner(self, text):
        return demo.ner(required(text, "Metin"))["entities"]

    @serialized
    def qa(self, context, questions):
        lines = [line.strip() for line in questions.splitlines() if line.strip()]
        if not 1 <= len(lines) <= 3:
            raise ValueError("Ayrı satırlara bir ile üç soru yazın.")
        numbered = {str(index): question for index, question in enumerate(lines, 1)}
        return demo.question_answering(required(context, "Bağlam"), numbered)["answers"]

    @serialized
    def summarization(self, text):
        return demo.summarization(required(text, "Metin"))

    @serialized
    def translation(self, text):
        return demo.translation(required(text, "Fransızca metin"))["translation"]

    @serialized
    def image_classification(self, photo):
        if not photo:
            raise ValueError("Bir JPG veya PNG fotoğraf seçin.")
        _, ranking = demo.image_classification(Path(photo))
        return ranking

    @serialized
    def asr(self, wav):
        if not wav:
            raise ValueError("Bir PCM16 WAV dosyası seçin.")
        return demo.asr(Path(wav))["transcript"]
