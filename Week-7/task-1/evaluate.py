"""Independent official-test evaluation of an explicitly supplied checkpoint."""
import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision.datasets import FashionMNIST

from common import ROOT, write_json
from engine import run_epoch
from model import NeuralNetwork
from preprocessing import preprocess


def load_model(checkpoint, device="cpu"):
    model = NeuralNetwork().to(device)
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
    model.eval()
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(2)
    dataset = FashionMNIST(args.data_dir, train=False, download=True, transform=preprocess)
    result = run_epoch(load_model(args.checkpoint), DataLoader(dataset, batch_size=64), "cpu")
    if args.output:
        write_json(args.output, result)
    print(result)


if __name__ == "__main__":
    main()
