"""MediaPipe 1.2.3 Magic Touch v2: set_image + a normalized positive stroke."""
import numpy as np
from PIL import Image
from _common import OUTPUT, arguments, base, image, mp, output_path, run


def main():
    parser = arguments("Interactive Segmenter", "interactive_segmentation.task", image=True, mask=True)
    parser.add_argument("--x", type=float, default=0.5)
    parser.add_argument("--y", type=float, default=0.45)
    parser.add_argument("--output", default=OUTPUT / "interactive-mask.png")
    parser.add_argument("--overlay", help="Optional colour overlay PNG inside Week-8/task-1/output.")
    args = parser.parse_args()
    if not (0 <= args.x <= 1 and 0 <= args.y <= 1):
        raise ValueError("The selected point must be normalized to [0,1].")
    vision = mp.tasks.vision
    stroke = vision.InteractiveSegmenterStroke(brush_mode=vision.InteractiveSegmenterBrushMode.POSITIVE, points=[vision.InteractiveSegmenterStrokePoint(x=args.x, y=args.y)], is_completed=True)
    with vision.InteractiveSegmenter.create_from_options(vision.InteractiveSegmenterOptions(base_options=base(args))) as task:
        task.set_image(image(args.image))
        mask_image = task.segment([stroke])
        mask = mask_image.numpy_view().copy().squeeze()
    if not np.isfinite(mask).all() or mask.min() < 0 or mask.max() > 1:
        raise RuntimeError("Unexpected confidence mask; expected finite values in [0,1].")
    if not np.any(mask):
        raise RuntimeError("The model returned an empty mask at this point.")
    # The v2 API returns a float confidence mask in [0,1]. Save its true values.
    pixels = np.clip(mask * 255 if np.issubdtype(mask.dtype, np.floating) else mask, 0, 255).astype(np.uint8)
    Image.fromarray(pixels).save(output_path(args.output))
    if args.overlay:
        from _presentation import overlay
        overlay(args.image, args.overlay, mask, (args.x, args.y))
    return {"point_xy": [args.x, args.y], "mask": str(args.output), "size": list(mask.shape), "range": [float(mask.min()), float(mask.max())]}


if __name__ == "__main__":
    run(main)
