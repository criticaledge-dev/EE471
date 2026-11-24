"""Reusable CPU inference functions for the ten Week 9 demos."""
import re
from pathlib import Path

from models import MODELS

SENTENCES = [
    "I've been waiting for a modern software practices course my whole life.",
    "I hate software courses",
]
ZERO_TEXT = "Berkshire keeps their cash reserves at an extremely high level."
LABELS = ["finance", "technology", "sports"]
PROMPT = "If I continue to complete all in-class exercises in this modern software practices course,"
MASKED = "To understand generative AI, one must study […] well."
CONTEXT = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently "
           "living and working in the beautiful city İzmir in Türkiye.")
QUESTIONS = {
    "PER": "What is the person's name?",
    "ORG": "At which institution does Nate work as a research assistant?",
    "LOC": "In which city does Nate currently live?",
}
TRANSLATION = "Ce cours est produit par Hugging Face."
SUMMARY = ("The 2008 Global Financial Crisis stands as the most severe economic collapse of "
           "the 21st century, often compared to the Great Depression of the 1930s. Triggered "
           "by the bursting of the United States housing bubble, its effects rippled across "
           "the globe, leading to the collapse of major financial institutions and a deep "
           "international recession. The crisis began with the subprime mortgage market. "
           "In the early 2000s, low interest rates and a push for homeownership led banks "
           "to issue high-risk loans to borrowers with poor credit.")

def cpu():
    import torch
    torch.set_num_threads(4)
    return torch

def pipeline_for(task, kind, **options):
    cpu()
    from huggingface_hub import hf_hub_download
    from transformers import pipeline
    config = hf_hub_download(MODELS[task], "config.json", local_files_only=True)
    return pipeline(kind, model=str(Path(config).parent), device=-1, **options)

def sentiment_analysis(texts=SENTENCES):
    results = pipeline_for("sentiment_analysis", "sentiment-analysis")(texts)
    return [{"text": text, **result} for text, result in zip(texts, results)]

def zero_shot_classification(text=ZERO_TEXT, labels=LABELS):
    result = pipeline_for("zero_shot_classification", "zero-shot-classification")(
        text, candidate_labels=labels)
    return {"text": text, "candidates": labels,
            "ranking": [{"label": label, "score": score}
                        for label, score in zip(result["labels"], result["scores"])]}

def text_generation(prompt=PROMPT):
    torch = cpu()
    torch.manual_seed(42)
    generator = pipeline_for("text_generation", "text-generation")
    alternatives = []
    for _ in range(12):
        for candidate in generator(prompt, do_sample=True, temperature=0.85, top_p=0.95,
                                   max_new_tokens=38, num_return_sequences=4,
                                   return_full_text=False,
                                   pad_token_id=generator.tokenizer.eos_token_id):
            # Keep a complete first sentence only. Reject unfinished or overlong candidates.
            match = re.match(r"^\s*([^\n]+?[.!?])(?=\s|$)", candidate["generated_text"])
            if not match or not re.search(r"[A-Za-z]", match[1]):
                continue
            text = prompt + " " + match[1]
            count = len(text.split())
            if count <= 35 and all(item["text"] != text for item in alternatives):
                alternatives.append({"text": text, "words": count})
                if len(alternatives) == 2:
                    return alternatives
    raise RuntimeError("The model did not generate two distinct complete sentences within 35 words.")

def fill_mask(text=MASKED):
    model = pipeline_for("fill_mask", "fill-mask")
    result = model(text.replace("[…]", model.tokenizer.mask_token), top_k=1)[0]
    return {"input": text, "token": result["token_str"].strip(),
            "sentence": result["sequence"], "score": result["score"]}

def ner(text=CONTEXT):
    predict = pipeline_for("ner", "token-classification", aggregation_strategy="simple")
    return {"context": text, "entities": [
        {"type": entity["entity_group"], "text": text[entity["start"]:entity["end"]],
         "score": float(entity["score"]), "start": int(entity["start"]), "end": int(entity["end"])}
        for entity in predict(text)]}

def question_answering(text=CONTEXT, questions=QUESTIONS):
    torch = cpu()
    from transformers import AutoModelForQuestionAnswering, AutoTokenizer

    model_id = MODELS["question_answering"]
    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    model = AutoModelForQuestionAnswering.from_pretrained(model_id, local_files_only=True).eval()
    answers = []
    for kind, question in questions.items():
        encoded = tokenizer(question, text, return_tensors="pt", return_offsets_mapping=True,
                            truncation="only_second", max_length=512)
        offsets = encoded.pop("offset_mapping")[0].tolist()
        context = torch.tensor([sequence == 1 and end > start
                                for sequence, (start, end) in zip(encoded.sequence_ids(), offsets)])
        if not context.any():
            raise ValueError("Question answering needs a nonempty context.")
        with torch.inference_mode():
            prediction = model(**encoded)
            starts = prediction.start_logits[0].float().masked_fill(~context, -torch.inf).softmax(0)
            ends = prediction.end_logits[0].float().masked_fill(~context, -torch.inf).softmax(0)
            positions = torch.arange(len(offsets))
            distances = positions[None, :] - positions[:, None]
            # Compare only ordered pairs of context tokens, up to 30 tokens per span.
            valid = context[:, None] & context[None, :] & (distances >= 0) & (distances < 30)
            probabilities = torch.outer(starts, ends).masked_fill(~valid, -1)
            start_token, end_token = divmod(int(probabilities.argmax()), len(offsets))
        start, end = offsets[start_token][0], offsets[end_token][1]
        answers.append({"type": kind, "question": question, "answer": text[start:end],
                        "start": start, "end": end,
                        "score": float(probabilities[start_token, end_token])})
    return {"context": text, "answers": answers}

def seq2seq(task, text, max_tokens):
    torch = cpu()
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    model_id = MODELS[task]
    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id, local_files_only=True).eval()
    with torch.inference_mode():
        tokens = model.generate(**tokenizer(text, return_tensors="pt"),
                                max_new_tokens=max_tokens, num_beams=4)
    generated = tokenizer.decode(tokens[0], skip_special_tokens=True).strip()
    if not generated:
        raise RuntimeError(f"{model_id} returned empty decoded text.")
    return generated

def summarization(text=SUMMARY):
    return {"input": text, "summary": seq2seq("summarization", "summarize: " + text, 100)}

def translation(text=TRANSLATION):
    return {"input": text, "direction": "fr → en",
            "translation": seq2seq("translation", text, 100)}

def image_classification(path):
    torch = cpu()
    from PIL import Image, ImageOps
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    model_id = MODELS["image_classification"]
    processor = AutoImageProcessor.from_pretrained(model_id, local_files_only=True, backend="pil")
    model = AutoModelForImageClassification.from_pretrained(model_id, local_files_only=True).eval()
    with Image.open(path) as source:
        if source.format not in {"JPEG", "PNG"}:
            raise ValueError("Use a JPEG or PNG photograph.")
        image = ImageOps.exif_transpose(source).convert("RGB")
    with torch.inference_mode():
        probabilities = model(**processor(images=image, return_tensors="pt")).logits[0].softmax(-1)
        scores, indices = probabilities.topk(3)
    return image, [{"label": model.config.id2label[index], "score": score}
                   for index, score in zip(indices.tolist(), scores.tolist())]

def asr(path):
    import wave
    import numpy as np

    torch = cpu()
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
    with wave.open(str(path), "rb") as clip:
        if clip.getsampwidth() != 2 or clip.getcomptype() != "NONE":
            raise ValueError("Use a signed 16-bit PCM WAV.")
        count, channels, rate = clip.getnframes(), clip.getnchannels(), clip.getframerate()
        if not 0 < count <= 30 * rate:
            raise ValueError("Use a nonempty WAV up to 30 seconds.")
        pcm = np.frombuffer(clip.readframes(count), dtype="<i2")
        if pcm.size != count * channels:
            raise ValueError("WAV data is truncated.")
        samples = pcm.reshape(-1, channels).mean(axis=1).astype(np.float32) / 32768
    if rate != 16000:
        target = np.arange(round(len(samples) * 16000 / rate)) * rate / 16000
        samples = np.interp(target, np.arange(len(samples)), samples).astype(np.float32)
    model_id = MODELS["asr"]
    processor = AutoProcessor.from_pretrained(model_id, local_files_only=True)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, local_files_only=True, dtype=torch.float32).eval()
    features = processor(samples, sampling_rate=16000, return_tensors="pt", return_attention_mask=True)
    with torch.inference_mode():
        tokens = model.generate(**features, language="en", task="transcribe", max_new_tokens=128)
    transcript = processor.batch_decode(tokens, skip_special_tokens=True)[0].strip()
    if not transcript:
        raise RuntimeError("Whisper returned an empty transcript.")
    return {"wav": str(Path(path).resolve()), "seconds": count / rate, "transcript": transcript}
