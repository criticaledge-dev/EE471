"""Show the tokenizer's existing CLS and SEP tokens around one sentence."""
from _local import load_tokenizer


def main():
    tokenizer = load_tokenizer()
    text = "This lesson is useful."
    vocabulary_size = len(tokenizer)
    plain_ids = tokenizer.encode(text, add_special_tokens=False)
    wrapped_ids = tokenizer.encode(text, add_special_tokens=True)
    boundary_ids = [tokenizer.cls_token_id, tokenizer.sep_token_id]
    if wrapped_ids != [boundary_ids[0], *plain_ids, boundary_ids[1]] or len(tokenizer) != vocabulary_size:
        raise AssertionError("Expected the existing CLS and SEP tokens around unchanged content.")

    print(f"Input: {text}")
    print(f"add_special_tokens=False: {tokenizer.convert_ids_to_tokens(plain_ids)}")
    print(f"add_special_tokens=True:  {tokenizer.convert_ids_to_tokens(wrapped_ids)}")
    print(f"PASS: {tokenizer.cls_token}={boundary_ids[0]}, {tokenizer.sep_token}={boundary_ids[1]}. Vocabulary: {vocabulary_size}.")


if __name__ == "__main__":
    main()
