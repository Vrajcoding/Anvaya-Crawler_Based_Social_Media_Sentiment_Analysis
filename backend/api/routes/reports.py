from fastapi import APIRouter
from typing import Dict, Any
from agents.orchestrator import orchestrator
from storage.db_client import db

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("")
def get_incidents():
    return db.get_incidents()

@router.post("/generate")
def generate_report(payload: Dict[str, Any]):
    return orchestrator.report_agent.process(payload)

