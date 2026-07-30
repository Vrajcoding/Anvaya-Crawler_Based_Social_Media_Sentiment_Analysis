from fastapi import APIRouter
from typing import Dict, Any
import datetime
from storage.db_client import db_client

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("")
def get_incidents():
    return db_client.get_incidents()

@router.post("/generate")
def generate_report(payload: Dict[str, Any]):
    incidents = db_client.get_incidents()
    posts = db_client.get_posts()
    return {
        "status": "success",
        "report_id": f"rep_{int(datetime.datetime.utcnow().timestamp())}",
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "summary": "Buildspec NLP Threat & Sentiment Report",
        "total_posts_analyzed": len(posts),
        "total_incidents": len(incidents),
        "incidents": incidents
    }
