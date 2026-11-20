"""Show the actual pose, face and hand landmark counts; no custom labels."""
from _common import arguments, base, image, mp, run


def main():
    args = arguments("Holistic Landmarker", "holistic_landmarker.task", image=True).parse_args()
    with mp.tasks.vision.HolisticLandmarker.create_from_options(mp.tasks.vision.HolisticLandmarkerOptions(base_options=base(args))) as task:
        result = task.detect(image(args.image))
    counts = {name: len(getattr(result, name)) for name in ("pose_landmarks", "face_landmarks", "left_hand_landmarks", "right_hand_landmarks")}
    if not any(counts.values()):
        raise RuntimeError("No holistic landmarks detected on this input.")
    if args.output:
        from _presentation import landmarks
        landmarks(args.image, args.output, [("pose", result.pose_landmarks), ("face", result.face_landmarks),
                  ("hand", result.left_hand_landmarks), ("hand", result.right_hand_landmarks)])
    return counts


if __name__ == "__main__":
    run(main)
