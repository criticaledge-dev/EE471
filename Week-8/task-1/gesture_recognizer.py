"""Recognize a gesture in an appropriate hand photograph."""
from _common import arguments, base, image, mp, run


def main():
    args = arguments("Gesture Recognizer", "gesture_recognizer.task", image=True).parse_args()
    options = mp.tasks.vision.GestureRecognizerOptions(base_options=base(args), num_hands=2)
    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as task:
        result = task.recognize(image(args.image))
    if not result.gestures:
        raise RuntimeError("No hand/gesture detected; use the documented thumb_up sample.")
    if args.output:
        from _presentation import landmarks
        labels = [f"{g[0].category_name}: {g[0].score:.5f}" for g in result.gestures]
        landmarks(args.image, args.output, [("hand", points) for points in result.hand_landmarks], labels)
    return {"hands": len(result.hand_landmarks), "gestures": [{"name": g[0].category_name, "score": round(g[0].score, 5)} for g in result.gestures]}


if __name__ == "__main__":
    run(main)
