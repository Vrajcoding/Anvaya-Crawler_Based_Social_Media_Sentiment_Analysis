import time
from typing import Dict, Any, List
from agents.base_agent import SentinelAgent
from storage.db_client import db
from utils.config import settings

class LearningAgent(SentinelAgent):
    """Hermes Meta-Agent for analyst feedback integration and continuous model retraining adjustment."""
    
    def __init__(self):
        super().__init__("learning_agent", "Human-In-The-Loop Learner")
        self.register_tool(
            name="ingest_feedback",
            func=db.add_feedback,
            description="Records duty officer classification corrections into active retraining queue"
        )
        self.register_tool(
            name="get_feedback_history",
            func=self._get_feedback_history,
            description="Retrieves history of duty officer corrections and model retraining logs"
        )
        self.register_tool(
            name="adjust_scoring_weights",
            func=self._adjust_scoring_weights,
            description="Dynamically tunes composite threat scoring weights based on feedback trends"
        )

    def _get_feedback_history(self) -> List[Dict[str, Any]]:
        return [m for m in self.memory if m.get("action") == "feedback_ingested"]

    def _adjust_scoring_weights(self, feedback: Dict[str, Any]) -> Dict[str, float]:
        corrected_label = feedback.get("corrected_label")
        if corrected_label == "Neutral":
            # Reduce false positive sensitivity slightly
            settings.WEIGHT_THREAT_CLASS = max(0.20, settings.WEIGHT_THREAT_CLASS - 0.01)
        elif corrected_label in ["Incitement to Violence", "Fake News", "Inflammatory"]:
            # Boost threat class sensitivity
            settings.WEIGHT_THREAT_CLASS = min(0.40, settings.WEIGHT_THREAT_CLASS + 0.01)
            
        return {
            "WEIGHT_THREAT_CLASS": settings.WEIGHT_THREAT_CLASS,
            "WEIGHT_SENTIMENT": settings.WEIGHT_SENTIMENT,
            "WEIGHT_HATE_SPEECH": settings.WEIGHT_HATE_SPEECH,
            "WEIGHT_COORDINATION": settings.WEIGHT_COORDINATION
        }

    def process(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        start_t = time.time()
        self.set_status("RUNNING", f"Ingesting correction on post #{str(feedback.get('post_id', 'unknown'))[:8]}")
        
        stored_fb = db.add_feedback(feedback)
        updated_weights = self._adjust_scoring_weights(feedback)
        
        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        self.total_processed += 1
        self.set_status("COMPLETED", f"Updated weights with label '{feedback.get('corrected_label')}'")
        
        self.log_memory({
            "action": "feedback_ingested",
            "post_id": feedback.get("post_id"),
            "corrected_label": feedback.get("corrected_label"),
            "updated_weights": updated_weights,
            "duration_ms": self.last_execution_time_ms
        })
        return {
            "status": "success",
            "message": "Feedback recorded. Model weights updated for retrain cycle.",
            "feedback": stored_fb,
            "active_weights": updated_weights
        }


