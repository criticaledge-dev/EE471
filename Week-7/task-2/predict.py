"""Reload CPU state_dict in a separate process and predict one manifest PNG."""
import argparse
import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError
import torch

from common import ROOT, sha256, write_json
from evaluate import load_model
from preprocessing import CLASSES, preprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "artifacts/baseline/cifar10_last.pth")
    parser.add_argument("--manifest", type=Path, default=ROOT / "demo_samples/manifest.json")
    parser.add_argument("--test-index", type=int, default=0)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("Output exists; choose a fresh path.")
    torch.set_num_threads(2)
    manifest = json.loads(args.manifest.read_text())
    sample = next(item for item in manifest["samples"] if item["official_test_index"] == args.test_index)
    image_path = args.manifest.parent / sample["file"]
    assert sha256(image_path) == sample["sha256"]
    try:
        with Image.open(image_path) as image:
            batch = preprocess(image).unsqueeze(0)
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValueError("Expected an intact 32x32 CIFAR10 demo PNG.") from None
    with torch.inference_mode():
        logits = load_model(args.checkpoint)(batch)[0]
        scores, labels = logits.softmax(0).topk(3)
    label = logits.argmax().item()
    result = {"checkpoint_sha256": sha256(args.checkpoint), "image": sample["file"],
              "official_test_index": args.test_index, "true_label": sample["label"], "true_class": sample["class"],
              "predicted_label": label, "predicted_class": CLASSES[label], "correct": label == sample["label"],
              "probability": scores[0].item(), "logits": logits.tolist(),
              "top3": {CLASSES[i]: score for score, i in zip(scores.tolist(), labels.tolist())}}
    if args.reference:
        reference = json.loads(args.reference.read_text())
        assert result["checkpoint_sha256"] == reference["checkpoint_sha256"]
        assert sample["file"] == reference["image"]
        torch.testing.assert_close(logits, torch.tensor(reference["logits"]), rtol=1e-6, atol=1e-6)
        result["reference_verified"] = True
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
