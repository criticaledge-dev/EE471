"""Shared offline model and tokenizer configuration for Task 4."""
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from transformers import AutoTokenizer

MODEL_ID = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"


def load_tokenizer(source=MODEL_ID):
    return AutoTokenizer.from_pretrained(source, local_files_only=True)
