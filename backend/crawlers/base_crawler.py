"""
base_crawler.py — Abstract base class and shared data model for SentinelAI v2.1 crawlers.
Defines the CrawlResult dataclass and BaseCrawler interface that all crawler implementations must satisfy.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


@dataclass
class EngagementMetrics:
    """Standardized engagement data returned by all crawlers."""
    likes: int = 0
    shares: int = 0
    comments: int = 0
    views: int = 0


@dataclass
class CrawlResult:
    """
    Standardized output object produced by every crawler (Scrapy, Playwright, or Hybrid).
    All downstream agents (NLP, Alert, Learning) consume this format.
    """
    id: str = ""
    platform: str = ""                    # "X", "YouTube", "Instagram", "GoogleSuggest", "Web"
    author_username: str = ""
    author_id: str = ""
    content: str = ""                     # Main post text / title / caption
    url: str = ""
    hashtags: List[str] = field(default_factory=list)
    language: str = "en"
    geo_location: Optional[Dict[str, Any]] = None
    engagement: EngagementMetrics = field(default_factory=EngagementMetrics)
    comments: List[Dict[str, str]] = field(default_factory=list)   # top comments
    thumbnail_url: str = ""
    source_type: str = "CRAWL"            # "SCRAPY", "PLAYWRIGHT", "REAL_WEB_CRAWL", etc.
    crawled_at: str = ""
    created_at: str = ""
    raw_meta: Dict[str, Any] = field(default_factory=dict)         # platform-specific extras

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dict compatible with the existing SocialPostItem schema."""
        return {
            "id": self.id,
            "platform": self.platform.lower(),
            "author_username": self.author_username,
            "author_id": self.author_id,
            "content": self.content,
            "url": self.url,
            "hashtags": self.hashtags,
            "language": self.language,
            "geo_location": self.geo_location,
            "engagement": {
                "likes": self.engagement.likes,
                "shares": self.engagement.shares,
                "comments": self.engagement.comments,
                "views": self.engagement.views,
            },
            "comments": self.comments,
            "thumbnail_url": self.thumbnail_url,
            "source_type": self.source_type,
            "crawled_at": self.crawled_at,
            "created_at": self.created_at,
        }


class BaseCrawler(ABC):
    """
    Abstract interface that every platform crawler must implement.
    Both ScrapyCrawler and PlaywrightCrawler extend this class.
    """

    @abstractmethod
    async def crawl(
        self,
        query: str,
        platform: str,
        limit: int = 20,
        fetch_comments: bool = False,
        time_filter: str = "any",
    ) -> List[CrawlResult]:
        """
        Execute a crawl for the given query on the specified platform.

        Args:
            query: Free-text search query or prompt
            platform: Target platform string (e.g. "X", "YouTube")
            limit: Maximum number of results to return
            fetch_comments: Whether to also fetch top comments for each post

        Returns:
            List of CrawlResult objects in standardised format
        """
        ...

    def supports_platform(self, platform: str) -> bool:
        """Return True if this crawler implementation handles the given platform."""
        return platform in self.supported_platforms()

    @abstractmethod
    def supported_platforms(self) -> List[str]:
        """Return the list of platform names this crawler handles."""
        ...
