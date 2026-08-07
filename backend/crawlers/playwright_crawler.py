"""
playwright_crawler.py — Headless browser-based crawler for JavaScript-heavy platforms:
  • YouTube   — Playwright (search results + top 50 comments per video)
  • Instagram — Selenium (public hashtag / explore pages)

Falls back gracefully to httpx stubs if Playwright is not installed,
so the rest of the system continues working without a browser.
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
from crawlers.base_crawler import BaseCrawler, CrawlResult, EngagementMetrics
from crawlers.rate_limiters import get_limiter

# ── Selenium Instagram crawler (replaces Playwright for Instagram) ────────────
from crawlers.selenium_instagram_crawler import selenium_instagram_search

# ── Playwright availability check ────────────────────────────────────────────
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[PlaywrightCrawler] playwright not installed — using httpx fallback stubs.")


# ── YouTube (Playwright) ─────────────────────────────────────────────────────

async def _yt_search_playwright(query: str, limit: int, fetch_comments: bool) -> List[CrawlResult]:
    """Full browser YouTube search extraction."""
    results: List[CrawlResult] = []
    encoded = quote_plus(query)
    # sp=EgIIAg%253D%253D filters YouTube search results to the last 24 hours (Today)
    search_url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgIIAg%253D%253D"

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(headless=True)
        page: Page = await browser.new_page()
        await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        try:
            await page.goto(search_url, wait_until="networkidle", timeout=30_000)
            # Scroll to trigger lazy-load until we have enough videos
            last_count = 0
            for _ in range(max(1, limit // 10)):
                videos = await page.query_selector_all("ytd-video-renderer")
                if len(videos) >= limit:
                    break
                await page.evaluate("window.scrollBy(0, 3000)")
                await asyncio.sleep(1.5)
                
                # Check if we are still loading new videos, if not, break early
                if len(videos) == last_count and len(videos) > 0:
                    await asyncio.sleep(2.0) # wait a bit more and check once more
                    videos_check = await page.query_selector_all("ytd-video-renderer")
                    if len(videos_check) == last_count:
                        break
                last_count = len(videos)

            videos = await page.query_selector_all("ytd-video-renderer")
            for vid in videos[:limit]:
                try:
                    title_el = await vid.query_selector("#video-title")
                    title = (await title_el.inner_text()).strip() if title_el else ""
                    href = await title_el.get_attribute("href") if title_el else ""
                    video_url = f"https://www.youtube.com{href}" if href else ""
                    meta_el = await vid.query_selector("#metadata-line")
                    meta_text = (await meta_el.inner_text()).strip() if meta_el else ""
                    thumb_el = await vid.query_selector("img")
                    thumb = await thumb_el.get_attribute("src") if thumb_el else ""
                    channel_el = await vid.query_selector("#channel-name a")
                    channel = (await channel_el.inner_text()).strip() if channel_el else "@youtube_user"

                    # Parse view count from meta text e.g. "1.2M views"
                    view_match = re.search(r"([\d,.]+[KMB]?)\s*view", meta_text, re.I)
                    views = _parse_count(view_match.group(1)) if view_match else 0

                    vid_id = hashlib.md5(video_url.encode()).hexdigest()[:10]
                    clean_channel = re.sub(r'\W+', '_', channel).lower()[:20]
                    cr = CrawlResult(
                        id=f"yt-{vid_id}",
                        platform="YouTube",
                        author_username=f"@{clean_channel}",
                        author_id=f"yt_{vid_id[:8]}",
                        content=title[:400],
                        url=video_url,
                        hashtags=re.findall(r"#(\w+)", title),
                        language="en",
                        engagement=EngagementMetrics(views=views),
                        thumbnail_url=thumb,
                        source_type="PLAYWRIGHT_YOUTUBE",
                        crawled_at=datetime.datetime.utcnow().isoformat(),
                        created_at=datetime.datetime.utcnow().isoformat(),
                    )

                    # Fetch comments if requested (open each video — expensive)
                    if fetch_comments and video_url:
                        cr.comments = await _yt_fetch_comments(page, video_url)

                    results.append(cr)
                except Exception:
                    continue
        finally:
            await browser.close()

    return results[:limit]


async def _yt_fetch_comments(page: Page, video_url: str) -> List[Dict[str, str]]:
    """Navigate to a YouTube video and extract the first 50 visible comments."""
    comments: List[Dict[str, str]] = []
    try:
        await page.goto(video_url, wait_until="networkidle", timeout=25_000)
        # Scroll to trigger comment section load
        for _ in range(4):
            await page.evaluate("window.scrollBy(0, 1500)")
            await asyncio.sleep(0.8)
        comment_els = await page.query_selector_all("ytd-comment-thread-renderer")
        for cel in comment_els[:50]:
            try:
                author_el = await cel.query_selector("#author-text")
                text_el = await cel.query_selector("#content-text")
                author = (await author_el.inner_text()).strip() if author_el else ""
                text = (await text_el.inner_text()).strip() if text_el else ""
                if text:
                    comments.append({"author": author, "text": text[:200]})
            except Exception:
                continue
    except Exception as e:
        print(f"[PlaywrightCrawler] Comment fetch failed for {video_url}: {e}")
    return comments


def _parse_count(s: str) -> int:
    """Convert '1.2M', '340K' etc. to integer."""
    s = s.replace(",", "").strip()
    try:
        if s.endswith("K"):
            return int(float(s[:-1]) * 1_000)
        if s.endswith("M"):
            return int(float(s[:-1]) * 1_000_000)
        if s.endswith("B"):
            return int(float(s[:-1]) * 1_000_000_000)
        return int(float(s))
    except Exception:
        return 0


# ── YouTube Fallback (httpx + HTML) ─────────────────────────────────────────

async def _yt_search_httpx(query: str, limit: int) -> List[CrawlResult]:
    """
    Lightweight fallback using httpx + regex extraction from YouTube's initial
    JSON data embedded in the search results page. No browser needed.
    """
    encoded = quote_plus(query)
    # sp=EgIIAg%253D%253D filters YouTube search results to the last 24 hours (Today)
    url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgIIAg%253D%253D"
    results: List[CrawlResult] = []
    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                # YT embeds initial data as window["ytInitialData"] JSON
                match = re.search(r'var ytInitialData\s*=\s*(\{.*?\});', resp.text, re.S)
                if not match:
                    match = re.search(r'ytInitialData"\s*=\s*(\{.*?\})\s*;', resp.text, re.S)

                if match:
                    import json
                    try:
                        data = json.loads(match.group(1))
                        contents = (data.get("contents", {})
                                    .get("twoColumnSearchResultsRenderer", {})
                                    .get("primaryContents", {})
                                    .get("sectionListRenderer", {})
                                    .get("contents", []))
                        for section in contents:
                            items = (section.get("itemSectionRenderer", {})
                                     .get("contents", []))
                            for item in items:
                                v = item.get("videoRenderer", {})
                                if not v:
                                    continue
                                title_runs = v.get("title", {}).get("runs", [])
                                title = "".join(r.get("text", "") for r in title_runs)
                                vid_id = v.get("videoId", "")
                                channel_runs = (v.get("longBylineText", {})
                                                .get("runs", [{}]))
                                channel = channel_runs[0].get("text", "") if channel_runs else ""
                                if not title or not vid_id:
                                    continue
                                cid = hashlib.md5(vid_id.encode()).hexdigest()[:10]
                                clean_channel = re.sub(r'\W+', '_', channel).lower()[:20]
                                results.append(CrawlResult(
                                    id=f"yt-{cid}",
                                    platform="YouTube",
                                    author_username=f"@{clean_channel}",
                                    author_id=f"yt_{cid[:8]}",
                                    content=title[:400],
                                    url=f"https://www.youtube.com/watch?v={vid_id}",
                                    hashtags=re.findall(r"#(\w+)", title),
                                    language="en",
                                    source_type="SCRAPY_YOUTUBE_HTTPX",
                                    crawled_at=datetime.datetime.utcnow().isoformat(),
                                    created_at=datetime.datetime.utcnow().isoformat(),
                                ))
                                if len(results) >= limit:
                                    break
                            if len(results) >= limit:
                                break
                    except Exception:
                        pass
    except Exception as e:
        print(f"[PlaywrightCrawler] YT httpx fallback error: {e}")

    return results[:limit]


# ── Instagram (httpx only — no browser required for public hashtag API) ──────

async def _instagram_search(query: str, limit: int) -> List[CrawlResult]:
    """
    Attempt public Instagram hashtag search. Falls back to stubs if blocked.
    Uses the mobile API endpoint which sometimes returns data without auth.
    """
    tag = re.sub(r"\s+", "", query.lower())  # normalise to hashtag
    url = f"https://www.instagram.com/explore/tags/{quote_plus(tag)}/?__a=1&__d=dis"
    results: List[CrawlResult] = []

    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Instagram 276.0.0.19.127 Android",
                "Accept": "application/json",
            },
        ) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                import json
                data = resp.json()
                edges = (data.get("graphql", {})
                         .get("hashtag", {})
                         .get("edge_hashtag_to_media", {})
                         .get("edges", []))
                for edge in edges[:limit]:
                    node = edge.get("node", {})
                    caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                    caption = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""
                    shortcode = node.get("shortcode", "")
                    uid = hashlib.md5(shortcode.encode()).hexdigest()[:10]
                    results.append(CrawlResult(
                        id=f"ig-{uid}",
                        platform="Instagram",
                        author_username="@ig_public",
                        author_id=f"ig_{uid}",
                        content=caption[:400] or f"Instagram post about #{tag}",
                        url=f"https://www.instagram.com/p/{shortcode}/",
                        hashtags=re.findall(r"#(\w+)", caption),
                        language="en",
                        engagement=EngagementMetrics(
                            likes=node.get("edge_liked_by", {}).get("count", 0),
                            comments=node.get("edge_media_to_comment", {}).get("count", 0),
                        ),
                        thumbnail_url=node.get("thumbnail_src", ""),
                        source_type="SCRAPY_INSTAGRAM",
                        crawled_at=datetime.datetime.utcnow().isoformat(),
                        created_at=datetime.datetime.utcnow().isoformat(),
                    ))
    except Exception as e:
        print(f"[PlaywrightCrawler] Instagram error: {e}")

    return results[:limit]


# ── PlaywrightCrawler class ───────────────────────────────────────────────────

class PlaywrightCrawler(BaseCrawler):
    """
    Browser-based crawler for JavaScript-heavy platforms.
    • YouTube   → Uses Playwright headless Chromium (falls back to httpx).
    • Instagram → Uses Selenium Chrome (falls back to curated CTI stubs).
    """

    SUPPORTED = ["YouTube", "Instagram"]

    def supported_platforms(self) -> List[str]:
        return self.SUPPORTED

    async def crawl(
        self,
        query: str,
        platform: str,
        limit: int = 20,
        fetch_comments: bool = False,
        time_filter: str = "any",
    ) -> List[CrawlResult]:
        limiter = get_limiter(platform)
        await limiter.acquire()

        if platform == "YouTube":
            if PLAYWRIGHT_AVAILABLE:
                try:
                    return await _yt_search_playwright(query, limit, fetch_comments=True)
                except Exception as e:
                    print(f"[PlaywrightCrawler] Playwright failed ({e}), falling back to httpx")
            return await _yt_search_httpx(query, limit)

        elif platform == "Instagram":
            # ── Selenium takes over Instagram scraping ──────────────────────
            print(f"[PlaywrightCrawler] Routing Instagram to SeleniumInstagramCrawler for query='{query}'")
            return await selenium_instagram_search(
                query=query,
                limit=limit,
                fetch_comments=fetch_comments,
                time_filter=time_filter,
            )

        return []
