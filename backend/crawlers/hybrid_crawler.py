"""
hybrid_crawler.py — HybridCrawler v2.0 Orchestrator (SentinelAI v2.1)

Intelligently routes each platform to the correct underlying crawler
(ScrapyCrawler for fast/lightweight, PlaywrightCrawler for JS-heavy)
and runs all platform crawls IN PARALLEL via asyncio.gather().

Also manages the in-memory watchlist for continuous monitoring queries.
"""
from __future__ import annotations

import asyncio
import datetime
import time
import uuid
from typing import Any, Dict, List, Optional

from crawlers.base_crawler import CrawlResult
from crawlers.scrapy_crawler import ScrapyCrawler
from crawlers.playwright_crawler import PlaywrightCrawler

# ── Platform → Crawler routing map ──────────────────────────────────────────
#   "fast"  → ScrapyCrawler (httpx-based, no browser)
#   "js"    → PlaywrightCrawler (headless Chromium)

PLATFORM_ROUTING: Dict[str, str] = {
    "X":             "fast",
    "GoogleSuggest": "fast",
    "Web":           "fast",
    "YouTube":       "js",
    "Instagram":     "js",
}

ALL_PLATFORMS = list(PLATFORM_ROUTING.keys())

# ── In-memory watchlist store ────────────────────────────────────────────────
_watchlist: Dict[str, Dict[str, Any]] = {}

# ── Global stat counters ─────────────────────────────────────────────────────
_stats = {
    "total_posts_crawled": 0,
    "total_crawl_calls": 0,
    "last_crawl_ts": None,
    "start_time": time.time(),
}


class HybridCrawler:
    """
    Central v2.1 crawl orchestrator.

    Usage:
        crawler = HybridCrawler()
        results = await crawler.crawl_multi_platform(
            queries=["cjp protest india"],
            platforms=["X", "YouTube", "GoogleSuggest"],
            limit=50,
            fetch_comments=True,
        )
    """

    def __init__(self):
        self._scrapy = ScrapyCrawler()
        self._playwright = PlaywrightCrawler()

    def _get_crawler(self, platform: str):
        """Return the correct crawler instance for the given platform."""
        mode = PLATFORM_ROUTING.get(platform, "fast")
        return self._scrapy if mode == "fast" else self._playwright

    # ── Single platform ──────────────────────────────────────────────────────

    async def crawl_platform(
        self,
        query: str,
        platform: str,
        limit: int = 20,
        fetch_comments: bool = False,
    ) -> Dict[str, Any]:
        """Crawl a single platform and return a result summary dict."""
        crawler = self._get_crawler(platform)
        start = time.monotonic()
        try:
            posts: List[CrawlResult] = await crawler.crawl(
                query=query,
                platform=platform,
                limit=limit,
                fetch_comments=fetch_comments,
            )
        except Exception as e:
            print(f"[HybridCrawler] {platform} crawl failed: {e}")
            posts = []

        elapsed = round(time.monotonic() - start, 2)
        _stats["total_posts_crawled"] += len(posts)

        return {
            "status": "success" if posts else "no_results",
            "platform": platform,
            "count": len(posts),
            "duration_s": elapsed,
            "posts": [p.to_dict() for p in posts],
        }

    # ── Multi-platform parallel ──────────────────────────────────────────────

    async def crawl_multi_platform(
        self,
        queries: List[str],
        platforms: Optional[List[str]] = None,
        limit: int = 20,
        fetch_comments: bool = False,
    ) -> Dict[str, Any]:
        """
        Crawl all specified platforms IN PARALLEL using asyncio.gather().

        Args:
            queries:        List of query strings (first one used as main query)
            platforms:      Platforms to crawl; defaults to ALL_PLATFORMS
            limit:          Max posts per platform
            fetch_comments: Whether to fetch top comments

        Returns:
            Aggregated result dict with per-platform breakdowns
        """
        if platforms is None:
            platforms = ALL_PLATFORMS

        # Validate platforms
        valid_platforms = [p for p in platforms if p in PLATFORM_ROUTING]
        if not valid_platforms:
            return {"error": "No valid platforms specified", "results": {}}

        query = queries[0] if queries else ""
        global_start = time.monotonic()

        # Fire all platform crawls in parallel
        tasks = [
            self.crawl_platform(query, platform, limit, fetch_comments)
            for platform in valid_platforms
        ]
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)

        total_elapsed = round(time.monotonic() - global_start, 2)
        _stats["total_crawl_calls"] += 1
        _stats["last_crawl_ts"] = datetime.datetime.utcnow().isoformat()

        results: Dict[str, Any] = {}
        total_posts = 0
        for platform, result in zip(valid_platforms, platform_results):
            if isinstance(result, Exception):
                results[platform] = {"status": "error", "error": str(result), "posts": []}
            else:
                results[platform] = result
                total_posts += result.get("count", 0)

        return {
            "query": query,
            "platforms_crawled": len(valid_platforms),
            "total_posts": total_posts,
            "duration_s": total_elapsed,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "results": results,
        }

    # ── Watchlist management ─────────────────────────────────────────────────

    def add_to_watchlist(
        self,
        query: str,
        platforms: List[str],
        frequency_minutes: int = 15,
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """Add a query to the in-memory watchlist for continuous monitoring."""
        wl_id = f"wl_{uuid.uuid4().hex[:8]}"
        _watchlist[wl_id] = {
            "watchlist_id": wl_id,
            "query": query,
            "platforms": platforms,
            "frequency_minutes": frequency_minutes,
            "priority": priority,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "last_run": None,
            "active": True,
        }
        return {
            "status": "success",
            "watchlist_id": wl_id,
            "message": f"Query added. Will crawl every {frequency_minutes} minutes.",
        }

    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Return all active watchlist entries."""
        return [v for v in _watchlist.values() if v.get("active")]

    # ── Status ───────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Return crawler health statistics."""
        uptime = int(time.time() - _stats["start_time"])
        return {
            "status": "active",
            "crawler_type": "HybridCrawler v2.0",
            "active_watchlists": len(self.get_watchlist()),
            "total_posts_crawled": _stats["total_posts_crawled"],
            "total_crawl_calls": _stats["total_crawl_calls"],
            "last_crawl": _stats["last_crawl_ts"],
            "platforms_enabled": ALL_PLATFORMS,
            "uptime_seconds": uptime,
        }


# ── Global singleton ─────────────────────────────────────────────────────────
_hybrid_crawler_instance: Optional[HybridCrawler] = None


def get_hybrid_crawler() -> HybridCrawler:
    """Return the shared HybridCrawler singleton (lazy init)."""
    global _hybrid_crawler_instance
    if _hybrid_crawler_instance is None:
        _hybrid_crawler_instance = HybridCrawler()
    return _hybrid_crawler_instance
