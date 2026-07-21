from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from utils.config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])

class OpenRouterConfigPayload(BaseModel):
    api_key: Optional[str] = None
    agent_nlp_model: Optional[str] = None
    agent_threat_model: Optional[str] = None
    agent_report_model: Optional[str] = None
    agent_alert_model: Optional[str] = None
    use_real_crawler: Optional[bool] = None

@router.get("/openrouter")
def get_openrouter_settings():
    return {
        "api_key": settings.OPENROUTER_API_KEY,
        "base_url": settings.OPENROUTER_BASE_URL,
        "agent_nlp_model": settings.AGENT_NLP_MODEL,
        "agent_threat_model": settings.AGENT_THREAT_MODEL,
        "agent_report_model": settings.AGENT_REPORT_MODEL,
        "agent_alert_model": settings.AGENT_ALERT_MODEL,
        "use_real_crawler": settings.USE_REAL_CRAWLER,
        "status": "active" if settings.OPENROUTER_API_KEY else "disabled"
    }

@router.post("/openrouter")
def update_openrouter_settings(payload: OpenRouterConfigPayload):
    if payload.api_key is not None:
        settings.OPENROUTER_API_KEY = payload.api_key
    if payload.agent_nlp_model is not None:
        settings.AGENT_NLP_MODEL = payload.agent_nlp_model
    if payload.agent_threat_model is not None:
        settings.AGENT_THREAT_MODEL = payload.agent_threat_model
    if payload.agent_report_model is not None:
        settings.AGENT_REPORT_MODEL = payload.agent_report_model
    if payload.agent_alert_model is not None:
        settings.AGENT_ALERT_MODEL = payload.agent_alert_model
    if payload.use_real_crawler is not None:
        settings.USE_REAL_CRAWLER = payload.use_real_crawler
        
    return {
        "message": "OpenRouter & Multi-Agent settings updated successfully",
        "settings": {
            "api_key": settings.OPENROUTER_API_KEY[:12] + "..." if settings.OPENROUTER_API_KEY else "",
            "agent_nlp_model": settings.AGENT_NLP_MODEL,
            "agent_threat_model": settings.AGENT_THREAT_MODEL,
            "agent_report_model": settings.AGENT_REPORT_MODEL,
            "agent_alert_model": settings.AGENT_ALERT_MODEL,
            "use_real_crawler": settings.USE_REAL_CRAWLER
        }
    }
