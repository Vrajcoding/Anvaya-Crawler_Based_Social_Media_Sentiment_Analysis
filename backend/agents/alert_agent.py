from typing import Dict, Any, Optional
from agents.base_agent import SentinelAgent
from storage.db_client import db

class AlertAgent(SentinelAgent):
    """Hermes Agent responsible for threat threshold evaluation, alert generation & escalation dispatch."""
    
    def __init__(self):
        super().__init__("alert_agent", "Alert & Escalation Engine")

    def process(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        threat_level = post.get("threat_level")
        score = post.get("threat_score", 0.0)
        
        if threat_level in ["Incitement to Violence", "Fake News", "Inflammatory"] or score >= 0.70:
            alert = {
                "post_id": post.get("id"),
                "severity": "CRITICAL" if score >= 0.85 else "HIGH",
                "threat_type": threat_level,
                "description": f"Detected high-severity {threat_level} threat on {post.get('platform').upper()}: '{post.get('content')[:80]}...'",
                "status": "open"
            }
            created_alert = db.add_alert(alert)
            self.log_memory({"action": "alert_triggered", "alert_id": created_alert["id"], "severity": created_alert["severity"]})
            return created_alert
            
        return None
