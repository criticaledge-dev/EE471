"""Optional, file-only demo presentation; never run inference or open a GUI.

Landmarks use Google's Python Samples' drawing_utils/drawing_styles approach:
google-ai-edge/mediapipe-samples examples/{pose,face}_landmarker/python/.
"""
import hashlib
import json
from pathlib import Path
import textwrap

from _paths import ROOT, OUTPUT
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def destination(path, suffix=".png"):
    path = Path(path).resolve()
    if not path.is_relative_to(OUTPUT.resolve()) or path.suffix.lower() != suffix:
        raise ValueError(f"Use a {suffix} path inside Week-8/task-1/output; original inputs must not be overwritten.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def photo(path):
    with Image.open(path) as source:
        return source.convert("RGB").copy()


def font(size=18):
    # Pillow's bundled font also works when system fonts are unavailable.
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def save(canvas, path, sources=(), details=None):
    path = destination(path)
    canvas.save(path, format="PNG")
    records = []
    for source, xy in sources:
        source = Path(source).resolve()
        with source.open("rb") as stream:
            sha = hashlib.file_digest(stream, "sha256").hexdigest()
        with Image.open(source) as image:
            size = list(image.size)
        records.append({"path": str(source), "sha256": sha, "xy": list(xy), "size": size})
    path.with_suffix(".png.json").write_text(json.dumps({"sources": records, "details": details}, ensure_ascii=False, indent=2), encoding="utf-8")


def draw_points(canvas, points, kind):
    if not points:
        return
    vision = mp.tasks.vision
    utils, styles = vision.drawing_utils, vision.drawing_styles
    if kind == "pose":
        utils.draw_landmarks(canvas, points, vision.PoseLandmarksConnections.POSE_LANDMARKS,
                             styles.get_default_pose_landmarks_style(), utils.DrawingSpec(color=(0, 255, 0), thickness=2))
    elif kind == "hand":
        utils.draw_landmarks(canvas, points, vision.HandLandmarksConnections.HAND_CONNECTIONS,
                             styles.get_default_hand_landmarks_style(), styles.get_default_hand_connections_style())
    elif kind == "face":
        connections = vision.FaceLandmarksConnections
        utils.draw_landmarks(canvas, points, connections.FACE_LANDMARKS_TESSELATION, None, styles.get_default_face_mesh_tesselation_style())
        utils.draw_landmarks(canvas, points, connections.FACE_LANDMARKS_CONTOURS, None, styles.get_default_face_mesh_contours_style())
        for iris in (connections.FACE_LANDMARKS_LEFT_IRIS, connections.FACE_LANDMARKS_RIGHT_IRIS):
            utils.draw_landmarks(canvas, points, iris, None, styles.get_default_face_mesh_iris_connections_style())


def landmarks(source, path, groups, labels=()):
    # RGB <-> BGR conversion preserves original photo colours and orientation.
    canvas = cv2.cvtColor(np.asarray(photo(source)), cv2.COLOR_RGB2BGR)
    for kind, points in groups:
        draw_points(canvas, points, kind)
    result = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    if labels:
        label(result, " | ".join(labels), (4, 4))
    save(result, path, [(source, (0, 0))], {"groups": [{"kind": k, "points": len(p)} for k, p in groups], "labels": list(labels)})


def label(canvas, text, xy):
    draw = ImageDraw.Draw(canvas)
    face = font(14)
    # Wrap labels, keeping scores visible even on narrow original images.
    lines = textwrap.wrap(text, width=max(15, int((canvas.width - xy[0] - 8) / 8)))
    text = "\n".join(lines)
    box = draw.multiline_textbbox(xy, text, font=face, spacing=2)
    draw.rectangle((max(0, box[0]-2), max(0, box[1]-2), box[2]+2, box[3]+2), fill="#172331")
    draw.multiline_text(xy, text, font=face, fill="white", spacing=2)


def boxes(source, path, detections):
    canvas = photo(source)
    draw = ImageDraw.Draw(canvas)
    for item in detections:
        x, y, w, h = item["box_xywh"]
        draw.rectangle((x, y, x+w, y+h), outline="#ff5722", width=3)
        text = f"{item['label'] or 'Face'} {item['score']:.5f}"
        label(canvas, text, (max(2, x), max(2, y-22)))
    save(canvas, path, [(source, (0, 0))], {"detections": detections})


def classification(source, path, scores):
    original = photo(source)
    panel = Image.new("RGB", (original.width+400, max(original.height, 220)), "#f3f6fa")
    panel.paste(original, (0, 0))
    draw = ImageDraw.Draw(panel)
    x = original.width+18
    draw.text((x, 18), "ImageNet top 3", fill="#172331", font=font(23))
    for i, item in enumerate(scores):
        draw.text((x, 65+i*43), f"{item['label']}: {item['score']:.5f}", fill="#172331", font=font(18))
    draw.text((x, 196), "Scores shown without filtering", fill="#555555", font=font(16))
    save(panel, path, [(source, (0, 0))], {"top_three": scores})


def comparison(first, second, path, result):
    a, b = photo(first), photo(second)
    height = max(a.height, b.height)
    canvas = Image.new("RGB", (max(a.width+b.width, 500), height+100), "#f3f6fa")
    canvas.paste(a, (0, 0))
    canvas.paste(b, (a.width, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, height+10), f"Cosine similarity: {result['cosine_similarity']:.5f}", font=font(22), fill="#172331")
    draw.text((12, height+48), f"Dimension: {result['dimension']} | Not identity verification", font=font(16), fill="#172331")
    save(canvas, path, [(first, (0, 0)), (second, (a.width, 0))], result)


def overlay(source, path, mask, point=None):
    original = np.asarray(photo(source)).copy()
    if mask.shape != original.shape[:2]:
        raise ValueError("Mask and original image dimensions do not match.")
    alpha = mask[..., None] * 0.48
    mixed = (original*(1-alpha) + np.array([0, 190, 220])*alpha).round().astype(np.uint8)
    canvas = Image.fromarray(mixed)
    if point is not None:
        x, y = point[0]*(canvas.width-1), point[1]*(canvas.height-1)
        ImageDraw.Draw(canvas).ellipse((x-5,y-5,x+5,y+5), fill="#ffff00", outline="black", width=2)
    save(canvas, path, [(source, (0, 0))], {"point_xy": point, "confidence_range": [float(mask.min()),float(mask.max())]})


def report(args, result, **inputs):
    """Opt-in PNG input/result card, returning the exact existing CLI result."""
    if not getattr(args, "report", None):
        return result
    title = Path(__import__("sys").argv[0]).stem.replace("_", " ").title()
    lines = []
    for heading, data in (("INPUT", inputs), ("REAL MODEL RESULT", result)):
        lines += [heading, ""]
        for key, value in data.items():
            value = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
            lines.extend(textwrap.wrap(f"{key}: {value}", width=88, break_long_words=False) or [""])
            lines.append("")
        lines.append("")
    canvas = Image.new("RGB", (1200, max(360, 110+len(lines)*29)), "#f3f6fa")
    draw = ImageDraw.Draw(canvas)
    draw.text((28, 20), title, font=font(29), fill="#172331")
    for i, text in enumerate(lines):
        draw.text((28, 85+i*29), text, font=font(21), fill="#172331")
    save(canvas, args.report, details={"input": inputs, "result": result})
    return result


def validate_artifact(path):
    """Check real generated PNG, source hashes, photo placement and modifications."""
    path = destination(path)
    metadata = json.loads(path.with_suffix(".png.json").read_text(encoding="utf-8"))
    with Image.open(path) as rendered:
        if rendered.format != "PNG":
            raise ValueError("Expected a real PNG, not a renamed file.")
        canvas = np.asarray(rendered.convert("RGB")).copy()
    if not np.ptp(canvas) or path.stat().st_size < 100:
        raise ValueError("Empty/flat presentation image.")
    matches = []
    for record in metadata["sources"]:
        source = Path(record["path"])
        with source.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == record["sha256"], "Input changed after rendering"
        original = np.asarray(photo(source))
        x,y = record["xy"]
        h,w = original.shape[:2]
        region = canvas[y:y+h,x:x+w]
        assert region.shape == original.shape, "Photo cropped/resized unexpectedly"
        exact = float(np.all(region == original, axis=2).mean())
        # Drawing leaves original background pixels in their exact original positions.
        assert exact > 0.25, "Photo does not match its original coordinates/orientation"
        matches.append(round(exact, 4))
    details = metadata["details"]
    if matches and not (isinstance(details, dict) and ("top_three" in details or "cosine_similarity" in details)):
        assert any(value < 1.0 for value in matches), "No annotation drawn on the photo"
    return {"png": str(path), "size": [canvas.shape[1],canvas.shape[0]], "source_matching_pixel_fraction": matches}
