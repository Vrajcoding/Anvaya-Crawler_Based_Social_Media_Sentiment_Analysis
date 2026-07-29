"""
selenium_x_crawler.py — Selenium-based X (Twitter) search crawler.

Strategy:
  1. Launch Chrome via Selenium (reuses same driver factory as Instagram crawler).
  2. Log into x.com using X_USERNAME / X_PASSWORD from .env.
     Handles X's current login form at /i/jf/onboarding/web?mode=login:
       - Single-field: "Email or username" → Continue → password → Log in
  3. Navigate to x.com/search?q=<query>&f=live (Latest tab).
  4. Scroll and extract tweet cards using stable data-testid selectors.
  5. Return CrawlResult objects with source_type="SELENIUM_X".

Falls back gracefully to [] on any failure so the caller can try
Nitter mirrors or synthetic stubs.

Requirements (all already installed for Instagram):
  pip install selenium webdriver-manager python-dotenv

Credentials:
  Set in .env:
    X_USERNAME=your_x_email_or_handle
    X_PASSWORD=your_x_password
  Optional: set X_HEADLESS=false to open a visible window.
"""
from __future__ import annotations

import asyncio
import datetime
import hashlib
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from urllib.parse import quote_plus

# ── dotenv ────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Selenium availability check ───────────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import (
        TimeoutException,
        NoSuchElementException,
        WebDriverException,
    )
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        _WDM_AVAILABLE = True
    except ImportError:
        _WDM_AVAILABLE = False
    SELENIUM_AVAILABLE = True
    print("[SeleniumX] Selenium available.")
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[SeleniumX] selenium not installed — X Selenium crawler disabled.")

from crawlers.base_crawler import CrawlResult, EngagementMetrics

# ── Credentials ───────────────────────────────────────────────────────────────
_X_USERNAME: str = os.getenv("X_USERNAME", "")
_X_PASSWORD: str = os.getenv("X_PASSWORD", "")
_X_HEADLESS: bool = os.getenv("X_HEADLESS", "false").lower() != "false"

# ── Driver factory (mirrors selenium_instagram_crawler._build_driver) ─────────

def _build_x_driver() -> "webdriver.Chrome":
    """
    Build a Chrome WebDriver with stealth settings for X.
    Uses a dedicated profile dir so it never conflicts with Instagram sessions.
    """
    import tempfile
    opts = ChromeOptions()

    if _X_HEADLESS:
        opts.add_argument("--headless=new")

    # Dedicated isolated profile
    profile_dir = os.path.join(tempfile.gettempdir(), "selenium_x_profile")
    os.makedirs(profile_dir, exist_ok=True)
    opts.add_argument(f"--user-data-dir={profile_dir}")

    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1366,768")
    opts.add_argument("--lang=en-US")
    opts.add_argument("--disable-notifications")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    driver: Optional["webdriver.Chrome"] = None
    last_exc: Optional[Exception] = None

    # Option 1: webdriver-manager
    if _WDM_AVAILABLE:
        try:
            path = ChromeDriverManager().install()
            driver = webdriver.Chrome(service=ChromeService(path), options=opts)
            print("[SeleniumX] Driver started via webdriver-manager.")
        except Exception as e:
            last_exc = e
            print(f"[SeleniumX] webdriver-manager failed: {e}")

    # Option 2: Selenium built-in manager
    if driver is None:
        try:
            driver = webdriver.Chrome(options=opts)
            print("[SeleniumX] Driver started via Selenium built-in manager.")
        except Exception as e:
            last_exc = e
            print(f"[SeleniumX] Selenium manager failed: {e}")

    if driver is None:
        raise WebDriverException(f"Could not start ChromeDriver. Last error: {last_exc}")

    # Hide webdriver flag
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
    except Exception:
        pass

    return driver


# ── Login ─────────────────────────────────────────────────────────────────────

def _human_type(element, text: str, delay: float = 0.08) -> None:
    """Type text character-by-character to mimic human input."""
    element.clear()
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)


def _login_x(driver: "webdriver.Chrome", username: str, password: str) -> bool:
    """
    Log into X. Handles the current /i/jf/onboarding/web?mode=login form.

    X's current form flow (2025/2026):
      1. Show "Email or username" input field
      2. Click "Continue" (single-step — NOT a Next button that reveals password)
      3. Show password field on the SAME page or a new page
      4. Click "Log in"

    Returns True if login succeeded.
    """
    wait = WebDriverWait(driver, 20)

    try:
        print("[SeleniumX] Navigating to X login…")
        driver.get("https://x.com/i/flow/login")
        time.sleep(3)

        print(f"[SeleniumX] Login URL: {driver.current_url}")

        # ── Step 1: Fill username / email ─────────────────────────────────
        username_selectors = [
            (By.NAME, "username_or_email"),        # new jf form
            (By.CSS_SELECTOR, "input[autocomplete='username']"),  # old form
            (By.NAME, "text"),
            (By.CSS_SELECTOR, "input[type='text']"),
        ]

        username_el = None
        for by, sel in username_selectors:
            try:
                username_el = wait.until(EC.visibility_of_element_located((by, sel)))
                print(f"[SeleniumX] Username input: {sel}")
                break
            except TimeoutException:
                continue

        if username_el is None:
            print("[SeleniumX] ❌ Username input not found.")
            return False

        # Use JS to set value (bypasses React controlled input quirks)
        driver.execute_script(
            "arguments[0].focus(); arguments[0].value = ''; "
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
            username_el
        )
        time.sleep(0.3)
        _human_type(username_el, username)
        time.sleep(0.5)

        # ── Step 2: Click "Continue" / "Next" ─────────────────────────────
        submit_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[normalize-space()='Continue']"),
            (By.XPATH, "//button[normalize-space()='Next']"),
            (By.XPATH, "//div[@role='button'][normalize-space()='Next']"),
        ]
        clicked = False
        for by, sel in submit_selectors:
            try:
                btn = driver.find_element(by, sel)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    clicked = True
                    print(f"[SeleniumX] Clicked continue/next: {sel}")
                    break
            except NoSuchElementException:
                continue

        if not clicked:
            username_el.send_keys(Keys.RETURN)
            print("[SeleniumX] Pressed Enter to advance.")

        time.sleep(2.5)

        # ── Handle identity confirmation step (unusual login) ─────────────
        try:
            unusual_el = driver.find_element(By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']")
            if unusual_el.is_displayed():
                print("[SeleniumX] Identity confirmation step — entering username…")
                _human_type(unusual_el, username)
                unusual_el.send_keys(Keys.RETURN)
                time.sleep(2)
        except NoSuchElementException:
            pass

        # ── Step 3: Fill password ──────────────────────────────────────────
        pw_selectors = [
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
        ]

        pw_el = None
        for by, sel in pw_selectors:
            try:
                pw_el = wait.until(EC.visibility_of_element_located((by, sel)))
                print(f"[SeleniumX] Password input: {sel}")
                break
            except TimeoutException:
                continue

        if pw_el is None:
            print("[SeleniumX] ❌ Password input not found.")
            return False

        # JS-focus to avoid any overlapping element issues
        driver.execute_script(
            "arguments[0].focus(); arguments[0].value = ''; "
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
            pw_el
        )
        time.sleep(0.3)
        _human_type(pw_el, password)
        time.sleep(0.5)

        # ── Step 4: Click "Log in" ─────────────────────────────────────────
        login_selectors = [
            (By.CSS_SELECTOR, "button[data-testid='LoginForm_Login_Button']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[normalize-space()='Log in']"),
            (By.XPATH, "//div[@role='button'][normalize-space()='Log in']"),
        ]
        logged_in_click = False
        for by, sel in login_selectors:
            try:
                btn = driver.find_element(by, sel)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    logged_in_click = True
                    print(f"[SeleniumX] Clicked Log in: {sel}")
                    break
            except NoSuchElementException:
                continue

        if not logged_in_click:
            pw_el.send_keys(Keys.RETURN)
            print("[SeleniumX] Pressed Enter to submit.")

        # Wait for navigation
        time.sleep(5)
        current_url = driver.current_url
        print(f"[SeleniumX] Post-login URL: {current_url}")

        # ── Check for login error message ──────────────────────────────────
        try:
            error_els = driver.find_elements(By.CSS_SELECTOR, "[data-testid='toast'] span, .error-text, [aria-live='assertive'] span")
            for el in error_els:
                txt = el.text.strip()
                if txt and len(txt) > 5:
                    print(f"[SeleniumX] ⚠️  X error message: {txt}")
        except Exception:
            pass

        # ── Verify success ─────────────────────────────────────────────────
        if (
            "home" in current_url
            or (
                "x.com" in current_url
                and "login" not in current_url
                and "flow" not in current_url
                and "onboarding" not in current_url
            )
        ):
            print("[SeleniumX] ✅ Login successful!")
            return True

        if any(k in current_url for k in ("verify", "challenge", "phone", "confirm")):
            print("[SeleniumX] ⚠️  X requires phone/email verification.")
            print("    Set X_HEADLESS=false to complete verification manually.")
            return False

        print(f"[SeleniumX] Login did not succeed. URL: {current_url}")
        return False

    except Exception as e:
        print(f"[SeleniumX] Login error: {e}")
        return False


# ── Tweet extraction ──────────────────────────────────────────────────────────

def _parse_count(s: str) -> int:
    if not s:
        return 0
    s = s.replace(",", "").strip()
    try:
        if s.upper().endswith("K"):
            return int(float(s[:-1]) * 1_000)
        if s.upper().endswith("M"):
            return int(float(s[:-1]) * 1_000_000)
        return int(float(s))
    except Exception:
        return 0


def _extract_tweets_selenium(driver: "webdriver.Chrome", limit: int) -> List[CrawlResult]:
    """
    Scroll the X search results page and extract tweet cards.
    Uses stable data-testid attributes.
    """
    results: List[CrawlResult] = []
    seen_ids: set = set()
    max_scrolls = 15
    scroll_count = 0
    no_new_streak = 0

    while len(results) < limit and scroll_count < max_scrolls:
        tweet_els = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
        before = len(results)

        for tweet_el in tweet_els:
            if len(results) >= limit:
                break
            try:
                # Author handle
                handle = ""
                try:
                    user_div = tweet_el.find_element(By.CSS_SELECTOR, "div[data-testid='User-Name']")
                    spans = user_div.find_elements(By.TAG_NAME, "span")
                    for sp in spans:
                        txt = sp.text.strip()
                        if txt.startswith("@"):
                            handle = txt
                            break
                except NoSuchElementException:
                    pass

                if not handle:
                    try:
                        link = tweet_el.find_element(By.CSS_SELECTOR, "a[href*='/status/']")
                        href = link.get_attribute("href") or ""
                        parts = href.replace("https://x.com/", "").split("/")
                        if parts:
                            handle = f"@{parts[0]}"
                    except NoSuchElementException:
                        pass

                if not handle:
                    continue

                # Tweet text
                tweet_text = ""
                try:
                    text_el = tweet_el.find_element(By.CSS_SELECTOR, "div[data-testid='tweetText']")
                    tweet_text = text_el.text.strip()
                except NoSuchElementException:
                    pass

                # Timestamp & URL
                created_at = ""
                tweet_url = ""
                try:
                    time_el = tweet_el.find_element(By.TAG_NAME, "time")
                    created_at = time_el.get_attribute("datetime") or ""
                    # Walk up to parent <a>
                    link_el = driver.execute_script(
                        "return arguments[0].closest('a');", time_el
                    )
                    if link_el:
                        href = link_el.get_attribute("href") or ""
                        if "/status/" in href:
                            tweet_url = href
                except NoSuchElementException:
                    pass

                dedup_key = tweet_url or hashlib.md5(
                    (handle + tweet_text[:60]).encode()
                ).hexdigest()

                if dedup_key in seen_ids:
                    continue
                seen_ids.add(dedup_key)

                # Engagement
                likes = retweets = replies = 0
                for testid, target in [("like", "likes"), ("retweet", "retweets"), ("reply", "replies")]:
                    try:
                        btn = tweet_el.find_element(By.CSS_SELECTOR, f"button[data-testid='{testid}']")
                        spans = btn.find_elements(
                            By.CSS_SELECTOR,
                            "span[data-testid='app-text-transition-container'] span"
                        )
                        for sp in spans:
                            val = sp.text.strip()
                            if val:
                                parsed = _parse_count(val)
                                if target == "likes":
                                    likes = parsed
                                elif target == "retweets":
                                    retweets = parsed
                                else:
                                    replies = parsed
                                break
                    except NoSuchElementException:
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
                    source_type="SELENIUM_X",
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

        driver.execute_script("window.scrollBy(0, 1800)")
        time.sleep(2)
        scroll_count += 1

    print(f"[SeleniumX] Extracted {len(results)} tweets after {scroll_count} scrolls.")
    return results[:limit]


# ── Sync worker (runs in thread pool) ────────────────────────────────────────

def _sync_x_search(query: str, limit: int) -> List[CrawlResult]:
    """Synchronous X crawl — called from asyncio via run_in_executor."""
    if not SELENIUM_AVAILABLE:
        print("[SeleniumX] Selenium not installed.")
        return []
    if not _X_USERNAME or not _X_PASSWORD:
        print("[SeleniumX] X credentials not set in .env.")
        return []

    driver = None
    try:
        driver = _build_x_driver()
        encoded = quote_plus(query)
        search_url = f"https://x.com/search?q={encoded}&f=live&src=typed_query"

        # ── Check if already logged in (saved session) ────────────────────
        driver.get("https://x.com/home")
        time.sleep(3)
        current_url = driver.current_url
        print(f"[SeleniumX] Home URL: {current_url}")
        logged_in = "home" in current_url and "login" not in current_url

        if not logged_in:
            print("[SeleniumX] Not logged in — attempting login…")
            logged_in = _login_x(driver, _X_USERNAME, _X_PASSWORD)

        if not logged_in:
            print("[SeleniumX] ❌ Login failed.")
            return []

        # ── Navigate to search ────────────────────────────────────────────
        print(f"[SeleniumX] Searching: {query!r}")
        driver.get(search_url)
        time.sleep(4)

        # Make sure we're on Latest tab
        if "f=live" not in driver.current_url:
            try:
                latest = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='f=live']"))
                )
                latest.click()
                time.sleep(2)
            except Exception:
                pass

        return _extract_tweets_selenium(driver, limit)

    except Exception as e:
        print(f"[SeleniumX] Crawl error: {e}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


# ── Public async API ──────────────────────────────────────────────────────────

async def selenium_x_search(
    query: str,
    limit: int = 20,
    fetch_comments: bool = False,
) -> List[CrawlResult]:
    """
    Search X (Twitter) for real tweets using Selenium Chrome.
    Async wrapper — runs the blocking Selenium calls in a thread pool.
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        results = await loop.run_in_executor(
            pool, lambda: _sync_x_search(query, limit)
        )
    return results
