from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from storage.db_client import db
from agents.orchestrator import orchestrator
from nlp.pipeline import nlp_pipeline

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("")
def get_posts(
    platform: Optional[str] = Query("all"),
    threat_level: Optional[str] = Query("all"),
    language: Optional[str] = Query("all"),
    query: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0)
):
    return db.get_posts(
        platform=platform,
        threat_level=threat_level,
        language=language,
        query=query,
        limit=limit,
        offset=offset
    )

@router.get("/{post_id}")
def get_post_detail(post_id: str):
    post = db.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.post("/analyze")
def analyze_custom_text(payload: dict):
    text = payload.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text parameter is required")
        
    raw_post = {
        "platform": payload.get("platform", "x"),
        "author_username": payload.get("author", "@analyst_custom"),
        "author_id": "usr_custom",
        "content": text,
        "url": "https://analyst.custom/input",
        "hashtags": [],
        "language": "en"
    }
    res = orchestrator.process_raw_post(raw_post)
    return res
