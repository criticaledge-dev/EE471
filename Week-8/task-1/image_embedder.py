"""Compare two images by cosine similarity, without dumping vectors."""
from _common import arguments, base, image, mp, run


def main():
    args = arguments("Image Embedder", "mobilenet_v3_small.tflite", image=True, second=True).parse_args()
    with mp.tasks.vision.ImageEmbedder.create_from_options(mp.tasks.vision.ImageEmbedderOptions(base_options=base(args), l2_normalize=True)) as task:
        a = task.embed(image(args.image)).embeddings[0]
        b = task.embed(image(args.compare)).embeddings[0]
        result = {"dimension": len(a.embedding), "cosine_similarity": round(task.cosine_similarity(a, b), 5)}
    if args.output:
        from _presentation import comparison
        comparison(args.image, args.compare, args.output, result)
    return result


if __name__ == "__main__":
    run(main)
