"""Generate local Postman JSON files without printing image/base64 data.

Uses only Python's standard library. This checks size/signature, not the complete
image structure; the website and Cog perform the actual image decoding.
"""
import argparse
import base64
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parent.parent / "outputs")
    args = parser.parse_args()
    with args.image.open("rb") as source:
        data = source.read(5 * 1024 * 1024 + 1)
    if not data or len(data) > 5 * 1024 * 1024:
        parser.error("Choose a non-empty image up to 5 MiB.")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    else:
        parser.error("Expected a JPEG or PNG signature.")
    payload = {"input": {"image": f"data:{mime};base64," + base64.b64encode(data).decode("ascii")}}
    body = json.dumps(payload)
    environment = {
        "name": "EE471 Week 6 - local image (do not share)",
        "values": [{"key": "prediction_body", "value": body, "type": "default", "enabled": True}],
        "_postman_variable_scope": "environment",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in (("postman-request.json", payload),
                          ("postman-environment.json", environment)):
        path = args.output_dir / name
        path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
        print(f"Created {path}; contains image data, keep local.")


if __name__ == "__main__":
    main()
