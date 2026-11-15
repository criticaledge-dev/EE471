"""Shared CPU inference runner; model-specific build metadata selects weights."""
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path as LocalPath
import sys
import time

from cog import BaseRunner, Input, Path
from PIL import Image, UnidentifiedImageError
import torch

from model import Net
from preprocessing import CLASSES, preprocess

ROOT = LocalPath(__file__).resolve().parent
CONFIG_FILE = ROOT / "model_config.json"
CONFIG = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.is_file() else {
    "name": "baseline", "checkpoint": "artifacts/baseline/cifar10_last.pth",
    "log_file": "/var/log/ee471/cifar10-baseline.log",
}
MODEL_NAME = CONFIG["name"]
CHECKPOINT = ROOT / CONFIG["checkpoint"]
LOG_FILE = LocalPath(CONFIG["log_file"])


def logger():
    log = logging.getLogger("ee471.cifar10_" + MODEL_NAME)
    log.setLevel(logging.INFO)
    log.propagate = False
    if not log.handlers:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        for handler in (logging.StreamHandler(sys.stdout), RotatingFileHandler(
            LOG_FILE, maxBytes=1_048_576, backupCount=2, encoding="utf-8"
        )):
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s model=" + MODEL_NAME + " %(message)s"))
            log.addHandler(handler)
    return log


class Runner(BaseRunner):
    def setup(self):
        self.log = logger()
        if not CHECKPOINT.is_file():
            raise RuntimeError(f"Missing {MODEL_NAME} checkpoint. See Week-7/README.md clean-clone "
                               "preparation: train.py produces baseline and optimize.py produces optimized weights. "
                               "Prepare the matching checkpoint before rebuilding; no automatic training/downloads.")
        torch.set_num_threads(2)
        checkpoint_sha = hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()
        if CONFIG.get("sha256") and checkpoint_sha != CONFIG["sha256"]:
            raise RuntimeError("Checkpoint SHA256 mismatch; rebuild with the recorded model weights.")
        self.model = Net().to("cpu")
        self.model.load_state_dict(torch.load(CHECKPOINT, map_location="cpu", weights_only=True))
        self.model.eval()
        self.log.info("Model ready on CPU; checkpoint_sha256=%s", checkpoint_sha)

    def run(self, image: Path = Input(description="32x32 CIFAR10-style PNG/JPEG, RGB with channel mean/std 0.5; no resizing")) -> dict:
        started = time.perf_counter()
        self.log.info("Prediction started")
        try:
            with Image.open(image) as source:
                if source.format not in ("PNG", "JPEG"):
                    raise ValueError("Only PNG and JPEG are supported.")
                batch = preprocess(source).unsqueeze(0)
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
            self.log.warning("Prediction rejected: valid 32x32 PNG/JPEG required")
            raise ValueError("Upload a valid 32x32 PNG/JPEG. Use a CIFAR10 demo PNG; no resize is applied.") from None
        with torch.inference_mode():
            scores, labels = self.model(batch)[0].softmax(0).topk(3)
        result = {CLASSES[label]: score for score, label in zip(scores.tolist(), labels.tolist())}
        self.log.info("Prediction completed in %.6fs; class=%s; top3=%s",
                      time.perf_counter() - started, CLASSES[labels[0].item()], json.dumps(result))
        return {"class": CLASSES[labels[0].item()], "score": scores[0].item(), "top3": result}
