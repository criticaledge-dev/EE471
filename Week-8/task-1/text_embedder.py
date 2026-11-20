"""Print embedding size and real cosine similarity without dumping the vector."""
from _common import arguments, base, mp, present, run


def main():
    parser = arguments("Text Embedder", "universal_sentence_encoder.tflite", text="The library is open today.", second=True)
    args = parser.parse_args()
    options = mp.tasks.text.TextEmbedderOptions(base_options=base(args), l2_normalize=True)
    with mp.tasks.text.TextEmbedder.create_from_options(options) as task:
        first = task.embed(args.text).embeddings[0]
        second = task.embed(args.compare or "You can visit the library today.").embeddings[0]
        return present(args, {"dimension": len(first.embedding), "cosine_similarity": round(task.cosine_similarity(first, second), 5)}, text=args.text, compare=args.compare or "You can visit the library today.")


if __name__ == "__main__":
    run(main)
