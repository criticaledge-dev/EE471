"""Create minimal, model-specific Cog contexts; never execute training."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent


def prepare():
    baseline = json.loads((ROOT / "results/baseline/metrics.json").read_text())
    optimized = json.loads((ROOT / "results/hpo/summary.json").read_text())
    specifications = {
        "baseline": ("artifacts/baseline/cifar10_last.pth", baseline["checkpoint"]["sha256"], baseline["test"]),
        "optimized": ("artifacts/optimized/cifar10_optimized.pth",
                      optimized["selection"]["optimized_checkpoint"]["sha256"], optimized["winner_test"]),
    }
    # Validate BOTH inputs before changing any build context.
    for name, (relative, expected, _) in specifications.items():
        path = ROOT / relative
        if not path.is_file():
            raise SystemExit(f"Missing {relative}. See Week-7/README.md clean-clone commands. Build never trains.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"{name}: checkpoint SHA256 does not match its recorded experiment. Build refused.")
    for name, (relative, expected, metrics) in specifications.items():
        context = ROOT / "outputs/build" / name
        context.mkdir(parents=True, exist_ok=True)
        allowed = {"cog.yaml", "requirements.txt", "cog_runner.py", "model.py", "preprocessing.py",
                   "checkpoint.pth", "model_config.json", ".dockerignore"}
        # Refuse stale unexpected content rather than recursively deleting anything.
        # Cog itself creates this metadata directory on the first build. It is
        # excluded by the context allowlist and must not block repeat builds.
        contents = [path for path in context.iterdir()
                    if not (path.name == ".cog" and path.is_dir() and not path.is_symlink())]
        if any(path.name not in allowed or path.is_dir() or path.is_symlink() for path in contents):
            raise SystemExit(f"Unexpected files in {context}; inspect this generated context before building.")
        for file in ("requirements.txt", "cog_runner.py", "model.py", "preprocessing.py"):
            shutil.copyfile(ROOT / file, context / file)
        shutil.copyfile(ROOT / relative, context / "checkpoint.pth")
        assert hashlib.sha256((context / "checkpoint.pth").read_bytes()).hexdigest() == expected
        config = {"name": "cifar10-"+name, "checkpoint": "checkpoint.pth", "sha256": expected,
                  "log_file": f"/var/log/ee471/cifar10-{name}.log"}
        (context / "model_config.json").write_text(json.dumps(config, indent=2) + "\n")
        yaml = (ROOT / "cog.yaml").read_text().replace("ee471-week7-cifar10-baseline", f"ee471-week7-cifar10-{name}")
        (context / "cog.yaml").write_text(yaml)
        (context / ".dockerignore").write_text("*\n" + "".join(f"!{file}\n" for file in sorted(allowed - {".dockerignore"})))
        # Derived website display data, with original measurements left untouched.
        derived = {**metrics, "checkpoint_sha256": expected,
                   "source": "results/baseline/metrics.json:test" if name == "baseline" else "results/hpo/summary.json#winner_test"}
        target = ROOT / "website" / f"{name}_metrics.json"
        if name == "optimized":
            target.write_text(json.dumps(derived, indent=2) + "\n")
        else:
            assert json.loads(target.read_text()) == derived
        print(f"{name}: isolated context ready; checkpoint_sha256={expected}")


if __name__ == "__main__":
    prepare()
