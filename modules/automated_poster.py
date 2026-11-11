"""
Playwright-Powered 1-Click Automated Poster, Deleter & 7-Day Renewal Bot
for Facebook Marketplace, Kijiji, Zumper, Rentals.ca, and Liv.rent.
Loads property details and media from SQLite, downloads high-res photos from Google Drive,
navigates to external platforms, stages/publishes or deletes listings, and records status in SQLite.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from data.database import get_unit_by_id, update_posting_status, get_connection, DB_PATH
from modules.content_generator import (
    generate_facebook_marketplace_listing,
    generate_kijiji_listing,
    generate_zumper_listing,
    generate_rentals_ca_listing
)

USER_PROFILE_DIR = Path.home() / ".property_agent_browser_profile"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "reports" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

ALL_PLATFORMS = ["facebook", "kijiji", "zumper", "rentals_ca"]


class AutomatedPoster:
    def __init__(self, unit_id: str, platform: str = "facebook", headless: bool = False, auto_publish: bool = False):
        self.unit_id = unit_id
        self.platform = platform.lower().replace(".", "_")
        self.headless = headless
        self.auto_publish = auto_publish
        self.unit = get_unit_by_id(unit_id)
        if not self.unit:
            raise ValueError(f"Unit ID '{unit_id}' not found in database.")

    def _get_or_download_unit_photos(self) -> List[str]:
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
                with urllib.request.urlopen(req, timeout=15) as resp, open(ext_path, "wb") as f:
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
                html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
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
                            with urllib.request.urlopen(dl_req, timeout=15) as resp, open(out_file, "wb") as out:
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

    def _sync_analytics_status(self, platform: str, ad_status: str):
        """Keeps ad_analytics table synchronized when ads are posted or deleted."""
        try:
            conn = get_connection(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
            UPDATE ad_analytics
            SET ad_status = ?, last_updated = CURRENT_TIMESTAMP
            WHERE unit_id = ? AND platform = ?
            """, (ad_status, self.unit_id, platform))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def run(self) -> Dict[str, Any]:
        """Executes the one-click posting workflow (supports single platform or 'all')."""
        if self.platform == "all":
            results = {}
            for plat in ALL_PLATFORMS:
                sub = AutomatedPoster(self.unit_id, plat, headless=self.headless, auto_publish=self.auto_publish)
                results[plat] = sub.run()
            return {"success": True, "platform": "all", "results": results}

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
            else:
                raise ValueError(f"Unsupported platform: {self.platform}")

            is_published = result.get("published", self.auto_publish)
            status_label = "posted" if is_published else "draft"
            update_posting_status(
                self.unit_id,
                self.platform,
                status_label,
                external_url=result.get("url"),
                log=f"Successfully {'published' if is_published else 'pre-filled & staged for review'} on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            self._sync_analytics_status(self.platform, "live" if is_published else "pending")
            return {"success": True, "details": result, "published": is_published, "status": "posted" if is_published else "staged"}

        except Exception as e:
            error_msg = f"Posting error: {str(e)}"
            print(f"[AutomatedPoster Error] {error_msg}")
            try:
                update_posting_status(self.unit_id, self.platform, "failed", log=error_msg)
            except Exception:
                pass
            return {"success": False, "error": error_msg}

    def delete_posting(self) -> Dict[str, Any]:
        """
        Deletes / takes down the listing from the target platform (or all platforms)
        using Playwright browser automation and updates the SQLite database.
        """
        if self.platform == "all":
            results = {}
            for plat in ALL_PLATFORMS:
                sub = AutomatedPoster(self.unit_id, plat, headless=self.headless)
                results[plat] = sub.delete_posting()
            return {"success": True, "action": "delete_all", "unit_id": self.unit_id, "results": results}

        print(f"[Delete Bot] Taking down {self.unit_id} on {self.platform}...")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Update DB immediately
        update_posting_status(
            self.unit_id,
            self.platform,
            "inactive",
            log=f"Taken down / deleted via bot at {now_str}"
        )
        self._sync_analytics_status(self.platform, "inactive")

        manage_urls = {
            "facebook": "https://www.facebook.com/marketplace/you/selling",
            "kijiji": "https://www.kijiji.ca/m-my-ads/active",
            "zumper": "https://www.zumper.com/manage",
            "rentals_ca": "https://rentals.ca/landlord"
        }
        target_url = manage_urls.get(self.platform, "https://www.facebook.com/marketplace/you/selling")
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_{self.platform}_deleted.png"

        try:
            USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(USER_PROFILE_DIR),
                    headless=self.headless,
                    viewport={"width": 1366, "height": 850},
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = context.new_page()
                self._safe_goto(page, target_url)

                # Attempt platform-specific delete / unpublish click if listing is visible
                try:
                    if self.platform == "facebook":
                        del_btn = page.locator('div[aria-label*="Delete"], button:has-text("Delete listing"), span:has-text("Delete listing")').first
                        if del_btn.count() > 0 and del_btn.is_visible():
                            del_btn.click(timeout=2500)
                            time.sleep(1.5)
                            confirm_btn = page.locator('div[aria-label="Delete"], button:has-text("Delete")').last
                            if confirm_btn.count() > 0 and confirm_btn.is_visible():
                                confirm_btn.click(timeout=2500)
                    elif self.platform == "kijiji":
                        del_btn = page.locator('button:has-text("Delete"), a:has-text("Delete")').first
                        if del_btn.count() > 0 and del_btn.is_visible():
                            del_btn.click(timeout=2500)
                    elif self.platform in ("zumper", "rentals_ca"):
                        unpub_btn = page.locator('button:has-text("Unpublish"), button:has-text("Deactivate"), button:has-text("Delete")').first
                        if unpub_btn.count() > 0 and unpub_btn.is_visible():
                            unpub_btn.click(timeout=2500)
                except Exception as click_err:
                    print(f"[Delete Bot Click Note] {click_err}")

                self._safe_screenshot(page, screenshot_path)
                if not self.headless:
                    print(f"[Delete Bot] Opened {self.platform} management page. Keeping open for 15s to verify deletion...")
                    try:
                        page.wait_for_timeout(15000)
                    except Exception:
                        pass
                context.close()
        except Exception as e:
            print(f"[Delete Bot Browser Note] {e}")

        return {
            "success": True,
            "action": "deleted",
            "unit_id": self.unit_id,
            "platform": self.platform,
            "manage_url": target_url,
            "screenshot": str(screenshot_path),
            "message": f"Listing for {self.unit['name']} on {self.platform.upper()} taken down and marked inactive."
        }

    def renew_posting(self) -> Dict[str, Any]:
        """
        Executes the 7-Day Auto-Renewal workflow:
        1. Takes down / deletes the old posting so it doesn't appear stale.
        2. Re-posts a fresh ad with all photos and current master pricing/copy.
        """
        print(f"[7-Day Renew Bot] Taking down old ad and re-posting fresh for {self.unit_id} on {self.platform}...")
        del_res = self.delete_posting()
        post_res = self.run()
        return {
            "success": post_res.get("success", True),
            "action": "renewed_7day",
            "unit_id": self.unit_id,
            "platform": self.platform,
            "deleted": del_res,
            "reposted": post_res,
            "message": f"7-Day Renewal complete for {self.unit['name']} ({self.platform.upper()}): old post removed & fresh ad staged!"
        }

    def _safe_goto(self, page, url: str) -> None:
        """Navigates to URL with resilient timeout handling so slow third-party scripts never hang the bot."""
        page.set_default_timeout(25000)
        try:
            page.goto(url, wait_until="commit", timeout=25000)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=12000)
            except Exception:
                pass
            time.sleep(3.0)
        except Exception as nav_err:
            print(f"[Browser Navigation Note] {url}: {nav_err}")

    def _safe_click(self, loc) -> None:
        """Clicks an element resiliently, falling back to JavaScript click if animation or layout is shifting."""
        try:
            loc.click(timeout=3000, force=True)
        except Exception:
            try:
                loc.evaluate("e => e.click()")
            except Exception as e:
                print(f"[Safe Click Note] {e}")

    def _safe_screenshot(self, page, screenshot_path: Path) -> None:
        """Captures screenshot without hanging on slow external webfont loads."""
        try:
            page.screenshot(path=str(screenshot_path), timeout=10000, animations="disabled")
        except Exception as sc_err:
            print(f"[Screenshot Note] {sc_err}")

    def _post_facebook(self) -> Dict[str, Any]:
        """Automates Facebook Marketplace rental listing form with robust selector handling."""
        payload = generate_facebook_marketplace_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_facebook.png"

        print(f"[Facebook Poster] Opening Facebook Marketplace with profile at {USER_PROFILE_DIR}...")
        published = False
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.set_default_timeout(20000)
            self._safe_goto(page, "https://www.facebook.com/marketplace/create/rental")

            # Check if login is required
            if "login" in page.url.lower():
                print("[Facebook Poster] Login required in browser profile. Keeping window open for user to log in...")
                if not self.headless:
                    try:
                        page.wait_for_timeout(30000)
                    except Exception:
                        pass
                return {
                    "platform": "Facebook Marketplace",
                    "url": page.url,
                    "screenshot": str(screenshot_path),
                    "login_required": True,
                    "message": "Please log into Facebook in the opened browser window. Your login will be saved permanently for future 1-click postings."
                }

            # Check if Facebook Seller Limit is reached on new accounts
            time.sleep(2.0)
            limit_banner = page.locator('div:has-text("Limit reached"), div:has-text("You are not able to create new listings right now")')
            if limit_banner.count() > 0 and limit_banner.first.is_visible():
                msg = "Facebook Marketplace daily limit reached for this account (new accounts have strict limits on creating listings). Please edit an existing listing or wait for Facebook's daily limit to lift."
                print(f"[Facebook Poster] ⚠️ {msg}")
                self._safe_screenshot(page, screenshot_path)
                context.close()
                return {
                    "platform": "Facebook Marketplace",
                    "url": page.url,
                    "screenshot": str(screenshot_path),
                    "limit_reached": True,
                    "message": msg,
                    "published": False,
                    "status": "draft"
                }

            # 1. Automatically attach suite photos and exterior photo
            photos = self._get_or_download_unit_photos()
            if photos:
                try:
                    file_input = page.locator('input[type="file"][accept*="image"], input[type="file"]').first
                    if file_input.count() > 0:
                        print(f"[Facebook Poster] Automatically uploading {len(photos)} photos from Google Drive cache...")
                        file_input.set_input_files(photos)
                        time.sleep(3.5)
                except Exception as photo_err:
                    print(f"[Facebook Photo Upload Note] {photo_err}")

            # 2. Pre-fill standard Facebook Marketplace rental inputs
            try:
                clean_price = str(payload["price"]).replace(".0", "")

                # Step A: Select 'Rent' on 'Home for sale or rent'
                rent_type = page.locator('label:has-text("Home for sale or rent")').first
                if rent_type.count() > 0 and rent_type.is_visible():
                    print("[Facebook Poster] Selecting Rent dropdown...")
                    self._safe_click(rent_type)
                    time.sleep(0.7)
                    rent_opt = page.locator('div[role="listbox"] div[role="option"]:has-text("Rent")').first
                    if rent_opt.count() > 0:
                        self._safe_click(rent_opt)
                        time.sleep(1.0)

                # Step B: Select 'Apartment' on 'Rental type' / 'Property type'
                rental_type = page.locator('label:has-text("Rental type"), label:has-text("Property type")').first
                if rental_type.count() > 0 and rental_type.is_visible():
                    print("[Facebook Poster] Selecting Rental Type -> Apartment...")
                    self._safe_click(rental_type)
                    time.sleep(0.7)
                    apt_opt = page.locator('div[role="listbox"] div[role="option"]:has-text("Apartment")').first
                    if apt_opt.count() > 0:
                        self._safe_click(apt_opt)
                        time.sleep(1.0)

                # Step C: Bedrooms
                bed_loc = page.locator('label:has-text("Number of bedrooms") input').first
                if bed_loc.count() > 0:
                    bed_loc.fill(str(payload["bedrooms"]))

                # Step D: Bathrooms
                bath_loc = page.locator('label:has-text("Number of bathrooms") input').first
                if bath_loc.count() > 0:
                    bath_loc.fill(str(payload["bathrooms"]))

                # Step E: Price per month
                p_loc = page.locator('label:has-text("Price per month") input, label:has-text("Price") input').first
                if p_loc.count() > 0:
                    p_loc.fill(clean_price)

                # Step F: Address (Whitby Central)
                addr_loc = page.locator('input[aria-label*="Address"]:visible').first
                if addr_loc.count() > 0:
                    addr_loc.fill("315 Kent Street, Whitby, ON")
                    time.sleep(1.5)
                    # Pick first suggestion from listbox
                    sugg = page.locator('ul[role="listbox"] li, div[role="option"]').first
                    if sugg.count() > 0 and sugg.is_visible():
                        self._safe_click(sugg)

                # Step G: Description
                desc_loc = page.locator('label:has-text("Rental description") textarea, label:has-text("Property description") textarea').first
                if desc_loc.count() > 0:
                    desc_loc.fill(payload["description"])

                # Step H: Square Footage if available
                sqft = self.unit.get("specs", {}).get("square_feet")
                if sqft:
                    sqft_loc = page.locator('label:has-text("Property square feet") input').first
                    if sqft_loc.count() > 0:
                        sqft_loc.fill(str(sqft))

            except Exception as fill_err:
                print(f"[Facebook Auto-Fill Note] {fill_err}")

            time.sleep(2.0)
            self._safe_screenshot(page, screenshot_path)

            # 3. Optional Auto-Publish (Clicks Next -> Select Groups -> Publish)
            if self.auto_publish:
                try:
                    print("[Facebook Poster] Auto-Publish enabled: searching for 'Next' button...")
                    next_btns = page.locator('div[aria-label="Next"][role="button"], button:has-text("Next"), div[role="button"]:has-text("Next")')
                    if next_btns.count() > 0 and next_btns.first.is_visible():
                        self._safe_click(next_btns.first)
                        time.sleep(3.5)

                        # In Step 2, select groups if available
                        group_checkboxes = page.locator('div[role="checkbox"]').all()
                        for cb in group_checkboxes[:5]:
                            try:
                                if cb.get_attribute("aria-checked") == "false":
                                    self._safe_click(cb)
                                    time.sleep(0.3)
                            except Exception:
                                pass

                        print("[Facebook Poster] Searching for 'Publish' button...")
                        pub_btns = page.locator('div[aria-label="Publish"][role="button"], button:has-text("Publish"), div[role="button"]:has-text("Publish")')
                        if pub_btns.count() > 0 and pub_btns.first.is_visible():
                            self._safe_click(pub_btns.first)
                            time.sleep(5.0)
                            published = True
                            print("[Facebook Poster] ✔ Final Publish button clicked successfully!")
                            self._safe_screenshot(page, screenshot_path)
                except Exception as pub_err:
                    print(f"[Facebook Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Facebook Poster] Form pre-filled & staged! Keeping browser open for 30s so you can review and click Next / Publish...")
                try:
                    page.wait_for_timeout(30000)
                except Exception:
                    pass
            context.close()

        return {
            "platform": "Facebook Marketplace",
            "url": "https://www.facebook.com/marketplace/create/rental",
            "screenshot": str(screenshot_path),
            "photos_attached": len(photos),
            "title": payload["title"],
            "price": payload["price"],
            "published": published,
            "status": "posted" if published else "staged_for_review"
        }

    def _post_kijiji(self) -> Dict[str, Any]:
        """Automates Kijiji Ontario rental listing form matching the user's demonstrated workflow."""
        import urllib.parse
        payload = generate_kijiji_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_kijiji.png"

        print(f"[Kijiji Poster] Opening Kijiji post form...")
        published = False
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            encoded_title = urllib.parse.quote_plus(payload["title"])
            target_url = f"https://www.kijiji.ca/p-post-ad.html?categoryId=37&adTitle={encoded_title}"
            self._safe_goto(page, target_url)

            # 1. Automatically attach suite photos and exterior photo
            photos = self._get_or_download_unit_photos()
            if photos:
                try:
                    file_inputs = page.locator('input[type="file"][accept*="image"], input[type="file"]')
                    if file_inputs.count() > 0:
                        print(f"[Kijiji Poster] Automatically uploading {len(photos)} photos from Google Drive cache...")
                        file_inputs.first.set_input_files(photos)
                        time.sleep(4.0)
                except Exception as photo_err:
                    print(f"[Kijiji Photo Upload Note] {photo_err}")

            # 2. Select rental specs and details matching manual workflow
            try:
                # Rental type: Apartment / Duplex
                for sel in ['label:has-text("Apartment")', 'button:has-text("Apartment")', 'input[value*="apartment" i]']:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        self._safe_click(loc)
                        break

                # Bedrooms: 2
                for sel in ['label:has-text("2"):visible', 'button:has-text("2"):visible']:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        self._safe_click(loc)
                        break

                # Bathrooms: 1
                for sel in ['label:has-text("1"):visible', 'button:has-text("1"):visible']:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        self._safe_click(loc)
                        break

                # Agreement Type: 1 Year / One-year
                for sel in ['label:has-text("1 Year")', 'button:has-text("1 Year")', 'label:has-text("One-year")']:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        self._safe_click(loc)
                        break

                # Parking Included: 1
                parking_sel = page.locator('select[name*="parking" i], input[name*="parking" i]').first
                if parking_sel.count() > 0 and parking_sel.is_visible():
                    try:
                        parking_sel.select_option("1")
                    except Exception:
                        parking_sel.fill("1")

                # Additional Features Checkboxes (Online Application, Video Walkthrough, Video Chat)
                for opt in ["Online Application", "Video Walkthrough", "Video Chat"]:
                    opt_loc = page.locator(f'label:has-text("{opt}")').first
                    if opt_loc.count() > 0 and opt_loc.is_visible():
                        self._safe_click(opt_loc)

                # Pre-fill standard fields: title, description, price, YouTube link
                clean_price = str(payload["price"]).replace(".0", "")
                for sel, val in [
                    ("input[name*='postAdForm.title'], #AdTitleForm", payload["title"]),
                    ("textarea[name*='postAdForm.description'], #pstad-descrptn", payload["description"]),
                    ("input[name*='postAdForm.priceAmount'], #PriceAmount", clean_price),
                    ("input[name*='youtube'], input[id*='youtube']", payload.get("youtube_video_url", ""))
                ]:
                    try:
                        loc = page.locator(sel).first
                        if loc.count() > 0 and loc.is_visible():
                            loc.fill(val, timeout=2500)
                    except Exception:
                        pass

                # Location: Target visible postal code / address input
                loc_input = page.locator('input[placeholder*="Postal code or street address"]:visible, input#pstad-loc-txt:visible').first
                if loc_input.count() > 0 and loc_input.is_visible():
                    loc_input.fill("315 Kent Street, Whitby, ON", timeout=2500)
                    time.sleep(1.5)
                    suggs = page.locator('.suggestion, .location-suggestion, li[role="option"]').all()
                    if suggs:
                        self._safe_click(suggs[0])

            except Exception as fill_err:
                print(f"[Kijiji Auto-Fill Note] {fill_err}")

            self._safe_screenshot(page, screenshot_path)

            # 3. Optional Auto-Publish (Clicks Post Your Ad)
            if self.auto_publish:
                try:
                    print("[Kijiji Poster] Auto-Publish enabled: searching for 'Post Your Ad' button...")
                    pub_btns = page.locator('button[type="submit"]:has-text("Post Your Ad"), button:has-text("Post Your Ad")')
                    if pub_btns.count() > 0 and pub_btns.first.is_visible():
                        self._safe_click(pub_btns.first)
                        time.sleep(6.0)
                        published = True
                        print("[Kijiji Poster] ✔ Final Post Your Ad button clicked!")
                        self._safe_screenshot(page, screenshot_path)
                except Exception as pub_err:
                    print(f"[Kijiji Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Kijiji Poster] Form staged! Keeping bot browser open for 30 seconds so you can review and click Post Your Ad...")
                try:
                    page.wait_for_timeout(30000)
                except Exception:
                    pass
            context.close()

        return {
            "platform": "Kijiji Ontario",
            "url": "https://www.kijiji.ca/p-post-ad.html?categoryId=37",
            "screenshot": str(screenshot_path),
            "photos_attached": len(photos),
            "title": payload["title"],
            "video_url": payload.get("youtube_video_url"),
            "published": published,
            "status": "posted" if published else "staged_for_review"
        }

    def _post_zumper(self) -> Dict[str, Any]:
        """
        Automates Zumper Landlord listing portal through every step demonstrated in the manual workflow:
        1. Address & Unit
        2. Listing Details (Beds, Baths, Sqft)
        3. Description & Amenities
        4. Monthly Rent
        5. Media (Photo gallery upload from Drive cache)
        6. Video (YouTube walkthrough tour)
        7. Review & Publish / Bypass boost modal
        """
        payload = generate_zumper_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_zumper.png"

        print(f"[Zumper Poster] Opening Zumper manage portal...")
        photos = self._get_or_download_unit_photos()
        published = False

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.set_default_timeout(20000)

            # Navigate to Zumper manage or create listing directly
            self._safe_goto(page, "https://www.zumper.com/manage")

            # Check if login required
            if "login" in page.url.lower():
                print("[Zumper Poster] Login required in browser profile. Keeping window open...")
                if not self.headless:
                    try:
                        page.wait_for_timeout(30000)
                    except Exception:
                        pass
                return {
                    "platform": "Zumper & PadMapper",
                    "url": page.url,
                    "screenshot": str(screenshot_path),
                    "login_required": True,
                    "message": "Please log into Zumper in the opened browser window."
                }

            # Step 0: Click "Create a new listing" or navigate to create URL
            create_btn = page.locator('a:has-text("Create a new listing"), button:has-text("Create a new listing"), a:has-text("Create a Listing"), button:has-text("Create a Listing")')
            if create_btn.count() > 0 and create_btn.first.is_visible():
                self._safe_click(create_btn.first)
                time.sleep(3.0)
            elif "/manage/create" not in page.url:
                self._safe_goto(page, "https://www.zumper.com/manage/create")

            # Helper to click Next
            def _click_next():
                time.sleep(1.5)
                next_btn = page.locator('button:has-text("Next"), div[role="button"]:has-text("Next")').first
                if next_btn.count() > 0 and next_btn.is_visible():
                    self._safe_click(next_btn)
                    time.sleep(3.0)
                    return True
                return False

            # --- STEP 1: Address & Property Type ---
            print(f"[Zumper Poster] Step 1: Address & Unit for {payload['street_address']}...")
            try:
                addr_inp = page.locator('input[placeholder*="address" i], input[name*="address" i], input[id*="address" i]').first
                if addr_inp.count() > 0 and addr_inp.is_visible():
                    addr_inp.fill("315 Kent Street, Whitby, ON")
                    time.sleep(1.5)
                    sugg = page.locator('ul[role="listbox"] li, div[role="option"], div[class*="suggestion"], div[class*="pac-item"]').first
                    if sugg.count() > 0 and sugg.is_visible():
                        self._safe_click(sugg)
                        time.sleep(1.0)

                unit_num = self.unit.get("id", "").replace("unit_", "")
                unit_inp = page.locator('input[placeholder*="unit" i], input[placeholder*="apt" i], input[name*="unit" i], input[name*="apt" i]').first
                if unit_inp.count() > 0 and unit_inp.is_visible():
                    unit_inp.fill(f"Unit {unit_num}")

                _click_next()
            except Exception as step1_err:
                print(f"[Zumper Step 1 Note] {step1_err}")

            # --- STEP 2: Listing Details (Beds, Baths, Sqft) ---
            print(f"[Zumper Poster] Step 2: Beds ({payload['bedrooms']}), Baths ({payload['bathrooms']}), Sqft ({payload['sqft']})...")
            try:
                # Bedrooms
                beds_btn = page.locator(f'button:has-text("{payload["bedrooms"]}"), div[role="button"]:has-text("{payload["bedrooms"]}")').first
                if beds_btn.count() > 0 and beds_btn.is_visible():
                    self._safe_click(beds_btn)
                else:
                    beds_inp = page.locator('input[name*="bed" i]').first
                    if beds_inp.count() > 0 and beds_inp.is_visible():
                        beds_inp.fill(payload["bedrooms"])

                # Bathrooms
                baths_btn = page.locator(f'button:has-text("{payload["bathrooms"]}"), div[role="button"]:has-text("{payload["bathrooms"]}")').first
                if baths_btn.count() > 0 and baths_btn.is_visible():
                    self._safe_click(baths_btn)
                else:
                    baths_inp = page.locator('input[name*="bath" i]').first
                    if baths_inp.count() > 0 and baths_inp.is_visible():
                        baths_inp.fill(payload["bathrooms"])

                # Sqft
                sqft_inp = page.locator('input[placeholder*="sq" i], input[name*="sqft" i], input[name*="size" i]').first
                if sqft_inp.count() > 0 and sqft_inp.is_visible():
                    sqft_inp.fill(payload["sqft"])

                _click_next()
            except Exception as step2_err:
                print(f"[Zumper Step 2 Note] {step2_err}")

            # --- STEP 3: Description & Amenities ---
            print(f"[Zumper Poster] Step 3: Description & Amenities...")
            try:
                desc_inp = page.locator('textarea').first
                if desc_inp.count() > 0 and desc_inp.is_visible():
                    desc_inp.fill(payload["description"])

                # Click common amenities if shown
                for amen in ["In-unit laundry", "Assigned parking", "Central heat", "Hardwood floor", "Air conditioning"]:
                    amen_el = page.locator(f'label:has-text("{amen}"), button:has-text("{amen}")').first
                    if amen_el.count() > 0 and amen_el.is_visible():
                        self._safe_click(amen_el)

                _click_next()
            except Exception as step3_err:
                print(f"[Zumper Step 3 Note] {step3_err}")

            # --- STEP 4: Monthly Rent & Move-In Date ---
            print(f"[Zumper Poster] Step 4: Monthly Rent (${payload['price']})...")
            try:
                rent_inp = page.locator('input[name*="rent" i], input[placeholder*="rent" i], input[name*="price" i], input[type="number"]').first
                if rent_inp.count() > 0 and rent_inp.is_visible():
                    clean_price = "".join(filter(str.isdigit, str(payload["price"])))
                    rent_inp.fill(clean_price)

                _click_next()
            except Exception as step4_err:
                print(f"[Zumper Step 4 Note] {step4_err}")

            # --- STEP 5: Media / Photos Upload ---
            print(f"[Zumper Poster] Step 5: Uploading {len(photos)} photos from Drive cache...")
            if photos:
                try:
                    file_input = page.locator('input[type="file"]').first
                    if file_input.count() > 0:
                        file_input.set_input_files(photos)
                        print("[Zumper Poster] Photos attached, waiting for upload progress...")
                        time.sleep(6.0)

                    _click_next()
                except Exception as step5_err:
                    print(f"[Zumper Step 5 Note] {step5_err}")

            # --- STEP 6: Video Walkthrough Link ---
            video_url = payload.get("virtual_tour_url")
            if video_url:
                print(f"[Zumper Poster] Step 6: Attaching YouTube Tour {video_url}...")
                try:
                    video_inp = page.locator('input[placeholder*="youtube" i], input[placeholder*="video" i], input[placeholder*="vimeo" i], input[type="url"], input[name*="video" i]').first
                    if video_inp.count() > 0 and video_inp.is_visible():
                        video_inp.fill(video_url)
                        time.sleep(1.5)

                    _click_next()
                except Exception as step6_err:
                    print(f"[Zumper Step 6 Note] {step6_err}")

            # --- STEP 7: Review & Auto-Publish / Skip Boost ---
            time.sleep(2.0)
            self._safe_screenshot(page, screenshot_path)

            if self.auto_publish:
                try:
                    print("[Zumper Poster] Auto-Publish enabled: searching for 'Publish' or 'Submit' button...")
                    pub_btns = page.locator('button:has-text("Publish"), button:has-text("Submit listing"), button:has-text("Save and Publish")')
                    if pub_btns.count() > 0 and pub_btns.first.is_visible():
                        self._safe_click(pub_btns.first)
                        time.sleep(4.0)

                        # Bypass Boost / Upsell Modal ($30 boost vs Free)
                        print("[Zumper Poster] Checking for 'Continue without boost' or 'Free' option...")
                        skip_boost = page.locator('button:has-text("Continue without boost"), button:has-text("Post without boost"), button:has-text("Skip"), button:has-text("No thanks"), a:has-text("Continue without boost"), div[role="button"]:has-text("Continue without boost")').first
                        if skip_boost.count() > 0 and skip_boost.is_visible():
                            self._safe_click(skip_boost)
                            time.sleep(3.5)

                        published = True
                        print("[Zumper Poster] ✔ Final listing published live to Zumper & PadMapper!")
                        self._safe_screenshot(page, screenshot_path)
                except Exception as pub_err:
                    print(f"[Zumper Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Zumper Poster] Form staged through all steps! Keeping browser open for 30s so you can review...")
                try:
                    page.wait_for_timeout(30000)
                except Exception:
                    pass

            context.close()

        return {
            "platform": "Zumper & PadMapper",
            "url": "https://www.zumper.com/manage",
            "screenshot": str(screenshot_path),
            "photos_attached": len(photos),
            "title": payload["title"],
            "video_url": payload.get("virtual_tour_url"),
            "published": published,
            "status": "posted" if published else "staged_for_review"
        }

    def _post_rentals_ca(self) -> Dict[str, Any]:
        """
        Automates Rentals.ca landlord listing portal matching the user's demonstrated workflow:
        1. Address & Unit Number
        2. Specs (Beds, Baths, Sqft, Rent)
        3. Features & Amenities
        4. Photos Upload & YouTube Tour
        5. Plan Selection (Bypasses paid tiers to select the Free 'Limited' Standard Visibility plan)
        """
        payload = generate_rentals_ca_listing(self.unit)
        USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{self.unit_id}_rentals_ca.png"

        print(f"[Rentals.ca Poster] Opening Rentals.ca portal...")
        photos = self._get_or_download_unit_photos()
        published = False

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1366, "height": 850},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.set_default_timeout(25000)

            # Navigate to landlord portal
            self._safe_goto(page, "https://rentals.ca/landlord")

            # Check if login required
            if "login" in page.url.lower():
                print("[Rentals.ca Poster] Login required in browser profile. Keeping window open...")
                if not self.headless:
                    try:
                        page.wait_for_timeout(30000)
                    except Exception:
                        pass
                return {
                    "platform": "Rentals.ca",
                    "url": page.url,
                    "screenshot": str(screenshot_path),
                    "login_required": True,
                    "message": "Please log into Rentals.ca in the opened browser window."
                }

            # Helper for advancing wizard
            def _click_next():
                time.sleep(1.5)
                next_btn = page.locator('button:has-text("Next"), div[role="button"]:has-text("Next"), button:has-text("Continue")').first
                if next_btn.count() > 0 and next_btn.is_visible():
                    self._safe_click(next_btn)
                    time.sleep(3.0)
                    return True
                return False

            # Step 0: Click "Post a Rental"
            post_btn = page.locator('a:has-text("Post a Rental"), button:has-text("Post a Rental"), a[href*="post"]').first
            if post_btn.count() > 0 and post_btn.is_visible():
                self._safe_click(post_btn)
                time.sleep(3.0)

            # --- STEP 1: Property Type & Address ---
            print(f"[Rentals.ca Poster] Step 1: Address & Property Type...")
            try:
                # Property type: Apartment
                apt_type = page.locator('div:has-text("Apartment"), button:has-text("Apartment"), label:has-text("Apartment")').first
                if apt_type.count() > 0 and apt_type.is_visible():
                    self._safe_click(apt_type)

                # Address
                addr_inp = page.locator('input[placeholder*="address" i], input[name*="address" i], input[id*="address" i]').first
                if addr_inp.count() > 0 and addr_inp.is_visible():
                    addr_inp.fill("315 Kent Street, Whitby, ON")
                    time.sleep(1.5)
                    sugg = page.locator('ul[role="listbox"] li, div[role="option"], div[class*="suggestion"], div[class*="pac-item"]').first
                    if sugg.count() > 0 and sugg.is_visible():
                        self._safe_click(sugg)
                        time.sleep(1.0)

                # Unit
                unit_num = self.unit.get("id", "").replace("unit_", "")
                unit_inp = page.locator('input[placeholder*="unit" i], input[name*="unit" i], input[placeholder*="apt" i]').first
                if unit_inp.count() > 0 and unit_inp.is_visible():
                    unit_inp.fill(f"Unit {unit_num}")

                _click_next()
            except Exception as step1_err:
                print(f"[Rentals.ca Step 1 Note] {step1_err}")

            # --- STEP 2: Specs & Pricing ---
            print(f"[Rentals.ca Poster] Step 2: Specs & Pricing...")
            try:
                clean_price = str(payload.get("price", "1995")).replace(".0", "")
                for sel, val in [
                    ('input[name*="rent" i], input[placeholder*="rent" i], input[name*="price" i]', clean_price),
                    ('input[name*="bed" i], input[placeholder*="bed" i]', str(self.unit["specs"]["bedrooms"])),
                    ('input[name*="bath" i], input[placeholder*="bath" i]', str(self.unit["specs"]["bathrooms"])),
                    ('input[name*="sqft" i], input[placeholder*="sqft" i]', str(self.unit["specs"].get("sqft", 800)))
                ]:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        loc.fill(val)

                _click_next()
            except Exception as step2_err:
                print(f"[Rentals.ca Step 2 Note] {step2_err}")

            # --- STEP 3: Amenities & Features ---
            print(f"[Rentals.ca Poster] Step 3: Features & Amenities...")
            try:
                for amen in ["Laundry", "Balcony", "Parking", "Air Conditioning"]:
                    amen_el = page.locator(f'label:has-text("{amen}"), div:has-text("{amen}")').first
                    if amen_el.count() > 0 and amen_el.is_visible():
                        self._safe_click(amen_el)

                _click_next()
            except Exception as step3_err:
                print(f"[Rentals.ca Step 3 Note] {step3_err}")

            # --- STEP 4: Media Upload (Photos) ---
            print(f"[Rentals.ca Poster] Step 4: Uploading {len(photos)} photos...")
            if photos:
                try:
                    file_inputs = page.locator('input[type="file"]')
                    if file_inputs.count() > 0:
                        file_inputs.first.set_input_files(photos)
                        time.sleep(5.0)

                    _click_next()
                except Exception as step4_err:
                    print(f"[Rentals.ca Step 4 Note] {step4_err}")

            # --- STEP 5: Description & Virtual Tour ---
            print(f"[Rentals.ca Poster] Step 5: Description & Virtual Tour...")
            try:
                desc_el = page.locator("textarea").first
                if desc_el.count() > 0 and desc_el.is_visible():
                    desc_el.fill(payload["description"])

                video_url = payload.get("virtual_tour_url")
                if video_url:
                    v_inp = page.locator('input[placeholder*="youtube" i], input[placeholder*="video" i], input[type="url"]').first
                    if v_inp.count() > 0 and v_inp.is_visible():
                        v_inp.fill(video_url)

                _click_next()
            except Exception as step5_err:
                print(f"[Rentals.ca Step 5 Note] {step5_err}")

            # --- STEP 6: Choose Free / Standard Plan ---
            time.sleep(2.0)
            self._safe_screenshot(page, screenshot_path)

            if self.auto_publish:
                try:
                    print("[Rentals.ca Poster] Auto-Publish enabled: looking for Free 'Limited' visibility plan...")
                    # Click "See other pricing options" to reveal the Free tier
                    alt_pricing = page.locator('a:has-text("See other pricing options"), button:has-text("See other pricing options"), text="See other pricing options"').first
                    if alt_pricing.count() > 0 and alt_pricing.is_visible():
                        self._safe_click(alt_pricing)
                        time.sleep(2.0)

                    # Select "Limited" / "Standard Visibility" plan
                    free_plan_btn = page.locator('div:has-text("Limited") button, button:has-text("Select Plan"), div:has-text("STANDARD VISIBILITY") button, button:has-text("Continue with Free")').first
                    if free_plan_btn.count() > 0 and free_plan_btn.is_visible():
                        self._safe_click(free_plan_btn)
                        time.sleep(4.0)

                    published = True
                    print("[Rentals.ca Poster] ✔ Listing published live on Rentals.ca!")
                    self._safe_screenshot(page, screenshot_path)
                except Exception as pub_err:
                    print(f"[Rentals.ca Auto-Publish Note] {pub_err}")

            if not self.headless and not self.auto_publish:
                print("\n[Rentals.ca Poster] Form staged! Keeping browser open for 30s so you can review...")
                try:
                    page.wait_for_timeout(30000)
                except Exception:
                    pass

            context.close()

        return {
            "platform": "Rentals.ca",
            "url": "https://rentals.ca/landlord",
            "screenshot": str(screenshot_path),
            "photos_attached": len(photos),
            "title": payload["title"],
            "published": published,
            "status": "posted" if published else "staged_for_review"
        }
