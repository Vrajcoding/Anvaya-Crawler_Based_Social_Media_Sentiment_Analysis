from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from agents.orchestrator import orchestrator

router = APIRouter(prefix="/agents", tags=["Hermes Multi-Agent Telemetry"])

@router.get("/status", summary="Get status and registered tools of all Hermes agents")
async def get_agents_status() -> Dict[str, Any]:
    """Returns real-time telemetry, execution latency, and registered tools for all 6 Hermes Agents."""
    agents_summary = orchestrator.get_all_agents_status()
    active_count = sum(1 for a in agents_summary if a["active"])
    
    return {
        "status": "success",
        "total_agents": len(agents_summary),
        "active_agents": active_count,
        "agents": agents_summary,
        "pipeline_stages": [
            {"stage": "1. Ingestion", "agent": "crawler_agent", "platforms": ["X", "Instagram", "Facebook", "YouTube"]},
            {"stage": "2. NLP & Classification", "agent": "nlp_classifier_agent", "models": ["OpenRouter Multi-Agent", "LanguageDetector", "ThreatScorer"]},
            {"stage": "3. Graph Analysis", "agent": "network_agent", "capabilities": ["Bot Cluster Detection", "Coordination Mapping"]},
            {"stage": "4. Alert & Dispatch", "agent": "alert_agent", "capabilities": ["Threshold Evaluation", "Urgent Police Summary"]},
            {"stage": "5. Feedback & Retraining", "agent": "learning_agent", "capabilities": ["Duty Officer Loop", "Model Weight Update"]},
            {"stage": "6. Briefing Synthesis", "agent": "report_agent", "capabilities": ["Formal CTI Reports", "Executive Synthesis"]}
        ]
    }

@router.post("/trigger_crawl", summary="Manually trigger Hermes Crawler Agent for a platform")
async def trigger_platform_crawl(payload: Dict[str, Optional[str]] = None) -> Dict[str, Any]:
    """Triggers the Hermes multi-agent pipeline on a fresh post crawled from target platform."""
    platform = payload.get("platform") if payload else None
    result = orchestrator.trigger_live_crawl_step(platform)
    return {
        "status": "success",
        "message": f"Processed post #{result['post']['id'][:8]} through 6-agent Hermes pipeline",
        "post": result["post"],
        "alert": result["alert"]
    }
