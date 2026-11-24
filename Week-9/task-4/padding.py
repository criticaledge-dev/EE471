"""Inspect padding and attention masks for two sentences in one batch."""
from _local import load_tokenizer


def main():
    tokenizer = load_tokenizer()
    texts = ["Hello.", "I enjoyed this practical lesson."]
    original = tokenizer(texts, add_special_tokens=True)["input_ids"]
    padded = tokenizer(texts, padding=True, add_special_tokens=True, return_attention_mask=True)
    before = [len(row) for row in original]
    after = [len(row) for row in padded["input_ids"]]
    if after != [max(before)] * len(texts) or before == after:
        raise AssertionError("Expected at least one row to be padded to the batch maximum.")
    for source, ids, mask in zip(original, padded["input_ids"], padded["attention_mask"], strict=True):
        expected_mask = [int(token != tokenizer.pad_token_id) for token in ids]
        retained = [token for token, use_token in zip(ids, mask, strict=True) if use_token]
        if mask != expected_mask or retained != source:
            raise AssertionError("Padding mask did not preserve the source tokens.")

    print(f"Sentences: {texts}")
    print(f"Lengths: {before} -> {after}")
    print(f"input_ids:      {padded['input_ids']}")
    print(f"attention_mask: {padded['attention_mask']}")
    print(f"PASS: added {tokenizer.pad_token} positions have mask 0.")


if __name__ == "__main__":
    main()
