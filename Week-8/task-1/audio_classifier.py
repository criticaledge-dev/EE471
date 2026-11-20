"""Classify a short local WAV using YAMNet; no microphone."""
from _common import ROOT, arguments, base, categories, mp, present, run, wav


def main():
    parser = arguments("Audio Classifier", "yamnet.tflite")
    parser.add_argument("audio", nargs="?", default=ROOT / "samples" / "speech_16000_hz_mono.wav")
    args = parser.parse_args()
    samples, rate = wav(args.audio)
    data = mp.tasks.components.containers.AudioData.create_from_array(samples, rate)
    with mp.tasks.audio.AudioClassifier.create_from_options(mp.tasks.audio.AudioClassifierOptions(base_options=base(args), max_results=2)) as task:
        results = task.classify(data)
    return present(args, {"windows": len(results), "first_window": categories(results[0])}, wav=str(args.audio), sample_rate_hz=rate, seconds=round(len(samples)/rate, 4))


if __name__ == "__main__":
    run(main)
