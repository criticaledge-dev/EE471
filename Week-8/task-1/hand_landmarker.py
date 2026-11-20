"""Detect 21 landmarks per hand; show only one wrist coordinate."""
from _common import arguments, base, image, mp, run


def main():
    args = arguments("Hand Landmarker", "hand_landmarker.task", image=True).parse_args()
    with mp.tasks.vision.HandLandmarker.create_from_options(mp.tasks.vision.HandLandmarkerOptions(base_options=base(args), num_hands=2)) as task:
        result = task.detect(image(args.image))
    if not result.hand_landmarks:
        raise RuntimeError("No hand detected; use the documented thumb_up sample.")
    if args.output:
        from _presentation import landmarks
        landmarks(args.image, args.output, [("hand", points) for points in result.hand_landmarks])
    return {"hands": [{"side": side[0].category_name, "landmarks": len(points), "wrist_xy": [round(points[0].x, 4), round(points[0].y, 4)]} for side, points in zip(result.handedness, result.hand_landmarks)]}


if __name__ == "__main__":
    run(main)
