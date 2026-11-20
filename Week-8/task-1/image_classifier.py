"""Top three ImageNet labels, not a custom cat-breed classifier."""
from _common import arguments, base, categories, image, mp, run


def main():
    args = arguments("Image Classifier", "efficientnet_lite0.tflite", image=True).parse_args()
    with mp.tasks.vision.ImageClassifier.create_from_options(mp.tasks.vision.ImageClassifierOptions(base_options=base(args), max_results=3)) as task:
        result = {"top_three": categories(task.classify(image(args.image)))}
    if args.output:
        from _presentation import classification
        classification(args.image, args.output, result["top_three"])
    return result


if __name__ == "__main__":
    run(main)
