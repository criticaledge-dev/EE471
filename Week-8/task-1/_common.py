"""Small CLI helpers shared by the independent MediaPipe Task 1 demos."""
import argparse
import json
from pathlib import Path
import sys
import wave

from _paths import ROOT, OUTPUT
import mediapipe as mp
import numpy as np

def arguments(tool, default_model, *, image=False, text=None, second=False, mask=False):
    parser = argparse.ArgumentParser(description=f"Real CPU MediaPipe {tool} demo")
    if image:
        parser.add_argument("image", type=Path)
        if not mask:
            parser.add_argument("--output", type=Path, help="Optional annotated PNG inside Week-8/task-1/output.")
    else:
        parser.add_argument("--report", type=Path, help="Optional input/result PNG card inside Week-8/task-1/output.")
    if text is not None:
        parser.add_argument("--text", default=text)
    if second:
        parser.add_argument("--compare", required=image, default=None)
    parser.add_argument("--model", type=Path, default=ROOT / "models" / default_model)
    return parser


def base(args):
    if not args.model.is_file():
        raise FileNotFoundError(f"Model missing: {args.model}. Run task-1/prepare_assets.py first.")
    return mp.tasks.BaseOptions(model_asset_path=str(args.model), delegate=mp.tasks.BaseOptions.Delegate.CPU)


def image(path):
    if not Path(path).is_file():
        raise FileNotFoundError(path)
    return mp.Image.create_from_file(str(path))


def categories(result):
    return [{"label": c.category_name, "score": round(float(c.score), 5)}
            for head in result.classifications for c in head.categories]


def detection(result):
    if not result.detections:
        raise RuntimeError("No detection on this input; try a suitable image. Not a completed positive demo.")
    return [{"label": d.categories[0].category_name, "score": round(d.categories[0].score, 5),
             "box_xywh": [d.bounding_box.origin_x, d.bounding_box.origin_y,
                           d.bounding_box.width, d.bounding_box.height]} for d in result.detections]


def wav(path):
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2 or source.getnchannels() != 1 or source.getcomptype() != "NONE":
            raise ValueError("This short demo accepts mono PCM16 WAV.")
        rate = source.getframerate()
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float32) / 32768
    if not samples.size:
        raise ValueError("Empty WAV")
    return samples, rate


def output_path(path):
    path = Path(path).resolve()
    if not path.is_relative_to(OUTPUT.resolve()):
        raise ValueError("Generated files must be inside Week-8/task-1/output; input files cannot be overwritten.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def cache(name):
    path = OUTPUT / name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def present(args, result, **inputs):
    if getattr(args, "report", None):
        from _presentation import report
        report(args, result, **inputs)
    return result


def run(main):
    try:
        result = main()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
