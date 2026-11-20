"""Save the real foreground confidence mask from Selfie Segmenter."""
import numpy as np
from PIL import Image
from _common import OUTPUT, arguments, base, image, mp, output_path, run


def main():
    parser = arguments("Image Segmenter", "selfie_segmenter.tflite", image=True, mask=True)
    parser.add_argument("--output", default=OUTPUT / "selfie-mask.png")
    parser.add_argument("--overlay", help="Optional colour overlay PNG inside Week-8/task-1/output.")
    args = parser.parse_args()
    options = mp.tasks.vision.ImageSegmenterOptions(base_options=base(args), output_category_mask=False, output_confidence_masks=True)
    with mp.tasks.vision.ImageSegmenter.create_from_options(options) as task:
        result = task.segment(image(args.image))
        mask_image = result.confidence_masks[0]
        mask = mask_image.numpy_view().copy().squeeze()
    if not np.isfinite(mask).all() or mask.min() < 0 or mask.max() > 1:
        raise RuntimeError("Unexpected confidence mask; expected finite values in [0,1].")
    if not (np.any(mask > 0.5) and np.any(mask < 0.5)):
        raise RuntimeError("No distinct foreground/background; use an appropriate person photograph.")
    Image.fromarray((mask * 255).astype(np.uint8)).save(output_path(args.output))
    if args.overlay:
        from _presentation import overlay
        overlay(args.image, args.overlay, mask)
    return {"mask": str(args.output), "size": list(mask.shape), "range": [float(mask.min()), float(mask.max())]}


if __name__ == "__main__":
    run(main)
