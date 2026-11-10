#!/usr/bin/env python3
"""
Account Connection Wizard for Kijiji Ontario and Zumper Landlord Portal
Connects your accounts by saving login cookies in your persistent browser profile.
Your passwords are never stored in plain text or pushed to GitHub.
"""

import sys
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
    print(f"2. Log in with your email/password (and 2FA code if prompted).")
    print(f"3. Once you see your active dashboard or home page, come back here.")
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
    print("""
╔══════════════════════════════════════════════════════════╗
║        Connect Kijiji & Zumper Accounts Wizard           ║
╚══════════════════════════════════════════════════════════╝
This saves your active login session in your local profile.
Zero passwords are saved in code.
""")
    print("Choose an option:")
    print(" 1) Connect Kijiji & Zumper together (Recommended)")
    print(" 2) Connect Kijiji Ontario only")
    print(" 3) Connect Zumper Landlord Portal only")
    print(" 4) Connect Facebook Marketplace")
    print(" 5) Exit")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == "1":
        connect_platform("Kijiji Ontario", "https://www.kijiji.ca/t-login.html")
        connect_platform("Zumper Landlord Portal", "https://www.zumper.com/manage")
    elif choice == "2":
        connect_platform("Kijiji Ontario", "https://www.kijiji.ca/t-login.html")
    elif choice == "3":
        connect_platform("Zumper Landlord Portal", "https://www.zumper.com/manage")
    elif choice == "4":
        connect_platform("Facebook Marketplace", "https://www.facebook.com/login")
    else:
        print("Exiting wizard.")
        sys.exit(0)

    print("\n🎉 Setup complete! Kijiji & Zumper are now connected.")
    print("You can now trigger 1-click postings from your web dashboard or CLI.\n")

if __name__ == "__main__":
    main()
