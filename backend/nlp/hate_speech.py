from typing import Dict, Any

class HateSpeechDetector:
    """Detects abusive language, communal hate speech, and derogatory slurs."""
    
    HATE_TERMS = [
        "गद्दार", "खदेड़", "बहिष्कार", "समुदाय के लोग", "गंदे", "मलेच्छ", "traitor", 
        "hateful", "bhiwandi", "abusive", "badla", "gaddar"
    ]

    @classmethod
    def detect(cls, text: str, lang: str = "en") -> Dict[str, Any]:
        lower_text = text.lower()
        matches = [term for term in cls.HATE_TERMS if term in lower_text]
        
        is_hate = len(matches) > 0
        confidence = min(0.60 + (len(matches) * 0.20), 0.98) if is_hate else 0.05
        
        return {
            "is_hate_speech": is_hate,
            "score": round(confidence, 2),
            "matched_terms": matches,
            "categories": ["communal_hate"] if is_hate else []
        }
