"""
Transformer-Based Hate Speech Detector for SentinelAI.

Uses Hate-speech-CNERG/hindi-abusive-MuRIL for Hindi/Hinglish/Gujarati
hate speech detection. Falls back to expanded keyword matching when
transformer models cannot be loaded.

Supports detection of:
  - Communal hate speech
  - Casteist slurs
  - Religious targeting
  - Gender-based abuse
  - Coded hate speech patterns
"""

import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger("sentinelai.nlp.hate")

# Lazy-loaded globals
_hate_pipeline = None
_model_loaded = False
_load_error = None

# Model configuration
# HateXplain model (~440MB) — much lighter than MuRIL (950MB) and effective
# for hate speech classification. Falls back to 80+ term keyword ensemble
# if disk/memory is insufficient.
HATE_MODEL_INDIC = "Hate-speech-CNERG/bert-base-uncased-hatexplain"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

# ── Expanded hate speech lexicon (80+ terms) ─────────────────────────────────

HATE_TERMS_BY_CATEGORY = {
    "communal_hate": [
        # Hindi
        "गद्दार", "मलेच्छ", "काफिर", "जिहादी", "आतंकी", "देशद्रोही",
        "सांप्रदायिक", "समुदाय के लोग", "विशेष समुदाय", "गंदे",
        "भगा दो", "खदेड़ दो", "निकालो", "बहिष्कार",
        # Gujarati
        "ખદેડી", "ખરાબ", "દ્રોહી", "કાફિર", "જિહાદી", "દેશદ્રોહી",
        "સાંપ્રદાયિક", "ભગાડો", "બહિષ્કાર",
        # Hinglish / Romanized
        "gaddar", "deshdrohi", "jihadi", "kaafir", "nikalo", "bhagao",
        "khadedo", "boycott",
        # English
        "traitor", "terrorist", "extremist", "infidel",
    ],
    "casteist_slurs": [
        # Hindi
        "चमार", "भंगी", "डोम", "नीच जाति", "छोटी जाति",
        # Gujarati
        "ચમાર", "ભંગી", "નીચ",
        # Hinglish
        "chamaar", "bhangi", "neech",
    ],
    "abusive_language": [
        # Hindi
        "हरामी", "कुत्ते", "सुअर", "कमीना", "भड़वा", "रंडी",
        "चुटिया", "गधा", "उल्लू", "बेशर्म",
        # Gujarati
        "હરામી", "કૂતરો", "કમીનો", "બેશરમ", "ગધેડો",
        # Hinglish / Romanized
        "harami", "kutte", "kamina", "saale", "bhadwa",
        "chutiya", "gadha", "ullu", "besharam",
        # English
        "bastard", "hateful", "scum", "filth", "abusive", "bigot",
    ],
    "threat_speech": [
        # Hindi
        "जान से मार दूंगा", "खून कर दूंगा", "सबक सिखाओ",
        "ठोक दो", "उड़ा दो", "सफाया करो",
        # Gujarati
        "જાનથી મારી નાખીશ", "સબક શીખવવો", "ઠોકી દો",
        # Hinglish
        "jaan se maar dunga", "thok do", "sabak sikhao", "udaa do",
        # English
        "i will kill", "death threat", "eliminate",
    ],
}

# Flatten all terms for quick matching
ALL_HATE_TERMS = []
TERM_TO_CATEGORY = {}
for category, terms in HATE_TERMS_BY_CATEGORY.items():
    for term in terms:
        ALL_HATE_TERMS.append(term.lower())
        TERM_TO_CATEGORY[term.lower()] = category


def _load_model():
    """Lazy-load the hate speech detection model (if configured)."""
    global _hate_pipeline, _model_loaded, _load_error
    if _model_loaded:
        return _hate_pipeline is not None
    
    if not HATE_MODEL_INDIC:
        _model_loaded = True
        logger.info("Hate speech transformer disabled. Using keyword ensemble.")
        return False
    
    try:
        from transformers import pipeline as hf_pipeline
        import torch

        device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Loading hate speech model: {HATE_MODEL_INDIC} (device={'cuda' if device == 0 else 'cpu'})")
        
        os.makedirs(CACHE_DIR, exist_ok=True)
        _hate_pipeline = hf_pipeline(
            "text-classification",
            model=HATE_MODEL_INDIC,
            tokenizer=HATE_MODEL_INDIC,
            cache_dir=CACHE_DIR,
            device=device,
            top_k=None,
            truncation=True,
            max_length=512,
        )
        _model_loaded = True
        logger.info("Hate speech transformer loaded successfully.")
        return True
    except Exception as e:
        _load_error = str(e)
        _model_loaded = True
        logger.warning(f"Failed to load hate speech transformer: {e}. Falling back to keyword detection.")
        return False


def _keyword_detect(text: str) -> Dict[str, Any]:
    """Expanded keyword-based hate speech detection."""
    lower = text.lower()
    matched_terms = []
    matched_categories = set()
    
    for term in ALL_HATE_TERMS:
        if term in lower:
            matched_terms.append(term)
            matched_categories.add(TERM_TO_CATEGORY[term])
    
    is_hate = len(matched_terms) > 0
    # Weighted confidence: more matches = higher confidence
    if is_hate:
        confidence = min(0.55 + (len(matched_terms) * 0.10), 0.95)
    else:
        confidence = 0.05
    
    return {
        "is_hate_speech": is_hate,
        "score": round(confidence, 4),
        "matched_terms": matched_terms[:10],  # Limit to first 10
        "categories": list(matched_categories),
        "model": "keyword_detector",
    }


class HateTransformerDetector:
    """High-accuracy hate speech detector combining MuRIL transformer with keyword signals."""
    
    TRANSFORMER_WEIGHT = 0.65
    KEYWORD_WEIGHT = 0.35
    
    # Label mapping for the MuRIL model
    LABEL_MAP = {
        "LABEL_0": "not_hate",
        "LABEL_1": "hate",
        "not-hate": "not_hate",
        "hate": "hate",
        "abusive": "hate",
        "not-abusive": "not_hate",
        "offensive": "hate",
        "not-offensive": "not_hate",
    }
    
    @classmethod
    def detect(cls, text: str, lang: str = "en") -> Dict[str, Any]:
        """
        Detect hate speech using ensemble of transformer + keyword signals.
        
        Returns:
            dict with: is_hate_speech, score, matched_terms, categories, model
        """
        if not text or not text.strip():
            return {
                "is_hate_speech": False,
                "score": 0.0,
                "matched_terms": [],
                "categories": [],
                "model": "default",
            }
        
        clean_text = text.strip()
        if len(clean_text) > 512:
            clean_text = clean_text[:512]
        
        # Get keyword detection results
        kw_result = _keyword_detect(text)
        
        # Try transformer
        if _load_model() and _hate_pipeline is not None:
            try:
                results = _hate_pipeline(clean_text)
                
                if isinstance(results, list) and len(results) > 0:
                    if isinstance(results[0], list):
                        results = results[0]
                    
                    # Parse transformer output
                    hate_score = 0.0
                    for item in results:
                        mapped = cls.LABEL_MAP.get(item["label"].lower(), item["label"].lower())
                        if mapped == "hate":
                            hate_score = max(hate_score, item["score"])
                    
                    # Ensemble score
                    kw_score = kw_result["score"] if kw_result["is_hate_speech"] else 0.0
                    ensemble_score = (cls.TRANSFORMER_WEIGHT * hate_score) + (cls.KEYWORD_WEIGHT * kw_score)
                    
                    is_hate = ensemble_score >= 0.45
                    
                    return {
                        "is_hate_speech": is_hate,
                        "score": round(ensemble_score, 4),
                        "matched_terms": kw_result["matched_terms"],
                        "categories": kw_result["categories"] if is_hate else [],
                        "model": f"ensemble({HATE_MODEL_INDIC}+keywords)",
                        "transformer_score": round(hate_score, 4),
                        "keyword_score": round(kw_score, 4),
                    }
            except Exception as e:
                logger.warning(f"Hate speech transformer inference error: {e}")
        
        # Fallback to keyword-only
        return kw_result


# Module-level convenience instance
hate_transformer = HateTransformerDetector()
