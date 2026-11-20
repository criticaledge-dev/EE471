"""Run all 22 real demos in isolated processes, continuing after failure.

Run from Week-8 after sourcing activate.sh and preparing assets. This uses
real models, not mocks. Logs stay in ignored task-1/output/.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from _paths import ROOT, OUTPUT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photos", type=Path, default=Path("/mnt/c/Users/LENOVO/Downloads"))
    parser.add_argument("--recording", action="store_true", help="Also generate optional PNGs/cards for all demos.")
    args = parser.parse_args()
    photo = lambda name: str(args.photos / name)
    commands = {
        "language_detector": [], "text_classifier": [], "text_embedder": [],
        "text_proofreader": [], "text_summarizer": [],
        "pose_landmarker": [photo("pose-1.jpg")],
        "face_landmarker": [photo("face-1.png")],
        "face_detector": [photo("face-3.png")],
        "gesture_recognizer": [str(ROOT / "samples/thumb_up.jpg")],
        "hand_landmarker": [str(ROOT / "samples/thumb_up.jpg")],
        "holistic_landmarker": [photo("pose-3.jpg")],
        "image_classifier": [str(ROOT / "samples/cat_and_dog.jpg")],
        "image_embedder": [photo("face-1.png"), "--compare", photo("face-2.png")],
        "image_segmenter": [photo("pose-3.jpg")],
        "interactive_segmenter": [photo("pose-3.jpg")],
        "object_detector": [str(ROOT / "samples/cat_and_dog.jpg")],
        "audio_transcriber": [str(ROOT / "samples/speech_16000_hz_mono.wav")],
        "audio_classifier": [], "text_to_speech": [],
        "decision_maker": [], "semantic_retriever": [], "universal_embedder": [],
    }
    directory = OUTPUT / ("task-1-recording-verification" if args.recording else "task-1-verification")
    directory.mkdir(parents=True, exist_ok=True)
    visuals = {"pose_landmarker", "face_landmarker", "face_detector", "gesture_recognizer", "hand_landmarker",
               "holistic_landmarker", "image_classifier", "image_embedder", "object_detector"}
    recording = OUTPUT / "recording"
    results = {}
    for tool, arguments in commands.items():
        if args.recording:
            flag = "--output" if tool in visuals else "--overlay" if tool in {"image_segmenter", "interactive_segmenter"} else "--report"
            arguments = [*arguments, flag, str(recording / f"{tool}.png")]
        command = [sys.executable, str(ROOT / "task-1" / f"{tool}.py"), *arguments]
        start = time.monotonic()
        stdout_path, stderr_path = directory / f"{tool}.json", directory / f"{tool}.stderr.log"
        # File-backed logs prevent unbounded native stdout/stderr in memory.
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            try:
                result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=180)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = 124
                stderr.write("Timeout: the real demo exceeded 180 seconds.\n")
        results[tool] = {"status": "verified" if code == 0 else "blocked", "returncode": code,
                         "seconds": round(time.monotonic() - start, 2), "command": command,
                         "stdout": str(stdout_path), "stderr": str(stderr_path)}
        if args.recording and code == 0:
            from _presentation import validate_artifact
            try:
                results[tool]["artifact"] = validate_artifact(recording / f"{tool}.png")
            except (OSError, ValueError, AssertionError) as error:
                results[tool].update(status="blocked", returncode=1, artifact_error=str(error))
        print(f"{tool}: {results[tool]['status']}", flush=True)
        (directory / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return int(any(item["returncode"] != 0 for item in results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
