#!/usr/bin/env python3
"""
Dedicated Rentals.ca Session Connector
Opens Rentals.ca in the bot's persistent browser context so you can log in.
Session tokens and cookies are saved permanently in ~/.property_agent_browser_profile
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = Path.home() / ".property_agent_browser_profile"

def main():
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Clean any stale Singleton locks
    for p in USER_DATA_DIR.glob("Singleton*"):
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass

    print("=" * 60, flush=True)
    print("🔑 Opening Rentals.ca Login Window...", flush=True)
    print(f"Profile: {USER_DATA_DIR}", flush=True)
    print("=" * 60, flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        page.set_default_timeout(60000)
        
        try:
            page.goto("https://rentals.ca/login", wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"[Note] Initial load: {e}", flush=True)

        print("\n👉 Browser is open on your screen! Please log in to Rentals.ca.", flush=True)
        print("The browser will remain open until you close the window or finish logging in.\n", flush=True)

        logged_in = False
        # Keep open for up to 30 minutes (360 * 5s = 1800s) or until user closes the window
        for i in range(360):
            time.sleep(5)
            try:
                if page.is_closed():
                    print("\nBrowser window was closed by user.", flush=True)
                    break
                cur_url = page.url
                if i % 6 == 0:
                    print(f"[{i*5}s] Current URL: {cur_url}", flush=True)
                if not logged_in and "login" not in cur_url.lower() and "rentals.ca" in cur_url.lower():
                    logged_in = True
                    print(f"\n🎉 Login detected! Current URL: {cur_url}", flush=True)
                    print("Session cookies are preserved. Feel free to navigate or close the window when ready.", flush=True)
            except Exception:
                break

        try:
            browser.close()
        except Exception:
            pass

    print("\n✅ Session saved in persistent profile ~/.property_agent_browser_profile!", flush=True)

if __name__ == "__main__":
    main()
