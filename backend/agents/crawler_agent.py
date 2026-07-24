import random
import time
from typing import Dict, Any, Optional, List
from agents.base_agent import SentinelAgent
from crawlers.hybrid_crawler import get_hybrid_crawler, ALL_PLATFORMS
from crawlers.spiders.synthetic_spider import SyntheticLiveCrawler
from crawlers.spiders.real_social_spider import RealSocialCrawler
from crawlers.spiders.x_crawler import XCrawler
from crawlers.spiders.instagram_crawler import InstagramCrawler
from crawlers.spiders.facebook_crawler import FacebookCrawler
from crawlers.spiders.youtube_crawler import YouTubeCrawler
from utils.config import settings

class CrawlerAgent(SentinelAgent):
    """Hermes Agent managing multi-platform social crawlers (X, YouTube, Instagram, Facebook, GoogleSuggest, Web),
    Watchlist targeting, and continuous ingestion schedules.
    """
    
    def __init__(self):
        super().__init__("crawler_agent", "Multi-Platform Scraper & Ingestion Scheduler")
        self.hybrid_crawler = get_hybrid_crawler()
        self.platform_crawlers = {
            "x": XCrawler,
            "instagram": InstagramCrawler,
            "facebook": FacebookCrawler,
            "youtube": YouTubeCrawler
        }
        self.round_robin_platforms = ["x", "instagram", "facebook", "youtube"]
        self._current_idx = 0

        # Register core Hermes execution tools
        self.register_tool(
            name="fetch_next_sample",
            func=self.fetch_next_sample,
            description="Harvests the next live post from target platform or round-robin schedule"
        )
        self.register_tool(
            name="crawl_prompt",
            func=self.crawl_prompt,
            description="Executes parallel multi-platform prompt crawl across X, YouTube, Instagram, GoogleSuggest, Web"
        )
        self.register_tool(
            name="crawl_account",
            func=self.crawl_account,
            description="Crawls posts, tweets, photos, and videos directly from a target user account handle/ID across X, Instagram, Facebook, and YouTube"
        )
        self.register_tool(
            name="add_to_watchlist",
            func=self.hybrid_crawler.add_to_watchlist,
            description="Registers search queries for continuous background crawler monitoring"
        )
        self.register_tool(
            name="get_crawler_status",
            func=self.hybrid_crawler.get_status,
            description="Returns health, active watchlists, uptime, and crawl counters"
        )

    def crawl_account(
        self,
        account_handle: str,
        platform: Optional[str] = "all",
        limit: int = 20
    ) -> Dict[str, Any]:
        """Harvests posts explicitly published by or targeting a specific user handle/account ID."""
        start_t = time.time()
        clean_handle = account_handle.strip()
        if not clean_handle.startswith("@"):
            clean_handle = f"@{clean_handle}"

        self.set_status("RUNNING", f"Harvesting account '{clean_handle}' on platform '{platform}'")
        target_platforms = [platform.lower()] if platform and platform.lower() in self.platform_crawlers else self.round_robin_platforms

        posts = []
        for p in target_platforms:
            crawler_cls = self.platform_crawlers[p]
            for _ in range(min(limit, 5)):
                try:
                    post = crawler_cls.get_next_post(clean_handle)
                    post["author_username"] = clean_handle
                    posts.append(post)
                except Exception as e:
                    self.log_memory({"action": "account_crawl_error", "error": str(e), "platform": p})

        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        self.total_processed += len(posts)
        self.set_status("COMPLETED", f"Harvested {len(posts)} posts for account '{clean_handle}'")
        self.log_memory({
            "action": "account_crawl",
            "account_handle": clean_handle,
            "platform": platform,
            "posts_harvested": len(posts),
            "duration_ms": self.last_execution_time_ms
        })
        return {
            "account_handle": clean_handle,
            "platform": platform,
            "count": len(posts),
            "duration_ms": self.last_execution_time_ms,
            "posts": posts
        }


    def fetch_next_sample(self, target_platform: Optional[str] = None) -> Dict[str, Any]:
        """Harvests the next live post from target platform or round-robin schedule."""
        start_t = time.time()
        platform = target_platform
        if not platform or platform == "all" or platform.lower() not in self.platform_crawlers:
            platform = self.round_robin_platforms[self._current_idx % len(self.round_robin_platforms)]
            self._current_idx += 1
        else:
            platform = platform.lower()
            
        crawler_cls = self.platform_crawlers[platform]
        try:
            post = crawler_cls.get_next_post()
            self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
            self.total_processed += 1
            self.set_status("COMPLETED", f"Harvested post from {platform.upper()}")
            self.log_memory({
                "action": "crawled_post",
                "post_id": post.get("id"),
                "platform": post.get("platform"),
                "source": post.get("source_type", f"{platform.upper()}_CRAWLER"),
                "duration_ms": self.last_execution_time_ms
            })
            return post
        except Exception as e:
            self.log_memory({"action": "crawl_fallback", "error": str(e), "platform": platform})
            if settings.USE_REAL_CRAWLER:
                post = RealSocialCrawler.get_next_crawled_post()
            else:
                post = SyntheticLiveCrawler.crawl_next_batch()
            self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
            self.total_processed += 1
            self.set_status("COMPLETED", f"Harvested fallback post for {platform.upper()}")
            return post

    def crawl_prompt(
        self,
        prompt: str,
        platforms: Optional[List[str]] = None,
        limit: int = 20,
        fetch_comments: bool = False
    ) -> Dict[str, Any]:
        """Runs parallel multi-platform prompt crawl via HybridCrawler."""
        start_t = time.time()
        self.set_status("RUNNING", f"Crawling prompt '{prompt[:25]}...' on {len(platforms or ALL_PLATFORMS)} platforms")
        result = self.invoke_tool(
            "crawl_multi_platform", # will be handled if using hybrid_crawler directly or fallback
            queries=[prompt],
            platforms=platforms or ALL_PLATFORMS,
            limit=limit,
            fetch_comments=fetch_comments
        ) if "crawl_multi_platform" in self.tools else None
        
        if not result:
            # Direct invocation if not registered in self.tools
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
            result = loop.run_until_complete(
                self.hybrid_crawler.crawl_multi_platform(
                    queries=[prompt],
                    platforms=platforms or ALL_PLATFORMS,
                    limit=limit,
                    fetch_comments=fetch_comments
                )
            )

        self.last_execution_time_ms = round((time.time() - start_t) * 1000, 2)
        total_posts = result.get("total_posts", 0)
        self.total_processed += total_posts
        self.set_status("COMPLETED", f"Crawled {total_posts} posts for '{prompt[:25]}...'")
        self.log_memory({
            "action": "prompt_crawl",
            "prompt": prompt,
            "total_posts": total_posts,
            "duration_ms": self.last_execution_time_ms
        })
        return result

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target_platform = payload.get("platform")
        prompt = payload.get("prompt")
        if prompt:
            return self.crawl_prompt(
                prompt=prompt,
                platforms=payload.get("platforms"),
                limit=payload.get("limit", 20),
                fetch_comments=payload.get("fetch_comments", False)
            )
        post = self.fetch_next_sample(target_platform)
        return post



