"""
selenium_instagram_crawler.py — Selenium-based Instagram hashtag/keyword crawler.

⚠️  Instagram requires login to view any content (confirmed by debug output).
    Set credentials in your .env file:
        INSTAGRAM_USERNAME=your_account@email.com
        INSTAGRAM_PASSWORD=your_password

Strategy:
  1. Launch Chrome via Selenium (visible mode to reduce bot detection).
  2. Log into Instagram using env-var credentials.
  3. Navigate to hashtag keyword search page.
  4. Collect post/reel links from the grid.
  5. Visit each post to extract caption, reel description, author, comments.
  6. Falls back to curated CTI stubs if login fails or Instagram blocks.

Requirements:
  pip install selenium webdriver-manager python-dotenv
"""
from __future__ import annotations

import asyncio
import datetime
import hashlib
import os
import random
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from crawlers.base_crawler import CrawlResult, EngagementMetrics


# Load .env so INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD are available
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
    print("[SeleniumInstagram] Selenium is available.")
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[SeleniumInstagram] selenium not installed — will use fallback stubs.")


# ── Chrome version detection ──────────────────────────────────────────────────

def _get_chrome_version() -> Optional[str]:
    import subprocess, re as _re
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in chrome_paths:
        try:
            result = subprocess.run(
                [path, "--version"], capture_output=True, text=True, timeout=5
            )
            match = _re.search(r"(\d+)\.\d+\.\d+\.\d+", result.stdout)
            if match:
                return match.group(1)
        except Exception:
            pass
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        ver, _ = winreg.QueryValueEx(key, "version")
        return ver.split(".")[0]
    except Exception:
        pass
    return None


# ── Driver factory ────────────────────────────────────────────────────────────

def _build_driver(headless: bool = False) -> "webdriver.Chrome":
    """
    Build a Chrome WebDriver with stealth settings.
    headless=False by default — Instagram detects and blocks headless mode.

    IMPORTANT: Uses a fresh temporary profile (NOT the user's default Chrome
    profile) so it always logs in with the .env credentials, not the personal
    account that may already be logged in on the user's browser.
    """
    import tempfile
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")

    # ── Fresh isolated profile — prevents inheriting personal Chrome sessions ──
    # Use a dedicated temp dir so each scraper run starts clean
    # NOTE: --incognito is intentionally NOT set here — it conflicts with
    # --user-data-dir and causes Chrome to silently fail or ignore the flag.
    temp_profile = os.path.join(tempfile.gettempdir(), "selenium_ig_profile")
    os.makedirs(temp_profile, exist_ok=True)
    opts.add_argument(f"--user-data-dir={temp_profile}")

    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1366,768")
    opts.add_argument("--lang=en-US")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-popup-blocking")

    # Chrome version detection — hardcode 150 as override since subprocess
    # detection returns None on this machine (chrome.exe not on PATH)
    chrome_major = _get_chrome_version() or "150"  # ← known installed version
    print(f"[SeleniumInstagram] Using Chrome major version: {chrome_major}")
    opts.add_argument(
        f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Safari/537.36"
    )

    driver: Optional["webdriver.Chrome"] = None
    last_exc: Optional[Exception] = None

    # Option 1: webdriver-manager PINNED to Chrome 150 (not latest which is 151)
    if _WDM_AVAILABLE:
        try:
            driver_path = ChromeDriverManager(driver_version=chrome_major).install()
            print(f"[SeleniumInstagram] ChromeDriver path: {driver_path}")
            svc = ChromeService(driver_path)
            driver = webdriver.Chrome(service=svc, options=opts)
            print(f"[SeleniumInstagram] Driver started (webdriver-manager v{chrome_major})")
        except Exception as e:
            last_exc = e
            print(f"[SeleniumInstagram] webdriver-manager failed: {e}")

    # Option 2: Selenium built-in manager
    if driver is None:
        try:
            driver = webdriver.Chrome(options=opts)
            print("[SeleniumInstagram] Driver started (Selenium built-in manager)")
        except Exception as e:
            last_exc = e
            print(f"[SeleniumInstagram] Selenium manager failed: {e}")

    if driver is None:
        raise WebDriverException(
            f"Could not start ChromeDriver. Last error: {last_exc}"
        )

    # Patch navigator.webdriver
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
    except Exception:
        pass

    return driver


# ── Instagram login ───────────────────────────────────────────────────────────

def _login_instagram(driver: "webdriver.Chrome", username: str, password: str) -> bool:
    """
    Log into Instagram. Returns True if login succeeded.
    """
    import tempfile
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        wait = WebDriverWait(driver, 20)
        time.sleep(random.uniform(3.5, 5.0))   # longer initial wait for JS to render

        print(f"[SeleniumInstagram] Login page title: {driver.title}")
        print(f"[SeleniumInstagram] Login page URL: {driver.current_url}")

        # Check if already logged in from a previous cached session
        if "login" not in driver.current_url:
            print("[SeleniumInstagram] ✅ Already logged in (session restored)! Skipping login form.")
            return True

        # Accept cookie / GDPR dialogs (try many button texts)
        cookie_xpaths = [
            "//button[contains(text(),'Allow all cookies')]",
            "//button[contains(text(),'Allow all')]",
            "//button[contains(text(),'Accept all')]",
            "//button[contains(text(),'Accept')]",
            "//button[contains(text(),'Allow essential')]",
            "//button[contains(text(),'Decline optional')]",
        ]
        for xpath in cookie_xpaths:
            try:
                btns = driver.find_elements(By.XPATH, xpath)
                for btn in btns:
                    if btn.is_displayed():
                        btn.click()
                        print(f"[SeleniumInstagram] Clicked cookie button: {btn.text[:40]!r}")
                        time.sleep(1.0)
                        break
            except Exception:
                pass

        time.sleep(2.0)

        # Use JS to check if login form is in DOM
        has_form = driver.execute_script(
            "return !!document.querySelector('input[name=username]')"
        )
        if not has_form:
            # Take screenshot to diagnose
            ss = os.path.join(tempfile.gettempdir(), "ig_login_fail.png")
            driver.save_screenshot(ss)
            print(f"[SeleniumInstagram] ⚠️  Username input NOT found in DOM. Screenshot: {ss}")
            print(f"[SeleniumInstagram] Page title: {driver.title} | URL: {driver.current_url}")
            # Try navigating directly to login again
            driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(4.0)

        # Instagram uses either name='username'/'password' OR name='email'/'pass'
        # (Meta/Facebook-style form). Try both variants.
        u_field = None
        for u_name in ["username", "email"]:
            try:
                u_field = wait.until(EC.presence_of_element_located((By.NAME, u_name)))
                print(f"[SeleniumInstagram] Found username field: name='{u_name}'")
                break
            except Exception:
                pass

        if not u_field:
            print("[SeleniumInstagram] ❌ Could not find any username/email input field!")
            return False

        u_field.clear()
        time.sleep(0.3)
        for ch in username:
            u_field.send_keys(ch)
            time.sleep(random.uniform(0.05, 0.13))
        print(f"[SeleniumInstagram] Typed username: {username}")

        time.sleep(random.uniform(0.5, 1.0))

        # Password field: try 'password' then 'pass'
        p_field = None
        for p_name in ["password", "pass"]:
            try:
                p_field = driver.find_element(By.NAME, p_name)
                print(f"[SeleniumInstagram] Found password field: name='{p_name}'")
                break
            except Exception:
                pass

        if not p_field:
            print("[SeleniumInstagram] ❌ Could not find any password input field!")
            return False

        p_field.clear()
        time.sleep(0.3)
        for ch in password:
            p_field.send_keys(ch)
            time.sleep(random.uniform(0.05, 0.10))
        print(f"[SeleniumInstagram] Typed password ({len(password)} chars)")

        time.sleep(random.uniform(0.5, 1.0))
        p_field.send_keys(Keys.RETURN)

        # Wait for home page / feed / onetap to load
        time.sleep(random.uniform(5.0, 7.0))

        # Dismiss "Save login info" / "Turn on notifications" dialogs
        skip_texts = ["not now", "skip", "close", "maybe later", "decline", "cancel", "later", "save info"]
        for _ in range(2):
            try:
                for btn in driver.find_elements(By.TAG_NAME, "button"):
                    if btn.is_displayed():
                        txt = btn.text.strip().lower()
                        if any(s in txt for s in skip_texts):
                            btn.click()
                            time.sleep(1.0)
                            break
            except Exception:
                pass
            time.sleep(1.0)

        # Check if login succeeded
        current = driver.current_url
        title = driver.title
        print(f"[SeleniumInstagram] After login — URL: {current} | Title: {title}")

        if "login" in current.lower() or "Page couldn't load" in title:
            ss = os.path.join(tempfile.gettempdir(), "ig_login_fail.png")
            driver.save_screenshot(ss)
            print(f"[SeleniumInstagram] Login FAILED — screenshot: {ss}")
            return False

        print(f"[SeleniumInstagram] ✅ Login succeeded! URL: {current}")
        return True

    except Exception as e:
        import traceback
        print(f"[SeleniumInstagram] Login error: {e}")
        traceback.print_exc()
        return False


# ── Core scraping logic (synchronous — runs in executor) ─────────────────────

def _scrape_instagram_sync(
    query: str,
    limit: int = 10,
    fetch_comments: bool = False,
    time_filter: str = "all",
) -> List[Dict[str, Any]]:
    """
    Synchronous blocking Instagram scraper using Selenium.
    Logs in first (required since Instagram blocks unauthenticated browsing),
    then scrapes hashtag search results.
    """
    if not SELENIUM_AVAILABLE:
        return []

    # Re-load .env every time so edits take effect WITHOUT restarting the server.
    _env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    try:
        from dotenv import load_dotenv as _load
        _load(dotenv_path=os.path.abspath(_env_path), override=True)
    except Exception:
        pass

    username = os.getenv("INSTAGRAM_USERNAME", "").strip()
    password = os.getenv("INSTAGRAM_PASSWORD", "").strip()

    PLACEHOLDERS = {"your_instagram_username_or_email", "your_instagram_password", "", "your_account@email.com"}
    if username in PLACEHOLDERS or password in PLACEHOLDERS or not username or not password:
        print(
            "[SeleniumInstagram] ❌ INSTAGRAM credentials not configured in .env!\n"
            f"   Current INSTAGRAM_USERNAME='{username}'\n"
            "   Please edit backend/.env and set real credentials."
        )
        return []

    tag = re.sub(r"[\s#]+", "", query.strip().lower())
    results: List[Dict[str, Any]] = []
    driver: Optional["webdriver.Chrome"] = None

    # ── Helper: parse K/M/B suffixed numbers ─────────────────────────────────
    def _parse_num(s: str) -> int:
        if not s:
            return 0
        s = s.strip().upper().replace(",", "").replace(".", "")
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

    # ── Helper: extract all /p/ and /reel/ links via JavaScript ──────────────
    def _collect_links_js(drv) -> List[str]:
        try:
            links = drv.execute_script("""
                var seen = {};
                var out = [];
                document.querySelectorAll('a[href]').forEach(function(a) {
                    var h = a.href || '';
                    if ((h.indexOf('/p/') !== -1 || h.indexOf('/reel/') !== -1)
                            && h.indexOf('instagram.com') !== -1
                            && !seen[h]) {
                        seen[h] = 1;
                        out.push(h);
                    }
                });
                return out;
            """)
            return links if isinstance(links, list) else []
        except Exception:
            return []

    # ── Helper: extract a single meta-tag content ─────────────────────────────
    def _meta(drv, selector: str) -> str:
        try:
            el = drv.find_element(By.CSS_SELECTOR, selector)
            return (el.get_attribute("content") or "").strip()
        except Exception:
            return ""

    # ── Helper: safe page get with timeout fallback ───────────────────────────
    def _safe_get(drv, url: str) -> bool:
        try:
            drv.get(url)
            return True
        except TimeoutException:
            print(f"[SeleniumInstagram] ⚠️ Page load timeout on {url} — skipping")
            try:
                drv.execute_script("window.stop();")
            except Exception:
                pass
            return False
        except Exception as e:
            print(f"[SeleniumInstagram] ⚠️ Navigation error on {url}: {e}")
            return False

    try:
        driver = _build_driver(headless=False)
        driver.set_page_load_timeout(25)

        # ── Step 1: Login ─────────────────────────────────────────────────────
        logged_in = _login_instagram(driver, username, password)
        if not logged_in:
            print("[SeleniumInstagram] Login failed — cannot scrape.")
            return []

        # ── Step 2: Build prioritised search URL list ─────────────────────────
        raw_query = query.strip()
        stop_words = {"the", "and", "for", "with", "about", "from", "this",
                      "that", "in", "on", "at", "of", "is", "are", "was"}
        words = [w for w in re.split(r"\s+", raw_query.lower())
                 if len(w) > 2 and w not in stop_words]

        candidate_urls: List[str] = []
        if words:
            candidate_urls.append(
                f"https://www.instagram.com/explore/tags/{quote_plus(words[0])}/"
            )
        if len(words) >= 2:
            candidate_urls.append(
                f"https://www.instagram.com/explore/tags/{quote_plus(words[0] + words[1])}/"
            )
        candidate_urls.append(
            f"https://www.instagram.com/explore/tags/{quote_plus(tag)}/"
        )
        candidate_urls.append(
            f"https://www.instagram.com/explore/search/keyword/?q={quote_plus(raw_query)}"
        )
        seen_u: set = set()
        search_urls = [u for u in candidate_urls if not (u in seen_u or seen_u.add(u))]  # type: ignore

        post_links: List[str] = []

        # ── Step 3: Visit search URLs and collect post links via scrolling ────
        for search_url in search_urls:
            if len(post_links) >= limit:
                break
            print(f"[SeleniumInstagram] Trying URL: {search_url}")
            if not _safe_get(driver, search_url):
                continue
            time.sleep(random.uniform(3.0, 4.5))

            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if any(s in body_text for s in ["No results", "couldn't find anything",
                                                  "Page Not Found", "Sorry, this page"]):
                    print(f"[SeleniumInstagram] ✗ No results at {search_url}")
                    continue
            except Exception:
                pass

            max_scrolls = max(20, (limit // 5) + 10)
            no_new_streak = 0
            last_count = 0
            print(f"[SeleniumInstagram] Scrolling up to {max_scrolls}× (need ≥{limit})...")

            for scroll_i in range(max_scrolls):
                # Scroll to absolute document bottom — triggers Instagram lazy loader
                driver.execute_script(
                    "window.scrollTo(0, "
                    "document.documentElement.scrollHeight || document.body.scrollHeight);"
                )
                time.sleep(random.uniform(1.5, 2.2))

                # Occasional micro-nudge to jolt lazy loader
                if scroll_i % 3 == 0:
                    driver.execute_script("window.scrollBy(0, -400);")
                    time.sleep(0.4)
                    driver.execute_script("window.scrollBy(0, 600);")
                    time.sleep(0.4)

                # Collect all /p/ and /reel/ hrefs via a single JS call
                added = 0
                for href in _collect_links_js(driver):
                    clean = re.sub(r"\?.*$", "", href).rstrip("/") + "/"
                    if clean not in post_links:
                        post_links.append(clean)
                        added += 1

                print(f"[SeleniumInstagram]   scroll {scroll_i+1}/{max_scrolls}: "
                      f"{len(post_links)} links (+{added})")

                if len(post_links) >= limit:
                    break

                if len(post_links) == last_count:
                    no_new_streak += 1
                    if no_new_streak >= 5:
                        print(f"[SeleniumInstagram] Stale ({no_new_streak} scrolls) — next URL")
                        break
                else:
                    no_new_streak = 0
                last_count = len(post_links)

            print(f"[SeleniumInstagram] ↳ {len(post_links)} links after {search_url}")

        if not post_links:
            print(f"[SeleniumInstagram] All URLs exhausted — no posts for '{raw_query}'")
            return []

        print(f"[SeleniumInstagram] ✅ {len(post_links)} unique links collected")

        # ── Step 4: Visit each post and extract content ───────────────────────
        to_visit = post_links[:min(limit, len(post_links))]
        budget_s = max(240, len(to_visit) * 15)
        t0 = time.monotonic()
        _NO_FILTER = {"any", "all", "", "none"}
        _FILTER_HOURS = {"24h": 24, "48h": 48, "1week": 168, "1month": 720}
        print(f"[SeleniumInstagram] Visiting {len(to_visit)} posts (budget {budget_s}s)...")

        for post_url in to_visit:
            if time.monotonic() - t0 > budget_s:
                print(f"[SeleniumInstagram] ⏰ Budget exhausted — {len(results)} posts")
                break

            try:
                if not _safe_get(driver, post_url):
                    continue
                time.sleep(random.uniform(1.2, 2.0))

                is_reel = "/reel/" in post_url
                caption = ""
                author  = "@ig_public"
                likes   = 0
                comments_count = 0
                post_date = None

                # ── A. Open Graph meta tags (PRIMARY) ────────────────────────
                og_desc   = _meta(driver, "meta[property='og:description']")
                og_title  = _meta(driver, "meta[property='og:title']")
                meta_desc = _meta(driver, "meta[name='description']")

                # Caption: og:description = full caption text
                if og_desc and og_desc.lower() not in {"instagram", ""}:
                    caption = og_desc

                # Author from og:title
                # "username on Instagram: 'caption'" or "Name (@handle) • Instagram"
                if og_title:
                    m = re.match(
                        r'^([A-Za-z0-9_.]+)\s+(?:\(@[^)]+\)\s+)?on\s+Instagram',
                        og_title, re.IGNORECASE
                    )
                    if m:
                        author = f"@{m.group(1).strip()}"
                    else:
                        m2 = re.search(r'\(@([A-Za-z0-9_.]+)\)', og_title)
                        if m2:
                            author = f"@{m2.group(1)}"

                # Likes / comments from meta[name='description']
                # "390K Likes, 1,223 Comments - username on July 22, 2026: 'caption'"
                if meta_desc:
                    ml = re.search(r'([\d.,KkMmBb]+)\s*[Ll]ikes?', meta_desc)
                    mc = re.search(r'([\d.,KkMmBb]+)\s*[Cc]omments?', meta_desc)
                    if ml:
                        likes = _parse_num(ml.group(1))
                    if mc:
                        comments_count = _parse_num(mc.group(1))
                    if not caption:
                        cap_m = re.search(
                            r'[A-Za-z0-9_.]+\s+on\s+[A-Za-z]+\s+\d+,\s+\d{4}\s*:\s*["\']?(.*)',
                            meta_desc, re.DOTALL
                        )
                        if cap_m:
                            caption = cap_m.group(1).strip().strip("\"'")

                # ── B. Page title fallback ────────────────────────────────────
                if not caption or caption.lower() in {"instagram", ""}:
                    ptitle = driver.title or ""
                    m_t = re.search(
                        r'(?:([\d.,kKmM]+)\s*likes?,\s*)?'
                        r'(?:([\d.,kKmM]+)\s*comments?\s*-\s*)?'
                        r'([A-Za-z0-9_.]+)\s+on\s+([A-Za-z]+\s+\d+,\s+\d{4})\s*:\s*["\']?(.*)',
                        ptitle, re.DOTALL
                    )
                    if m_t:
                        ls, cs, aus, ds, caps = m_t.groups()
                        if caps:
                            caption = caps.strip().strip("\"'")
                        if aus and author == "@ig_public":
                            author = f"@{aus}"
                        if ls and likes == 0:
                            likes = _parse_num(ls)
                        if cs and comments_count == 0:
                            comments_count = _parse_num(cs)

                # ── C. DOM fallback — h1 then first long span ─────────────────
                if not caption or caption.lower() in {"instagram", ""}:
                    try:
                        for h1 in driver.find_elements(By.TAG_NAME, "h1"):
                            txt = h1.text.strip()
                            if len(txt) > 15:
                                caption = txt
                                break
                    except Exception:
                        pass

                if not caption or caption.lower() in {"instagram", ""}:
                    try:
                        for sp in driver.find_elements(
                                By.CSS_SELECTOR, "span[dir='auto']"):
                            txt = sp.text.strip()
                            if len(txt) > 30 and txt.lower() != "instagram":
                                caption = txt
                                break
                    except Exception:
                        pass

                # ── D. Author from article profile link ───────────────────────
                if author == "@ig_public":
                    try:
                        for a_el in driver.find_elements(
                                By.CSS_SELECTOR, "article a[href^='/']"):
                            hv = a_el.get_attribute("href") or ""
                            m_u = re.search(
                                r'instagram\.com/([A-Za-z0-9_.]{2,30})/?$', hv
                            )
                            if m_u:
                                cand = m_u.group(1)
                                if cand not in {"explore", "p", "reel", "reels",
                                                "stories", "direct", "accounts"}:
                                    author = f"@{cand}"
                                    break
                    except Exception:
                        pass

                # ── E. Date extraction ────────────────────────────────────────
                try:
                    tel = driver.find_element(By.CSS_SELECTOR, "time[datetime]")
                    dt_s = tel.get_attribute("datetime") or ""
                    if dt_s:
                        import dateutil.parser
                        post_date = dateutil.parser.isoparse(dt_s).replace(tzinfo=None)
                except Exception:
                    pass

                if not post_date and meta_desc:
                    md = re.search(r'on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', meta_desc)
                    if md:
                        try:
                            post_date = datetime.datetime.strptime(md.group(1), "%B %d, %Y")
                        except Exception:
                            pass

                # ── F. Time filter ────────────────────────────────────────────
                if post_date and time_filter not in _NO_FILTER:
                    age_h = (datetime.datetime.now() - post_date).total_seconds() / 3600
                    max_h = _FILTER_HOURS.get(time_filter, 0)
                    if max_h > 0 and age_h > max_h:
                        print(f"[SeleniumInstagram] ⏩ Skipping (age={age_h:.0f}h > {time_filter})")
                        continue

                # ── G. Comments (only when fetch_comments=True) ───────────────
                post_comments: List[Dict[str, str]] = []
                if fetch_comments:
                    try:
                        seen_c: set = set()
                        skip_ui = {"reply", "hide replies", "see translation",
                                   "load more comments", "view more comments"}
                        for sp in driver.find_elements(
                                By.CSS_SELECTOR, "span[dir='auto']"):
                            txt = sp.text.strip()
                            ltxt = txt.lower()
                            if (txt and len(txt) > 3 and txt not in seen_c
                                    and ltxt not in skip_ui
                                    and " likes" not in ltxt
                                    and not (ltxt.startswith("view all")
                                             and "replies" in ltxt)
                                    and txt != caption):
                                post_comments.append({"author": "user", "text": txt[:300]})
                                seen_c.add(txt)
                            if len(post_comments) >= 20:
                                break
                    except Exception as ce:
                        print(f"[SeleniumInstagram] Comment extraction failed: {ce}")

                # ── H. Build result ───────────────────────────────────────────
                sc = re.search(r"/(?:p|reel)/([A-Za-z0-9_-]+)/?", post_url)
                shortcode = sc.group(1) if sc else uuid.uuid4().hex[:8]
                uid = hashlib.md5(shortcode.encode()).hexdigest()[:10]
                hashtags = re.findall(r"#(\w+)", caption) or [tag]
                ctype = "REEL" if is_reel else "POST"

                if not caption or caption.lower() in {"instagram", ""}:
                    caption = f"Instagram {ctype.lower()} about #{tag}"

                print(f"[SeleniumInstagram] ✅ {ctype} | {author} | "
                      f"{likes:,}L {comments_count:,}C | {caption[:80]!r}")

                results.append({
                    "id": f"ig-{uid}",
                    "platform": "Instagram",
                    "author_username": author,
                    "author_id": f"ig_{uid}",
                    "content": caption[:600],
                    "url": post_url,
                    "hashtags": hashtags,
                    "language": "en",
                    "likes": likes,
                    "post_comments": post_comments,
                    "shortcode": shortcode,
                    "content_type": ctype,
                    "source_type": "SELENIUM_INSTAGRAM",
                    "crawled_at": datetime.datetime.utcnow().isoformat(),
                    "created_at": (post_date.isoformat() if post_date
                                   else datetime.datetime.utcnow().isoformat()),
                })

            except Exception as exc:
                print(f"[SeleniumInstagram] Error on {post_url}: {exc}")
                continue

    except WebDriverException as exc:
        print(f"[SeleniumInstagram] WebDriver error: {exc}")
    except Exception as exc:
        import traceback
        print(f"[SeleniumInstagram] Unexpected error: {exc}")
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    print(f"[SeleniumInstagram] 🏁 Done — {len(results)} posts for '{query}'")
    return results


# ── Fallback stub generator ───────────────────────────────────────────────────

def _generate_fallback_stubs(tag: str, limit: int) -> List[CrawlResult]:
    """Returns realistic CTI stubs when scraping is unavailable."""
    samples = [
        f"⚠️ Alert near market area! Tensions rising. Stay safe. #SuratAlert #GujaratPolice #{tag}",
        f"Fact Check: Viral video about #{tag} is MISLEADING. Official sources clarify. #FactCheck",
        f"🔥 Rumour spreading about #{tag} — Police on ground, situation monitored. #GujaratCyberWatch",
        f"Community update: Peace maintained in #{tag} zone. Authorities request calm. #AhmedabadUpdates",
        f"Breaking: Coordinated misinformation campaign detected around #{tag}. #CyberAlert #InstaWatch",
    ]
    results = []
    for text in samples[:limit]:
        uid = uuid.uuid4().hex[:8]
        results.append(CrawlResult(
            id=f"ig-stub-{uid}",
            platform="Instagram",
            author_username=f"@ig_monitor_{uid[:4]}",
            author_id=f"ig_{uid}",
            content=text,
            url=f"https://www.instagram.com/explore/tags/{tag}/",
            hashtags=re.findall(r"#(\w+)", text),
            language="en",
            engagement=EngagementMetrics(
                likes=random.randint(100, 5000),
                comments=random.randint(10, 300),
                shares=random.randint(5, 200),
            ),
            source_type="SELENIUM_IG_STUB",
            crawled_at=datetime.datetime.utcnow().isoformat(),
            created_at=datetime.datetime.utcnow().isoformat(),
        ))
    return results


# ── Public async entry-point ──────────────────────────────────────────────────

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="selenium_ig")


async def selenium_instagram_search(
    query: str,
    limit: int = 10,
    fetch_comments: bool = False,
    time_filter: str = "all",
) -> List[CrawlResult]:
    """
    Async wrapper — runs blocking Selenium in a thread executor.
    Falls back to stubs if credentials are missing or scraping fails.
    """
    tag = re.sub(r"[\s#]+", "", query.strip().lower())
    results: List[CrawlResult] = []

    if SELENIUM_AVAILABLE:
        try:
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(
                _executor,
                lambda: _scrape_instagram_sync(query, limit, fetch_comments, time_filter),
            )
            for r in raw:
                results.append(CrawlResult(
                    id=r["id"],
                    platform=r["platform"],
                    author_username=r["author_username"],
                    author_id=r["author_id"],
                    content=r["content"],
                    url=r["url"],
                    hashtags=r["hashtags"],
                    language=r["language"],
                    engagement=EngagementMetrics(
                        likes=r.get("likes", 0),
                        comments=len(r.get("post_comments", [])),
                    ),
                    comments=r.get("post_comments", []),
                    source_type=r["source_type"],
                    crawled_at=r["crawled_at"],
                    created_at=r["created_at"],
                ))
        except Exception as exc:
            print(f"[SeleniumInstagram] Executor error: {exc}")

    if not results:
        print(f"[SeleniumInstagram] No live results for #{tag} — using fallback stubs.")
        results = _generate_fallback_stubs(tag, min(limit, 5))


    return results[:limit]

def _generate_fallback_stubs(tag: str, limit: int) -> List[CrawlResult]:
    """Returns realistic CTI stubs when scraping is unavailable."""
    samples = [
        f"⚠️ Alert near market area! Tensions rising. Stay safe. #SuratAlert #GujaratPolice #{tag}",
        f"Fact Check: Viral video about #{tag} is MISLEADING. Official sources clarify. #FactCheck",
        f"🔥 Rumour spreading about #{tag} — Police on ground, situation monitored. #GujaratCyberWatch",
        f"Community update: Peace maintained in #{tag} zone. Authorities request calm. #AhmedabadUpdates",
        f"Breaking: Coordinated misinformation campaign detected around #{tag}. #CyberAlert #InstaWatch",
    ]
    results = []
    for text in samples[:limit]:
        uid = uuid.uuid4().hex[:8]
        results.append(CrawlResult(
            id=f"ig-stub-{uid}",
            platform="Instagram",
            author_username=f"@ig_monitor_{uid[:4]}",
            author_id=f"ig_{uid}",
            content=text,
            url=f"https://www.instagram.com/explore/tags/{tag}/",
            hashtags=re.findall(r"#(\w+)", text),
            language="en",
            engagement=EngagementMetrics(
                likes=random.randint(100, 5000),
                comments=random.randint(10, 300),
                shares=random.randint(5, 200),
            ),
            source_type="SELENIUM_IG_STUB",
            crawled_at=datetime.datetime.utcnow().isoformat(),
            created_at=datetime.datetime.utcnow().isoformat(),
        ))
    return results


# ── Public async entry-point ──────────────────────────────────────────────────

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="selenium_ig")


async def selenium_instagram_search(
    query: str,
    limit: int = 10,
    fetch_comments: bool = False,
    time_filter: str = "all",
) -> List[CrawlResult]:
    """
    Async wrapper — runs blocking Selenium in a thread executor.
    Falls back to stubs if credentials are missing or scraping fails.
    """
    tag = re.sub(r"[\s#]+", "", query.strip().lower())
    results: List[CrawlResult] = []

    if SELENIUM_AVAILABLE:
        try:
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(
                _executor,
                lambda: _scrape_instagram_sync(query, limit, fetch_comments, time_filter),
            )
            for r in raw:
                results.append(CrawlResult(
                    id=r["id"],
                    platform=r["platform"],
                    author_username=r["author_username"],
                    author_id=r["author_id"],
                    content=r["content"],
                    url=r["url"],
                    hashtags=r["hashtags"],
                    language=r["language"],
                    engagement=EngagementMetrics(
                        likes=r.get("likes", 0),
                        comments=len(r.get("post_comments", [])),
                    ),
                    comments=r.get("post_comments", []),
                    source_type=r["source_type"],
                    crawled_at=r["crawled_at"],
                    created_at=r["created_at"],
                ))
        except Exception as e:
            print(f"[SeleniumInstagram] Executor error: {e}")

    if not results:
        print(f"[SeleniumInstagram] No live results for #{tag} — using fallback stubs.")
        results = _generate_fallback_stubs(tag, min(limit, 5))

    return results[:limit]
