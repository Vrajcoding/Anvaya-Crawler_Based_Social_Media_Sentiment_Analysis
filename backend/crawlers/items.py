from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SocialPostItem(BaseModel):
    id: Optional[str] = None
    platform: str
    author_username: str
    author_id: str
    content: str
    url: str
    hashtags: List[str] = []
    language: Optional[str] = None
    geo_location: Optional[Dict[str, Any]] = None
    engagement: Dict[str, int] = {"likes": 0, "shares": 0, "comments": 0}
    sentiment: Optional[Dict[str, Any]] = None
    threat_level: Optional[str] = None
    threat_score: Optional[float] = None
    is_hate_speech: bool = False
    is_bot: bool = False
    coordination_group: Optional[str] = None
    crawled_at: Optional[str] = None
    created_at: Optional[str] = None

class WatchlistItem(BaseModel):
    id: Optional[str] = None
    type: str  # keyword, hashtag, profile
    value: str
    platform: str = "all"
    geo_target: Optional[str] = None
    priority: str = "normal"  # high, normal, low
    active: bool = True
