from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import datetime
from storage.db_client import db_client
from nlp_service.models.inference import run_nlp_pipeline
from pydantic import BaseModel, Field

router = APIRouter(prefix="/posts", tags=["posts"])

class CreatePostRequest(BaseModel):
    platform: str = Field(..., example="x")
    author_username: str = Field(..., example="@tester")
    content: str = Field(..., example="sample content")
    url: Optional[str] = Field(default="https://example.com/post/1")


@router.get("")
def get_posts(
    platform: Optional[str] = Query("all"),
    threat_level: Optional[str] = Query("all"),
    language: Optional[str] = Query("all"),
    query: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0)
):
    return db_client.get_posts(
        platform=platform,
        threat_level=threat_level,
        language=language,
        query=query,
        limit=limit,
        offset=offset
    )

@router.get("/{post_id}")
def get_post_detail(post_id: str):
    post = db_client.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.post("", status_code=201)
def create_post(payload: CreatePostRequest):
    post_data = payload.dict()
    post_id = f"post_{int(datetime.datetime.utcnow().timestamp()*1000)}"
    post_data["id"] = post_id
    
    nlp_res = run_nlp_pipeline(post_id=post_id, text=payload.content)
    post_data["nlp_analysis"] = nlp_res
    post_data["threat_level"] = nlp_res.get("threat_category", {}).get("label", "Neutral")
    post_data["sentiment"] = nlp_res.get("sentiment", {}).get("label", "neutral")
    post_data["is_hate_speech"] = nlp_res.get("hate_speech", {}).get("flag", False)
    post_data["crawled_at"] = datetime.datetime.utcnow().isoformat()

    db_client.save_post(post_data)
    return post_data

@router.post("/analyze")
def analyze_custom_text(payload: dict):
    text = payload.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text parameter is required")
        
    post_id = f"custom_{int(datetime.datetime.utcnow().timestamp()*1000)}"
    nlp_res = run_nlp_pipeline(post_id=post_id, text=text)
    
    raw_post = {
        "id": post_id,
        "platform": payload.get("platform", "x"),
        "author_username": payload.get("author", "@analyst_custom"),
        "content": text,
        "nlp_analysis": nlp_res,
        "threat_level": nlp_res.get("threat_category", {}).get("label", "Neutral"),
        "sentiment": nlp_res.get("sentiment", {}).get("label", "neutral"),
        "is_hate_speech": nlp_res.get("hate_speech", {}).get("flag", False),
        "requires_human_review": nlp_res.get("requires_human_review", False),
        "crawled_at": datetime.datetime.utcnow().isoformat()
    }
    db_client.save_post(raw_post)
    return raw_post
