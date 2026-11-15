"""Read the original local checkpoint with the original training transform."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluate import load_model
from preprocessing import CLASSES, preprocess

torch.set_num_threads(2)
parser = argparse.ArgumentParser()
parser.add_argument("--model", choices=("baseline", "optimized"), default="baseline")
args = parser.parse_args()
checkpoint = ROOT / ("artifacts/baseline/fashion_mnist_last.pth" if args.model == "baseline" else "artifacts/optimized/fashion_mnist_optimized.pth")
manifest = json.loads((ROOT / "demo_samples/manifest.json").read_text())
sample = next(item for item in manifest["samples"] if item["official_test_index"] == 0)
image_path = ROOT / "demo_samples" / sample["file"]
assert hashlib.sha256(image_path.read_bytes()).hexdigest() == sample["sha256"]
model = load_model(checkpoint)
with Image.open(image_path) as image:
    batch = preprocess(image).unsqueeze(0)
    image.convert("RGB").save(ROOT / "outputs/demo-converted.jpg", quality=95)
with torch.inference_mode():
    scores, labels = model(batch)[0].softmax(0).topk(3)
output = {CLASSES[label]: score for score, label in zip(scores.tolist(), labels.tolist())}
print(json.dumps({"image": image_path.name, "true_label": sample["label"], "true_class": sample["class"],
    "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(), "output": output}))
