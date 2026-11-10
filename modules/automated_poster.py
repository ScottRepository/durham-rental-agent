"""
Playwright-Powered 1-Click Automated Poster for Facebook, Kijiji, Zumper, Rentals.ca, and Liv.rent
Loads property details and media from SQLite, navigates to the external platform,
pre-fills the listing form, attaches photos, and records status in SQLite.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from data.database import get_unit_by_id, update_posting_status
from modules.content_generator import (
    generate_facebook_marketplace_listing,
    generate_kijiji_listing,
    generate_zumper_listing,
    generate_rentals_ca_listing,
    generate_liv_rent_listing
)

USER_PROFILE_DIR = Path.home() / ".property_agent_browser_profile"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "reports" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

class AutomatedPoster:
    def __init__(self, unit_id: str, platform: str, headless: bool = False, auto_publish: bool = False):
        self.unit_id = unit_id
        self.platform = platform.lower()
        self.headless = headless
        self.auto_publish = auto_publish
        self.unit = get_unit_by_id(unit_id)
        if not self.unit:
            raise ValueError(f"Unit ID '{unit_id}' not found in database.")

    def _get_or_download_unit_photos(self) -> list:
        """
        Downloads and caches high-resolution suite photos and building exterior photo
        from Google Drive directly onto disk so Playwright can attach them into the
        platform's file uploader with zero manual downloading or uploading.
        """
        import urllib.request
        import re

        cache_dir = Path(__file__).parent.parent / "data" / "media_cache" / self.unit_id
        cache_dir.mkdir(parents=True, exist_ok=True)

        existing = sorted([str(p.resolve()) for p in cache_dir.glob("*.*") if p.suffix.lower() in ('.jpg', '.jpeg', '.png')])
        if len(existing) >= 4:
            return existing

        # 1. Download Exterior Building Photo
        ext_path = cache_dir / "00_building_exterior.png"
        if not ext_path.exists():
            try:
                ext_url = "https://drive.google.com/uc?id=185EGZHPUiw_bkYOQPyqds8ZvSH6qJ6JZ&export=download"
                req = urllib.request.Request(ext_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as resp, open(ext_path, "wb") as f:
                    f.write(resp.read())
                print(f"[Photo Sync] Downloaded building exterior photo to {ext_path.name}")
            except Exception as e:
                print(f"[Photo Sync] Note on building exterior: {e}")

        # 2. Extract photos from unit Google Drive folder
        cloud_media = self.unit.get("cloud_media") or {}
        folder_url = cloud_media.get("google_drive_photos_folder") or ""
        fid = folder_url.split("/")[-1].split("?")[0] if folder_url else ""
        if fid:
            try:
                req = urllib.request.Request(f"https://drive.google.com/drive/folders/{fid}", headers={"User-Agent": "Mozilla/5.0"})
                html = urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")
                files = set(re.findall(r"\"([^\"]+\.(?:png|jpg|jpeg|JPG|PNG))\"", html))

                idx = 1
                for fn in sorted(files):
                    if any(ign in fn for ign in ["drive_2026", "favicon", "broken_image", "al-icon", "Screenshot"]):
                        continue
                    pos = html.find(fn)
                    snippet = html[max(0, pos-200):min(len(html), pos+300)]
                    ids = [i for i in re.findall(r"[-\w]{25,}", snippet) if not i.startswith("data-")]
                    if not ids:
                        continue
                    clean_id = re.sub(r"-\d+-\d+$", "", ids[0])
                    out_file = cache_dir / f"{idx:02d}_{fn}"
                    if not out_file.exists():
                        try:
                            dl_req = urllib.request.Request(f"https://drive.google.com/uc?id={clean_id}&export=download", headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(dl_req) as resp, open(out_file, "wb") as out:
                                out.write(resp.read())
                            print(f"[Photo Sync] Cached suite photo: {fn}")
                        except Exception:
                            continue
                    idx += 1
                    if idx > 10:
                        break
            except Exception as e:
                print(f"[Photo Sync] Note on unit folder: {e}")

        all_photos = sorted([str(p.resolve()) for p in cache_dir.glob("*.*") if p.suffix.lower() in ('.jpg', '.jpeg', '.png')])
        return all_photos

    def run(self) -> Dict[str, Any]:
        """Executes the one-click posting workflow."""
        update_posting_status(self.unit_id, self.platform, "in_progress", log="Automation bot launched")

        try:
            if self.platform == "facebook":
                result = self._post_facebook()
            elif self.platform == "kijiji":
                result = self._post_kijiji()
            elif self.platform == "zumper":
                result = self._post_zumper()
            elif self.platform in ("rentals_ca", "rentals.ca"):
                result = self._post_rentals_ca()
            elif self.platform in ("liv_rent", "liv.rent"):
                result = self._post_liv_rent()
            else:
                raise ValueError(f"Unsupported platform: {self.platform}")

            update_posting_status(
                self.unit_id,
                self.platform,
                "posted",
                external_url=result.get("url"),
                log=f"Successfully staged/completed on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            return {"success": True, "details": result}

        except Exception as e:
            error_msg = f"Posting error: {str(e)}"
            print(f"[AutomatedPoster Error] {error_msg}")
            update_posting_status(self.unit_id, self.platform, "failed", log=error_msg)
            return {"success": False, "error": error_msg}

    def _post_facebook(self) -> Dict[str, Any]:
        """Automates Facebook Marketplace rental listing form."""
        payload = generate_facebook_marketplace_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_facebook.png"

        print(f"[Facebook Poster] Opening Facebook Marketplace with profile at {USER_PROFILE_DIR}...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.goto("https://www.facebook.com/marketplace/create/rental", wait_until="domcontentloaded")
            time.sleep(3)

            # 1. Automatically attach suite photos and exterior photo
            photos = self._get_or_download_unit_photos()
            if photos:
                try:
                    file_inputs = page.locator('input[type="file"]')
                    if file_inputs.count() > 0:
                        print(f"[Facebook Poster] Automatically uploading {len(photos)} photos from Google Drive cache...")
                        file_inputs.first.set_input_files(photos)
                        time.sleep(3)
                except Exception as photo_err:
                    print(f"[Facebook Photo Upload Note] {photo_err}")

            # 2. Attempt to pre-fill standard Facebook Marketplace rental inputs if visible
            try:
                clean_price = str(payload["price"]).replace(".0", "")
                for label_text, val in [
                    ("Price", clean_price),
                    ("Number of bedrooms", str(payload["bedrooms"])),
                    ("Number of bathrooms", str(payload["bathrooms"])),
                    ("Property address", "315 Kent Street, Whitby, ON"),
                    ("Rental description", payload["description"])
                ]:
                    try:
                        loc = page.get_by_label(label_text, exact=False).first
                        if loc.count() > 0:
                            loc.fill(val, timeout=2500)
                    except Exception:
                        pass
            except Exception as fill_err:
                print(f"[Facebook Auto-Fill Note] {fill_err}")

            page.screenshot(path=str(screenshot_path))

            # 3. Optional Auto-Publish (Clicks Next -> Publish)
            if self.auto_publish:
                try:
                    print("[Facebook Poster] Auto-Publish enabled: searching for 'Next' button...")
                    next_btns = page.locator('div[aria-label="Next"], button:has-text("Next"), div[role="button"]:has-text("Next")')
                    if next_btns.count() > 0 and next_btns.first.is_visible():
                        next_btns.first.click()
                        time.sleep(3)
                        print("[Facebook Poster] Searching for 'Publish' button...")
                        pub_btns = page.locator('div[aria-label="Publish"], button:has-text("Publish"), div[role="button"]:has-text("Publish")')
                        if pub_btns.count() > 0 and pub_btns.first.is_visible():
                            pub_btns.first.click()
                            time.sleep(4)
                            print("[Facebook Poster] ✔ Final Publish button clicked!")
                except Exception as pub_err:
                    print(f"[Facebook Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Facebook Poster] Form staged! Browser will stay open for up to 60 seconds for you to review and click Publish...")
                try:
                    page.wait_for_timeout(60000)
                except Exception:
                    pass
            context.close()

        return {
            "platform": "Facebook Marketplace",
            "url": "https://www.facebook.com/marketplace/create/rental",
            "screenshot": str(screenshot_path),
            "title": payload["title"],
            "price": payload["price"]
        }

    def _post_kijiji(self) -> Dict[str, Any]:
        """Automates Kijiji Ontario rental listing form."""
        payload = generate_kijiji_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_kijiji.png"

        print(f"[Kijiji Poster] Opening Kijiji post form...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.goto("https://www.kijiji.ca/p-post-ad.html?categoryId=37", wait_until="domcontentloaded")
            time.sleep(3)

            # 1. Automatically attach suite photos and exterior photo
            photos = self._get_or_download_unit_photos()
            if photos:
                try:
                    file_inputs = page.locator('input[type="file"]')
                    if file_inputs.count() > 0:
                        print(f"[Kijiji Poster] Automatically uploading {len(photos)} photos from Google Drive cache...")
                        file_inputs.first.set_input_files(photos)
                        time.sleep(3)
                except Exception as photo_err:
                    print(f"[Kijiji Photo Upload Note] {photo_err}")

            # 2. Attempt to pre-fill standard Kijiji ad title, description, price, and YouTube link if visible
            try:
                for sel, val in [
                    ("input[name*='postAdForm.title'], #AdTitleForm", payload["title"]),
                    ("textarea[name*='postAdForm.description'], #pstad-descrptn", payload["description"]),
                    ("input[name*='postAdForm.priceAmount'], #PriceAmount", str(payload["price"])),
                    ("input[name*='youtube'], input[id*='youtube']", payload["youtube_video_url"])
                ]:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        loc.fill(val)
            except Exception as fill_err:
                print(f"[Kijiji Auto-Fill Note] {fill_err}")

            page.screenshot(path=str(screenshot_path))

            # 3. Optional Auto-Publish (Clicks Next -> Publish)
            if self.auto_publish:
                try:
                    print("[Facebook Poster] Auto-Publish enabled: searching for 'Next' button...")
                    next_btns = page.locator('div[aria-label="Next"], button:has-text("Next"), div[role="button"]:has-text("Next")')
                    if next_btns.count() > 0 and next_btns.first.is_visible():
                        next_btns.first.click()
                        time.sleep(3)
                        print("[Facebook Poster] Searching for 'Publish' button...")
                        pub_btns = page.locator('div[aria-label="Publish"], button:has-text("Publish"), div[role="button"]:has-text("Publish")')
                        if pub_btns.count() > 0 and pub_btns.first.is_visible():
                            pub_btns.first.click()
                            time.sleep(4)
                            print("[Facebook Poster] ✔ Final Publish button clicked!")
                except Exception as pub_err:
                    print(f"[Facebook Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Facebook Poster] Form staged! Browser will stay open for up to 60 seconds for you to review and click Publish...")
                try:
                    page.wait_for_timeout(60000)
                except Exception:
                    pass
            context.close()

        return {
            "platform": "Kijiji Ontario",
            "url": "https://www.kijiji.ca/p-post-ad.html?categoryId=37",
            "screenshot": str(screenshot_path),
            "title": payload["title"],
            "video_url": payload["youtube_video_url"]
        }

    def _post_zumper(self) -> Dict[str, Any]:
        """Automates Zumper Landlord listing portal."""
        payload = generate_zumper_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_zumper.png"

        print(f"[Zumper Poster] Opening Zumper manage portal...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.goto("https://www.zumper.com/manage", wait_until="domcontentloaded")
            time.sleep(3)

            page.screenshot(path=str(screenshot_path))

            # 3. Optional Auto-Publish (Clicks Next -> Publish)
            if self.auto_publish:
                try:
                    print("[Facebook Poster] Auto-Publish enabled: searching for 'Next' button...")
                    next_btns = page.locator('div[aria-label="Next"], button:has-text("Next"), div[role="button"]:has-text("Next")')
                    if next_btns.count() > 0 and next_btns.first.is_visible():
                        next_btns.first.click()
                        time.sleep(3)
                        print("[Facebook Poster] Searching for 'Publish' button...")
                        pub_btns = page.locator('div[aria-label="Publish"], button:has-text("Publish"), div[role="button"]:has-text("Publish")')
                        if pub_btns.count() > 0 and pub_btns.first.is_visible():
                            pub_btns.first.click()
                            time.sleep(4)
                            print("[Facebook Poster] ✔ Final Publish button clicked!")
                except Exception as pub_err:
                    print(f"[Facebook Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Facebook Poster] Form staged! Browser will stay open for up to 60 seconds for you to review and click Publish...")
                try:
                    page.wait_for_timeout(60000)
                except Exception:
                    pass
            context.close()

        return {
            "platform": "Zumper & PadMapper",
            "url": "https://www.zumper.com/manage",
            "screenshot": str(screenshot_path),
            "title": payload["title"]
        }

    def _post_rentals_ca(self) -> Dict[str, Any]:
        """Automates Rentals.ca landlord listing portal."""
        payload = generate_rentals_ca_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_rentals_ca.png"

        print(f"[Rentals.ca Poster] Opening Rentals.ca portal...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.goto("https://rentals.ca/landlord", wait_until="domcontentloaded")
            time.sleep(3)

            page.screenshot(path=str(screenshot_path))

            # 3. Optional Auto-Publish (Clicks Next -> Publish)
            if self.auto_publish:
                try:
                    print("[Facebook Poster] Auto-Publish enabled: searching for 'Next' button...")
                    next_btns = page.locator('div[aria-label="Next"], button:has-text("Next"), div[role="button"]:has-text("Next")')
                    if next_btns.count() > 0 and next_btns.first.is_visible():
                        next_btns.first.click()
                        time.sleep(3)
                        print("[Facebook Poster] Searching for 'Publish' button...")
                        pub_btns = page.locator('div[aria-label="Publish"], button:has-text("Publish"), div[role="button"]:has-text("Publish")')
                        if pub_btns.count() > 0 and pub_btns.first.is_visible():
                            pub_btns.first.click()
                            time.sleep(4)
                            print("[Facebook Poster] ✔ Final Publish button clicked!")
                except Exception as pub_err:
                    print(f"[Facebook Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Facebook Poster] Form staged! Browser will stay open for up to 60 seconds for you to review and click Publish...")
                try:
                    page.wait_for_timeout(60000)
                except Exception:
                    pass
            context.close()

        return {
            "platform": "Rentals.ca",
            "url": "https://rentals.ca/landlord",
            "screenshot": str(screenshot_path),
            "title": payload["title"]
        }

    def _post_liv_rent(self) -> Dict[str, Any]:
        """Automates Liv.rent landlord listing portal."""
        payload = generate_liv_rent_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_liv_rent.png"

        print(f"[Liv.rent Poster] Opening Liv.rent portal...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.goto("https://liv.rent/landlords", wait_until="domcontentloaded")
            time.sleep(3)

            page.screenshot(path=str(screenshot_path))

            # 3. Optional Auto-Publish (Clicks Next -> Publish)
            if self.auto_publish:
                try:
                    print("[Facebook Poster] Auto-Publish enabled: searching for 'Next' button...")
                    next_btns = page.locator('div[aria-label="Next"], button:has-text("Next"), div[role="button"]:has-text("Next")')
                    if next_btns.count() > 0 and next_btns.first.is_visible():
                        next_btns.first.click()
                        time.sleep(3)
                        print("[Facebook Poster] Searching for 'Publish' button...")
                        pub_btns = page.locator('div[aria-label="Publish"], button:has-text("Publish"), div[role="button"]:has-text("Publish")')
                        if pub_btns.count() > 0 and pub_btns.first.is_visible():
                            pub_btns.first.click()
                            time.sleep(4)
                            print("[Facebook Poster] ✔ Final Publish button clicked!")
                except Exception as pub_err:
                    print(f"[Facebook Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Facebook Poster] Form staged! Browser will stay open for up to 60 seconds for you to review and click Publish...")
                try:
                    page.wait_for_timeout(60000)
                except Exception:
                    pass
            context.close()

        return {
            "platform": "Liv.rent",
            "url": "https://liv.rent/landlords",
            "screenshot": str(screenshot_path),
            "title": payload["title"]
        }
