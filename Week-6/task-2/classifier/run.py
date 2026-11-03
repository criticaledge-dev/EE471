"""CPU ImageNet inference using the Cog 0.23.1 Runner interface."""

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path as LocalPath
import sys
import time

import torch
from cog import BaseRunner, Input, Path
from PIL import Image, UnidentifiedImageError
from torchvision import models

WEIGHTS = models.ResNet50_Weights.IMAGENET1K_V1
HUB_DIR = LocalPath("/opt/ee471/torch/hub")
LOG_FILE = LocalPath("/var/log/ee471/classifier.log")


def make_logger():
    logger = logging.getLogger("ee471.classifier")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handlers = [logging.StreamHandler(sys.stdout), RotatingFileHandler(
            LOG_FILE, maxBytes=1_048_576, backupCount=2, encoding="utf-8"
        )]
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger


class Runner(BaseRunner):
    def setup(self):
        self.logger = make_logger()
        self.logger.info("Loading ResNet50 IMAGENET1K_V1 on CPU")
        torch.hub.set_dir(str(HUB_DIR))
        checkpoint = HUB_DIR / "checkpoints" / WEIGHTS.url.rsplit("/", 1)[-1]
        if not checkpoint.is_file():
            raise RuntimeError("Model weights are missing; rebuild the Cog image.")
        # This is the same cache populated by build.run. Missing weights must
        # fail rather than silently download at runtime or use random weights.
        self.model = models.resnet50(weights=WEIGHTS).to("cpu")
        self.model.eval()
        self.transform = WEIGHTS.transforms()
        self.categories = WEIGHTS.meta["categories"]
        self.logger.info("Model ready; pretrained weights loaded from %s", checkpoint)

    def run(self, image: Path = Input(description="Image to classify with ImageNet ResNet50")) -> dict:
        started = time.perf_counter()
        self.logger.info("Prediction started")
        try:
            with Image.open(image) as source:
                rgb = source.convert("RGB")
                tensor = self.transform(rgb).unsqueeze(0)
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            self.logger.warning("Prediction rejected: invalid or unreadable image")
            raise ValueError("Invalid or unreadable image; upload a valid image file.") from exc
        with torch.inference_mode():
            scores, indices = self.model(tensor)[0].softmax(0).topk(3)
        result = {self.categories[index]: float(score)
                  for score, index in zip(scores.tolist(), indices.tolist())}
        self.logger.info("Prediction completed in %.3fs; top3=%s",
                         time.perf_counter() - started, json.dumps(result))
        return result
