"""Load a state_dict in a separate process and predict one 28x28 image."""
import argparse
import json
from pathlib import Path

from PIL import Image
import torch

from common import sha256, write_json
from evaluate import load_model
from preprocessing import CLASSES, preprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(2)
    model = load_model(args.checkpoint)
    with Image.open(args.image) as image:
        batch = preprocess(image).unsqueeze(0)
    with torch.inference_mode():
        logits = model(batch)[0]
        probabilities = logits.softmax(0)
    label = logits.argmax().item()
    result = {"predicted_label": label, "predicted_class": CLASSES[label],
              "probability": probabilities[label].item(), "image": args.image.name,
              "checkpoint_sha256": sha256(args.checkpoint), "reference_verified": False}
    if args.reference:
        reference = json.loads(args.reference.read_text(encoding="utf-8"))
        assert reference["checkpoint_sha256"] == result["checkpoint_sha256"]
        torch.testing.assert_close(logits, torch.tensor(reference["expected_logits"]), rtol=1e-6, atol=1e-6)
        assert label == reference["predicted_label"]
        result.update(reference_verified=True, true_label=reference["true_label"], true_class=reference["true_class"])
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
