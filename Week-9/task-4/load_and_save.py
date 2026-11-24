"""Compare a cached DistilBERT prediction with a local save/reload."""
from pathlib import Path

from _local import MODEL_ID, load_tokenizer

import torch
from transformers import AutoModelForSequenceClassification

DESTINATION = Path(__file__).resolve().parent / "output" / "distilbert-sst2"
TEXT = "I enjoyed this practical lesson."


def predict(model, tokenizer):
    inputs = tokenizer(TEXT, return_tensors="pt")
    with torch.inference_mode():
        logits = model(**inputs).logits[0]
    probabilities = logits.softmax(dim=-1)
    index = int(probabilities.argmax())
    return inputs["input_ids"], logits, model.config.id2label[index], float(probabilities[index])


def main():
    torch.set_num_threads(4)
    tokenizer = load_tokenizer()
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, local_files_only=True).eval()
    before_ids, before_logits, before_label, before_score = predict(model, tokenizer)

    DESTINATION.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(DESTINATION)
    tokenizer.save_pretrained(DESTINATION)
    del model, tokenizer

    restored_tokenizer = load_tokenizer(DESTINATION)
    restored_model = AutoModelForSequenceClassification.from_pretrained(
        DESTINATION, local_files_only=True
    ).eval()
    after_ids, after_logits, after_label, after_score = predict(restored_model, restored_tokenizer)
    torch.testing.assert_close(before_ids, after_ids, rtol=0, atol=0)
    torch.testing.assert_close(before_logits, after_logits, rtol=1e-6, atol=1e-6)
    if before_label != after_label:
        raise AssertionError("The predicted label changed after reload.")

    print(f"Input: {TEXT}")
    print(f"Saved to: {DESTINATION}")
    print(f"Before: {before_label} ({before_score:.6f})")
    print(f"After:  {after_label} ({after_score:.6f})")
    print("PASS: token IDs, logits and label match after offline reload.")


if __name__ == "__main__":
    main()
