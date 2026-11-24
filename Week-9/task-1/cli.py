"""Run one demo per process. All inference is offline."""
import argparse
import json
import os
from pathlib import Path
import textwrap

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import demo
from models import MODELS

OUTPUT = Path(__file__).resolve().parent / "output"

def output_file(name, suffix):
    path = (OUTPUT / name).resolve()
    if not path.is_relative_to(OUTPUT.resolve()) or path.suffix.lower() != suffix:
        raise ValueError(f"Use a {suffix} filename under {OUTPUT}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def save_image(image, ranking, path):
    from PIL import Image, ImageDraw, ImageFont
    image.thumbnail((640, 540))
    lines = [
        line
        for index, row in enumerate(ranking, 1)
        for line in textwrap.wrap(f"{index}. {row['label']}  {row['score']:.4%}", width=51)
    ]
    canvas = Image.new("RGB", (max(image.width, 560), image.height + max(190, 64 + 23 * len(lines))), "#172332")
    canvas.paste(image, ((canvas.width - image.width) // 2, 0))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=19)
    draw.text((20, image.height + 10), "ViT · ImageNet top 3", fill="#9ce4ff", font=font)
    y = image.height + 44
    for line in lines:
        draw.text((20, y), line, fill="white", font=font)
        y += 23
    canvas.save(path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="task", required=True)
    for task in MODELS:
        command = modes.add_parser(task)
        if task == "image_classification":
            command.add_argument("image", type=Path)
            command.add_argument("--output", default="vit-top3.png")
        elif task == "asr":
            command.add_argument("wav", type=Path)
            command.add_argument("--output", help="Optional transcript TXT filename")
        elif task == "question_answering":
            command.add_argument("--ner-results", type=Path,
                                 help="NER JSON captured separately for span comparison")
    args = parser.parse_args()
    try:
        if args.task == "image_classification":
            path = output_file(args.output, ".png")
            if path == args.image.resolve() or (path.exists() and path.samefile(args.image)):
                raise ValueError("Output and input photo must differ.")
            image, ranking = demo.image_classification(args.image)
            save_image(image, ranking, path)
            result = {"image": str(args.image.resolve()), "top_three": ranking, "png": str(path)}
        elif args.task == "asr":
            result = demo.asr(args.wav)
            if args.output:
                path = output_file(args.output, ".txt")
                if path.exists() and path.samefile(args.wav):
                    raise ValueError("Output and input WAV must differ.")
                path.write_text(result["transcript"] + "\n", encoding="utf-8")
        else:
            result = getattr(demo, args.task)()
            if args.task == "question_answering" and args.ner_results:
                ner = json.loads(args.ner_results.read_text(encoding="utf-8"))
                if ner["context"] != result["context"]:
                    raise ValueError("NER and QA must use the same context.")
                for answer in result["answers"]:
                    spans = [e for e in ner["entities"] if e["type"] == answer["type"]]
                    answer["ner_same_type"] = [e["text"] for e in spans]
                    answer["ner_exact_span_match"] = any(
                        (e["start"], e["end"]) == (answer["start"], answer["end"]) for e in spans)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"{args.task} ({MODELS[args.task]}): {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
