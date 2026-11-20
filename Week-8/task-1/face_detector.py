"""Face bounding boxes from a still image."""
from _common import arguments, base, detection, image, mp, run


def main():
    args = arguments("Face Detector", "blaze_face_short_range.tflite", image=True).parse_args()
    with mp.tasks.vision.FaceDetector.create_from_options(mp.tasks.vision.FaceDetectorOptions(base_options=base(args))) as task:
        result = {"faces": detection(task.detect(image(args.image)))}
    if args.output:
        from _presentation import boxes
        boxes(args.image, args.output, result["faces"])
    return result


if __name__ == "__main__":
    run(main)
