"""Independent checkpoint evaluation, with no training or selection."""
import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision.datasets import CIFAR10

from common import ROOT, sha256, versions, write_json
from engine import run_epoch
from model import Net
from preprocessing import CLASSES, preprocess


def load_model(checkpoint, device="cpu"):
    model = Net().to(device)
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
    return model.eval()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "artifacts/baseline/cifar10_last.pth")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("Output exists; choose a fresh path.")
    torch.set_num_threads(2)
    dataset = CIFAR10(args.data_dir, train=False, download=False, transform=preprocess)
    assert tuple(dataset.classes) == CLASSES
    result = {"device": "cpu", "versions": versions(), "checkpoint_sha256": sha256(args.checkpoint),
              "test": run_epoch(load_model(args.checkpoint), DataLoader(dataset, batch_size=4, shuffle=False, num_workers=0), "cpu")}
    if args.output:
        write_json(args.output, result)
    print(result)
