"""
playwright_crawler.py — Headless browser-based crawler for JavaScript-heavy platforms:
  • YouTube  — search results + top 50 comments per video
  • Instagram — public hashtag / explore pages

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

# ── Playwright availability check ────────────────────────────────────────────
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[PlaywrightCrawler] playwright not installed — using httpx fallback stubs.")


# ── YouTube (Playwright) ─────────────────────────────────────────────────────

async def _yt_search_playwright(query: str, limit: int, fetch_comments: bool, time_filter: str = "all") -> List[CrawlResult]:
    """Full browser YouTube search extraction."""
    results: List[CrawlResult] = []
    encoded = quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"
    if time_filter == "24h":
        search_url += "&sp=EgIIQA%253D%253D"

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(headless=True)
        page: Page = await browser.new_page()
        await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        try:
            await page.goto(search_url, wait_until="networkidle", timeout=30_000)
            # Scroll to trigger lazy-load
            await page.evaluate("window.scrollBy(0, 2000)")
            await asyncio.sleep(1.5)

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
    # If it's a shorts URL, convert to watch?v= URL to load the standard comment interface
    if "/shorts/" in video_url:
        video_url = video_url.replace("/shorts/", "/watch?v=")
        
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
    url = f"https://www.youtube.com/results?search_query={encoded}"
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

    # Final fallback: stubs
    if not results:
        for i in range(min(limit, 5)):
            uid = uuid.uuid4().hex[:8]
            results.append(CrawlResult(
                id=f"yt-stub-{uid}",
                platform="YouTube",
                author_username="@yt_monitor",
                author_id=f"yt_{uid}",
                content=f"[Simulated] YouTube result for: {query} — video #{i+1}",
                url=f"https://www.youtube.com/results?search_query={encoded}",
                source_type="SCRAPY_YT_STUB",
                crawled_at=datetime.datetime.utcnow().isoformat(),
                created_at=datetime.datetime.utcnow().isoformat(),
            ))

    return results[:limit]


# ── Instagram (httpx & playwright) ───────────────────────────────────────────

async def _instagram_search_playwright(query: str, limit: int, fetch_comments: bool, time_filter: str = "all") -> List[CrawlResult]:
    """Attempt public Instagram hashtag search using Playwright to bypass basic blocks."""
    tag = re.sub(r"\s+", "", query.lower())
    search_url = f"https://www.instagram.com/explore/tags/{quote_plus(tag)}/"
    results: List[CrawlResult] = []

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(headless=True)
        page: Page = await browser.new_page()
        try:
            await page.goto(search_url, wait_until="networkidle", timeout=25_000)
            await asyncio.sleep(2.0)
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(1.0)
                
            post_links = await page.query_selector_all("a[href^='/p/']")
            for link in post_links:
                if len(results) >= limit:
                    break
                href = await link.get_attribute("href")
                if not href:
                    continue
                shortcode = href.split("/")[2]
                uid = hashlib.md5(shortcode.encode()).hexdigest()[:10]
                post_url = f"https://www.instagram.com{href}"
                
                cr = CrawlResult(
                    id=f"ig-{uid}",
                    platform="Instagram",
                    author_username="@ig_public",
                    author_id=f"ig_{uid}",
                    content=f"Instagram post about #{tag}",
                    url=post_url,
                    hashtags=[tag],
                    language="en",
                    source_type="PLAYWRIGHT_INSTAGRAM",
                    crawled_at=datetime.datetime.utcnow().isoformat(),
                    created_at=datetime.datetime.utcnow().isoformat(),
                )
                
                if fetch_comments or time_filter == "24h":
                    p = await browser.new_page()
                    try:
                        await p.goto(post_url, wait_until="networkidle", timeout=20_000)
                        await asyncio.sleep(1.5)
                        
                        time_el = await p.query_selector("time")
                        if time_el and time_filter == "24h":
                            dt_str = await time_el.get_attribute("datetime")
                            if dt_str:
                                dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                                if (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() > 86400:
                                    await p.close()
                                    continue
                        
                        cap_el = await p.query_selector("h1")
                        if cap_el:
                            cr.content = await cap_el.inner_text()
                            
                        if fetch_comments:
                            comment_els = await p.query_selector_all("ul li span")
                            for cel in comment_els[:10]:
                                text = (await cel.inner_text()).strip()
                                if text and text != cr.content:
                                    cr.comments.append({"author": "unknown", "text": text[:200]})
                    except Exception:
                        pass
                    finally:
                        await p.close()

                results.append(cr)
        except Exception as e:
            print(f"[PlaywrightCrawler] Playwright Instagram error: {e}")
        finally:
            await browser.close()
            
    return results[:limit]


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

    # Fallback stubs if blocked
    if not results:
        for i in range(min(limit, 4)):
            uid = uuid.uuid4().hex[:8]
            results.append(CrawlResult(
                id=f"ig-stub-{uid}",
                platform="Instagram",
                author_username=f"@ig_user_{uid[:5]}",
                author_id=f"ig_{uid}",
                content=f"[Simulated] Instagram post about #{tag} — #{i+1}",
                url=f"https://www.instagram.com/explore/tags/{tag}/",
                hashtags=[tag],
                source_type="PLAYWRIGHT_IG_STUB",
                crawled_at=datetime.datetime.utcnow().isoformat(),
                created_at=datetime.datetime.utcnow().isoformat(),
            ))

    return results[:limit]


# ── PlaywrightCrawler class ───────────────────────────────────────────────────

class PlaywrightCrawler(BaseCrawler):
    """
    Browser-based crawler for JavaScript-heavy platforms.
    Uses full Playwright headless Chromium when available,
    falls back to httpx-based extraction otherwise.
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
        time_filter: str = "all",
    ) -> List[CrawlResult]:
        limiter = get_limiter(platform)
        await limiter.acquire()

        if platform == "YouTube":
            if PLAYWRIGHT_AVAILABLE:
                try:
                    return await _yt_search_playwright(query, limit, fetch_comments, time_filter)
                except Exception as e:
                    print(f"[PlaywrightCrawler] Playwright failed ({e}), falling back to httpx")
            return await _yt_search_httpx(query, limit)

        elif platform == "Instagram":
            if PLAYWRIGHT_AVAILABLE:
                res = await _instagram_search_playwright(query, limit, fetch_comments, time_filter)
                if res:
                    return res
                print("[PlaywrightCrawler] Playwright Instagram returned 0 results, falling back to httpx")
            return await _instagram_search(query, limit)

        return []
