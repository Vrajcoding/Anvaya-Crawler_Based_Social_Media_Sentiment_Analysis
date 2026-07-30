"""
Pre-downloads all transformer models used by the Hermes NLP pipeline.

Run once after pip install to cache models locally:
    python -m nlp.download_models

Models downloaded:
  1. cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual (sentiment)
  2. facebook/bart-large-mnli (zero-shot threat classification)
  3. Hate-speech-CNERG/hindi-abusive-MuRIL (hate speech detection)
"""

import os
import sys

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

MODELS = [
    ("sentiment", "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"),
    ("zero-shot threat", "facebook/bart-large-mnli"),
    ("hate speech", "Hate-speech-CNERG/hindi-abusive-MuRIL"),
]


def download_all():
    """Download and cache all required transformer models."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    print("=" * 70)
    print("SentinelAI — Hermes NLP Model Downloader")
    print(f"Cache directory: {CACHE_DIR}")
    print("=" * 70)
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
    except ImportError:
        print("ERROR: transformers library not installed. Run: pip install transformers torch")
        sys.exit(1)
    
    for i, (name, model_id) in enumerate(MODELS, 1):
        print(f"\n[{i}/{len(MODELS)}] Downloading: {model_id} ({name})...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=CACHE_DIR)
            
            if "mnli" in model_id or "bart" in model_id:
                model = AutoModelForSeq2SeqLM.from_pretrained(model_id, cache_dir=CACHE_DIR)
            else:
                model = AutoModelForSequenceClassification.from_pretrained(model_id, cache_dir=CACHE_DIR)
            
            print(f"  ✓ {name} model downloaded and cached successfully.")
        except Exception as e:
            print(f"  ✗ Failed to download {name} model: {e}")
    
    print("\n" + "=" * 70)
    print("Model download complete. Models cached in:", CACHE_DIR)
    print("=" * 70)


if __name__ == "__main__":
    download_all()
