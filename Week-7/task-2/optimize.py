"""Four controlled two-epoch trials; freeze validation selection before test."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import time

import torch
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision.datasets import CIFAR10

from common import ROOT, indices_hash, seed_everything, sha256, split_indices, versions, write_json
from engine import run_epoch
from evaluate import load_model
from model import Net
from preprocessing import CLASSES, preprocess

TRIALS = (("sgd_lr_0_003", "SGD", .003), ("sgd_lr_0_01", "SGD", .01),
          ("adam_lr_0_0003", "Adam", .0003), ("adam_lr_0_001", "Adam", .001))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def state_hash(model):
    digest = hashlib.sha256()
    for name, value in model.state_dict().items():
        digest.update(name.encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


class TrackedSubset(Dataset):
    """Observe actual consumed indices without touching RNG or tensor values."""
    def __init__(self, dataset, indices):
        self.dataset, self.indices = dataset, indices
        self.reset_trace()

    def __len__(self):
        return len(self.indices)

    def reset_trace(self):
        self.trace, self.count = hashlib.sha256(), 0

    def __getitem__(self, index):
        actual = self.indices[index]
        self.trace.update(struct.pack("<q", actual))
        self.count += 1
        return self.dataset[actual]


def reference_batch_hashes(indices):
    # DataLoader/RandomSampler consume their generator, including the base seed,
    # in exactly the same way as baseline train.py. No model/test data is used.
    loader = DataLoader(indices, batch_size=4, shuffle=True,
                        generator=torch.Generator().manual_seed(42), num_workers=0)
    result = []
    for _ in range(2):
        digest = hashlib.sha256()
        for batch in loader:
            for index in batch.tolist():
                digest.update(struct.pack("<q", index))
        result.append(digest.hexdigest())
    return result


def select_winner(trials):
    if not trials:
        raise ValueError("No completed candidates")
    for trial in trials:
        final = trial["last_epoch"]
        validation = final["validation"]
        if final["epoch"] != 2 or not all(math.isfinite(validation[key]) for key in ("accuracy", "loss")):
            raise ValueError("Selection requires finite second-epoch validation metrics")
    return max(trials, key=lambda trial: (trial["last_epoch"]["validation"]["accuracy"],
                                        -trial["last_epoch"]["validation"]["loss"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "results/hpo")
    parser.add_argument("--candidate-dir", type=Path, default=ROOT / "artifacts/hpo")
    parser.add_argument("--optimized", type=Path, default=ROOT / "artifacts/optimized/cifar10_optimized.pth")
    args = parser.parse_args()
    if args.run_dir.exists() or args.candidate_dir.exists() or args.optimized.exists():
        parser.error("HPO output exists. Use fresh run/candidate/optimized paths; no previous artifacts are overwritten.")
    baseline = json.loads((ROOT / "results/baseline/metrics.json").read_text())
    baseline_file = ROOT / "artifacts/baseline/cifar10_last.pth"
    baseline_digest = sha256(baseline_file)
    assert baseline_digest == baseline["checkpoint"]["sha256"]
    expected = {"learning_rate": .001, "batch_size": 4, "epochs": 2, "seed": 42,
                "device": "cpu", "cpu_threads": 2,
                "num_workers": 0, "optimizer": "SGD", "momentum": .9, "weight_decay": 0,
                "dampening": 0, "nesterov": False,
                "loss": "CrossEntropyLoss"}
    for key, value in expected.items():
        assert baseline["config"][key] == value, f"Baseline protocol mismatch: {key}"
    assert baseline["status"] == "completed" and len(baseline["epochs"]) == 2
    assert baseline["epochs"][-1]["epoch"] == 2
    assert all(row["train"]["samples"] == 45000 and row["validation"]["samples"] == 5000 for row in baseline["epochs"])
    assert baseline["test"]["samples"] == 10000
    assert tuple(baseline["classes"]) == CLASSES
    for name, recorded_hash in baseline["source_sha256"].items():
        assert sha256(ROOT / name) == recorded_hash, f"Baseline source changed: {name}"
    actual_versions = versions()
    for name in ("python", "torch", "torchvision", "Pillow", "numpy"):
        assert actual_versions[name] == baseline["versions"][name], f"Environment mismatch: {name}"
    dataset = CIFAR10(args.data_dir, train=True, download=False, transform=preprocess)
    assert len(dataset) == 50000 and tuple(dataset.classes) == CLASSES
    train_ids, validation_ids = split_indices(len(dataset), 42)
    assert indices_hash(train_ids) == baseline["split"]["train_indices_sha256_le_int64"]
    assert indices_hash(validation_ids) == baseline["split"]["validation_indices_sha256_le_int64"]
    expected_orders = reference_batch_hashes(train_ids)
    seed_everything(42, 2)
    expected_initial = state_hash(Net())
    report = {"status": "running_trials", "started_at_utc": utc_now(), "versions": actual_versions,
        "protocol": {**expected, "architecture": baseline["config"]["architecture"],
                     "transform": baseline["config"]["transform"], "checkpoint_epoch": 2},
        "baseline_audit": {"compatible": True, "reused_without_retraining": True,
            "checkpoint_sha256": baseline_digest, "split": baseline["split"],
            "original_source_hashes_verified": True,
            "source_sha256": {name: sha256(ROOT / name) for name in
                ("train.py", "model.py", "preprocessing.py", "common.py", "engine.py", "evaluate.py")},
            "batch_order_note": "Historical baseline trace was not recorded; reconstructed from unchanged baseline loader/seed protocol",
            "reconstructed_batch_order_sha256": expected_orders,
            "reconstructed_initial_state_sha256": expected_initial},
        "baseline_reference": {"last_validation": baseline["epochs"][-1]["validation"],
            "test": baseline["test"], "training_and_validation_seconds": baseline["training_and_validation_seconds"]},
        "trials": [], "selection": None, "winner_test": None}
    write_json(args.run_dir / "summary.json", report)
    print("BASELINE_COMPATIBLE reused without training; split, source, version and checkpoint hashes verified", flush=True)
    search_started = time.perf_counter()
    for trial_id, optimizer_name, lr in TRIALS:
        # Reset all initialization and batch-order RNG state for EVERY candidate.
        seed_everything(42, 2)
        tracked = TrackedSubset(dataset, train_ids)
        train_loader = DataLoader(tracked, batch_size=4, shuffle=True,
            generator=torch.Generator().manual_seed(42), num_workers=0)
        validation_loader = DataLoader(Subset(dataset, validation_ids), batch_size=4, shuffle=False, num_workers=0)
        model = Net().to("cpu")
        initial = state_hash(model)
        assert initial == expected_initial, "Candidate initialization differs"
        optimizer = (torch.optim.SGD(model.parameters(), lr=lr, momentum=.9, weight_decay=0)
                     if optimizer_name == "SGD" else torch.optim.Adam(model.parameters(), lr=lr,
                         betas=(.9, .999), eps=1e-8, weight_decay=0, amsgrad=False))
        trial = {"id": trial_id, "optimizer": optimizer_name, "learning_rate": lr,
                 "optimizer_defaults": optimizer.defaults, "initial_state_sha256": initial,
                 "epochs": [], "test": None, "status": "training"}
        trial_started = time.perf_counter()
        print("TRIAL", trial_id, "optimizer", optimizer.defaults, flush=True)
        for epoch in range(1, 3):
            tracked.reset_trace()
            started = time.perf_counter()
            train = run_epoch(model, train_loader, "cpu", optimizer)
            validation = run_epoch(model, validation_loader, "cpu")
            order = tracked.trace.hexdigest()
            assert tracked.count == 45000 and order == expected_orders[epoch - 1], "Batch order differs from baseline protocol"
            assert all(math.isfinite(metrics[key]) for metrics in (train, validation) for key in ("loss", "accuracy"))
            row = {"epoch": epoch, "train": train, "validation": validation,
                   "seconds": time.perf_counter() - started, "observed_batch_order_sha256": order}
            trial["epochs"].append(row)
            write_json(args.run_dir / "trials" / f"{trial_id}.json", trial)
            print(f"{trial_id} {epoch}/2 train_loss={train['loss']:.6f} train_acc={train['accuracy']:.4%} "
                  f"val_loss={validation['loss']:.6f} val_acc={validation['accuracy']:.4%} seconds={row['seconds']:.2f}", flush=True)
        trial["training_and_validation_seconds"] = sum(row["seconds"] for row in trial["epochs"])
        trial["elapsed_seconds_before_checkpoint"] = time.perf_counter() - trial_started
        checkpoint = args.candidate_dir / f"{trial_id}_last.pth"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save({name: value.detach().cpu() for name, value in model.state_dict().items()}, checkpoint)
        trial.update(status="completed", last_epoch=trial["epochs"][-1], checkpoint={
            "path": str(checkpoint), "bytes": checkpoint.stat().st_size, "sha256": sha256(checkpoint)})
        write_json(args.run_dir / "trials" / f"{trial_id}.json", trial)
        report["trials"].append(trial)
        write_json(args.run_dir / "summary.json", report)
    report["candidate_training_and_validation_seconds"] = sum(t["training_and_validation_seconds"] for t in report["trials"])
    winner = select_winner(report["trials"])
    args.optimized.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(winner["checkpoint"]["path"], args.optimized)
    ranking = sorted(report["trials"], key=lambda t: (-t["last_epoch"]["validation"]["accuracy"], t["last_epoch"]["validation"]["loss"]))
    selection = {"validation_ranking": [t["id"] for t in ranking],
        "baseline_validation": baseline["epochs"][-1]["validation"],
        "validation_gain_vs_baseline_percentage_points": 100*(winner["last_epoch"]["validation"]["accuracy"]-baseline["epochs"][-1]["validation"]["accuracy"]),
        "winner": winner["id"], "optimizer": winner["optimizer"], "learning_rate": winner["learning_rate"],
        "optimizer_defaults": winner["optimizer_defaults"], "eligible_trials": [t["id"] for t in report["trials"]],
        "criterion": "highest epoch-2 validation accuracy; ties: lower epoch-2 validation loss; exact ties: listed order",
        "validation": winner["last_epoch"]["validation"], "frozen_at_utc": utc_now(),
        "test_used_for_selection": False, "demo_used_for_selection": False,
        "optimized_checkpoint": {"path": str(args.optimized), "sha256": sha256(args.optimized),
                                 "bytes": args.optimized.stat().st_size, "format": "CPU state_dict only"}}
    report.update(status="selection_frozen_before_test", selection=selection)
    write_json(args.run_dir / "selection.json", selection)
    write_json(args.run_dir / "summary.json", report)
    print("SELECTION_FROZEN", winner["id"], selection["validation"], flush=True)
    # The official test set is first instantiated here, AFTER the decision file.
    test = CIFAR10(args.data_dir, train=False, download=False, transform=preprocess)
    assert len(test) == 10000 and tuple(test.classes) == CLASSES
    selected_model = load_model(args.optimized)
    test_started = time.perf_counter()
    report["winner_test"] = run_epoch(selected_model, DataLoader(test, batch_size=4, shuffle=False, num_workers=0), "cpu")
    report["winner_test_seconds"] = time.perf_counter() - test_started
    report["comparison"] = {
        "validation_accuracy_gain_percentage_points": 100 * (selection["validation"]["accuracy"] - baseline["epochs"][-1]["validation"]["accuracy"]),
        "test_accuracy_gain_percentage_points": 100 * (report["winner_test"]["accuracy"] - baseline["test"]["accuracy"]),
        "test_loss_delta_optimized_minus_baseline": report["winner_test"]["loss"] - baseline["test"]["loss"],
        "validation_accuracy_improved": selection["validation"]["accuracy"] > baseline["epochs"][-1]["validation"]["accuracy"],
        "test_accuracy_improved": report["winner_test"]["accuracy"] > baseline["test"]["accuracy"]}
    # Only after selection/test use the fixed manifest cat example for reload verification.
    with torch.inference_mode():
        image, label = test[0]
        logits = selected_model(image.unsqueeze(0))[0].tolist()
    manifest = json.loads((ROOT / "demo_samples/manifest.json").read_text())
    sample = next(item for item in manifest["samples"] if item["official_test_index"] == 0)
    assert sha256(ROOT / "demo_samples" / sample["file"]) == sample["sha256"]
    write_json(args.run_dir / "optimized_reload_reference.json", {"image": sample["file"], "official_test_index": 0,
        "true_label": label, "true_class": CLASSES[label], "logits": logits,
        "predicted_label": max(range(10), key=logits.__getitem__), "checkpoint_sha256": sha256(args.optimized)})
    assert sha256(baseline_file) == baseline_digest, "Baseline checkpoint changed"
    report.update(status="completed", completed_at_utc=utc_now(), total_search_seconds=time.perf_counter() - search_started)
    write_json(args.run_dir / "summary.json", report)
    print("WINNER_TEST", report["winner_test"], "COMPARISON", report["comparison"], flush=True)
    print("OPTIMIZED_CHECKPOINT", selection["optimized_checkpoint"], flush=True)


if __name__ == "__main__":
    main()
