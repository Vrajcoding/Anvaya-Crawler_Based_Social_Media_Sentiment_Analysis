"""
analysis/trends.py — upgraded with real MAD z-score spike detection.
Delegates to analytics/spikes.py for real statistics.
"""

from typing import List, Dict, Any
from storage.db_client import db
from analytics.spikes import spike_detector


class TrendAnalyzer:
    """Spike and trend detector for regional keywords and hashtags (real MAD z-score)."""

    @staticmethod
    def get_trending_hashtags(top_n: int = 10) -> List[Dict[str, Any]]:
        posts = db.get_posts(limit=500)["items"]
        return spike_detector.get_trending_hashtags(posts, top_n=top_n)

    @staticmethod
    def get_trending_keywords(top_n: int = 10) -> List[Dict[str, Any]]:
        posts = db.get_posts(limit=500)["items"]
        return spike_detector.get_trending_keywords(posts, top_n=top_n)

    @staticmethod
    def get_volume_timeline(bucket_minutes: int = 30) -> List[Dict[str, Any]]:
        posts = db.get_posts(limit=500)["items"]
        return spike_detector.get_volume_timeline(posts, bucket_minutes=bucket_minutes)
