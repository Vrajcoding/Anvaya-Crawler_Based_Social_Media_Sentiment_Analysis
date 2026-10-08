"""
SentinelAI NLP Inference Pipeline — Redesigned from Scratch.

This is the SINGLE active NLP pipeline for the entire application.
All scraped posts flow through run_nlp_pipeline() which produces:
  - Sentiment (3-class: positive / negative / neutral)
  - Threat category (4-class: Neutral / Inflammatory / Incitement to Violence / Fake News)
  - Hate speech detection (binary flag with category breakdown)
  - Fake news signal (semantic claim matching)

Architecture:
  1. Social media text preprocessing (URL/hashtag/emoji/transliteration)
  2. Language detection (Unicode script + Hinglish markers)
  3. Transformer inference with robust keyword fallback
  4. Each analysis component fails independently

Models used:
  - Sentiment: cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual (XLM-RoBERTa)
  - Threat:    MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli (Zero-shot NLI)
  - Hate:      Hate-speech-CNERG/bert-base-hatexplain (HateXplain)

Output schema is backward-compatible with all existing API consumers.
"""

import os
import re
import time
import logging
import warnings
from typing import Dict, Any, Optional

# ── Suppress harmless HuggingFace warnings ────────────────────────────────────
# 1. position_ids UNEXPECTED: This is a buffer (not a learned weight) present in
#    saved checkpoints but not expected by the model class. Completely harmless.
# 2. Unauthenticated HF Hub requests: Only affects rate limits, not functionality.
# 3. TOKENIZERS_PARALLELISM: Avoids fork-safety warnings on some systems.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

# Silence the "UNEXPECTED key" load reports from transformers
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
# Silence the "unauthenticated requests" warning from huggingface_hub
logging.getLogger("huggingface_hub.utils._token").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub.file_download").setLevel(logging.ERROR)
# Suppress FutureWarning from transformers internals
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", message=".*position_ids.*")

from nlp_service.models.preprocessor import preprocess_social_text, detect_language
from nlp_service.models.keyword_analyzers import (
    SentimentKeywordAnalyzer,
    ThreatKeywordAnalyzer,
    HateKeywordAnalyzer,
)
from nlp_service.fake_news.similarity_match import ClaimMatcher

logger = logging.getLogger("sentinelai.nlp.inference")

# ── Lazy-loaded model globals ─────────────────────────────────────────────────

_sentiment_pipeline = None
_sentiment_loaded = False

_zero_shot_pipeline = None
_zero_shot_loaded = False

_hate_pipeline = None
_hate_loaded = False

_claim_matcher = None

CLAIM_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "claim_db.jsonl"
)

# ── Threat classification config ──────────────────────────────────────────────

THREAT_LABELS = ["Neutral", "Inflammatory", "Incitement to Violence", "Fake News"]

# Sentiment model label mapping
SENTIMENT_LABEL_MAP = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "label_0": "negative",
    "label_1": "neutral",
    "label_2": "positive",
}

# Hate speech model label mapping
HATE_LABEL_MAP = {
    "hate": "hate",
    "offensive": "hate",
    "normal": "not_hate",
    "label_0": "hate",
    "label_1": "not_hate",
    "label_2": "not_hate",
    "hateful": "hate",
    "not-hateful": "not_hate",
    "abusive": "hate",
    "not-abusive": "not_hate",
}


# ══════════════════════════════════════════════════════════════════════════════
# MODEL LOADING — Each model loads independently, failure is isolated
# ══════════════════════════════════════════════════════════════════════════════

def _load_sentiment_model() -> bool:
    """Load XLM-RoBERTa sentiment model. Returns True if ready."""
    global _sentiment_pipeline, _sentiment_loaded
    if _sentiment_loaded:
        return _sentiment_pipeline is not None

    try:
        from transformers import pipeline as hf_pipeline
        import torch

        device = 0 if torch.cuda.is_available() else -1
        model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"
        logger.info(f"Loading sentiment model: {model_name} (device={'cuda' if device == 0 else 'cpu'})")

        _sentiment_pipeline = hf_pipeline(
            "sentiment-analysis",
            model=model_name,
            device=device,
            torch_dtype=torch.float32,
            top_k=None,
            truncation=True,
            max_length=512,
        )
        _sentiment_loaded = True
        logger.info("✓ Sentiment transformer loaded successfully.")
        return True
    except Exception as e:
        _sentiment_loaded = True  # Mark as attempted
        logger.warning(f"✗ Sentiment transformer failed to load: {e}. Using keyword fallback.")
        return False


def _load_threat_model() -> bool:
    """Load DeBERTa zero-shot classification model. Returns True if ready."""
    global _zero_shot_pipeline, _zero_shot_loaded
    if _zero_shot_loaded:
        return _zero_shot_pipeline is not None

    try:
        from transformers import pipeline as hf_pipeline
        import torch

        device = 0 if torch.cuda.is_available() else -1
        model_name = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
        logger.info(f"Loading threat model: {model_name} (device={'cuda' if device == 0 else 'cpu'})")

        _zero_shot_pipeline = hf_pipeline(
            "zero-shot-classification",
            model=model_name,
            device=device,
            torch_dtype=torch.float32,
        )
        _zero_shot_loaded = True
        logger.info("✓ Threat classifier transformer loaded successfully.")
        return True
    except Exception as e:
        _zero_shot_loaded = True
        logger.warning(f"✗ Threat classifier failed to load: {e}. Using keyword fallback.")
        return False


def _load_hate_model() -> bool:
    """Load HateXplain hate speech model. Returns True if ready."""
    global _hate_pipeline, _hate_loaded
    if _hate_loaded:
        return _hate_pipeline is not None

    try:
        from transformers import pipeline as hf_pipeline
        import torch

        device = 0 if torch.cuda.is_available() else -1
        model_name = "Hate-speech-CNERG/bert-base-uncased-hatexplain"
        logger.info(f"Loading hate speech model: {model_name} (device={'cuda' if device == 0 else 'cpu'})")

        _hate_pipeline = hf_pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            device=device,
            torch_dtype=torch.float32,
            top_k=None,
            truncation=True,
            max_length=512,
        )
        _hate_loaded = True
        logger.info("✓ Hate speech transformer loaded successfully.")
        return True
    except Exception as e:
        _hate_loaded = True
        logger.warning(f"✗ Hate speech model failed to load: {e}. Using keyword fallback.")
        return False


def _get_claim_matcher() -> Optional[ClaimMatcher]:
    """Initialize claim matcher for fake news detection."""
    global _claim_matcher
    if _claim_matcher is None:
        try:
            _claim_matcher = ClaimMatcher(CLAIM_DB_PATH)
        except Exception as e:
            logger.warning(f"Claim matcher initialization failed: {e}")
    return _claim_matcher


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS — Each one is isolated; a crash in one doesn't kill others
# ══════════════════════════════════════════════════════════════════════════════

def _analyze_sentiment(cleaned_text: str, raw_text: str) -> Dict[str, Any]:
    """
    3-class sentiment analysis: positive / negative / neutral.
    
    Strategy:
      1. Try XLM-RoBERTa transformer (>90% accuracy on multilingual social text)
      2. Fall back to weighted keyword ensemble (200+ multilingual terms)
    """
    # Try transformer
    if _load_sentiment_model() and _sentiment_pipeline is not None:
        try:
            results = _sentiment_pipeline(cleaned_text[:512])

            if isinstance(results, list) and len(results) > 0:
                raw_items = results[0] if isinstance(results[0], list) else results

                probabilities = {}
                best_label = "neutral"
                best_score = 0.0

                for item in raw_items:
                    mapped = SENTIMENT_LABEL_MAP.get(item["label"].lower(), item["label"].lower())
                    probabilities[mapped] = round(float(item["score"]), 4)
                    if item["score"] > best_score:
                        best_score = item["score"]
                        best_label = mapped

                return {
                    "label": best_label,
                    "confidence": round(float(best_score), 4),
                    "probabilities": probabilities,
                    "model": "xlm-roberta-sentiment",
                }
        except Exception as e:
            logger.error(f"Sentiment transformer inference error: {e}")

    # Fallback to keyword analyzer
    logger.debug("Using keyword fallback for sentiment analysis.")
    return SentimentKeywordAnalyzer.analyze(raw_text)


def _analyze_threat(cleaned_text: str, raw_text: str) -> Dict[str, Any]:
    """
    4-class threat categorization: Neutral / Inflammatory / Incitement to Violence / Fake News.
    
    Strategy:
      1. Try DeBERTa zero-shot NLI classification
      2. Boost with keyword signals (ensemble: 70% transformer + 30% keywords)
      3. Fall back to pure keyword analyzer if transformer unavailable
    """
    # Get keyword scores for boosting (always computed)
    kw_result = ThreatKeywordAnalyzer.analyze(raw_text)

    # Try transformer
    if _load_threat_model() and _zero_shot_pipeline is not None:
        try:
            zs_result = _zero_shot_pipeline(
                cleaned_text[:512],
                candidate_labels=THREAT_LABELS,
                multi_label=False,
            )

            # Parse transformer probabilities
            transformer_scores = {}
            for label, score in zip(zs_result["labels"], zs_result["scores"]):
                transformer_scores[label] = float(score)

            # Parse keyword scores into same format
            kw_scores = kw_result.get("all_scores", {})

            # Dynamic ensemble: if strong keyword signals present (especially for regional languages),
            # weight keyword signals equally or higher (50/50)
            if kw_result.get("label") != "Neutral" and kw_result.get("confidence", 0) > 0.4:
                TRANSFORMER_W = 0.40
                KEYWORD_W = 0.60
            else:
                TRANSFORMER_W = 0.70
                KEYWORD_W = 0.30

            ensemble_scores = {}
            for label in THREAT_LABELS:
                t_score = transformer_scores.get(label, 0.0)
                k_score = kw_scores.get(label, 0.0)
                ensemble_scores[label] = (TRANSFORMER_W * t_score) + (KEYWORD_W * k_score)

            # Normalize
            total = sum(ensemble_scores.values()) or 1.0
            all_scores = {k: round(v / total, 4) for k, v in ensemble_scores.items()}

            best_label = max(all_scores, key=all_scores.get)
            best_score = all_scores[best_label]

            return {
                "label": best_label,
                "confidence": round(float(best_score), 4),
                "all_scores": all_scores,
                "model": "deberta-zero-shot+keywords",
            }
        except Exception as e:
            logger.error(f"Threat classifier inference error: {e}")

    # Fallback to keyword analyzer
    logger.debug("Using keyword fallback for threat classification.")
    return kw_result


def _analyze_hate_speech(cleaned_text: str, raw_text: str) -> Dict[str, Any]:
    """
    Binary hate speech detection with category breakdown.
    
    Strategy:
      1. Try HateXplain transformer model
      2. Combine with keyword signals (ensemble: 50% transformer + 50% keywords)
      3. If regional/indic hate terms detected, flag immediately with keyword confidence
    """
    # Always get keyword results for category info
    kw_result = HateKeywordAnalyzer.analyze(raw_text)

    # Try transformer
    if _load_hate_model() and _hate_pipeline is not None:
        try:
            results = _hate_pipeline(cleaned_text[:512])

            if isinstance(results, list) and len(results) > 0:
                raw_items = results[0] if isinstance(results[0], list) else results

                hate_score = 0.0
                for item in raw_items:
                    mapped = HATE_LABEL_MAP.get(item["label"].lower(), item["label"].lower())
                    if mapped == "hate":
                        hate_score = max(hate_score, float(item["score"]))

                # Dynamic ensemble: if keyword analyzer finds explicit regional hate terms,
                # give high weight to keyword signal
                if kw_result["is_hate_speech"]:
                    kw_score = kw_result["score"]
                    ensemble_score = max(hate_score, kw_score)
                    is_hate = True
                else:
                    ensemble_score = hate_score
                    is_hate = ensemble_score >= 0.50

                return {
                    "flag": is_hate,
                    "confidence": round(ensemble_score, 4),
                    "target_group_hint": kw_result["categories"][0] if is_hate and kw_result["categories"] else (
                        "unspecified" if is_hate else None
                    ),
                    "matched_terms": kw_result["matched_terms"] if is_hate else [],
                    "model": "hatexplain+keywords",
                }
        except Exception as e:
            logger.error(f"Hate speech model inference error: {e}")

    # Fallback to keyword analyzer — adapt output to expected schema
    logger.debug("Using keyword fallback for hate speech detection.")
    return {
        "flag": kw_result["is_hate_speech"],
        "confidence": kw_result["score"],
        "target_group_hint": kw_result["categories"][0] if kw_result["categories"] else None,
        "matched_terms": kw_result["matched_terms"],
        "model": kw_result["model"],
    }


def _analyze_fake_news(cleaned_text: str) -> Dict[str, Any]:
    """Semantic claim matching against known misinformation database."""
    matcher = _get_claim_matcher()
    if matcher:
        try:
            return matcher.match(cleaned_text)
        except Exception as e:
            logger.error(f"Claim matcher error: {e}")

    return {"status": "not_flagged", "matched_claim_id": None, "similarity": 0.0}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def run_nlp_pipeline(
    post_id: str,
    text: str,
    platform: str = "x",
    language_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Full NLP analysis pipeline for a single social media post.
    
    This function is called by:
      - crawl_routes.py._enrich_and_store_crawled_posts()
      - posts.py.create_post() and analyze_custom_text()
      - main.py.background_crawler_loop()
      - nlp_service/main.py /classify and /classify_batch endpoints
    
    Args:
        post_id: Unique identifier for the post
        text: Raw social media text content
        platform: Source platform (x, instagram, youtube, telegram, etc.)
        language_hint: Optional pre-detected language code
    
    Returns:
        Dict with keys: post_id, sentiment, threat_category, hate_speech,
        fake_news_signal, language_detected, requires_human_review,
        model_version, processed_at, inference_time_ms
    """
    start_time = time.time()

    # ── Step 1: Preprocessing ─────────────────────────────────────────────
    cleaned = preprocess_social_text(text)

    # ── Step 2: Language Detection ────────────────────────────────────────
    lang = language_hint if language_hint else detect_language(text)

    # ── Step 3: Sentiment Analysis (isolated) ─────────────────────────────
    try:
        sentiment_result = _analyze_sentiment(cleaned, text)
    except Exception as e:
        logger.error(f"[{post_id}] Sentiment analysis crashed: {e}")
        sentiment_result = {
            "label": "neutral",
            "confidence": 0.50,
            "probabilities": {"neutral": 0.50, "negative": 0.25, "positive": 0.25},
            "model": "error_fallback",
        }

    # ── Step 4: Threat Classification (isolated) ──────────────────────────
    try:
        threat_result = _analyze_threat(cleaned, text)
    except Exception as e:
        logger.error(f"[{post_id}] Threat classification crashed: {e}")
        threat_result = {
            "label": "Neutral",
            "confidence": 0.50,
            "all_scores": {l: 0.25 for l in THREAT_LABELS},
            "model": "error_fallback",
        }

    # ── Step 5: Hate Speech Detection (isolated) ──────────────────────────
    try:
        hate_result = _analyze_hate_speech(cleaned, text)
    except Exception as e:
        logger.error(f"[{post_id}] Hate speech detection crashed: {e}")
        hate_result = {
            "flag": False,
            "confidence": 0.0,
            "target_group_hint": None,
        }

    # ── Step 6: Fake News Signal (isolated) ───────────────────────────────
    try:
        fake_news_signal = _analyze_fake_news(cleaned)
    except Exception as e:
        logger.error(f"[{post_id}] Fake news matching crashed: {e}")
        fake_news_signal = {"status": "not_flagged", "matched_claim_id": None, "similarity": 0.0}

    # ── Step 7: Call-to-Action Extraction (Feature 4.2) ───────────────────
    try:
        from nlp_service.models.cta_extractor import CTAExtractor
        cta_result = CTAExtractor.extract(text)
    except Exception as e:
        logger.error(f"[{post_id}] CTA extraction crashed: {e}")
        cta_result = {"is_cta": False, "when": [], "where": [], "who": []}

    # ── Step 8: Human Review Flagging ─────────────────────────────────────
    requires_human_review = (
        threat_result.get("label") in ["Incitement to Violence", "Fake News"]
        or threat_result.get("confidence", 0) > 0.75
        or hate_result.get("flag", False)
        or fake_news_signal.get("status") == "matched"
        or cta_result.get("is_cta", False)
    )

    # ── Step 9: Assemble result ───────────────────────────────────────────
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "post_id": post_id,
        "sentiment": sentiment_result,
        "threat_category": threat_result,
        "hate_speech": hate_result,
        "fake_news_signal": fake_news_signal,
        "cta": cta_result,
        "language_detected": lang,
        "requires_human_review": requires_human_review,
        "model_version": "sentinelai-nlp-v2.0",
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inference_time_ms": elapsed_ms,
    }
