"""
Session & Authentication Verifier for Facebook, Kijiji, and Zumper
Verifies that saved cookies in ~/.property_agent_browser_profile maintain active login state.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = Path.home() / ".property_agent_browser_profile"
SCREENSHOTS_DIR = Path(__file__).parent / "reports" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def test_facebook_session():
    print("\n[Testing Facebook Session]...")
    screenshot_path = SCREENSHOTS_DIR / "facebook_session_test.png"

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=True,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=25000)
            time.sleep(4)
        except Exception as e:
            print(f"Navigation note: {e}")

        url = page.url
        title = page.title()
        content = page.content()
        page.screenshot(path=str(screenshot_path))
        browser.close()

    print(f" • Landed URL: {url}")
    print(f" • Page Title: {title}")
    print(f" • Screenshot saved: {screenshot_path}")

    is_logged_in = "login" not in url.lower() and ("facebook" in title.lower() or "feed" in content.lower() or "marketplace" in content.lower())
    if is_logged_in:
        print("✅ Facebook Session: ACTIVE & AUTHENTICATED")
        return True, url, str(screenshot_path)
    else:
        print("⚠️ Facebook Session: Redirected to login page.")
        return False, url, str(screenshot_path)

def test_kijiji_session():
    print("\n[Testing Kijiji Session]...")
    screenshot_path = SCREENSHOTS_DIR / "kijiji_session_test.png"

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=True,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        try:
            page.goto("https://www.kijiji.ca/m-my-ads/active", wait_until="domcontentloaded", timeout=25000)
            time.sleep(3)
        except Exception as e:
            print(f"Navigation note: {e}")

        url = page.url
        title = page.title()
        content = page.content()
        page.screenshot(path=str(screenshot_path))
        browser.close()

    print(f" • Landed URL: {url}")
    print(f" • Page Title: {title}")
    print(f" • Screenshot saved: {screenshot_path}")

    is_logged_in = "login" not in url.lower() and ("my-ads" in url.lower() or "my ads" in title.lower() or "active" in url.lower() or "sign out" in content.lower())
    if is_logged_in:
        print("✅ Kijiji Session: ACTIVE & AUTHENTICATED")
        return True, url, str(screenshot_path)
    else:
        print("⚠️ Kijiji Session: Redirected to login page.")
        return False, url, str(screenshot_path)

def test_zumper_session():
    print("\n[Testing Zumper Session]...")
    screenshot_path = SCREENSHOTS_DIR / "zumper_session_test.png"

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=True,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        try:
            page.goto("https://www.zumper.com/manage", wait_until="domcontentloaded", timeout=25000)
            time.sleep(3)
        except Exception as e:
            print(f"Navigation note: {e}")

        url = page.url
        title = page.title()
        content = page.content()
        page.screenshot(path=str(screenshot_path))
        browser.close()

    print(f" • Landed URL: {url}")
    print(f" • Page Title: {title}")
    print(f" • Screenshot saved: {screenshot_path}")

    is_logged_in = "login" not in url.lower() and ("manage" in url.lower() or "properties" in content.lower() or "dashboard" in url.lower())
    if is_logged_in:
        print("✅ Zumper Session: ACTIVE & AUTHENTICATED")
        return True, url, str(screenshot_path)
    else:
        print("⚠️ Zumper Session: Redirected to login page.")
        return False, url, str(screenshot_path)

if __name__ == "__main__":
    fb_ok, fb_url, fb_shot = test_facebook_session()
    k_ok, k_url, k_shot = test_kijiji_session()
    z_ok, z_url, z_shot = test_zumper_session()

    print("\n" + "="*55)
    print("ALL ACCOUNTS SESSION STATUS:")
    print(f" • Facebook: {'✅ ACTIVE' if fb_ok else '⚠️ RE-LOGIN NEEDED'}")
    print(f" • Kijiji:   {'✅ ACTIVE' if k_ok else '⚠️ RE-LOGIN NEEDED'}")
    print(f" • Zumper:   {'✅ ACTIVE' if z_ok else '⚠️ RE-LOGIN NEEDED'}")
    print("="*55)
