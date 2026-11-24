"""Download only required files for models beyond the four supplied caches."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
from models import MODELS, CACHED

FILES = {"config.json", "tokenizer.json", "tokenizer_config.json",
         "special_tokens_map.json", "vocab.json", "merges.txt", "vocab.txt",
         "spm.model", "spiece.model", "sentencepiece.bpe.model", "source.spm",
         "target.spm", "generation_config.json", "added_tokens.json"}

def prepare(task):
    model = MODELS[task]
    info = HfApi().model_info(model, token=False)
    names = {item.rfilename for item in info.siblings}
    weight = next((name for name in ("model.safetensors", "pytorch_model.bin") if name in names), None)
    if weight is None:
        raise ValueError(f"No supported single-file PyTorch checkpoint: {model}")
    selected = sorted((FILES & names) | {weight})
    snapshot = snapshot_download(model, allow_patterns=selected, max_workers=2, token=False)
    return model, Path(snapshot).name, weight

if __name__ == "__main__":
    tasks = sorted(MODELS.keys() - CACHED)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", nargs="*", metavar="TASK")
    args = parser.parse_args()
    if set(args.tasks) - set(tasks):
        parser.error("Eligible tasks: " + ", ".join(tasks))
    names = args.tasks or tasks
    failed = False
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(prepare, name) for name in names}
        for name, future in futures.items():
            try:
                print(*future.result(), flush=True)
            except Exception as exc:
                print(f"{name}: {exc}", flush=True)
                failed = True
    raise SystemExit(failed)
