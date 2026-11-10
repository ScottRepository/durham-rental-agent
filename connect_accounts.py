#!/usr/bin/env python3
"""
Account Connection Wizard for Facebook Marketplace, Kijiji, and Zumper
Connects your accounts by saving login cookies in your persistent browser profile.
Your passwords are never stored in plain text or pushed to GitHub.
"""

import sys
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = Path.home() / ".property_agent_browser_profile"

def connect_platform(platform_name: str, target_url: str):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n" + "="*60)
    print(f" 🔑 Connecting {platform_name}...")
    print(f" Profile Directory: {USER_DATA_DIR}")
    print("="*60)
    print(f"1. A browser window will now open to {platform_name}.")
    print(f"2. Log in with your new dedicated account credentials.")
    print(f"3. Once you see your feed or home page, come back here.")
    print("="*60 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        page.goto(target_url)

        input(f"👉 Once you are logged in to {platform_name}, press [ENTER] to save session: ")
        
        print(f"✅ Session for {platform_name} saved successfully!\n")
        browser.close()

def main():
    parser = argparse.ArgumentParser(description="Account Connection Wizard")
    parser.add_argument("--facebook", action="store_true", help="Connect Facebook directly")
    parser.add_argument("--kijiji", action="store_true", help="Connect Kijiji directly")
    parser.add_argument("--zumper", action="store_true", help="Connect Zumper directly")
    args = parser.parse_args()

    if args.facebook:
        connect_platform("Facebook Marketplace", "https://www.facebook.com/login")
        return
    elif args.kijiji:
        connect_platform("Kijiji Ontario", "https://www.kijiji.ca/t-login.html")
        return
    elif args.zumper:
        connect_platform("Zumper Landlord Portal", "https://www.zumper.com/manage")
        return

    print("""
╔══════════════════════════════════════════════════════════╗
║    Durham Rental Agent - Account Connection Wizard       ║
╚══════════════════════════════════════════════════════════╝
This saves your active login session in your local profile.
Zero passwords are saved in code or sent over the internet.
""")
    print("Choose an option:")
    print(" 1) Connect Facebook Marketplace (New Account)")
    print(" 2) Connect Kijiji Ontario")
    print(" 3) Connect Zumper Landlord Portal")
    print(" 4) Connect All Accounts")
    print(" 5) Exit")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == "1":
        connect_platform("Facebook Marketplace", "https://www.facebook.com/login")
    elif choice == "2":
        connect_platform("Kijiji Ontario", "https://www.kijiji.ca/t-login.html")
    elif choice == "3":
        connect_platform("Zumper Landlord Portal", "https://www.zumper.com/manage")
    elif choice == "4":
        connect_platform("Facebook Marketplace", "https://www.facebook.com/login")
        connect_platform("Kijiji Ontario", "https://www.kijiji.ca/t-login.html")
        connect_platform("Zumper Landlord Portal", "https://www.zumper.com/manage")
    else:
        print("Exiting wizard.")
        sys.exit(0)

    print("\n🎉 Setup complete! All selected accounts are now connected.")

if __name__ == "__main__":
    main()
