from fastapi import APIRouter
from typing import Dict, Any
from agents.orchestrator import orchestrator

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("")
def submit_feedback(payload: Dict[str, Any]):
    return orchestrator.learning_agent.process(payload)

