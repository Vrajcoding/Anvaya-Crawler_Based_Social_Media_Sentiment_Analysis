from typing import Dict, Any
from agents.base_agent import SentinelAgent
from nlp.pipeline import nlp_pipeline
from scoring.threat_scorer import ThreatScorer

class NLPClassifierAgent(SentinelAgent):
    """Hermes Agent responsible for multilingual language detection, sentiment, threat classification & composite scoring."""
    
    def __init__(self):
        super().__init__("nlp_classifier_agent", "NLP & Threat Classifier")

    def process(self, post: Dict[str, Any]) -> Dict[str, Any]:
        text = post.get("content", "")
        image_url = post.get("image_url")
        
        # 1. NLP Pipeline Processing
        nlp_res = nlp_pipeline.process(text, image_url)
        
        # Extract features
        sentiment_neg = 0.90 if nlp_res["sentiment"]["label"] == "negative" else 0.10
        threat_class_score = nlp_res["threat_classification"]["score"]
        hate_speech_score = nlp_res["hate_speech"]["score"] if nlp_res["hate_speech"]["is_hate_speech"] else 0.0
        velocity = 0.80 if post.get("engagement", {}).get("likes", 0) > 1000 else 0.30
        coord_score = 0.85 if post.get("coordination_group") else 0.0
        bot_score = 0.90 if post.get("is_bot") else 0.0
        
        # 2. Composite Threat Score Calculation
        score_res = ThreatScorer.calculate_score(
            sentiment_neg=sentiment_neg,
            threat_class_score=threat_class_score,
            hate_speech_score=hate_speech_score,
            engagement_velocity=velocity,
            coordination_score=coord_score,
            bot_likelihood=bot_score
        )
        
        enriched_post = {
            **post,
            "language": nlp_res["language"],
            "sentiment": nlp_res["sentiment"],
            "threat_level": nlp_res["threat_level"],
            "threat_score": score_res["composite_score"],
            "threat_severity": score_res["severity"],
            "is_hate_speech": nlp_res["hate_speech"]["is_hate_speech"],
            "nlp_breakdown": nlp_res,
            "scoring_breakdown": score_res["breakdown"]
        }
        
        self.log_memory({"action": "classified_post", "post_id": post.get("id"), "threat_level": nlp_res["threat_level"]})
        return enriched_post
