"""Exercise the real Gradio controls in Playwright against a running app."""
import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

CASES = [
    ("Metin", "Sentiment", "sentiment", ("NEGATIVE", "I hate software courses")),
    ("Metin", "Zero-shot", "zero_shot", ("finance", "sports", "technology")),
    ("Metin", "Generation", "text_generation", ("26", "35")),
    ("Metin", "Fill-mask", "fill_mask", ("one must study AI well.",)),
    ("Metin", "NER", "ner", ("Nate", "Izmir Institute of Technology", "İzmir")),
    ("Metin", "QA", "qa", ("Nate", "Izmir Institute of Technology", "İzmir")),
    ("Metin", "Summarization", "summarization", ("Trigger", "the crisis began with the subprime mortgage market")),
    ("Metin", "Translation", "translation", ("This course is produced by Hugging Face.",)),
    ("Görsel", None, "image_classification", ("Egyptian cat", "tabby", "tiger cat")),
    ("Ses", None, "asr", ("Send a text to Mike. I'll be home late tomorrow.",)),
]
SAMPLES = Path(__file__).resolve().parents[2] / "Week-8" / "samples"


def memory(pid):
    if pid is None:
        return
    fields = [line.strip() for line in Path(f"/proc/{pid}/status").read_text().splitlines()
              if line.startswith(("VmRSS:", "VmHWM:"))]
    print(" | ".join(fields), flush=True)


def select_tab(page, title):
    page.get_by_role("tab", name=title, exact=True).click()


def run_demo(page, name, expected):
    page.locator(f"#{name}-run").click()
    result = page.locator(f"#{name}-result")
    for text in expected:
        if name in {"translation", "asr"}:
            expect(result.locator("textarea")).to_have_value(text, timeout=120_000)
        else:
            expect(result).to_contain_text(text, timeout=120_000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:7860")
    parser.add_argument("--server-pid", type=int, help="Optional Linux Gradio PID for resident memory measurements")
    parser.add_argument("--photo", type=Path, default=SAMPLES / "cat_and_dog.jpg")
    parser.add_argument("--wav", type=Path, default=SAMPLES / "speech_16000_hz_mono.wav")
    args = parser.parse_args()
    with sync_playwright() as browser:
        chromium = browser.chromium.launch(args=["--mute-audio"])
        page = chromium.new_page()
        page.goto(args.url, wait_until="domcontentloaded")
        memory(args.server_pid)
        for group, name, key, expected in CASES:
            select_tab(page, group)
            if name:
                select_tab(page, name)
            if key == "image_classification":
                photo = page.locator("#photo-input")
                expect(photo.locator("img").first).to_be_visible()
                photo.get_by_role("button", name="Remove Image", exact=True).click()
                photo.locator("input[type=file]").set_input_files(args.photo)
                page.wait_for_function(
                    """() => [...document.querySelectorAll('#photo-input img')]
                         .some(img => img.complete && img.naturalWidth > 0 && img.naturalHeight > 0)""")
                print("Photo uploaded and preview decoded", flush=True)
            if key == "asr":
                audio = page.locator("#audio-input")
                expect(audio.locator("time").last).to_have_text("0:04")
                audio.get_by_role("button", name="Clear", exact=True).click()
                audio.locator("input[type=file]").set_input_files(args.wav)
                expect(audio.locator("time").last).to_have_text("0:04")
                expect(audio.locator("time").first).to_have_text("0:00")
                audio.get_by_role("button", name="Play", exact=True).click()
                expect(audio.locator("time").first).to_have_text("0:01")
                audio.get_by_role("button", name="Pause", exact=True).click()
                print("WAV playback advanced in Chromium", flush=True)
            run_demo(page, key, expected)
            print(f"{key} OK", flush=True)
            memory(args.server_pid)
        select_tab(page, "Metin")
        select_tab(page, "Translation")
        translation = page.get_by_role("textbox", name="Fransızca", exact=True)
        translation.fill("Bonjour.")
        run_demo(page, "translation", ("Hello.",))
        print("Editable translation after Whisper OK", flush=True)
        memory(args.server_pid)
        chromium.close()


if __name__ == "__main__":
    main()
