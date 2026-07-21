from fastapi import APIRouter
from typing import Dict, Any
from agents.learning_agent import LearningAgent

router = APIRouter(prefix="/feedback", tags=["feedback"])
learning_agent = LearningAgent()

@router.post("")
def submit_feedback(payload: Dict[str, Any]):
    return learning_agent.process(payload)
