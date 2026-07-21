import time
from typing import Dict, Any
from agents.base_agent import SentinelAgent
from nlp.pipeline import nlp_pipeline
from scoring.threat_scorer import ThreatScorer
from utils.openrouter_client import openrouter_client
from utils.config import settings

class NLPClassifierAgent(SentinelAgent):
    """Hermes Agent responsible for multilingual language detection, sentiment, threat classification & composite scoring using OpenRouter API."""
    
    def __init__(self):
        super().__init__("nlp_classifier_agent", "NLP & Threat Classifier (OpenRouter Multi-Agent)")
        
        # Register core NLP tools for Hermes function calling / inspection
        self.register_tool(
            name="language_detect",
            func=nlp_pipeline.lang_detector.detect,
            description="Detects Gujarati, Hindi, English, and code-mixed Hinglish scripts/slang"
        )
        self.register_tool(
            name="classify_threat_lexicon",
            func=nlp_pipeline.classifier.classify,
            description="Multi-class threat categorization based on regional CTI lexicons"
        )
        self.register_tool(
            name="detect_hate_speech",
            func=nlp_pipeline.hate_detector.detect,
            description="Identifies communal hate speech, slurs, and derogatory language"
        )
        self.register_tool(
            name="extract_meme_ocr",
            func=nlp_pipeline.ocr_engine.extract_text_from_image,
            description="Extracts embedded text from meme images and viral infographics"
        )

    def process(self, post: Dict[str, Any]) -> Dict[str, Any]:
        start_t = time.time()
        self.set_status("RUNNING", f"Classifying post {post.get('id', 'unknown')[:8]} from {post.get('platform', 'social')}")
        
        text = post.get("content", "")
        image_url = post.get("image_url")
        
        # 1. Base NLP Pipeline Processing using registered tools / pipeline
        nlp_res = nlp_pipeline.process(text, image_url)
        
        # 2. OpenRouter API Multi-Agent Inference (if API key configured)
        if settings.OPENROUTER_API_KEY:
            prompt = f"""You are an advanced National Security & Cyber Threat Intelligence (CTI) AI Agent monitoring Indian social media (Hindi, Gujarati, English, Hinglish).
Analyze the following social media post for public safety threats, misinformation, hate speech, communal incitement, or riots.

Post Content: "{text}"
Author: {post.get('author_username', 'Unknown')}
Platform: {post.get('platform', 'Unknown')}

Return ONLY valid JSON with exactly the following keys:
- "language": string ("gu", "hi", "en", or "hinglish")
- "sentiment_label": string ("positive", "negative", or "neutral")
- "sentiment_score": float between 0.0 and 1.0 (confidence of sentiment)
- "threat_level": string (MUST be one of: "Neutral", "Inflammatory", "Fake News", or "Incitement to Violence")
- "threat_score": float between 0.0 and 1.0 (severity of public threat)
- "is_hate_speech": boolean
- "hate_speech_score": float between 0.0 and 1.0
- "analysis_reason": short explanation of why this classification was assigned.
"""
            messages = [
                {"role": "system", "content": "You are SentinelAI, an expert law enforcement intelligence classifier for Indian social media monitoring. Output strictly JSON."},
                {"role": "user", "content": prompt}
            ]
            
            ai_res = openrouter_client.chat_completion(
                messages=messages,
                model=settings.AGENT_THREAT_MODEL or settings.AGENT_NLP_MODEL,
                temperature=0.1,
                max_tokens=600,
                response_format_json=True
            )
            
            if ai_res and isinstance(ai_res, dict) and "threat_level" in ai_res:
                nlp_res["language"] = ai_res.get("language", nlp_res["language"])
                nlp_res["sentiment"] = {
                    "label": ai_res.get("sentiment_label", "negative"),
                    "score": float(ai_res.get("sentiment_score", 0.90))
                }
                nlp_res["threat_level"] = ai_res.get("threat_level", "Neutral")
                nlp_res["threat_classification"] = {
                    "level": nlp_res["threat_level"],
                    "score": float(ai_res.get("threat_score", 0.1)),
                    "reason": ai_res.get("analysis_reason", "AI intelligence classification")
                }
                nlp_res["hate_speech"] = {
                    "is_hate_speech": bool(ai_res.get("is_hate_speech", False)),
                    "score": float(ai_res.get("hate_speech_score", 0.0))
                }
        
        # Extract features for scoring
        sentiment_neg = 0.90 if nlp_res["sentiment"]["label"] == "negative" else 0.10
        threat_class_score = nlp_res["threat_classification"].get("score", 0.2)
        hate_speech_score = nlp_res["hate_speech"]["score"] if nlp_res["hate_speech"]["is_hate_speech"] else 0.0
        velocity = 0.80 if post.get("engagement", {}).get("likes", 0) > 1000 else 0.30
        coord_score = 0.85 if post.get("coordination_group") else 0.0
        bot_score = 0.90 if post.get("is_bot") else 0.0
        
        # 3. Composite Threat Score Calculation
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
        
        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        self.total_processed += 1
        self.set_status("COMPLETED", f"Assigned {score_res['severity']} ({score_res['composite_score']}) via {settings.AGENT_THREAT_MODEL.split('/')[1] if settings.OPENROUTER_API_KEY else 'Hybrid Lexicon'}")
        
        self.log_memory({
            "action": "classified_post",
            "post_id": post.get("id"),
            "threat_level": nlp_res["threat_level"],
            "threat_score": score_res["composite_score"],
            "duration_ms": self.last_execution_time_ms,
            "openrouter_used": bool(settings.OPENROUTER_API_KEY)
        })
        return enriched_post


