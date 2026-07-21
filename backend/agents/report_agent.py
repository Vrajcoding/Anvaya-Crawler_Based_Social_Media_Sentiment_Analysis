import time
from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import SentinelAgent
from storage.db_client import db
from utils.openrouter_client import openrouter_client
from utils.config import settings

class ReportAgent(SentinelAgent):
    """Hermes Agent generating formal Cyber Threat Intelligence (CTI) incident summaries using OpenRouter API."""
    
    def __init__(self):
        super().__init__("report_agent", "CTI Incident Report Generator (OpenRouter Multi-Agent)")
        self.register_tool(
            name="compile_incident_report",
            func=self.generate_report,
            description="Synthesizes critical threat data into formal law enforcement incident briefs"
        )

    def generate_report(self, title: str, description: str, severity: str = "HIGH") -> Dict[str, Any]:
        start_t = time.time()
        self.set_status("RUNNING", f"Synthesizing CTI briefing: '{title[:30]}...'")
        
        posts = db.get_posts(limit=15)["items"]
        critical_posts = [p for p in posts if p.get("threat_score", 0) >= 0.70]
        
        # OpenRouter AI Synthesis if available
        ai_summary = ""
        ai_recommendations = ""
        if settings.OPENROUTER_API_KEY and critical_posts:
            post_snippets = "\n".join([f"- [{p.get('threat_level')}] on {p.get('platform', 'unknown').upper()}: \"{p.get('content', '')[:120]}\"" for p in critical_posts[:6]])
            prompt = f"""You are SentinelAI Report Agent (`{settings.AGENT_REPORT_MODEL}`), drafting an official Cyber Threat Intelligence & Police Incident Briefing for the Home Department, Gujarat & National Cyber Control Room (Helpline 1930).
Incident Title: {title}
Severity: {severity}
Description: {description}

Flagged Critical Posts:
{post_snippets}

Provide valid JSON with two strings:
- "executive_synthesis": A 3-sentence professional police intelligence analysis summarizing the tactical threat situation.
- "actionable_recommendations": 3 specific tactical actions for cyber cell officers and field police to mitigate the threat.
"""
            messages = [
                {"role": "system", "content": "You are a senior law enforcement intelligence officer synthesizing CTI reports. Output strict JSON."},
                {"role": "user", "content": prompt}
            ]
            ai_res = openrouter_client.chat_completion(
                messages=messages,
                model=settings.AGENT_REPORT_MODEL or "deepseek/deepseek-chat:free",
                temperature=0.2,
                max_tokens=700,
                response_format_json=True
            )
            if ai_res and isinstance(ai_res, dict):
                ai_summary = ai_res.get("executive_synthesis", "")
                ai_recommendations = ai_res.get("actionable_recommendations", "")

        report_content = f"""# 🛡️ SENTINEL AI — CYBER THREAT INTELLIGENCE REPORT
**Generated At:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**AI Synthesis Agent:** `{settings.AGENT_REPORT_MODEL}` (OpenRouter Multi-Agent)
**Classification:** HIGHLY CONFIDENTIAL / LAW ENFORCEMENT ONLY
**Incident Title:** {title}
**Severity Level:** {severity}

## 1. Executive Summary
{ai_summary or description}

## 2. Tactical Recommendations & Action Plan
{ai_recommendations or "- Immediately alert local jurisdiction police control room.\n- Issue formal advisory combating rumor spread on social media.\n- Coordinate with platform nodes (X, Facebook, Telegram) to take down inflammatory URLs."}

## 3. Threat Vector & Key Metrics
- Total Monitored Posts in Window: {len(posts)}
- High/Critical Threat Flagged Posts: {len(critical_posts)}
- Predominant Languages: Gujarati (`gu`), Hindi (`hi`), English (`en`), Hinglish
- Bot Net Amplification Detected: {"YES" if any(p.get("is_bot") for p in posts) else "NO"}

## 4. Top Flagged Incident Posts
"""
        for i, p in enumerate(critical_posts[:5], 1):
            report_content += f"""
### Incident #{i}: [{p.get('threat_level')}] on {p.get('platform', 'unknown').upper()}
- **Author:** {p.get('author_username')}
- **Location:** {p.get('geo_location', {}).get('city', 'Unknown')}
- **Content:** "{p.get('content')}"
- **Threat Score:** {p.get('threat_score')} / 1.0
- **URL:** {p.get('url')}
"""

        incident = {
            "title": title,
            "description": description,
            "severity": severity,
            "status": "open",
            "report_md": report_content,
            "created_at": datetime.utcnow().isoformat()
        }
        
        saved_inc = db.add_incident(incident)
        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        self.total_processed += 1
        self.set_status("COMPLETED", f"Generated incident report #{saved_inc['id'][:8]}")
        
        self.log_memory({"action": "report_generated", "incident_id": saved_inc["id"], "ai_model": settings.AGENT_REPORT_MODEL, "duration_ms": self.last_execution_time_ms})
        return saved_inc

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.generate_report(
            title=payload.get("title", "CTI Summary"),
            description=payload.get("description", "Routine briefing"),
            severity=payload.get("severity", "HIGH")
        )


