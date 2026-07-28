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

# Import the new Video OCR engine
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
try:
    from nlp.video_ocr import video_ocr
    print("[SeleniumInstagram] OCR Engine loaded successfully.")
except Exception as e:
    print(f"[SeleniumInstagram] ⚠️ OCR Engine could not be loaded: {e}")
    video_ocr = None

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
    # Use the directory of this file to find the backend .env reliably.
    _env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    try:
        from dotenv import load_dotenv as _load
        _load(dotenv_path=os.path.abspath(_env_path), override=True)
    except Exception:
        pass

    # Read credentials from environment
    username = os.getenv("INSTAGRAM_USERNAME", "").strip()
    password = os.getenv("INSTAGRAM_PASSWORD", "").strip()

    PLACEHOLDERS = {"your_instagram_username_or_email", "your_instagram_password", "", "your_account@email.com"}
    if username in PLACEHOLDERS or password in PLACEHOLDERS or not username or not password:
        print(
            "[SeleniumInstagram] ❌ INSTAGRAM credentials not configured in .env!\n"
            f"   Current INSTAGRAM_USERNAME='{username}'\n"
            "   Please edit backend/.env and set real credentials, then trigger a crawl again."
        )
        return []

    tag = re.sub(r"[\s#]+", "", query.strip().lower())
    results: List[Dict[str, Any]] = []
    driver: Optional["webdriver.Chrome"] = None

    try:
        driver = _build_driver(headless=False)   # visible mode — less detection

        # ── Step 1: Login ─────────────────────────────────────────────────────
        logged_in = _login_instagram(driver, username, password)
        if not logged_in:
            print("[SeleniumInstagram] Login failed — cannot scrape.")
            return []

        # ── Step 2: Build search URLs to try ────────────────────────────────
        # Strategy: try multiple URLs until we find posts.
        raw_query = query.strip()
        words = [w for w in re.split(r"\s+", raw_query.lower()) if len(w) > 2
                 and w not in {"the", "and", "for", "with", "about", "from", "this", "that", "in", "on", "at", "of"}]

        search_urls_to_try = []

        # 1. Exact keyword search
        search_urls_to_try.append(
            f"https://www.instagram.com/explore/search/keyword/?q={quote_plus(raw_query)}"
        )

        # 2. Keyword search without stop words (e.g. "surat protest" instead of "protests in surat")
        if len(words) > 0 and " ".join(words) != raw_query.lower():
            clean_query = " ".join(words)
            search_urls_to_try.append(
                f"https://www.instagram.com/explore/search/keyword/?q={quote_plus(clean_query)}"
            )

        # 3. Hashtag explore with first meaningful word
        if words:
            search_urls_to_try.append(
                f"https://www.instagram.com/explore/tags/{quote_plus(words[0])}/"
            )

        # 4. Hashtag explore with first two words joined (e.g. suratprotest)
        if len(words) >= 2:
            search_urls_to_try.append(
                f"https://www.instagram.com/explore/tags/{quote_plus(words[0] + words[1])}/"
            )

        post_links: List[str] = []

        for search_url in search_urls_to_try:
            if post_links:
                break
            print(f"[SeleniumInstagram] Trying URL: {search_url}")
            driver.get(search_url)
            time.sleep(random.uniform(3.5, 5.0))

            # Check for "No results" page
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                if "No results" in page_text or "couldn't find anything" in page_text:
                    print(f"[SeleniumInstagram] No results on {search_url} — trying next URL...")
                    continue
            except Exception:
                pass

            # Scroll to lazy-load the post grid
            for _ in range(5):
                driver.execute_script("window.scrollBy(0, 700);")
                time.sleep(random.uniform(0.7, 1.2))

            # ── Step 3: Collect post + reel links ─────────────────────────────
            for sel in ["a[href*='/p/']", "a[href*='/reel/']","a[href*='/reels/']"]:
                try:
                    for a in driver.find_elements(By.CSS_SELECTOR, sel):
                        href = a.get_attribute("href") or ""
                        if href and href not in post_links:
                            post_links.append(href)
                        if len(post_links) >= limit * 2:
                            break
                except Exception:
                    pass

            print(f"[SeleniumInstagram] Found {len(post_links)} links on {search_url}")

        if not post_links:
            print(f"[SeleniumInstagram] All URLs exhausted — no posts found for '{raw_query}'")
            return []

        print(f"[SeleniumInstagram] Total {len(post_links)} post/reel links collected")

        # ── Step 4: Visit each post to extract content ────────────────────────
        for post_url in post_links[:limit]:
            try:
                driver.get(post_url)
                time.sleep(random.uniform(2.5, 3.5))
                is_reel = "/reel/" in post_url

                # ---- Robust extraction via page title / meta tag ----
                caption = ""
                author = "@ig_public"
                likes = 0
                comments_count = 0
                post_date = None

                try:
                    # 1. Date extraction independent of title regex
                    try:
                        time_el = driver.find_element(By.CSS_SELECTOR, "time[datetime]")
                        dt_str = time_el.get_attribute("datetime")
                        if dt_str:
                            import dateutil.parser
                            post_date = dateutil.parser.isoparse(dt_str).replace(tzinfo=None)
                    except Exception:
                        pass
                        
                    title = driver.title or ""
                    # Instagram titles often look like:
                    # "390K likes, 1,223 comments - username on July 22, 2026: 'Caption text...'"
                    # Or: "username on July 22, 2026: 'Caption text...'"
                    
                    # Regex to extract all parts
                    pattern = r'(?:([\d.,kKmM]+)\s*likes?,\s*)?(?:([\d.,kKmM]+)\s*comments?\s*-\s*)?([^\s]+)\s+on\s+([A-Za-z]+\s+\d+,\s+\d{4})\s*:\s*["\'](.*)["\']'
                    m = re.search(pattern, title)
                    if m:
                        likes_str, comments_str, author_str, date_str, caption_str = m.groups()
                        
                        if caption_str:
                            caption = caption_str.strip()
                        if author_str:
                            author = f"@{author_str}" if not author_str.startswith("@") else author_str
                        
                        # Parse likes/comments with K/M multipliers
                        def parse_num(s):
                            if not s: return 0
                            s = s.upper().replace(',', '')
                            if 'K' in s: return int(float(s.replace('K', '')) * 1000)
                            if 'M' in s: return int(float(s.replace('M', '')) * 1000000)
                            return int(float(s))
                        
                        likes = parse_num(likes_str)
                        comments_count = parse_num(comments_str)
                        
                        # Fallback date parsing from title
                        if not post_date and date_str:
                            try:
                                post_date = datetime.datetime.strptime(date_str, "%B %d, %Y")
                            except Exception:
                                pass
                    else:
                        # Fallback if title regex fails
                        caption = driver.title
                        
                except Exception as e:
                    print(f"[SeleniumInstagram] Title parse error: {e}")

                # ---- 24 Hour Filter ----
                if post_date:
                    # Check if post is older than 24 hours
                    age_hours = (datetime.datetime.now() - post_date).total_seconds() / 3600
                    if age_hours > 24:
                        print(f"[SeleniumInstagram] ⚠️ Skipping post - older than 24h ({age_hours:.1f}h old)")
                        continue

                # ---- Comments extraction (real DOM parsing) ----
                post_comments: List[Dict[str, str]] = []
                try:
                    spans = driver.find_elements(By.CSS_SELECTOR,"span[dir='auto']")

                    seen: set = set()
                    for span in spans:
                        txt = span.text.strip()
                        if txt and len(txt) > 2 and txt not in seen:
                            lower_txt = txt.lower()
                            # Skip common Instagram UI elements
                            if lower_txt in ["reply", "hide replies", "see translation"] or " likes" in lower_txt or (lower_txt.startswith("view all") and "replies" in lower_txt):
                                continue

                            if not caption or caption == driver.title:
                                if len(txt) > 20:
                                    caption=txt
                                    seen.add(txt)
                                    continue
                            if txt != caption:
                                # Check if comment contains the search keyword (using 'words' or 'raw_query' defined above)
                                match = False
                                for w in words:
                                    if w in lower_txt:
                                        match = True
                                        break
                                
                                if match or raw_query in lower_txt:
                                    post_comments.append({"author": "user", "text": txt[:300]})
                                    seen.add(txt)
                            if len(post_comments)>= 15:
                                break
                except Exception as e:
                    print(f"[SeleniumInstagram] Comment extraction failed: {e}")

                # ---- Build result ----
                sc_match = re.search(r"/(?:p|reel)/([A-Za-z0-9_-]+)/?", post_url)
                shortcode = sc_match.group(1) if sc_match else uuid.uuid4().hex[:8]
                uid = hashlib.md5(shortcode.encode()).hexdigest()[:10]
                hashtags = re.findall(r"#(\w+)", caption) or [tag]
                ctype = "REEL" if is_reel else "POST"

                # ---- OCR Extraction for Reels ----
                if is_reel and video_ocr:
                    try:
                        import tempfile
                        # Wait a moment to ensure video is fully rendered
                        time.sleep(1.0)
                        ss_path = os.path.join(tempfile.gettempdir(), f"reel_ocr_{shortcode}.png")
                        try:
                            # Attempt to screenshot only the video element if found
                            video_el = driver.find_element(By.TAG_NAME, "video")
                            video_el.screenshot(ss_path)
                        except Exception:
                            # Fallback: screenshot the entire page
                            driver.save_screenshot(ss_path)
                        
                        ocr_text = video_ocr.extract_text_from_image(ss_path)
                        
                        if ocr_text:
                            caption += f" [OCR_TEXT: {ocr_text}]"
                            print(f"[SeleniumInstagram] OCR Extracted: {ocr_text[:60]}...")
                            
                        try:
                            os.remove(ss_path)
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"[SeleniumInstagram] Reel OCR failed: {e}")

                print(f"[SeleniumInstagram] {ctype} | {author} | {likes} L, {comments_count} C | {caption[:60]!r}")


                results.append({
                    "id": f"ig-{uid}",
                    "platform": "Instagram",
                    "author_username": author,
                    "author_id": f"ig_{uid}",
                    "content": caption[:600] or f"Instagram {ctype.lower()} about #{tag}",
                    "url": post_url,
                    "hashtags": hashtags,
                    "language": "en",
                    "likes": likes,
                    "post_comments": post_comments,
                    "shortcode": shortcode,
                    "content_type": ctype,
                    "source_type": "SELENIUM_INSTAGRAM",
                    "crawled_at": datetime.datetime.utcnow().isoformat(),
                    "created_at": datetime.datetime.utcnow().isoformat(),
                })

            except Exception as e:
                print(f"[SeleniumInstagram] Error on {post_url}: {e}")
                continue

    except WebDriverException as e:
        print(f"[SeleniumInstagram] WebDriver error: {e}")
    except Exception as e:
        print(f"[SeleniumInstagram] Unexpected error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

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
        except Exception as e:
            print(f"[SeleniumInstagram] Executor error: {e}")

    if not results:
        print(f"[SeleniumInstagram] No live results for #{tag} — using fallback stubs.")
        results = _generate_fallback_stubs(tag, min(limit, 5))

    return results[:limit]
