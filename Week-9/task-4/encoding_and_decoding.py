"""Encode one sentence and decode the resulting token IDs."""
from _local import load_tokenizer


def main():
    tokenizer = load_tokenizer()
    text = "Transformers are useful."
    ids = tokenizer.encode(text, add_special_tokens=False)
    decoded = tokenizer.decode(ids)
    if decoded != text.lower() or tokenizer.encode(decoded, add_special_tokens=False) != ids:
        raise AssertionError("The uncased text and token IDs did not round-trip.")

    print(f"Input:   {text}")
    print(f"IDs:     {ids}")
    print(f"Decoded: {decoded}")
    print("PASS: decoded text normalizes case and re-encodes to the same IDs.")


if __name__ == "__main__":
    main()
