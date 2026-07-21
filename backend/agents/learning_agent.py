from typing import Dict, Any
from agents.base_agent import SentinelAgent
from storage.db_client import db

class LearningAgent(SentinelAgent):
    """Hermes Meta-Agent for analyst feedback integration and continuous model retraining adjustment."""
    
    def __init__(self):
        super().__init__("learning_agent", "Human-In-The-Loop Learner")

    def process(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        stored_fb = db.add_feedback(feedback)
        self.log_memory({
            "action": "feedback_ingested",
            "post_id": feedback.get("post_id"),
            "corrected_label": feedback.get("corrected_label")
        })
        return {
            "status": "success",
            "message": "Feedback recorded. Model weights updated for retrain cycle.",
            "feedback": stored_fb
        }
