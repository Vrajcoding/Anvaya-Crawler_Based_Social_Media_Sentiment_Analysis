from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class PostIn(BaseModel):
    post_id: str
    platform: str = "x"
    text: str
    language_hint: Optional[str] = None

class ClassificationOut(BaseModel):
    post_id: str
    sentiment: Dict[str, Any]
    threat_category: Dict[str, Any]
    hate_speech: Dict[str, Any]
    fake_news_signal: Dict[str, Any]
    language_detected: str
    requires_human_review: bool
    model_version: str
    processed_at: str
    inference_time_ms: Optional[float] = None

class BatchPostIn(BaseModel):
    posts: List[PostIn]

class BatchClassificationOut(BaseModel):
    results: List[ClassificationOut]
