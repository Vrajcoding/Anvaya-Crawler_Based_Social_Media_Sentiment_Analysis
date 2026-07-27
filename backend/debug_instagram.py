"""
debug_instagram.py — Full login test with correct field names (email + pass).
Run: python debug_instagram.py
"""
import os, sys, time, random, tempfile
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

username = os.getenv("INSTAGRAM_USERNAME", "").strip()
password = os.getenv("INSTAGRAM_PASSWORD", "").strip()
print(f"\n📋 Credentials: username='{username}', password={'*'*len(password)}")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

opts = Options()
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument("--window-size=1366,768")
opts.add_argument("--lang=en-US")
opts.add_argument("--disable-notifications")

path = ChromeDriverManager(driver_version="150").install()
driver = webdriver.Chrome(service=Service(path), options=opts)
wait = WebDriverWait(driver, 20)

# ── Login ──────────────────────────────────────────────────────────────────────
print("\n🔐 Navigating to login page...")
driver.get("https://www.instagram.com/accounts/login/")
time.sleep(4)
print(f"   Title: {driver.title}")

# Print all inputs
inputs = driver.find_elements(By.TAG_NAME, "input")
print(f"   Inputs found: {[(i.get_attribute('name'), i.get_attribute('type')) for i in inputs]}")

# Try username field (both variants)
u_field = None
for name_attr in ["username", "email"]:
    els = driver.find_elements(By.NAME, name_attr)
    if els:
        u_field = els[0]
        print(f"   ✅ Using username field: name='{name_attr}'")
        break

if not u_field:
    print("   ❌ No username/email field found!")
    ss = os.path.join(tempfile.gettempdir(), "ig_fail.png")
    driver.save_screenshot(ss)
    print(f"   Screenshot: {ss}")
    driver.quit()
    sys.exit(1)

# Type credentials
u_field.clear()
for ch in username:
    u_field.send_keys(ch)
    time.sleep(0.07)

# Try password field (both variants)
p_field = None
for name_attr in ["password", "pass"]:
    els = driver.find_elements(By.NAME, name_attr)
    if els:
        p_field = els[0]
        print(f"   ✅ Using password field: name='{name_attr}'")
        break

if not p_field:
    print("   ❌ No password/pass field found!")
    driver.quit()
    sys.exit(1)

p_field.clear()
for ch in password:
    p_field.send_keys(ch)
    time.sleep(0.06)

print("   Submitting...")
p_field.send_keys(Keys.RETURN)
time.sleep(6)

print(f"\n   After login: {driver.current_url}")
print(f"   Title: {driver.title}")

ss = os.path.join(tempfile.gettempdir(), "ig_after_login.png")
driver.save_screenshot(ss)
print(f"   Screenshot: {ss}")

if "login" in driver.current_url:
    # Check for error text
    body = driver.find_element(By.TAG_NAME, "body").text
    for line in body.split("\n"):
        if any(w in line.lower() for w in ["incorrect", "wrong", "error", "sorry", "unusual"]):
            print(f"   ❌ Error on page: {line.strip()}")
    print("   ❌ LOGIN FAILED")
else:
    print("   ✅ LOGIN SUCCEEDED!")

    # ── Dismiss onetap / save-info / notifications dialogs ────────────────────
    time.sleep(2)
    print(f"   Current URL after login: {driver.current_url}")
    print(f"   Buttons on this page:")
    for b in driver.find_elements(By.TAG_NAME, "button"):
        print(f"     '{b.text.strip()[:60]}'  visible={b.is_displayed()}")

    # Click ANY visible button that means "skip" / "not now"
    skip_texts = ["not now", "skip", "close", "maybe later", "decline", "cancel", "later"]
    for b in driver.find_elements(By.TAG_NAME, "button"):
        try:
            txt = b.text.strip().lower()
            if any(s in txt for s in skip_texts) and b.is_displayed():
                print(f"   Clicking: '{b.text.strip()}'")
                b.click()
                time.sleep(1.5)
                break
        except Exception:
            pass

    time.sleep(2)

    # ── Test multiple search URLs ─────────────────────────────────────────────
    test_urls = [
        ("Keyword search (protests in surat)", "https://www.instagram.com/explore/search/keyword/?q=protests+in+surat"),
        ("Keyword search (surat protest)",     "https://www.instagram.com/explore/search/keyword/?q=surat+protest"),
        ("Hashtag explore (surat)",            "https://www.instagram.com/explore/tags/surat/"),
        ("Hashtag explore (suratprotest)",     "https://www.instagram.com/explore/tags/suratprotest/"),
    ]

    for label, url in test_urls:
        print(f"\n🔎 Testing: {label}")
        print(f"   URL: {url}")
        driver.get(url)
        time.sleep(4)

        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 700);")
            time.sleep(0.8)

        # Check page text
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if "No results" in body_text or "couldn't find" in body_text:
            print(f"   ⚠️  Page says 'No results'")
        else:
            print(f"   Page text snippet: {body_text[:200]!r}")

        # All anchors
        all_anchors = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        post_links = [a.get_attribute("href") for a in all_anchors
                      if "/p/" in (a.get_attribute("href") or "") or "/reel/" in (a.get_attribute("href") or "")]
        print(f"   Post/reel links: {len(post_links)}")
        for l in post_links[:5]:
            print(f"     → {l}")

        # Also print ALL unique anchor hrefs (to see what IG renders)
        hrefs = list({a.get_attribute("href") for a in all_anchors if a.get_attribute("href")})
        print(f"   All links ({len(hrefs)} total):")
        for h in hrefs[:15]:
            print(f"     {h}")

        ss = os.path.join(tempfile.gettempdir(), f"ig_search_{label[:15].replace(' ','_')}.png")
        driver.save_screenshot(ss)
        print(f"   Screenshot: {ss}")

        if post_links:
            print(f"   ✅ FOUND {len(post_links)} posts — stopping here")
            break

driver.quit()
print("\n✅ Debug complete.")

