"""Synthesize a real local PCM16 WAV with Phonon; never play speakers."""
import wave
import numpy as np
from _common import OUTPUT, arguments, base, cache, mp, output_path, present, run


def main():
    parser = arguments("Text to Speech", "phonon_int8.litertlm", text="Hello. Welcome to the library.")
    parser.add_argument("--output", default=OUTPUT / "speech.wav")
    args = parser.parse_args()
    options = mp.tasks.audio.TextToSpeechOptions(base_options=base(args), cache_dir=cache("tts-cache"))
    with mp.tasks.audio.TextToSpeech.create_from_options(options) as task:
        audio = task.synthesize(args.text)
        samples = np.asarray(audio.samples).copy()
        rate = audio.sample_rate_hz
    if not samples.size or not np.any(samples):
        raise RuntimeError("No non-silent audio produced.")
    with wave.open(str(output_path(args.output)), "wb") as target:
        target.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        target.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())
    return present(args, {"wav": str(args.output), "sample_rate_hz": rate, "seconds": round(len(samples) / rate, 3)}, text=args.text, playback="Not started automatically; open the WAV manually.")


if __name__ == "__main__":
    run(main)
