#!/usr/bin/env python3
"""
Dedicated Rentals.ca Session Connector
Opens Rentals.ca in the bot's persistent browser context so you can log in once.
Session tokens and cookies are saved permanently in ~/.property_agent_browser_profile
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = Path.home() / ".property_agent_browser_profile"

def main():
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("🔑 Opening Rentals.ca Landlord Login...")
    print(f"Profile Directory: {USER_DATA_DIR}")
    print("=" * 60)
    print("1. Browser window will open to https://rentals.ca/login")
    print("2. Enter your email and password and sign in.")
    print("3. Your session will be permanently saved for 1-click bot postings!")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        page.goto("https://rentals.ca/login")
        try:
            input("\n👉 Press [ENTER] here once you have signed into Rentals.ca: ")
        except (KeyboardInterrupt, EOFError):
            pass
        browser.close()
    print("\n✅ Rentals.ca login session saved successfully!")

if __name__ == "__main__":
    main()
