"""Full CIFAR10 baseline: fixed 45k/5k split, two epochs, final checkpoint only."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import time

import torch
from torch.utils.data import DataLoader, Subset
from torchvision.datasets import CIFAR10

from common import ROOT, indices_hash, seed_everything, sha256, split_indices, versions, write_json
from engine import run_epoch
from export_samples import export
from model import Net
from preprocessing import CLASSES, preprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "results/baseline")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "artifacts/baseline/cifar10_last.pth")
    parser.add_argument("--demo-dir", type=Path, default=ROOT / "demo_samples")
    args = parser.parse_args()
    if args.run_dir.exists() or args.checkpoint.exists() or args.demo_dir.exists():
        parser.error("Output exists; choose fresh run/checkpoint/demo paths. Previous results are never overwritten.")
    started = time.perf_counter()
    seed_everything(42, 2)
    config = {"seed": 42, "device": "cpu", "cpu_threads": 2, "num_workers": 0, "epochs": 2,
              "batch_size": 4, "optimizer": "SGD", "learning_rate": .001, "momentum": .9,
              "dampening": 0, "weight_decay": 0, "nesterov": False, "loss": "CrossEntropyLoss",
              "architecture": "Conv(3,6,5)-ReLU-Pool(2)-Conv(6,16,5)-ReLU-Pool(2)-Flatten-Linear(400,120)-ReLU-Linear(120,84)-ReLU-Linear(84,10)",
              "transform": "32x32 RGB; ToTensor; mean=(.5,.5,.5), std=(.5,.5,.5); no augmentation/resize"}
    report = {"status": "started", "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "versions": versions(), "config": config, "classes": CLASSES, "epochs": [],
              "source_sha256": {name: sha256(ROOT / name) for name in
                                ("model.py", "preprocessing.py", "train.py", "engine.py", "common.py", "evaluate.py", "export_samples.py")}}
    write_json(args.run_dir / "metrics.json", report)
    print("CONFIG", config, flush=True)
    data_started = time.perf_counter()
    dataset = CIFAR10(args.data_dir, train=True, download=True, transform=preprocess)
    assert len(dataset) == 50000 and tuple(dataset.classes) == CLASSES
    report["dataset_classes_verified"] = list(dataset.classes)
    report["training_data_download_and_load_seconds"] = time.perf_counter() - data_started
    train_ids, validation_ids = split_indices(50000, 42)
    split = {"dataset": "CIFAR10 official training set", "total": 50000, "train": 45000, "validation": 5000,
             "seed": 42, "method": "torch.randperm with independent torch.Generator.manual_seed(42); first 45000 train, remaining 5000 validation",
             "train_indices_sha256_le_int64": indices_hash(train_ids),
             "validation_indices_sha256_le_int64": indices_hash(validation_ids), "official_test_used_for_selection": False}
    write_json(args.run_dir / "split.json", split)
    report["split"] = split
    train_loader = DataLoader(Subset(dataset, train_ids), batch_size=4, shuffle=True,
                              generator=torch.Generator().manual_seed(42), num_workers=0)
    validation_loader = DataLoader(Subset(dataset, validation_ids), batch_size=4, shuffle=False, num_workers=0)
    model = Net().to("cpu")
    optimizer = torch.optim.SGD(model.parameters(), lr=.001, momentum=.9)
    report["optimizer_defaults"] = optimizer.defaults
    for epoch in range(1, 3):
        start = time.perf_counter()
        print(f"EPOCH {epoch}/2 training 45000 examples...", flush=True)
        train = run_epoch(model, train_loader, "cpu", optimizer)
        train_seconds = time.perf_counter() - start
        validation_start = time.perf_counter()
        validation = run_epoch(model, validation_loader, "cpu")
        row = {"epoch": epoch, "train": train, "validation": validation,
               "training_seconds": train_seconds, "validation_seconds": time.perf_counter() - validation_start,
               "seconds": time.perf_counter() - start}
        report["epochs"].append(row)
        write_json(args.run_dir / "metrics.json", report)
        print("EPOCH_RESULT", row, flush=True)
    report["training_seconds"] = sum(row["training_seconds"] for row in report["epochs"])
    report["training_and_validation_seconds"] = sum(row["seconds"] for row in report["epochs"])
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save({name: value.detach().cpu() for name, value in model.state_dict().items()}, args.checkpoint)
    report["checkpoint"] = {"path": str(args.checkpoint), "bytes": args.checkpoint.stat().st_size,
                            "sha256": sha256(args.checkpoint), "format": "CPU state_dict only"}
    report["checkpoint_selection"] = "epoch 2 final checkpoint; no validation/test checkpoint selection"
    # The official test dataset is first instantiated AFTER final checkpoint save.
    test_start = time.perf_counter()
    test = CIFAR10(args.data_dir, train=False, download=False, transform=preprocess)
    assert len(test) == 10000 and tuple(test.classes) == CLASSES
    report["test"] = run_epoch(model, DataLoader(test, batch_size=4, shuffle=False, num_workers=0), "cpu")
    report["final_test_load_and_evaluation_seconds"] = time.perf_counter() - test_start
    manifest = export(test, args.demo_dir)
    sample = next(item for item in manifest["samples"] if item["official_test_index"] == 0)
    with torch.inference_mode():
        logits = model(test[0][0].unsqueeze(0))[0].tolist()
    write_json(args.run_dir / "reload_reference.json", {"image": sample["file"], "official_test_index": 0,
               "true_label": test.targets[0], "true_class": CLASSES[test.targets[0]], "logits": logits,
               "checkpoint_sha256": sha256(args.checkpoint)})
    report.update(status="completed", completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  total_seconds_including_data_test_and_export=time.perf_counter() - started)
    write_json(args.run_dir / "metrics.json", report)
    print("FINAL_TEST", report["test"], "TRAIN_SECONDS", report["training_seconds"],
          "TOTAL_SECONDS", report["total_seconds_including_data_test_and_export"], flush=True)


if __name__ == "__main__":
    main()
