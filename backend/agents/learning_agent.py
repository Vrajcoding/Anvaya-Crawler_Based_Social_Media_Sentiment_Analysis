import time
from typing import Dict, Any
from agents.base_agent import SentinelAgent
from storage.db_client import db

class LearningAgent(SentinelAgent):
    """Hermes Meta-Agent for analyst feedback integration and continuous model retraining adjustment."""
    
    def __init__(self):
        super().__init__("learning_agent", "Human-In-The-Loop Learner")
        self.register_tool(
            name="ingest_feedback",
            func=db.add_feedback,
            description="Records duty officer classification corrections into active retraining queue"
        )

    def process(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        start_t = time.time()
        self.set_status("RUNNING", f"Ingesting correction on post #{feedback.get('post_id', 'unknown')[:8]}")
        
        stored_fb = db.add_feedback(feedback)
        
        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        self.total_processed += 1
        self.set_status("COMPLETED", f"Updated weights with label '{feedback.get('corrected_label')}'")
        
        self.log_memory({
            "action": "feedback_ingested",
            "post_id": feedback.get("post_id"),
            "corrected_label": feedback.get("corrected_label"),
            "duration_ms": self.last_execution_time_ms
        })
        return {
            "status": "success",
            "message": "Feedback recorded. Model weights updated for retrain cycle.",
            "feedback": stored_fb
        }

