"""Classify raised arms in a single, upright photo."""
import argparse
from pathlib import Path

MODEL = Path(__file__).resolve().parent / "models" / "pose_landmarker_lite.task"
# Image landmarks use the subject's anatomical left/right.
ARM_POINTS = {"left": (11, 13, 15), "right": (12, 14, 16)}
MIN_VISIBILITY = 0.5
HEIGHT_MARGIN = 0.02


def visible(point) -> bool:
    return (point.visibility or 0.0) >= MIN_VISIBILITY


def raised(landmarks, side) -> bool:
    if not landmarks:
        return False
    shoulder_index, _, wrist_index = ARM_POINTS[side]
    shoulder, wrist = landmarks[shoulder_index], landmarks[wrist_index]
    return visible(shoulder) and visible(wrist) and shoulder.y - wrist.y >= HEIGHT_MARGIN


def classify(landmarks) -> str:
    left = raised(landmarks, "left")
    right = raised(landmarks, "right")
    if left and right:
        return "both"
    return "left" if left else "right" if right else "None"


def load_model():
    import mediapipe as mp

    if not MODEL.is_file():
        raise ValueError("Model missing; run bash download_model.sh first.")
    return mp.tasks.vision.PoseLandmarker.create_from_options(
        mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL)),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_poses=1,
        )
    )


def save_overlay(photo, landmarks, label, output) -> None:
    from PIL import ImageDraw

    canvas = photo.copy()
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    radius = max(3, min(width, height) // 55)
    if landmarks:
        for side, indices in ARM_POINTS.items():
            points = [landmarks[index] for index in indices]
            xy = [(round(p.x * width), round(p.y * height)) for p in points]
            color = "#00dc7d" if raised(landmarks, side) else "#ffad38"
            for i in range(2):
                if visible(points[i]) and visible(points[i + 1]):
                    draw.line(xy[i:i + 2], fill=color, width=radius)
            for (x, y), point in zip(xy, points):
                if visible(point):
                    draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                                 fill=color, outline="black")
    caption = f"Result: {label}"
    x0, y0, x1, y1 = draw.textbbox((8, 6), caption, font_size=18)
    draw.rectangle((x0 - 4, y0 - 3, x1 + 4, y1 + 3), fill="#152033")
    draw.text((8, 6), caption, fill="white", font_size=18)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG")


def predict(detector, image_path: Path, output: Path | None = None) -> str:
    import mediapipe as mp
    import numpy as np
    from PIL import Image, ImageOps

    if output is not None:
        if output.suffix.lower() != ".png":
            raise ValueError("Overlay output must have a .png extension.")
        if output.resolve() == image_path.resolve() or (
            output.exists() and image_path.exists() and output.samefile(image_path)
        ):
            raise ValueError("Overlay output must be different from the input.")

    try:
        with Image.open(image_path) as source:
            if source.format not in {"JPEG", "PNG"}:
                raise ValueError("Expected a JPEG or PNG image.")
            upright = ImageOps.exif_transpose(source).convert("RGB")
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(upright))
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Could not read a valid JPEG or PNG image.") from exc

    poses = detector.detect(image).pose_landmarks
    landmarks = poses[0] if poses else []
    label = classify(landmarks)
    if output is not None:
        save_overlay(upright, landmarks, label, output)
    return label


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, help="optional annotated PNG")
    args = parser.parse_args()
    try:
        with load_model() as detector:
            print(predict(detector, args.image, args.output))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
