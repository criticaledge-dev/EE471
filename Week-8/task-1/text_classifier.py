"""Positive/negative sentiment classification, not general topic classification."""
from _common import arguments, base, categories, mp, present, run


def main():
    args = arguments("Text Classifier", "average_word_classifier.tflite", text="This movie was wonderful and I loved it.").parse_args()
    with mp.tasks.text.TextClassifier.create_from_options(mp.tasks.text.TextClassifierOptions(base_options=base(args))) as task:
        return present(args, {"sentiment": categories(task.classify(args.text))}, text=args.text)


if __name__ == "__main__":
    run(main)
