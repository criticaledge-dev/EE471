import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import random

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent


def seed_everything(seed, threads):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)


def versions():
    return {"python": platform.python_version(), "platform": platform.platform(),
            **{name: importlib.metadata.version(name) for name in ("torch", "torchvision", "Pillow", "numpy")}}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def split_indices(size, seed):
    # Separate generator: split does not consume model-initialization RNG.
    order = torch.randperm(size, generator=torch.Generator().manual_seed(seed)).tolist()
    count = size * 9 // 10
    train, validation = order[:count], order[count:]
    assert not set(train).intersection(validation)
    return train, validation


def indices_hash(indices):
    return hashlib.sha256(np.asarray(indices, dtype="<i8").tobytes()).hexdigest()
