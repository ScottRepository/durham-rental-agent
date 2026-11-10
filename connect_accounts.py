#!/usr/bin/env python3
"""
Account Connection & Session Setup Wizard
Launches a real browser window with your persistent profile.
Log in ONCE to Facebook, Kijiji, and Zumper. Your session cookies
remain saved locally so the automated posting bot never asks for passwords again.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = Path.home() / ".property_agent_browser_profile"

PLATFORMS = {
    "1": ("Facebook Marketplace", "https://www.facebook.com/login"),
    "2": ("Kijiji Ontario", "https://www.kijiji.ca/t-login.html"),
    "3": ("Zumper Landlord Portal", "https://www.zumper.com/manage"),
    "4": ("Connect All 3 Accounts Sequentially", "all")
}

def connect_platform(platform_name: str, target_url: str):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n========================================================")
    print(f" Connecting {platform_name}...")
    print(f" Profile Directory: {USER_DATA_DIR}")
    print(f"========================================================")
    print(f"1. A browser window will now open to {platform_name}.")
    print(f"2. Log in using your normal credentials and complete any 2FA/SMS code.")
    print(f"3. Once you see your feed or dashboard, press [ENTER] here in the terminal.")
    print(f"========================================================\n")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        page.goto(target_url)

        input(f"👉 Once you have successfully logged in to {platform_name}, press [ENTER] to save session: ")
        
        print(f"✅ Session for {platform_name} successfully saved to local profile!")
        browser.close()

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║    Durham Rental Agent - Account Connection Wizard       ║
╚══════════════════════════════════════════════════════════╝
This saves your login sessions locally on your computer.
Your passwords are NEVER stored in code or pushed to GitHub.
""")
    print("Choose which account you would like to connect:")
    print(" 1) Facebook Marketplace")
    print(" 2) Kijiji Ontario")
    print(" 3) Zumper Landlord Portal")
    print(" 4) Connect All 3 (Recommended)")
    print(" 5) Exit")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == "1":
        connect_platform("Facebook", "https://www.facebook.com/login")
    elif choice == "2":
        connect_platform("Kijiji", "https://www.kijiji.ca/t-login.html")
    elif choice == "3":
        connect_platform("Zumper", "https://www.zumper.com/manage")
    elif choice == "4":
        connect_platform("Facebook", "https://www.facebook.com/login")
        connect_platform("Kijiji", "https://www.kijiji.ca/t-login.html")
        connect_platform("Zumper", "https://www.zumper.com/manage")
    else:
        print("Exiting setup.")
        sys.exit(0)

    print("\n🎉 All selected accounts are now connected!")
    print("The agent can now pre-fill and post listings automatically on your behalf.\n")

if __name__ == "__main__":
    main()
