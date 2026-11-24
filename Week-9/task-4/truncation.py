"""Compare full and truncated content with the same special-token setting."""
from _local import load_tokenizer


def main():
    tokenizer = load_tokenizer()
    text = "This short demo shows how a tokenizer removes tokens beyond a fixed input limit."
    limit = 10
    options = {"add_special_tokens": True, "return_special_tokens_mask": True}
    full = tokenizer(text, truncation=False, **options)
    short = tokenizer(text, truncation=True, max_length=limit, **options)

    def content(encoded):
        return [token for token, special in zip(encoded["input_ids"], encoded["special_tokens_mask"], strict=True)
                if not special]

    original, retained = content(full), content(short)
    full_count, short_count = len(full["input_ids"]), len(short["input_ids"])
    if not (full_count > short_count == limit and retained == original[:len(retained)]
            and sum(full["special_tokens_mask"]) == sum(short["special_tokens_mask"])):
        raise AssertionError("Expected right truncation with the same special-token count.")
    removed = original[len(retained):]

    print(f"Input: {text}")
    print(f"Tokens: {full_count} -> {short_count} (max_length={limit}, special tokens on)")
    print(f"Kept:    {tokenizer.decode(retained)}")
    print(f"Removed: {tokenizer.decode(removed)}")
    print("PASS: suffix removed and special-token count preserved.")


if __name__ == "__main__":
    main()
