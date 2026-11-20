"""Detect objects and display actual COCO labels/boxes."""
from _common import arguments, base, detection, image, mp, run


def main():
    args = arguments("Object Detector", "efficientdet_lite0.tflite", image=True).parse_args()
    options = mp.tasks.vision.ObjectDetectorOptions(base_options=base(args), max_results=3, score_threshold=0.4)
    with mp.tasks.vision.ObjectDetector.create_from_options(options) as task:
        result = {"objects": detection(task.detect(image(args.image)))}
    if args.output:
        from _presentation import boxes
        boxes(args.image, args.output, result["objects"])
    return result


if __name__ == "__main__":
    run(main)
