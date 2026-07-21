import time
from typing import Dict, Any, Optional
from agents.base_agent import SentinelAgent
from storage.db_client import db
from utils.openrouter_client import openrouter_client
from utils.config import settings

class AlertAgent(SentinelAgent):
    """Hermes Agent responsible for threat threshold evaluation, alert generation & escalation dispatch using OpenRouter API."""
    
    def __init__(self):
        super().__init__("alert_agent", "Alert & Escalation Engine (OpenRouter Multi-Agent)")
        self.register_tool(
            name="evaluate_thresholds",
            func=self._check_thresholds,
            description="Evaluates if composite threat score and category exceed emergency action limits"
        )
        self.register_tool(
            name="dispatch_emergency",
            func=self._dispatch_summary,
            description="Generates 1-sentence urgent police dispatch summary using OpenRouter LLM"
        )

    def _check_thresholds(self, threat_level: str, score: float) -> bool:
        return threat_level in ["Incitement to Violence", "Fake News", "Inflammatory"] or score >= 0.70

    def _dispatch_summary(self, post: Dict[str, Any], threat_level: str, score: float) -> str:
        description = f"Detected high-severity {threat_level} threat on {post.get('platform', 'unknown').upper()}: '{post.get('content', '')[:80]}...'"
        if settings.OPENROUTER_API_KEY:
            prompt = f"""You are SentinelAI Emergency Alert Dispatch Agent (`{settings.AGENT_ALERT_MODEL}`).
Generate a 1-sentence urgent police dispatch description and threat assessment for duty officers regarding this detected post:
Platform: {post.get('platform')}
Author: {post.get('author_username')}
Threat Level: {threat_level} (Score: {score})
Content: "{post.get('content')}"

Return JSON with key: "dispatch_summary" (string, max 25 words, crisp and urgent)."""
            messages = [
                {"role": "system", "content": "You are a police emergency dispatch agent. Output JSON only."},
                {"role": "user", "content": prompt}
            ]
            ai_res = openrouter_client.chat_completion(
                messages=messages,
                model=settings.AGENT_ALERT_MODEL or "qwen/qwen-2.5-7b-instruct:free",
                temperature=0.1,
                max_tokens=150,
                response_format_json=True
            )
            if ai_res and isinstance(ai_res, dict) and ai_res.get("dispatch_summary"):
                description = f"[{settings.AGENT_ALERT_MODEL.split('/')[1].split(':')[0].upper()}] {ai_res.get('dispatch_summary')}"
        return description

    def process(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        start_t = time.time()
        threat_level = post.get("threat_level")
        score = post.get("threat_score", 0.0)
        
        self.set_status("RUNNING", f"Evaluating {post.get('id', 'unknown')[:8]} (Score: {score})")
        
        if self._check_thresholds(threat_level, score):
            severity = "CRITICAL" if score >= 0.85 else "HIGH"
            description = self._dispatch_summary(post, threat_level, score)

            alert = {
                "post_id": post.get("id"),
                "severity": severity,
                "threat_type": threat_level,
                "description": description,
                "status": "open"
            }
            created_alert = db.add_alert(alert)
            self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
            self.total_processed += 1
            self.set_status("COMPLETED", f"Triggered {severity} alert #{created_alert['id'][:8]}")
            self.log_memory({
                "action": "alert_triggered",
                "alert_id": created_alert["id"],
                "severity": created_alert["severity"],
                "duration_ms": self.last_execution_time_ms,
                "model": settings.AGENT_ALERT_MODEL
            })
            return created_alert
            
        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        self.set_status("IDLE", f"Post below alert threshold ({score} < 0.70)")
        return None


