from typing import Dict, Any
from agents.base_agent import SentinelAgent
from crawlers.spiders.synthetic_spider import SyntheticLiveCrawler

class CrawlerAgent(SentinelAgent):
    """Hermes Agent managing dynamic crawl targets, Watchlist prioritization, and continuous ingestion."""
    
    def __init__(self):
        super().__init__("crawler_agent", "Ingestion & Scraper Scheduler")

    def fetch_next_sample(self) -> Dict[str, Any]:
        post = SyntheticLiveCrawler.crawl_next_batch()
        return post

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        post = SyntheticLiveCrawler.crawl_next_batch()
        self.log_memory({"action": "crawled_post", "post_id": post["id"], "platform": post["platform"]})
        return post
