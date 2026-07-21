import random
from typing import Dict, Any, Optional
from agents.base_agent import SentinelAgent
from crawlers.spiders.synthetic_spider import SyntheticLiveCrawler
from crawlers.spiders.real_social_spider import RealSocialCrawler
from crawlers.spiders.x_crawler import XCrawler
from crawlers.spiders.instagram_crawler import InstagramCrawler
from crawlers.spiders.facebook_crawler import FacebookCrawler
from crawlers.spiders.youtube_crawler import YouTubeCrawler
from utils.config import settings

class CrawlerAgent(SentinelAgent):
    """Hermes Agent managing multi-platform social crawlers (X, Instagram, Facebook, YouTube),
    Watchlist targeting, and continuous ingestion schedules.
    """
    
    def __init__(self):
        super().__init__("crawler_agent", "Multi-Platform Scraper & Ingestion Scheduler")
        self.platform_crawlers = {
            "x": XCrawler,
            "instagram": InstagramCrawler,
            "facebook": FacebookCrawler,
            "youtube": YouTubeCrawler
        }
        self.round_robin_platforms = ["x", "instagram", "facebook", "youtube"]
        self._current_idx = 0

    def fetch_next_sample(self, target_platform: Optional[str] = None) -> Dict[str, Any]:
        """Harvests the next live post from target platform or round-robin schedule."""
        platform = target_platform
        if not platform or platform == "all" or platform not in self.platform_crawlers:
            platform = self.round_robin_platforms[self._current_idx % len(self.round_robin_platforms)]
            self._current_idx += 1
            
        crawler_cls = self.platform_crawlers[platform]
        try:
            post = crawler_cls.get_next_post()
            self.log_memory({
                "action": "crawled_post",
                "post_id": post.get("id"),
                "platform": post.get("platform"),
                "source": post.get("source_type", f"{platform.upper()}_CRAWLER")
            })
            return post
        except Exception as e:
            # Fallback to general hybrid spider if platform crawler hits transient network error
            self.log_memory({"action": "crawl_fallback", "error": str(e), "platform": platform})
            if settings.USE_REAL_CRAWLER:
                return RealSocialCrawler.get_next_crawled_post()
            return SyntheticLiveCrawler.crawl_next_batch()

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target_platform = payload.get("platform")
        post = self.fetch_next_sample(target_platform)
        return post


