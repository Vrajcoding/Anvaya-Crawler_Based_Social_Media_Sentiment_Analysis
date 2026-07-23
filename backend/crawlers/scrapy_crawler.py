"""
scrapy_crawler.py — Lightweight httpx/BeautifulSoup-based crawler for:
  • X / Twitter      — via nitter RSS mirrors + public search
  • GoogleSuggest    — via Google autocomplete JSON API (no auth)
  • Web              — via DuckDuckGo HTML scrape

No Scrapy framework dependency needed — named "scrapy" to follow the v2.1 architecture
naming convention distinguishing fast (this) from Playwright (browser) crawlers.
"""
from __future__ import annotations
import asyncio
import datetime
import hashlib
import re
import uuid
from typing import Any, Dict, List
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from crawlers.base_crawler import BaseCrawler, CrawlResult, EngagementMetrics
from crawlers.rate_limiters import get_limiter

# ── Nitter instances (public X mirrors, no API key) ─────────────────────────
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]


class ScrapyCrawler(BaseCrawler):
    """
    Fast, httpx-based crawler for X (via nitter), GoogleSuggest, and Web.
    No API tokens required — uses public endpoints only.
    """

    SUPPORTED = ["X", "GoogleSuggest", "Web"]

    def supported_platforms(self) -> List[str]:
        return self.SUPPORTED

    # ── Dispatcher ──────────────────────────────────────────────────────────

    async def crawl(
        self,
        query: str,
        platform: str,
        limit: int = 20,
        fetch_comments: bool = False,
    ) -> List[CrawlResult]:
        limiter = get_limiter(platform)
        await limiter.acquire()

        if platform == "X":
            return await self._crawl_x(query, limit)
        elif platform == "GoogleSuggest":
            return await self._crawl_google_suggest(query, limit)
        elif platform == "Web":
            return await self._crawl_web(query, limit)
        return []

    # ── X / Twitter (via Nitter RSS) ────────────────────────────────────────

    async def _crawl_x(self, query: str, limit: int) -> List[CrawlResult]:
        """Fetch tweets via nitter's RSS search endpoint."""
        results: List[CrawlResult] = []
        encoded = quote_plus(query)

        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "SentinelAI-Crawler/2.1 (research)"},
        ) as client:
            for base in NITTER_INSTANCES:
                try:
                    url = f"{base}/search/rss?q={encoded}&f=tweets"
                    resp = await client.get(url)
                    if resp.status_code == 200 and "<rss" in resp.text:
                        results = self._parse_nitter_rss(resp.text, limit)
                        if results:
                            break
                except Exception:
                    continue  # try next mirror

        # Fallback: return synthetic-style stubs so dashboard is never empty
        if not results:
            results = self._synthetic_x_stubs(query, limit)

        return results[:limit]

    def _parse_nitter_rss(self, xml_text: str, limit: int) -> List[CrawlResult]:
        soup = BeautifulSoup(xml_text, "xml")
        items = soup.find_all("item")[:limit]
        results = []
        for item in items:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            creator = item.find("dc:creator") or item.find("creator")

            text = title.text if title else ""
            post_url = link.text if link else ""
            author = creator.text.strip() if creator else "@unknown"
            ts = pub_date.text if pub_date else datetime.datetime.utcnow().isoformat()

            hashtags = re.findall(r"#(\w+)", text)
            post_id = hashlib.md5(post_url.encode()).hexdigest()[:12]

            results.append(CrawlResult(
                id=f"x-{post_id}",
                platform="X",
                author_username=author if author.startswith("@") else f"@{author}",
                author_id=f"usr_{post_id[:8]}",
                content=text[:400],
                url=post_url,
                hashtags=hashtags,
                language="en",
                engagement=EngagementMetrics(likes=0, shares=0, comments=0),
                source_type="SCRAPY_NITTER",
                crawled_at=datetime.datetime.utcnow().isoformat(),
                created_at=ts,
            ))
        return results

    def _synthetic_x_stubs(self, query: str, limit: int) -> List[CrawlResult]:
        """Fallback stubs when all nitter mirrors fail."""
        stubs = []
        topics = query.split()[:3]
        for i in range(min(limit, 5)):
            uid = uuid.uuid4().hex[:8]
            stubs.append(CrawlResult(
                id=f"x-stub-{uid}",
                platform="X",
                author_username=f"@monitor_{uid[:5]}",
                author_id=f"usr_{uid}",
                content=f"[Simulated] Monitoring topic: {query} — post #{i+1}",
                url=f"https://x.com/search?q={quote_plus(query)}",
                hashtags=[t.strip("#.,") for t in topics],
                language="en",
                source_type="SCRAPY_STUB",
                crawled_at=datetime.datetime.utcnow().isoformat(),
                created_at=datetime.datetime.utcnow().isoformat(),
            ))
        return stubs

    # ── Google Suggest ───────────────────────────────────────────────────────

    async def _crawl_google_suggest(self, query: str, limit: int) -> List[CrawlResult]:
        """
        Fetch Google autocomplete suggestions. Returns up to `limit` items.
        Endpoint: https://suggestqueries.google.com/complete/search?client=firefox&q=…
        Returns JSON array: ["query", ["sug1", "sug2", ...], ...]
        """
        encoded = quote_plus(query)
        url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={encoded}&hl=en"
        results: List[CrawlResult] = []

        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    suggestions = data[1] if len(data) > 1 else []
                    for sug in suggestions[:limit]:
                        sid = hashlib.md5(sug.encode()).hexdigest()[:10]
                        results.append(CrawlResult(
                            id=f"gs-{sid}",
                            platform="GoogleSuggest",
                            author_username="@google_suggest",
                            author_id="google_autocomplete",
                            content=sug,
                            url=f"https://www.google.com/search?q={quote_plus(sug)}",
                            hashtags=[],
                            language="en",
                            source_type="SCRAPY_GOOGLE_SUGGEST",
                            crawled_at=datetime.datetime.utcnow().isoformat(),
                            created_at=datetime.datetime.utcnow().isoformat(),
                        ))
            except Exception as e:
                print(f"[ScrapyCrawler] GoogleSuggest error: {e}")

        return results[:limit]

    # ── Generic Web (DuckDuckGo HTML) ────────────────────────────────────────

    async def _crawl_web(self, query: str, limit: int) -> List[CrawlResult]:
        """Scrape DuckDuckGo HTML results (no API key needed)."""
        encoded = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        results: List[CrawlResult] = []

        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/124.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            try:
                resp = await client.post(url, data={"q": query, "b": ""})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for result_div in soup.select(".result")[:limit]:
                        title_tag = result_div.select_one(".result__title a")
                        snippet_tag = result_div.select_one(".result__snippet")
                        if not title_tag:
                            continue
                        title = title_tag.get_text(strip=True)
                        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                        href = title_tag.get("href", "")
                        # DuckDuckGo wraps links — extract actual URL
                        m = re.search(r"uddg=([^&]+)", href)
                        actual_url = m.group(1) if m else href
                        from urllib.parse import unquote
                        actual_url = unquote(actual_url)

                        wid = hashlib.md5(actual_url.encode()).hexdigest()[:10]
                        content = f"{title}. {snippet}".strip()
                        results.append(CrawlResult(
                            id=f"web-{wid}",
                            platform="Web",
                            author_username="@web_result",
                            author_id="ddg_search",
                            content=content[:500],
                            url=actual_url,
                            hashtags=re.findall(r"#(\w+)", content),
                            language="en",
                            source_type="SCRAPY_WEB_DDG",
                            crawled_at=datetime.datetime.utcnow().isoformat(),
                            created_at=datetime.datetime.utcnow().isoformat(),
                        ))
            except Exception as e:
                print(f"[ScrapyCrawler] Web crawl error: {e}")

        return results[:limit]
