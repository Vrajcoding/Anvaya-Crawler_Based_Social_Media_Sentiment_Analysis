from fastapi import APIRouter
from typing import Dict, Any
import datetime
from storage.db_client import db_client

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("")
def submit_feedback(payload: Dict[str, Any]):
    post_id = payload.get("post_id")
    corrected_sentiment = payload.get("corrected_sentiment")
    corrected_threat = payload.get("corrected_threat_level")
    
    if post_id:
        post = db_client.get_post_by_id(post_id)
        if post:
            if corrected_sentiment:
                post["sentiment"] = corrected_sentiment
            if corrected_threat:
                post["threat_level"] = corrected_threat
            post["human_reviewed"] = True
            db_client.save_post(post)

    return {
        "status": "success",
        "message": "Officer feedback recorded for continuous fine-tuning dataset.",
        "received_at": datetime.datetime.utcnow().isoformat(),
        "payload": payload
    }
