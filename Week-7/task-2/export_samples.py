"""Export the first official test example of each class, without prediction selection."""
import argparse
from pathlib import Path

from PIL import Image
import torch
from torchvision.datasets import CIFAR10

from common import ROOT, sha256, write_json
from preprocessing import CLASSES, preprocess


def export(dataset, destination):
    if destination.exists():
        raise ValueError("Demo destination exists; choose a fresh directory.")
    assert tuple(dataset.classes) == CLASSES
    destination.mkdir(parents=True)
    samples = []
    for label, name in enumerate(CLASSES):
        index = dataset.targets.index(label)
        path = destination / f"test_{index:05d}_label_{label}_{name}.png"
        Image.fromarray(dataset.data[index]).save(path)
        with Image.open(path) as png:
            assert png.mode == "RGB" and png.size == (32, 32)
            assert torch.equal(preprocess(png), dataset[index][0])
        samples.append({"file": path.name, "official_test_index": index, "label": label,
                        "class": name, "sha256": sha256(path), "bytes": path.stat().st_size})
    manifest = {"dataset": "CIFAR10 official test set", "selection": "first test index per ground-truth class; no predictions used",
                "classes": CLASSES, "transform": "RGB 32x32; ToTensor; channel mean/std 0.5/0.5; no resize/augmentation",
                "png_transform_matches_dataset": True, "samples": samples}
    write_json(destination / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "demo_samples")
    args = parser.parse_args()
    export(CIFAR10(args.data_dir, train=False, download=False, transform=preprocess), args.output_dir)
