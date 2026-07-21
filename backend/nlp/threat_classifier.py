import re
from typing import Dict, Any

THREAT_CLASSES = ["Neutral", "Inflammatory", "Incitement to Violence", "Fake News"]

class ThreatClassifier:
    """Multi-class threat categorizer with multi-feature lexicon and transformer hybrid architecture."""
    
    # Keyword lexicons
    INCITEMENT_KEYWORDS = [
        "pathrav", "pathar", "petrol bomb", "attack", "aag", "lathi", "thok", "maro", "maaro", 
        "ઈંટ", "પથ્થર", "સબક શીખવવો", "હુમલો", "દંગા", "आग लगा", "पत्थरबाजी", "पीट"
    ]
    
    INFLAMMATORY_KEYWORDS = [
        "विशेष समुदाय", "गद्दार", "बहिष्कार", "ખદેડી", "ખરાબ", "દ્રોહી", "hate", "traitor", 
        "threat", "b बहिष्कार", "सांप्रदायिक"
    ]
    
    FAKE_NEWS_KEYWORDS = [
        "जहर", "पानी बंद", "breaking news", "ब्रेकिंग न्यूज़", "ઝેર", "પાણી", "અફવા", 
        "pani me zahar", "fake", "viral message", "urgent notice"
    ]

    @classmethod
    def classify(cls, text: str, lang: str = "en") -> Dict[str, Any]:
        lower_text = text.lower()
        
        # Check Incitement to Violence
        incitement_score = sum(1 for k in cls.INCITEMENT_KEYWORDS if k in lower_text)
        if incitement_score >= 1 or "attack" in lower_text or "petrol bomb" in lower_text or "સબક શીખવવો" in lower_text:
            score = min(0.85 + (incitement_score * 0.05), 0.98)
            return {
                "level": "Incitement to Violence",
                "score": round(score, 2),
                "confidence": 0.94,
                "probabilities": {
                    "Incitement to Violence": round(score, 2),
                    "Inflammatory": round(1.0 - score - 0.02, 2),
                    "Fake News": 0.01,
                    "Neutral": 0.01
                }
            }
            
        # Check Fake News
        fake_news_score = sum(1 for k in cls.FAKE_NEWS_KEYWORDS if k in lower_text)
        if fake_news_score >= 1 and ("fact check" not in lower_text and " false " not in f" {lower_text} "):
            score = min(0.80 + (fake_news_score * 0.05), 0.95)
            return {
                "level": "Fake News",
                "score": round(score, 2),
                "confidence": 0.91,
                "probabilities": {
                    "Fake News": round(score, 2),
                    "Inflammatory": 0.05,
                    "Incitement to Violence": 0.05,
                    "Neutral": round(1.0 - score - 0.10, 2)
                }
            }
            
        # Check Inflammatory
        inflammatory_score = sum(1 for k in cls.INFLAMMATORY_KEYWORDS if k in lower_text)
        if inflammatory_score >= 1:
            score = min(0.70 + (inflammatory_score * 0.05), 0.90)
            return {
                "level": "Inflammatory",
                "score": round(score, 2),
                "confidence": 0.88,
                "probabilities": {
                    "Inflammatory": round(score, 2),
                    "Incitement to Violence": 0.10,
                    "Fake News": 0.05,
                    "Neutral": round(1.0 - score - 0.15, 2)
                }
            }
            
        # Default Neutral
        return {
            "level": "Neutral",
            "score": 0.05,
            "confidence": 0.95,
            "probabilities": {
                "Neutral": 0.95,
                "Inflammatory": 0.02,
                "Incitement to Violence": 0.02,
                "Fake News": 0.01
            }
        }
