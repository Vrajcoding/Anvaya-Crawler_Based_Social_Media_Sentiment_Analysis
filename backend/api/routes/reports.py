from fastapi import APIRouter
from typing import Dict, Any
from agents.report_agent import ReportAgent
from storage.db_client import db

router = APIRouter(prefix="/reports", tags=["reports"])
report_agent = ReportAgent()

@router.get("")
def get_incidents():
    return db.get_incidents()

@router.post("/generate")
def generate_report(payload: Dict[str, Any]):
    title = payload.get("title", "Social Media Threat Escalation Briefing")
    description = payload.get("description", "Automated threat intelligence incident report compiled by SentinelAI.")
    severity = payload.get("severity", "HIGH")
    return report_agent.generate_report(title, description, severity)
