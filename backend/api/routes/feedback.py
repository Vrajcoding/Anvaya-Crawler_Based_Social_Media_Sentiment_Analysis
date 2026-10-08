import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from io import BytesIO
from storage.db_client import db_client

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("")
def submit_feedback(payload: dict):
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

    # Save to feedback log for training dataset
    db_client.add_feedback(payload)

    return {
        "status": "success",
        "message": "Officer feedback recorded for continuous fine-tuning dataset.",
        "payload": payload
    }

@router.get("/export-dataset")
def export_training_dataset():
    """
    Feature 4.4: Active Learning Loop.
    Exports all human-reviewed posts as a JSONL dataset for fine-tuning.
    """
    posts = db_client.get_posts(limit=5000)["items"]
    reviewed = [p for p in posts if p.get("human_reviewed")]
    
    output = ""
    for p in reviewed:
        sample = {
            "text": p.get("content", ""),
            "label_threat": p.get("threat_level", "Neutral"),
            "label_sentiment": p.get("sentiment", "neutral")
        }
        output += json.dumps(sample) + "\n"
        
    buffer = BytesIO(output.encode('utf-8'))
    return StreamingResponse(
        buffer, 
        media_type="application/jsonl",
        headers={"Content-Disposition": "attachment; filename=active_learning_dataset.jsonl"}
    )
