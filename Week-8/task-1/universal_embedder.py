"""Text modality of the official universal embedding task."""
from _common import arguments, base, cache, mp, present, run


def options(args):
    return mp.tasks.retrieval.UniversalEmbedderOptions(base_options=base(args), l2_normalize=True, cache_dir=cache("universal-cache"))


def main():
    args = arguments("Universal Embedder", "embeddinggemma-2-text-270m.litertlm", text="The library lends books.", second=True).parse_args()
    with mp.tasks.retrieval.UniversalEmbedder.create_from_options(options(args)) as task:
        a = task.embed_text(args.text).embeddings[0]
        b = task.embed_text(args.compare or "You can borrow books from the library.").embeddings[0]
        return present(args, {"modality": "text", "dimension": len(a.embedding), "cosine_similarity": round(task.cosine_similarity(a, b), 5)}, text=args.text, compare=args.compare or "You can borrow books from the library.")


if __name__ == "__main__":
    run(main)
