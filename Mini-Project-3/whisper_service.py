"""Local English transcription and explicit one-time model preparation."""

MODEL_ID = "openai/whisper-base.en"
MODEL_FILES = [
    "config.json", "generation_config.json", "preprocessor_config.json",
    "tokenizer_config.json", "special_tokens_map.json", "tokenizer.json",
    "vocab.json", "merges.txt", "normalizer.json", "added_tokens.json",
    "model.safetensors",
]


def load_model():
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

    processor = AutoProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        MODEL_ID, local_files_only=True, use_safetensors=True
    ).eval()
    return processor, model


def transcribe(pcm, sample_rate, processor, model):
    import numpy as np
    import torch

    audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    features = processor(
        audio, sampling_rate=sample_rate, return_tensors="pt", return_attention_mask=True
    )
    with torch.inference_mode():
        tokens = model.generate(**features, do_sample=False)
    return processor.batch_decode(tokens, skip_special_tokens=True)[0].strip()


if __name__ == "__main__":
    from huggingface_hub import snapshot_download

    path = snapshot_download(MODEL_ID, allow_patterns=MODEL_FILES, token=False)
    load_model()
    print(f"{MODEL_ID} hazır. Önbellek: {path}")
