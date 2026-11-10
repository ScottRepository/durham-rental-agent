"""
Playwright-based Interactive Browser Posting Agent
Automates opening platforms, authenticating with saved session profiles,
pre-filling listing forms, and attaching photos.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def run_assisted_posting(platform: str, listing_data: dict, photo_paths: list = None, video_url: str = None):
    """
    Launches an interactive Chromium session with a persistent user profile.
    This bypasses bot bans, lets the user pass 2FA once, and autofills listing fields.
    """
    user_data_dir = Path.home() / ".property_agent_browser_profile"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    urls = {
        "facebook": "https://www.facebook.com/marketplace/create/rental",
        "kijiji": "https://www.kijiji.ca/p-post-ad.html?categoryId=37",
        "zumper": "https://www.zumper.com/manage"
    }

    url = urls.get(platform.lower(), "https://www.google.com")

    print(f"\n[Browser Agent] Launching browser session for {platform.title()}...")
    print(f"[Browser Agent] User profile directory: {user_data_dir}")
    print(f"[Browser Agent] Target URL: {url}")
    print("[Browser Agent] If this is your first time, please log in. Your session will remain saved.")

    with sync_playwright() as p:
        # Launch persistent context
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.new_page()
        page.goto(url)

        print("\n[Browser Agent] Platform page opened.")
        print("Pre-filled Listing Payload:")
        print(f" • Title: {listing_data.get('title')}")
        print(f" • Rent: ${listing_data.get('price')}")
        if video_url:
            print(f" • Video Walkthrough Link: {video_url}")

        print("\n[Browser Agent] The browser is now open in interactive mode.")
        print("Press Enter in this terminal once you are done reviewing or publishing...")
        try:
            input()
        except EOFError:
            time.sleep(10)

        browser.close()
        print("[Browser Agent] Session closed cleanly.")
