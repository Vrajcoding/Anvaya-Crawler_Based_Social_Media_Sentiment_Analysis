import sys
import os
from typing import List
from fastapi import FastAPI, HTTPException

# Ensure path resolution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_service.schemas import PostIn, ClassificationOut, BatchPostIn, BatchClassificationOut
from nlp_service.models.inference import run_nlp_pipeline

app = FastAPI(
    title="SentinelAI NLP Threat & Sentiment Classification Service",
    description="Local-language NLP service for Gujarati, Hindi, Hinglish threat categorization and sentiment analysis.",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "nlp_threat_sentiment_service"}

@app.post("/classify", response_model=ClassificationOut)
async def classify_post(post: PostIn):
    try:
        res = run_nlp_pipeline(
            post_id=post.post_id,
            text=post.text,
            platform=post.platform,
            language_hint=post.language_hint
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/classify_batch", response_model=BatchClassificationOut)
async def classify_batch(batch: BatchPostIn):
    try:
        results = []
        for post in batch.posts:
            res = run_nlp_pipeline(
                post_id=post.post_id,
                text=post.text,
                platform=post.platform,
                language_hint=post.language_hint
            )
            results.append(res)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
