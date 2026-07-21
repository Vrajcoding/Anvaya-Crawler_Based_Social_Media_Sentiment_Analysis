from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import SentinelAgent
from storage.db_client import db

class ReportAgent(SentinelAgent):
    """Hermes Agent generating formal Cyber Threat Intelligence (CTI) incident summaries."""
    
    def __init__(self):
        super().__init__("report_agent", "CTI Incident Report Generator")

    def generate_report(self, title: str, description: str, severity: str = "HIGH") -> Dict[str, Any]:
        posts = db.get_posts(limit=10)["items"]
        critical_posts = [p for p in posts if p.get("threat_score", 0) >= 0.70]
        
        report_content = f"""# 🛡️ SENTINEL AI — CYBER THREAT INTELLIGENCE REPORT
**Generated At:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Classification:** HIGHLY CONFIDENTIAL / LAW ENFORCEMENT ONLY
**Incident Title:** {title}
**Severity Level:** {severity}

## 1. Executive Summary
{description}

## 2. Threat Vector & Key Findings
- Total Monitored Posts in Window: {len(posts)}
- High/Critical Threat Flagged Posts: {len(critical_posts)}
- Predominant Languages: Gujarati, Hindi, Hinglish
- Bot Net Amplification Detected: {"YES" if any(p.get("is_bot") for p in posts) else "NO"}

## 3. Top Flagged Incident Posts
"""
        for i, p in enumerate(critical_posts[:5], 1):
            report_content += f"""
### Incident #{i}: [{p.get('threat_level')}] on {p.get('platform').upper()}
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
        self.log_memory({"action": "report_generated", "incident_id": saved_inc["id"]})
        return saved_inc
