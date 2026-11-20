"""Download official Task 1 assets; never install or change the Python environment."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request

from _paths import ROOT, OUTPUT
G = "https://storage.googleapis.com/mediapipe-models/"
MODELS = {
    "language_detector": "language_detector/language_detector/float32/1/language_detector.tflite",
    "text_classifier": "text_classifier/average_word_classifier/float32/latest/average_word_classifier.tflite",
    "text_embedder": "text_embedder/universal_sentence_encoder/float32/latest/universal_sentence_encoder.tflite",
    "text_proofreader": "text_proofreader/200m/latest/proofread_quant_200m.litertlm",
    "text_summarizer": "text_summarizer/200m/latest/summarization_quant_200m_2modes.litertlm",
    "face_detector": "face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
    "gesture_recognizer": "gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task",
    "hand_landmarker": "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    "holistic_landmarker": "holistic_landmarker/holistic_landmarker/float16/latest/holistic_landmarker.task",
    "image_classifier": "image_classifier/efficientnet_lite0/int8/latest/efficientnet_lite0.tflite",
    "image_embedder": "image_embedder/mobilenet_v3_small/float32/latest/mobilenet_v3_small.tflite",
    "image_segmenter": "image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite",
    "interactive_segmenter": "interactive_segmenter_v2/magic_touch/int8/latest/interactive_segmentation.task",
    "object_detector": "object_detector/efficientdet_lite0/int8/latest/efficientdet_lite0.tflite",
    "audio_classifier": "audio_classifier/yamnet/float32/latest/yamnet.tflite",
    "decision_maker": "decision_maker/laya/float32/laya_s256/latest/laya_s256.task",
}
ASSETS = {key: (G + path, "models/" + path.rsplit("/", 1)[1]) for key, path in MODELS.items()}
ASSETS.update({
    "text_to_speech": ("https://huggingface.co/litert-community/phonon-31m-en/resolve/main/phonon_int8.litertlm", "models/phonon_int8.litertlm"),
    "universal_embedder": ("https://huggingface.co/litert-community/embeddinggemma-2-text-270m-litert-lm/resolve/main/embeddinggemma-2-text-270m.litertlm", "models/embeddinggemma-2-text-270m.litertlm"),
    "hand_sample": ("https://storage.googleapis.com/mediapipe-assets/thumb_up.jpg", "samples/thumb_up.jpg"),
    "object_sample": ("https://storage.googleapis.com/mediapipe-tasks/object_detector/cat_and_dog.jpg", "samples/cat_and_dog.jpg"),
})
LOCK = Path(__file__).with_name("assets.lock.json")
EXPECTED = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}


def download(key):
    url, relative = ASSETS[key]
    dest = ROOT / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=45) as head:
            size = int(head.headers.get("Content-Length", "0"))
        if not dest.exists() or (size and dest.stat().st_size != size):
            partial = dest.with_suffix(dest.suffix + ".part")
            start = partial.stat().st_size if partial.exists() else 0
            request = urllib.request.Request(url, headers={"Range": f"bytes={start}-"} if start else {})
            with urllib.request.urlopen(request, timeout=60) as source:
                append = start and source.status == 206
                with partial.open("ab" if append else "wb") as target:
                    while block := source.read(1024 * 1024):
                        target.write(block)
            if size and partial.stat().st_size != size:
                raise ValueError(f"Incomplete download: {partial.stat().st_size}/{size}")
            partial.replace(dest)
        with dest.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if key in EXPECTED and digest != EXPECTED[key]["sha256"]:
            raise ValueError("SHA256 differs from the verified asset. Check the official model version before using it.")
        result = {"asset": key, "path": relative, "bytes": dest.stat().st_size,
                  "sha256": digest, "url": url}
    except Exception as exc:
        result = {"asset": key, "error": f"{type(exc).__name__}: {exc}", "url": url}
    print(json.dumps(result), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", nargs="*", choices=list(ASSETS))
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(download, args.assets or list(ASSETS)))
    out = OUTPUT / "expansion" / "downloads.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    raise SystemExit(any("error" in r for r in results))
