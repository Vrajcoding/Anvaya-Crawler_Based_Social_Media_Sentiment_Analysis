from typing import List, Dict, Any
from storage.db_client import db

class WatchlistManager:
    """Manages active search terms, regional hashtags, and social profile watchlists."""
    
    @staticmethod
    def get_active_keywords() -> List[str]:
        items = db.get_watchlist()
        return [i["value"] for i in items if i.get("type") == "keyword" and i.get("active")]

    @staticmethod
    def get_active_hashtags() -> List[str]:
        items = db.get_watchlist()
        return [i["value"] for i in items if i.get("type") == "hashtag" and i.get("active")]

    @staticmethod
    def get_active_profiles() -> List[str]:
        items = db.get_watchlist()
        return [i["value"] for i in items if i.get("type") == "profile" and i.get("active")]
