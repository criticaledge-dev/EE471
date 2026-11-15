"""One fixed five-epoch baseline. Official test is evaluated only at the end."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import time

import torch
from torch.utils.data import DataLoader, Subset
from torchvision.datasets import FashionMNIST

from common import ROOT, indices_hash, seed_everything, sha256, split_indices, versions, write_json
from engine import run_epoch
from model import NeuralNetwork
from preprocessing import CLASSES, preprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "results/baseline")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "artifacts/baseline/fashion_mnist_last.pth")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--overwrite", action="store_true", help="Replace this run's own metrics/checkpoint")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("threads must be positive")
    if not args.overwrite and ((args.run_dir / "metrics.json").exists() or args.checkpoint.exists()):
        parser.error("Run already exists; choose new output paths or explicitly use --overwrite.")
    seed_everything(args.seed, args.threads)
    started = time.perf_counter()
    config = {"learning_rate": .001, "batch_size": 64, "epochs": 5, "seed": args.seed,
              "train_fraction": .9, "validation_fraction": .1, "device": args.device,
              "cpu_threads": args.threads, "num_workers": 0, "optimizer": "SGD",
              "momentum": 0, "weight_decay": 0, "loss": "CrossEntropyLoss",
              "architecture": "Flatten -> Linear(784,512) -> ReLU -> Linear(512,512) -> ReLU -> Linear(512,10)",
              "transform": "28x28 grayscale; ToTensor [0,1]; no normalization/augmentation"}
    report = {"status": "in_progress", "run_type": "full_baseline", "config": config,
              "versions": versions(), "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "epochs": [], "test": None, "checkpoint_selection": "last epoch, never best validation/test"}
    write_json(args.run_dir / "metrics.json", report)
    print("CONFIG", config, flush=True)
    dataset = FashionMNIST(args.data_dir, train=True, download=True, transform=preprocess)
    assert tuple(dataset.classes) == CLASSES
    train_ids, validation_ids = split_indices(len(dataset), args.seed)
    split = {"dataset": "FashionMNIST official training set", "total": len(dataset),
             "train": len(train_ids), "validation": len(validation_ids), "seed": args.seed,
             "method": "torch.randperm with independent seeded generator; first 90% train",
             "train_indices_sha256_le_int64": indices_hash(train_ids),
             "validation_indices_sha256_le_int64": indices_hash(validation_ids),
             "official_test_used_for_selection": False}
    write_json(args.run_dir / "split.json", split)
    report["split"] = split
    generator = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(Subset(dataset, train_ids), batch_size=64, shuffle=True,
                              generator=generator, num_workers=0)
    validation_loader = DataLoader(Subset(dataset, validation_ids), batch_size=64, shuffle=False, num_workers=0)
    model = NeuralNetwork().to(args.device)
    optimizer = torch.optim.SGD(model.parameters(), lr=.001)
    training_started = time.perf_counter()
    for epoch in range(1, 6):
        epoch_started = time.perf_counter()
        train = run_epoch(model, train_loader, args.device, optimizer)
        validation = run_epoch(model, validation_loader, args.device)
        row = {"epoch": epoch, "train": train, "validation": validation,
               "seconds": time.perf_counter() - epoch_started}
        report["epochs"].append(row)
        write_json(args.run_dir / "metrics.json", report)
        print(f"EPOCH {epoch}/5 train_loss={train['loss']:.6f} train_acc={train['accuracy']:.4%} "
              f"val_loss={validation['loss']:.6f} val_acc={validation['accuracy']:.4%} "
              f"seconds={row['seconds']:.2f}", flush=True)
    report["training_and_validation_seconds"] = time.perf_counter() - training_started
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save({name: value.detach().cpu() for name, value in model.state_dict().items()}, args.checkpoint)
    report["checkpoint"] = {"path": str(args.checkpoint), "bytes": args.checkpoint.stat().st_size,
                            "sha256": sha256(args.checkpoint), "format": "state_dict only"}
    # No official test loader is used inside the training/validation loop.
    test = FashionMNIST(args.data_dir, train=False, download=True, transform=preprocess)
    report["test"] = run_epoch(model, DataLoader(test, batch_size=64, shuffle=False), args.device)
    with torch.inference_mode():
        image, label = test[0]
        logits = model(image.unsqueeze(0).to(args.device))[0].cpu().tolist()
    write_json(args.run_dir / "reload_reference.json", {
        "official_test_index": 0, "true_label": label, "true_class": CLASSES[label],
        "expected_logits": logits, "predicted_label": max(range(10), key=logits.__getitem__),
        "checkpoint_sha256": report["checkpoint"]["sha256"]})
    report["status"] = "completed"
    report["total_seconds_including_data"] = time.perf_counter() - started
    write_json(args.run_dir / "metrics.json", report)
    print("TEST", report["test"], flush=True)
    print("TRAINING_AND_VALIDATION_SECONDS", report["training_and_validation_seconds"], flush=True)
    print("CHECKPOINT", report["checkpoint"], flush=True)


if __name__ == "__main__":
    main()
