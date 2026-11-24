"""Model IDs shared by the preparation script and inference functions."""
MODELS = {
    "sentiment_analysis": "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    "zero_shot_classification": "MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33",
    "text_generation": "HuggingFaceTB/SmolLM2-360M",
    "fill_mask": "distilbert/distilroberta-base",
    "ner": "dslim/bert-base-NER",
    "question_answering": "distilbert/distilbert-base-cased-distilled-squad",
    "summarization": "google-t5/t5-small",
    "translation": "Helsinki-NLP/opus-mt-fr-en",
    "image_classification": "google/vit-base-patch16-224",
    "asr": "openai/whisper-large-v3",
}
CACHED = {"text_generation", "translation", "image_classification", "asr"}
