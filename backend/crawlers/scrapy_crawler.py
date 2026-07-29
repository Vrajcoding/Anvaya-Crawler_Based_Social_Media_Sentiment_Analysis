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

# ── Selenium X crawler (primary source for real tweets) ──────────────────────
try:
    from crawlers.selenium_x_crawler import selenium_x_search as _x_search
    _X_CRAWLER_AVAILABLE = True
    print("[ScrapyCrawler] Selenium X crawler loaded.")
except ImportError:
    _X_CRAWLER_AVAILABLE = False
    print("[ScrapyCrawler] selenium_x_crawler not found — will use Nitter/stubs for X.")

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

    SUPPORTED = ["X", "GoogleSuggest", "Web", "Reddit"]

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
        elif platform == "Reddit":
            return await self._crawl_reddit(query, limit)
        return []

    # ── X / Twitter (via Nitter RSS) ────────────────────────────────────────

    async def _crawl_x(self, query: str, limit: int) -> List[CrawlResult]:
        """
        Fetch real tweets using a 3-tier strategy:
          1. Playwright browser login on x.com (real data, requires X credentials in .env)
          2. Nitter RSS mirrors (public, no auth — but often rate-limited / dead)
          3. Synthetic stubs (dashboard never empty fallback)
        """
        results: List[CrawlResult] = []

        # ── Tier 1: Selenium browser login (real tweets) ──────────────────
        if _X_CRAWLER_AVAILABLE:
            try:
                print(f"[ScrapyCrawler] Trying Selenium X browser for query='{query}'")
                results = await _x_search(query=query, limit=limit)
                if results:
                    print(f"[ScrapyCrawler] Selenium X returned {len(results)} real tweets.")
                    return results[:limit]
                else:
                    print("[ScrapyCrawler] Selenium X returned 0 results — falling back to Nitter.")
            except Exception as e:
                print(f"[ScrapyCrawler] Selenium X error: {e} — falling back to Nitter.")

        # ── Tier 2: Nitter RSS mirrors ────────────────────────────────────
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
                            print(f"[ScrapyCrawler] Nitter mirror {base} returned {len(results)} tweets.")
                            return results[:limit]
                except Exception:
                    continue  # try next mirror

        # ── Tier 3: Synthetic stubs (last resort) ─────────────────────────
        print("[ScrapyCrawler] All X sources failed — using synthetic stubs.")
        results = self._synthetic_x_stubs(query, limit)
        return results[:limit]

    def _parse_nitter_rss(self, xml_text: str, limit: int) -> List[CrawlResult]:
        soup = BeautifulSoup(xml_text, "xml")
        items = soup.find_all("item")[:limit]
        results = []
        for item in soup.find_all("item"):
            if len(results) >= limit:
                break
            
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            creator = item.find("dc:creator") or item.find("creator")

            ts = pub_date.text if pub_date else datetime.datetime.utcnow().isoformat()
            
            # ---- 24 Hour Filter ----
            try:
                import email.utils
                import time
                parsed_ts = email.utils.parsedate_tz(ts)
                if parsed_ts:
                    ts_timestamp = email.utils.mktime_tz(parsed_ts)
                    age_hours = (time.time() - ts_timestamp) / 3600
                    if age_hours > 24:
                        continue
            except Exception:
                pass

            text = title.text if title else ""
            post_url = link.text if link else ""
            author = creator.text.strip() if creator else "@unknown"

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
                # Add 'df': 'd' to restrict search to the past 24 hours (day)
                resp = await client.post(url, data={"q": query, "b": "", "df": "d"})
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


    # ── Reddit (public JSON API + RSS fallback, no auth) ────────────────────

    # Reddit-like browser headers that avoid 403/redirect-to-login issues
    _REDDIT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    async def _crawl_reddit(self, query: str, limit: int) -> List[CrawlResult]:
        """
        Fetch real Reddit posts using a 3-tier strategy:
          1. reddit.com/search.json  (main JSON API)
          2. old.reddit.com/search.json  (older API, less restricted)
          3. reddit.com/search.rss  (RSS — always public)
        Extracts full post title + selftext body so results are content-rich.
        """
        results = await self._reddit_json(query, limit, base="https://www.reddit.com")
        if not results:
            results = await self._reddit_json(query, limit, base="https://old.reddit.com")
        if not results:
            results = await self._reddit_rss(query, limit)
        return results[:limit]

    async def _reddit_json(self, query: str, limit: int, base: str) -> List[CrawlResult]:
        """
        Fetch Reddit posts using paginated JSON search API.
        Reddit allows max 100 per page; we page through using the 'after' cursor
        until we reach the requested `limit` or run out of results.
        """
        encoded    = quote_plus(query)
        # Reddit max per-page is 100
        page_size  = min(limit, 100)
        results: List[CrawlResult] = []
        after: str = ""   # pagination cursor

        async with httpx.AsyncClient(
            timeout=25.0,
            follow_redirects=True,
            headers=self._REDDIT_HEADERS,
        ) as client:
            while len(results) < limit:
                need       = limit - len(results)
                fetch_size = min(need, 100)   # never exceed Reddit's per-page cap
                url = (
                    f"{base}/search.json"
                    f"?q={encoded}&sort=new&limit={fetch_size}&type=link&t=day"
                    + (f"&after={after}" if after else "")
                )

                try:
                    resp = await client.get(url)
                    print(f"[Reddit] {base} page → HTTP {resp.status_code} | fetched={len(results)}/{limit}")

                    # Reddit sometimes returns HTML (login wall) — detect it
                    ct = resp.headers.get("content-type", "")
                    if resp.status_code != 200 or "text/html" in ct:
                        print(f"[Reddit] Non-JSON response from {base}, stopping.")
                        break

                    data  = resp.json().get("data", {})
                    posts = data.get("children", [])
                    after = data.get("after") or ""   # next page cursor

                    print(f"[Reddit] Page returned {len(posts)} posts, next_after={after!r}")

                    if not posts:
                        break   # no more results

                    for child in posts:
                        if len(results) >= limit:
                            break
                        p = child.get("data", {})
                        post_id   = p.get("id", uuid.uuid4().hex[:8])
                        title     = (p.get("title") or "").strip()
                        selftext  = (p.get("selftext") or "").strip()

                        # Strip "[removed]" / "[deleted]" placeholders
                        if selftext in ("[removed]", "[deleted]", ""):
                            selftext = ""

                        # Build rich content: title + body paragraph
                        if selftext:
                            content = f"{title}\n\n{selftext}"
                        else:
                            domain  = p.get("domain", "")
                            content = f"{title} [{domain}]" if domain else title

                        author      = p.get("author") or "unknown"
                        subreddit   = p.get("subreddit") or ""
                        permalink   = p.get("permalink") or ""
                        post_url    = f"https://www.reddit.com{permalink}" if permalink else ""
                        score       = p.get("score") or 0
                        num_coms    = p.get("num_comments") or 0
                        created_utc = p.get("created_utc")
                        created_at  = (
                            datetime.datetime.utcfromtimestamp(created_utc).isoformat()
                            if created_utc else datetime.datetime.utcnow().isoformat()
                        )
                        flair    = p.get("link_flair_text") or ""
                        hashtags = re.findall(r"#(\w+)", content)

                        results.append(CrawlResult(
                            id=f"reddit-{post_id}",
                            platform="Reddit",
                            author_username=f"u/{author}",
                            author_id=f"reddit_{author}",
                            content=content[:800],
                            url=post_url,
                            hashtags=hashtags,
                            language="en",
                            engagement=EngagementMetrics(
                                likes=score,
                                shares=0,
                                comments=num_coms,
                                views=0,
                            ),
                            source_type="SCRAPY_REDDIT_JSON",
                            crawled_at=datetime.datetime.utcnow().isoformat(),
                            created_at=created_at,
                            raw_meta={"subreddit": subreddit, "flair": flair},
                        ))

                    # If Reddit returned fewer than we asked for, there are no more pages
                    if len(posts) < fetch_size or not after:
                        break

                except Exception as e:
                    print(f"[Reddit] JSON crawl error ({base}): {e}")
                    break

        print(f"[Reddit] Total collected: {len(results)} posts")
        return results

    async def _reddit_rss(self, query: str, limit: int) -> List[CrawlResult]:
        """Last-resort: scrape Reddit's public RSS search feed."""
        encoded = quote_plus(query)
        url = f"https://www.reddit.com/search.rss?q={encoded}&sort=new&t=day"
        results: List[CrawlResult] = []

        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={**self._REDDIT_HEADERS, "Accept": "application/rss+xml, text/xml, */*"},
        ) as client:
            try:
                resp = await client.get(url)
                print(f"[Reddit RSS] HTTP {resp.status_code}")
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "xml")
                    entries = soup.find_all("entry")[:limit]
                    for entry in entries:
                        title_tag   = entry.find("title")
                        content_tag = entry.find("content") or entry.find("summary")
                        link_tag    = entry.find("link")
                        author_tag  = entry.find("author")
                        updated_tag = entry.find("updated")

                        title   = title_tag.get_text(strip=True)   if title_tag   else ""
                        body    = content_tag.get_text(strip=True)  if content_tag  else ""
                        # Strip HTML tags from RSS body
                        body    = re.sub(r"<[^>]+>", " ", body).strip()
                        # Remove boilerplate Reddit RSS text
                        body    = re.sub(
                            r"submitted by.*|<!-- SC_OFF -->.*|<!-- SC_ON -->.*", "",
                            body, flags=re.DOTALL
                        ).strip()

                        if body and body != title:
                            content = f"{title}\n\n{body}"
                        else:
                            content = title

                        link   = link_tag.get("href", "")  if link_tag   else ""
                        author = ""
                        if author_tag:
                            a_name = author_tag.find("name")
                            author = a_name.get_text(strip=True) if a_name else ""

                        ts      = updated_tag.get_text(strip=True) if updated_tag else ""
                        uid     = hashlib.md5((link or title).encode()).hexdigest()[:10]
                        hashtags = re.findall(r"#(\w+)", content)

                        results.append(CrawlResult(
                            id=f"reddit-rss-{uid}",
                            platform="Reddit",
                            author_username=f"u/{author}" if author else "@reddit_rss",
                            author_id=f"reddit_{author or uid}",
                            content=content[:800],
                            url=link,
                            hashtags=hashtags,
                            language="en",
                            source_type="SCRAPY_REDDIT_RSS",
                            crawled_at=datetime.datetime.utcnow().isoformat(),
                            created_at=ts or datetime.datetime.utcnow().isoformat(),
                        ))
            except Exception as e:
                print(f"[Reddit RSS] Error: {e}")

        return results
