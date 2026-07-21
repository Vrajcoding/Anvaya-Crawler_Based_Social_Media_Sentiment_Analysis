from typing import Dict, Any
from utils.config import settings

class ThreatScorer:
    """Calculates composite threat score based on NLP, engagement velocity, network coordination, and bot heuristics."""
    
    @staticmethod
    def calculate_score(
        sentiment_neg: float,
        threat_class_score: float,
        hate_speech_score: float,
        engagement_velocity: float = 0.5,
        coordination_score: float = 0.0,
        bot_likelihood: float = 0.0
    ) -> Dict[str, Any]:
        
        w1 = settings.WEIGHT_SENTIMENT
        w2 = settings.WEIGHT_THREAT_CLASS
        w3 = settings.WEIGHT_HATE_SPEECH
        w4 = settings.WEIGHT_VELOCITY
        w5 = settings.WEIGHT_COORDINATION
        w6 = settings.WEIGHT_BOT
        
        composite = (
            (w1 * sentiment_neg) +
            (w2 * threat_class_score) +
            (w3 * hate_speech_score) +
            (w4 * engagement_velocity) +
            (w5 * coordination_score) +
            (w6 * bot_likelihood)
        )
        
        composite = min(max(composite, 0.0), 1.0)
        
        # Severity Mapping
        if composite >= settings.THRESHOLD_CRITICAL:
            severity = "CRITICAL"
            color = "#EF4444"  # Red
        elif composite >= settings.THRESHOLD_HIGH:
            severity = "HIGH"
            color = "#F97316"  # Orange
        elif composite >= settings.THRESHOLD_MEDIUM:
            severity = "MEDIUM"
            color = "#EAB308"  # Yellow
        else:
            severity = "LOW"
            color = "#22C55E"  # Green
            
        return {
            "composite_score": round(composite, 2),
            "severity": severity,
            "color": color,
            "breakdown": {
                "sentiment_component": round(w1 * sentiment_neg, 3),
                "threat_component": round(w2 * threat_class_score, 3),
                "hate_component": round(w3 * hate_speech_score, 3),
                "velocity_component": round(w4 * engagement_velocity, 3),
                "coordination_component": round(w5 * coordination_score, 3),
                "bot_component": round(w6 * bot_likelihood, 3)
            }
        }
