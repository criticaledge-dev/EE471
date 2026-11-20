"""Classify head direction as left, right, or straight, from the viewer's side."""
import argparse
import math
from pathlib import Path

MODEL = Path(__file__).resolve().parent / "models" / "face_landmarker.task"
STRAIGHT_LIMIT_DEGREES = 15.0


def estimate_yaw(matrix) -> float:
    # Column 2 is the transformed forward axis. Read its horizontal (X/Z) angle.
    return math.degrees(math.atan2(matrix[0, 2], matrix[2, 2]))


def load_model():
    import mediapipe as mp

    if not MODEL.is_file():
        raise ValueError("Model missing; run bash download_model.sh first.")
    return mp.tasks.vision.FaceLandmarker.create_from_options(
        mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL)),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_faces=1,
            output_facial_transformation_matrixes=True,
        )
    )


def save_preview(photo, label: str, yaw: float, output: Path) -> None:
    from PIL import Image, ImageDraw

    width, height = photo.size
    preview = Image.new("RGB", (max(width, 200), height + 66), "#142033")
    preview.paste(photo, ((preview.width - width) // 2, 0))
    draw = ImageDraw.Draw(preview)
    draw.text((14, height + 7), f"Result: {label}", fill="white", font_size=19)
    draw.text((14, height + 36), f"Yaw: {yaw:+.1f}\N{DEGREE SIGN}", fill="#c9d8ea", font_size=15)

    # Icon is a symbol for the label, not a ray showing where the eyes look.
    x, y = preview.width - 32, height + 33
    accent = "#62dfc6"
    if label == "straight":
        draw.ellipse((x - 11, y - 11, x + 11, y + 11), outline=accent, width=3)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=accent)
    else:
        sign = -1 if label == "left" else 1
        tip = x + sign * 15
        draw.line((x - sign * 13, y, tip, y), fill=accent, width=4)
        draw.line([(tip - sign * 9, y - 8), (tip, y), (tip - sign * 9, y + 8)],
                  fill=accent, width=4)

    output.parent.mkdir(parents=True, exist_ok=True)
    preview.save(output, format="PNG")


def predict(detector, image_path: Path, output: Path | None = None) -> str:
    import mediapipe as mp
    import numpy as np
    from PIL import Image, ImageOps

    if output is not None:
        if output.suffix.lower() != ".png":
            raise ValueError("Preview output must have a .png extension.")
        if output.resolve() == image_path.resolve() or (
            output.exists() and image_path.exists() and output.samefile(image_path)
        ):
            raise ValueError("Preview output must be different from the input.")

    try:
        with Image.open(image_path) as source:
            if source.format not in {"JPEG", "PNG"}:
                raise ValueError("Expected a JPEG or PNG image.")
            upright = ImageOps.exif_transpose(source).convert("RGB")
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(upright))
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Could not read a valid JPEG or PNG image.") from exc

    transforms = detector.detect(image).facial_transformation_matrixes
    if not transforms:
        raise ValueError("No face detected.")
    yaw = estimate_yaw(transforms[0])
    if abs(yaw) <= STRAIGHT_LIMIT_DEGREES:
        label = "straight"
    else:
        label = "left" if yaw < 0 else "right"
    if output is not None:
        save_preview(upright, label, yaw, output)
    return label


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, help="optional PNG with direction and yaw")
    args = parser.parse_args()
    try:
        with load_model() as detector:
            print(predict(detector, args.image, args.output))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
