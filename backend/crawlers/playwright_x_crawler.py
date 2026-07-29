"""
playwright_x_crawler.py — Playwright-based X (Twitter) search crawler.

Strategy:
  1. Launch Chromium via Playwright with stealth flags.
  2. Log into x.com using X_USERNAME / X_PASSWORD from .env.
     Handles BOTH the old multi-step form AND X's new single-page form
     (/i/jf/onboarding/web) which shows username + password simultaneously.
  3. Navigate to https://x.com/search?q=<query>&f=live (Latest tab).
  4. Scroll and extract real tweet cards.
  5. Return CrawlResult objects with source_type="PLAYWRIGHT_X".

Falls back gracefully to [] if Playwright is not installed,
or if credentials are missing / login fails.

Requirements:
  pip install playwright
  playwright install chromium
  # In .env:
  X_USERNAME=your_x_email_or_handle
  X_PASSWORD=your_x_password
  # Optional — open a visible window (for first-time phone verification):
  X_HEADLESS=false
"""
from __future__ import annotations

import asyncio
import datetime
import hashlib
import os
import re
from typing import List
from urllib.parse import quote_plus

# ── dotenv ────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Playwright availability check ─────────────────────────────────────────────
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[XCrawler] playwright not installed — X Playwright crawler disabled.")

from crawlers.base_crawler import CrawlResult, EngagementMetrics

# ── Credentials ───────────────────────────────────────────────────────────────
_X_USERNAME: str = os.getenv("X_USERNAME", "")
_X_PASSWORD: str = os.getenv("X_PASSWORD", "")

# Saved auth state — skip login on subsequent runs
_AUTH_STATE_PATH: str = os.path.join(
    os.path.dirname(__file__), ".x_auth_state.json"
)

# Debug screenshot — saved on login failure for diagnosis
_DEBUG_SCREENSHOT: str = os.path.join(
    os.path.dirname(__file__), ".x_login_debug.png"
)

# ── Stealth browser launch args ───────────────────────────────────────────────
_STEALTH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--window-size=1280,900",
    "--disable-extensions",
]

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_count(s: str) -> int:
    """Convert '1.2M', '340K', '5' to an integer."""
    if not s:
        return 0
    s = s.replace(",", "").strip()
    try:
        if s.upper().endswith("K"):
            return int(float(s[:-1]) * 1_000)
        if s.upper().endswith("M"):
            return int(float(s[:-1]) * 1_000_000)
        if s.upper().endswith("B"):
            return int(float(s[:-1]) * 1_000_000_000)
        return int(float(s))
    except Exception:
        return 0


async def _dismiss_cookie_banner(page: Page) -> None:
    """Dismiss any GDPR / cookie consent popup if present."""
    selectors = [
        "button:has-text('Accept all cookies')",
        "button:has-text('Decline optional cookies')",
        "button:has-text('Refuse non-essential cookies')",
        "[data-testid='cookie-consent-confirm-button']",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.count() > 0:
                await btn.click(timeout=3_000)
                await asyncio.sleep(1)
                print(f"[XCrawler] Dismissed cookie banner via: {sel}")
                return
        except Exception:
            pass


async def _do_login(page: Page, username: str, password: str) -> bool:
    """
    Login to X (Twitter). Handles both:
      - Old multi-step form  (username → Next → password → Log in)
      - New single-page form (/i/jf/onboarding/web) — both fields at once,
        where the username field intercepts pointer events on the password field.

    Uses JavaScript focus + keyboard.type() to bypass pointer-event interception.
    """
    try:
        print("[XCrawler] Navigating to X login page…")
        await page.goto(
            "https://x.com/i/flow/login",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await asyncio.sleep(3)
        await _dismiss_cookie_banner(page)
        await asyncio.sleep(1)
        print(f"[XCrawler] Login page URL: {page.url}")

        # ── Step 1: Fill username ──────────────────────────────────────────
        username_sel = None
        for sel in [
            "input[name='username_or_email']",   # new /i/jf/onboarding form
            "input[autocomplete='username']",     # old /i/flow/login form
            "input[name='text']",
            "input[type='text']",
        ]:
            try:
                loc = page.locator(sel).first
                await loc.wait_for(state="visible", timeout=6_000)
                username_sel = sel
                print(f"[XCrawler] Username input found: {sel}")
                break
            except Exception:
                continue

        if not username_sel:
            print("[XCrawler] ❌ Username input not found — saving screenshot.")
            await page.screenshot(path=_DEBUG_SCREENSHOT)
            return False

        # JS-focus then press_sequentially to fire React's onChange events
        await page.evaluate(f"""
            (() => {{
                const el = document.querySelector("{username_sel}");
                if (el) {{ el.focus(); el.value = ""; el.dispatchEvent(new Event('input', {{bubbles: true}})); }}
            }})();
        """)
        await asyncio.sleep(0.3)
        await page.locator(username_sel).first.press_sequentially(username, delay=90)
        await asyncio.sleep(0.8)

        # ── Detect: single-page form or multi-step? ───────────────────────
        pw_already_visible = (
            await page.locator("input[name='password'], input[type='password']").count() > 0
        )
        print(f"[XCrawler] Password field already visible: {pw_already_visible}")

        if not pw_already_visible:
            # Multi-step: advance to password screen
            advanced = False
            for sel in [
                "button[data-testid='LoginForm_Forward_Button']",
                "div[role='button']:has-text('Next')",
                "button:has-text('Next')",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.count() > 0:
                        await btn.click(timeout=5_000)
                        advanced = True
                        break
                except Exception:
                    pass
            if not advanced:
                await page.keyboard.press("Enter")
            await asyncio.sleep(2.5)

            # Handle "unusual activity" identity confirmation if it appears
            unusual_sel = "input[data-testid='ocfEnterTextTextInput']"
            try:
                if await page.locator(unusual_sel).count() > 0:
                    print("[XCrawler] Identity confirmation step — re-entering username…")
                    await page.locator(unusual_sel).first.fill(username)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)
            except Exception:
                pass

        # ── Step 2: Fill password via JS focus + keyboard.type() ───────────
        # keyboard.type() sends to the currently focused element,
        # bypassing any pointer-event interception.
        pw_sel = None
        for sel in ["input[name='password']", "input[type='password']"]:
            try:
                loc = page.locator(sel).first
                await loc.wait_for(state="visible", timeout=8_000)
                pw_sel = sel
                print(f"[XCrawler] Password input found: {sel}")
                break
            except Exception:
                continue

        if not pw_sel:
            print("[XCrawler] ❌ Password input not found — saving screenshot.")
            await page.screenshot(path=_DEBUG_SCREENSHOT)
            return False

        # Focus the password field via JavaScript (no click → no interception)
        await page.evaluate(f"""
            (() => {{
                const el = document.querySelector("{pw_sel}");
                if (el) {{ el.focus(); el.value = ""; el.dispatchEvent(new Event('input', {{bubbles: true}})); }}
            }})();
        """)
        await asyncio.sleep(0.3)
        # Type into the focused element
        await page.keyboard.type(password, delay=90)
        await asyncio.sleep(0.5)

        # ── Step 3: Submit ─────────────────────────────────────────────────
        submitted = False
        for sel in [
            "button[data-testid='LoginForm_Login_Button']",
            "button[type='submit']",
            "div[role='button']:has-text('Log in')",
            "button:has-text('Log in')",
            "button:has-text('Sign in')",
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0:
                    await btn.click(timeout=5_000)
                    submitted = True
                    print(f"[XCrawler] Clicked submit: {sel}")
                    break
            except Exception:
                pass

        if not submitted:
            print("[XCrawler] No submit button found — pressing Enter…")
            await page.keyboard.press("Enter")

        await asyncio.sleep(5)
        current_url = page.url
        print(f"[XCrawler] Post-login URL: {current_url}")

        # ── Verify success ─────────────────────────────────────────────────
        if (
            "home" in current_url
            or "/search" in current_url
            or (
                "x.com" in current_url
                and "login" not in current_url
                and "flow" not in current_url
                and "onboarding" not in current_url
            )
        ):
            print("[XCrawler] ✅ Login successful!")
            return True

        if any(k in current_url for k in ("verify", "challenge", "phone", "confirm")):
            print("[XCrawler] ⚠️  X requires phone/email verification.")
            print("    Set X_HEADLESS=false and re-run to complete verification manually.")
            await page.screenshot(path=_DEBUG_SCREENSHOT)
            print(f"[XCrawler] Screenshot → {_DEBUG_SCREENSHOT}")
            return False

        print(f"[XCrawler] Unknown post-login state: {current_url}")
        await page.screenshot(path=_DEBUG_SCREENSHOT)
        print(f"[XCrawler] Screenshot → {_DEBUG_SCREENSHOT}")
        return False

    except Exception as e:
        print(f"[XCrawler] Login error: {e}")
        try:
            await page.screenshot(path=_DEBUG_SCREENSHOT)
            print(f"[XCrawler] Screenshot → {_DEBUG_SCREENSHOT}")
        except Exception:
            pass
        return False


# ── Tweet extraction ──────────────────────────────────────────────────────────

async def _extract_tweets(page: Page, limit: int) -> List[CrawlResult]:
    """
    Scroll the search results page and extract tweet data.
    Uses X's stable data-testid attributes.
    """
    results: List[CrawlResult] = []
    seen_ids: set = set()
    max_scrolls = 15
    scroll_count = 0
    no_new_streak = 0

    while len(results) < limit and scroll_count < max_scrolls:
        tweet_els = await page.query_selector_all("article[data-testid='tweet']")
        before = len(results)

        for tweet_el in tweet_els:
            if len(results) >= limit:
                break
            try:
                # Author handle
                user_el = await tweet_el.query_selector("div[data-testid='User-Name']")
                if not user_el:
                    continue

                handle = ""
                name_spans = await user_el.query_selector_all("span")
                for span in name_spans:
                    txt = (await span.inner_text()).strip()
                    if txt.startswith("@"):
                        handle = txt
                        break

                if not handle:
                    link_el = await tweet_el.query_selector("a[href*='/status/']")
                    if link_el:
                        href = await link_el.get_attribute("href") or ""
                        parts = href.strip("/").split("/")
                        if parts:
                            handle = f"@{parts[0]}"

                if not handle:
                    continue

                # Tweet text
                text_el = await tweet_el.query_selector("div[data-testid='tweetText']")
                tweet_text = (await text_el.inner_text()).strip() if text_el else ""

                # Timestamp & URL
                created_at = ""
                tweet_url = ""
                time_el = await tweet_el.query_selector("time")
                if time_el:
                    created_at = await time_el.get_attribute("datetime") or ""
                    try:
                        link = await time_el.evaluate_handle("el => el.closest('a')")
                        if link:
                            href = await link.get_attribute("href")
                            if href and "/status/" in href:
                                tweet_url = (
                                    f"https://x.com{href}"
                                    if href.startswith("/")
                                    else href
                                )
                    except Exception:
                        pass

                dedup_key = tweet_url or hashlib.md5(
                    (handle + tweet_text[:60]).encode()
                ).hexdigest()

                if dedup_key in seen_ids:
                    continue
                seen_ids.add(dedup_key)

                # Engagement
                likes = retweets = replies = 0
                for testid, target in [
                    ("like", "likes"),
                    ("retweet", "retweets"),
                    ("reply", "replies"),
                ]:
                    try:
                        btn = await tweet_el.query_selector(f"button[data-testid='{testid}']")
                        if btn:
                            spans = await btn.query_selector_all(
                                "span[data-testid='app-text-transition-container'] span"
                            )
                            for sp in spans:
                                val = (await sp.inner_text()).strip()
                                if val:
                                    parsed = _parse_count(val)
                                    if target == "likes":
                                        likes = parsed
                                    elif target == "retweets":
                                        retweets = parsed
                                    else:
                                        replies = parsed
                                    break
                    except Exception:
                        pass

                hashtags = re.findall(r"#(\w+)", tweet_text)
                post_id = hashlib.md5(dedup_key.encode()).hexdigest()[:12]

                results.append(CrawlResult(
                    id=f"x-{post_id}",
                    platform="X",
                    author_username=handle,
                    author_id=f"usr_{handle.lstrip('@')[:16]}",
                    content=tweet_text[:500],
                    url=tweet_url,
                    hashtags=hashtags,
                    language="en",
                    engagement=EngagementMetrics(
                        likes=likes,
                        shares=retweets,
                        comments=replies,
                    ),
                    source_type="PLAYWRIGHT_X",
                    crawled_at=datetime.datetime.utcnow().isoformat(),
                    created_at=created_at or datetime.datetime.utcnow().isoformat(),
                ))

            except Exception:
                continue

        after = len(results)
        if after == before:
            no_new_streak += 1
            if no_new_streak >= 3:
                break
        else:
            no_new_streak = 0

        await page.evaluate("window.scrollBy(0, 1800)")
        await asyncio.sleep(2)
        scroll_count += 1

    print(f"[XCrawler] Extracted {len(results)} tweets after {scroll_count} scrolls.")
    return results[:limit]


# ── Main public API ───────────────────────────────────────────────────────────

async def playwright_x_search(
    query: str,
    limit: int = 20,
    fetch_comments: bool = False,
    headless: bool = True,
) -> List[CrawlResult]:
    """
    Search X (Twitter) for real tweets using a Playwright browser login.

    Set X_HEADLESS=false in your environment to open a visible browser window
    (needed for first-time phone/email verification).
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("[XCrawler] Playwright not available — skipping X browser crawl.")
        return []

    if not _X_USERNAME or not _X_PASSWORD:
        print("[XCrawler] X_USERNAME / X_PASSWORD not set in .env — skipping.")
        return []

    # Allow env override: X_HEADLESS=false → visible browser
    if os.getenv("X_HEADLESS", "true").lower() == "false":
        headless = False

    encoded_query = quote_plus(query)
    search_url = f"https://x.com/search?q={encoded_query}&f=live&src=typed_query"
    results: List[CrawlResult] = []

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=headless,
            args=_STEALTH_ARGS,
            slow_mo=50,
        )

        context_kwargs = dict(
            viewport={"width": 1280, "height": 900},
            user_agent=_USER_AGENT,
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            },
        )

        if os.path.exists(_AUTH_STATE_PATH):
            context: BrowserContext = await browser.new_context(
                storage_state=_AUTH_STATE_PATH,
                **context_kwargs,
            )
            print("[XCrawler] Loaded saved X auth state.")
        else:
            context = await browser.new_context(**context_kwargs)

        # Spoof navigator.webdriver to hide Playwright from bot detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        """)

        page: Page = await context.new_page()

        try:
            # Check if already logged in
            print("[XCrawler] Checking X login status…")
            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=25_000)
            await asyncio.sleep(3)
            await _dismiss_cookie_banner(page)

            current_url = page.url
            print(f"[XCrawler] Home URL: {current_url}")
            logged_in = "home" in current_url and "login" not in current_url

            if not logged_in:
                print("[XCrawler] Not logged in — attempting login…")
                logged_in = await _do_login(page, _X_USERNAME, _X_PASSWORD)
                if logged_in:
                    await context.storage_state(path=_AUTH_STATE_PATH)
                    print(f"[XCrawler] ✅ Auth state saved → {_AUTH_STATE_PATH}")

            if not logged_in:
                print("[XCrawler] ❌ Login failed — returning empty results.")
                return []

            # Navigate to search
            print(f"[XCrawler] Searching X: {query!r}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(4)

            # Ensure Latest tab
            if "f=live" not in page.url:
                try:
                    latest_tab = page.locator("a[href*='f=live']")
                    if await latest_tab.count() > 0:
                        await latest_tab.first.click()
                        await asyncio.sleep(2)
                except Exception:
                    pass

            results = await _extract_tweets(page, limit)

        except Exception as e:
            print(f"[XCrawler] Crawl error: {e}")
        finally:
            await browser.close()

    return results
