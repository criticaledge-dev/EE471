"""First official-test occurrence of each class, selected without predictions."""
import argparse
from pathlib import Path

from torchvision.datasets import FashionMNIST

from common import ROOT, sha256, write_json
from preprocessing import CLASSES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "demo_samples")
    args = parser.parse_args()
    dataset = FashionMNIST(args.data_dir, train=False, download=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    samples = []
    for label, name in enumerate(CLASSES):
        index = (dataset.targets == label).nonzero()[0].item()
        image, actual = dataset[index]
        assert actual == label
        slug = name.lower().replace("/", "_").replace("-", "_").replace(" ", "_")
        file = args.output_dir / f"test_{index:05d}_label_{label}_{slug}.png"
        image.save(file)
        samples.append({"file": file.name, "official_test_index": index, "label": label,
                        "class": name, "mode": image.mode, "size": list(image.size),
                        "bytes": file.stat().st_size, "sha256": sha256(file)})
    write_json(args.output_dir / "manifest.json", {
        "dataset": "FashionMNIST official test", "selection": "first occurrence of each ground-truth class; no prediction filtering",
        "samples": samples, "total_png_bytes": sum(x["bytes"] for x in samples)})
    print(f"Exported {len(samples)} labeled PNGs; {sum(x['bytes'] for x in samples)} bytes total")


if __name__ == "__main__":
    main()
