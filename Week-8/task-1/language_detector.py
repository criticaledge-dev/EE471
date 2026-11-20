"""Detect the language of a short text using Google's language detector."""
from _common import arguments, base, mp, present, run


def main():
    args = arguments("Language Detector", "language_detector.tflite", text="This library has many interesting books.").parse_args()
    options = mp.tasks.text.LanguageDetectorOptions(base_options=base(args), max_results=2)
    with mp.tasks.text.LanguageDetector.create_from_options(options) as task:
        result = task.detect(args.text)
    return present(args, {"languages": [{"code": d.language_code, "probability": round(d.probability, 5)} for d in result.detections]}, text=args.text)


if __name__ == "__main__":
    run(main)
