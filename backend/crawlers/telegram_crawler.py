"""
telegram_crawler.py — Telethon-based Telegram public hashtag crawler for SentinelAI

Uses the MTProto API (via Telethon) to search ALL public Telegram channels for posts
matching a query/hashtag without requiring you to be a member of those channels.

This uses functions.channels.SearchPostsRequest — the same API the official Telegram
app uses for its global hashtag search tab.

Requirements:
    pip install telethon

Configuration (backend/.env):
    TELEGRAM_API_ID=12345678
    TELEGRAM_API_HASH=abcdef1234567890
    TELEGRAM_SESSION_NAME=sentinelai_session   (optional, default used if absent)

First-run interactive login:
    cd backend
    python crawlers/telegram_crawler.py
    (Enter phone number + OTP when prompted — creates a .session file)

Subsequent runs (in FastAPI) are fully non-interactive.
"""
from __future__ import annotations

import asyncio
import datetime
import hashlib
import os
import re
import sys
from typing import Any, Dict, List, Optional

# Make sure 'backend/' is on sys.path so the script can be run from any directory
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from crawlers.base_crawler import BaseCrawler, CrawlResult, EngagementMetrics

# ── Telethon availability guard ──────────────────────────────────────────────
try:
    from telethon import TelegramClient, functions, types as tg_types

    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    print("[TelegramCrawler] 'telethon' not installed — install via: pip install telethon")


def _clean_text(text: str) -> str:
    """
    Remove all hashtags from message text while preserving other formatting.
    Mirrors the process_message_text() logic from the reference script.
    """
    if not text:
        return ""
    # Remove hashtags (with surrounding whitespace), replace with single space
    cleaned = re.sub(r"\s*#\w+\s*", " ", text)
    return cleaned.strip()


def _parse_int(value: Any, default: int = 0) -> int:
    """Safely coerce a value to int."""
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


class TelegramCrawler(BaseCrawler):
    """
    Crawls public Telegram channels using the MTProto API (Telethon).

    Uses functions.channels.SearchPostsRequest to search ALL public Telegram
    channels for a given hashtag — the same way the official Telegram app's
    global hashtag search works. No channel membership required.
    """

    SUPPORTED = ["Telegram"]

    def supported_platforms(self) -> List[str]:
        return self.SUPPORTED

    # ── Persistent singleton client + rate-limit state ────────────────────

    _client: Optional[Any] = None          # reused across all requests
    _client_lock: Optional[Any] = None     # asyncio.Lock — set on first use
    _last_request_at: float = 0.0          # unix timestamp of last search
    MIN_REQUEST_GAP_SECS: float = 3.0      # minimum seconds between searches

    @classmethod
    def _get_credentials(cls):
        """Load Telegram credentials from backend/.env."""
        _env_path = os.path.join(_backend_dir, ".env")
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=_env_path, override=False)
        except ImportError:
            pass

        api_id_raw = os.getenv("TELEGRAM_API_ID", "")
        api_hash = os.getenv("TELEGRAM_API_HASH", "")
        session_name = os.getenv("TELEGRAM_SESSION_NAME", "sentinelai_session")

        # Always use absolute path so .session file resolves correctly
        session_path = os.path.join(_backend_dir, session_name)

        try:
            api_id = int(api_id_raw)
        except (ValueError, TypeError):
            api_id = None

        return api_id, api_hash, session_path

    @classmethod
    async def _get_client(cls) -> Optional[Any]:
        """
        Return a PERSISTENT connected TelegramClient — creates once, reuses forever.
        Behaves like a normal Telegram app that stays logged in, which is the
        safest pattern and avoids the ban risk of connect/disconnect on every call.
        """
        import asyncio as _asyncio

        if not TELETHON_AVAILABLE:
            print("[TelegramCrawler] ❌ Telethon not installed.")
            return None

        api_id, api_hash, session_path = cls._get_credentials()
        if not api_id or not api_hash:
            print(
                "[TelegramCrawler] ❌ TELEGRAM_API_ID / TELEGRAM_API_HASH not set in .env\n"
                "  → Get them at https://my.telegram.org/apps"
            )
            return None

        # Initialise the asyncio lock once (cannot create at class-definition time
        # because there is no running event loop yet)
        if cls._client_lock is None:
            cls._client_lock = _asyncio.Lock()

        async with cls._client_lock:
            # Reuse existing client if still connected and authorised
            if cls._client is not None and cls._client.is_connected():
                return cls._client

            print(f"[TelegramCrawler] 🔌 Connecting to Telegram (session: {session_path})...")
            cls._client = TelegramClient(session_path, api_id, api_hash)
            try:
                await cls._client.connect()
                if not await cls._client.is_user_authorized():
                    print(
                        "[TelegramCrawler] ❌ Session not authorized.\n"
                        "  → Run:  cd backend && python crawlers/telegram_crawler.py"
                    )
                    await cls._client.disconnect()
                    cls._client = None
                    return None
                print("[TelegramCrawler] ✅ Connected and authorized! (connection will be reused)")
                return cls._client
            except Exception as exc:
                print(f"[TelegramCrawler] ❌ Connection error: {exc}")
                try:
                    await cls._client.disconnect()
                except Exception:
                    pass
                cls._client = None
                return None


    # ── Public crawl entry point ─────────────────────────────────────────────

    async def crawl(
        self,
        query: str,
        platform: str,
        limit: int = 20,
        fetch_comments: bool = False,
        time_filter: str = "any",
    ) -> List[CrawlResult]:
        if platform != "Telegram":
            return []
        return await self._crawl_telegram(query, limit)

    # ── Core hashtag search (MTProto SearchPostsRequest) ────────────────────

    async def _crawl_telegram(self, query: str, limit: int) -> List[CrawlResult]:
        """
        Search ALL public Telegram channels for the given hashtag using
        functions.channels.SearchPostsRequest (MTProto global hashtag search).
        """
        import asyncio as _asyncio
        import time as _time

        keyword = query.lstrip("#").strip()
        print(f"[TelegramCrawler] 🔍 Searching for hashtag: #{keyword} (limit={limit})")

        # ── Rate limiting: enforce minimum gap between searches ───────────────
        # This makes the account behave like a normal user, not a bot hammer.
        now = _time.monotonic()
        gap = now - TelegramCrawler._last_request_at
        if gap < TelegramCrawler.MIN_REQUEST_GAP_SECS:
            wait = TelegramCrawler.MIN_REQUEST_GAP_SECS - gap
            print(f"[TelegramCrawler] ⏳ Rate limiting — waiting {wait:.1f}s before next request")
            await _asyncio.sleep(wait)
        TelegramCrawler._last_request_at = _time.monotonic()

        client = await self._get_client()

        if client is not None:
            # NOTE: Do NOT disconnect after each search — keep connection alive.
            # Reconnecting every request is the #1 ban trigger.
            results = await self._search_posts_request(client, keyword, limit)
            print(f"[TelegramCrawler] ✅ SearchPostsRequest returned {len(results)} results")
            return results

        # Only reach here if client is None (no credentials / not authorized)
        print("[TelegramCrawler] ⚠️ No MTProto client — falling back to web preview")
        web_results = await self._crawl_web_preview(keyword, limit)
        if web_results:
            return web_results

        return self._stub_results(query, limit)


    async def _search_posts_request(
        self, client: Any, keyword: str, limit: int
    ) -> List[CrawlResult]:
        """
        Execute functions.channels.SearchPostsRequest — global public hashtag search.

        Parameters mirror the reference script exactly:
            hashtag   = keyword (WITHOUT the '#')
            limit     = how many posts to fetch
        """
        results: List[CrawlResult] = []

        try:
            response = await client(
                functions.channels.SearchPostsRequest(
                    hashtag=keyword,          # Pass keyword WITHOUT '#'
                    offset_rate=0,
                    offset_peer=tg_types.InputPeerEmpty(),
                    offset_id=0,
                    limit=limit,
                )
            )
        except Exception as exc:
            print(f"[TelegramCrawler] SearchPostsRequest failed: {exc}")
            return results

        if not response or not response.messages:
            print(f"[TelegramCrawler] No messages found for hashtag: #{keyword}")
            return results

        for msg in response.messages:
            original_text = getattr(msg, "message", "") or ""
            cleaned_text = _clean_text(original_text)

            # Skip messages that were media-only or contained only hashtags
            if not cleaned_text:
                continue

            # ── Build the direct post URL ─────────────────────────────────
            post_link = "Link unavailable"
            author_username = "unknown"
            try:
                chat = await client.get_entity(msg.peer_id)
                if hasattr(chat, "username") and chat.username:
                    post_link = f"https://t.me/{chat.username}/{msg.id}"
                    author_username = chat.username
                elif hasattr(chat, "id"):
                    # Private/mega-group — link may still be constructable via id
                    post_link = f"https://t.me/c/{chat.id}/{msg.id}"
                    author_username = getattr(chat, "title", str(chat.id))
            except Exception:
                pass  # Silently skip unresolvable entities (same as reference script)

            # ── Engagement metrics ────────────────────────────────────────
            views = _parse_int(getattr(msg, "views", 0))
            forwards = _parse_int(getattr(msg, "forwards", 0))
            replies_obj = getattr(msg, "replies", None)
            reply_count = _parse_int(getattr(replies_obj, "replies", 0)) if replies_obj else 0

            # ── Timestamp ────────────────────────────────────────────────
            date_obj = getattr(msg, "date", None)
            created_at = (
                date_obj.isoformat() if date_obj else datetime.datetime.utcnow().isoformat()
            )

            # ── Unique ID ────────────────────────────────────────────────
            uid = hashlib.md5(
                f"tg-{author_username}-{msg.id}".encode()
            ).hexdigest()[:12]

            results.append(
                CrawlResult(
                    id=f"tg-{uid}",
                    platform="Telegram",
                    author_username=f"@{author_username}",
                    author_id=str(author_username),
                    content=cleaned_text[:800],
                    url=post_link,
                    hashtags=re.findall(r"#(\w+)", original_text),
                    language="en",
                    engagement=EngagementMetrics(
                        likes=0,
                        shares=forwards,
                        comments=reply_count,
                        views=views,
                    ),
                    source_type="TELETHON_SEARCH_POSTS",
                    crawled_at=datetime.datetime.utcnow().isoformat(),
                    created_at=created_at,
                    raw_meta={
                        "msg_id": msg.id,
                        "author": author_username,
                        "hashtag_searched": keyword,
                    },
                )
            )

        return results

    # ── Web-preview fallback (no auth required) ──────────────────────────────

    async def _crawl_web_preview(self, keyword: str, limit: int) -> List[CrawlResult]:
        """
        Scrape Telegram's public web preview at t.me/s/<keyword>.
        This is used when the authenticated MTProto client is unavailable.
        Works without any credentials — useful for public channels whose
        username matches the search keyword exactly.
        """
        results: List[CrawlResult] = []

        try:
            import httpx as _httpx
        except ImportError:
            print("[TelegramCrawler] 'httpx' not installed — skipping web preview fallback.")
            return results

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        url = f"https://t.me/s/{keyword}"
        try:
            async with _httpx.AsyncClient(
                timeout=10.0, follow_redirects=True, headers=headers
            ) as http:
                resp = await http.get(url)

            if resp.status_code != 200:
                return results

            html = resp.text

            # Extract message text blocks and their links from the Telegram web page
            msg_blocks = re.findall(
                r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
                html,
                re.DOTALL,
            )
            msg_links = re.findall(
                r'href="(https://t\.me/[^/]+/\d+)"',
                html,
            )

            for i, block in enumerate(msg_blocks[:limit]):
                # Strip HTML tags and collapse whitespace
                clean = re.sub(r"<[^>]+>", " ", block).strip()
                clean = re.sub(r"\s+", " ", clean).strip()
                clean = _clean_text(clean)  # also strip any remaining hashtags

                if not clean or len(clean) < 5:
                    continue

                post_url = msg_links[i] if i < len(msg_links) else url
                uid = hashlib.md5(f"tg-web-{keyword}-{i}".encode()).hexdigest()[:12]

                results.append(
                    CrawlResult(
                        id=f"tg-{uid}",
                        platform="Telegram",
                        author_username=f"@{keyword}",
                        author_id=keyword,
                        content=clean[:800],
                        url=post_url,
                        hashtags=re.findall(r"#(\w+)", clean),
                        language="en",
                        source_type="TELEGRAM_WEB_PREVIEW",
                        crawled_at=datetime.datetime.utcnow().isoformat(),
                        created_at=datetime.datetime.utcnow().isoformat(),
                    )
                )
        except Exception as exc:
            print(f"[TelegramCrawler] Web preview fetch failed for {url}: {exc}")

        return results

    # ── Stub fallback ────────────────────────────────────────────────────────

    def _stub_results(self, query: str, limit: int) -> List[CrawlResult]:
        """
        Returns placeholder results when no credentials are configured and
        web preview also failed. Keeps the UI functional with a clear message.
        """
        import uuid as _uuid

        stubs = []
        for i in range(min(limit, 3)):
            uid = _uuid.uuid4().hex[:10]
            stubs.append(
                CrawlResult(
                    id=f"tg-stub-{uid}",
                    platform="Telegram",
                    author_username="@telegram_channel",
                    author_id=uid,
                    content=(
                        f"[Telegram not configured] Set TELEGRAM_API_ID and "
                        f"TELEGRAM_API_HASH in backend/.env to enable live Telegram "
                        f"hashtag search. Query: #{query} — result #{i + 1}"
                    ),
                    url="https://my.telegram.org/apps",
                    source_type="TELEGRAM_STUB",
                    crawled_at=datetime.datetime.utcnow().isoformat(),
                    created_at=datetime.datetime.utcnow().isoformat(),
                )
            )
        return stubs


# ── Interactive first-run login ───────────────────────────────────────────────
if __name__ == "__main__":
    """
    Run this script directly ONCE to authenticate your Telegram userbot session.
    It will prompt for your phone number and the OTP sent to your Telegram app.
    After that the FastAPI server can use Telegram non-interactively forever.

    Usage:
        cd backend
        python crawlers/telegram_crawler.py
    """
    try:
        from dotenv import load_dotenv as _load_dotenv
        _load_dotenv(os.path.join(_backend_dir, ".env"))
    except ImportError:
        pass

    api_id_raw = os.getenv("TELEGRAM_API_ID", "")
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    session_name = os.getenv("TELEGRAM_SESSION_NAME", "sentinelai_session")
    session_path = os.path.join(_backend_dir, session_name)

    if not api_id_raw or not api_hash:
        print(
            "\nERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in backend/.env\n"
            "Get them at: https://my.telegram.org/apps\n"
        )
        sys.exit(1)

    if not TELETHON_AVAILABLE:
        print("\nERROR: Telethon is not installed. Run:  pip install telethon\n")
        sys.exit(1)

    async def _interactive_login():
        client = TelegramClient(session_path, int(api_id_raw), api_hash)
        await client.start()  # Prompts phone number + OTP on first run
        print(f"\n✅ Session saved as '{session_path}.session'")
        print("You can now start the FastAPI backend — Telegram will work automatically.")
        await client.disconnect()

    asyncio.run(_interactive_login())
