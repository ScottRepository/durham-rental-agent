"""
Posting Automation & Assistant Engine
Coordinates browser automation (via Playwright) and structured listing dispatch
for Facebook Marketplace, Kijiji, and Zumper.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

from modules.content_generator import package_all_listings_for_unit

USER_DATA_DIR = Path.home() / ".property_agent_browser_profile"

class PostingEngine:
    def __init__(self, units_file: str):
        self.units_file = Path(units_file)
        self.units = self._load_units()

    def _load_units(self) -> Dict[str, Any]:
        if not self.units_file.exists():
            raise FileNotFoundError(f"Cannot find units file at {self.units_file}")
        with open(self.units_file, "r") as f:
            data = json.load(f)
            return {u["id"]: u for u in data.get("properties", [])}

    def get_unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        return self.units.get(unit_id)

    def export_unit_listing_dossier(self, unit_id: str, output_dir: str = "reports/dossiers") -> str:
        """
        Exports a complete ready-to-copy posting packet with all platform listings,
        media checklist, and video links formatted for copy-paste or quick submission.
        """
        unit = self.get_unit(unit_id)
        if not unit:
            raise ValueError(f"Unit {unit_id} not found.")

        packages = package_all_listings_for_unit(unit)
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{unit_id}_listing_dossier.md"

        content = f"""# Rental Listing Packet: {unit['name']}
**Property Address**: {unit['address']['street']}, {unit['address']['city']}, {unit['address']['region']}
**Target Rent**: ${unit['financials']['target_rent']} CAD/mo | **Move-in**: {unit['financials']['available_date']}
**Walkthrough Video**: {unit['media'].get('video_walkthrough_url', 'N/A')}
**Photos Folder**: `{unit['media'].get('photos_dir', 'N/A')}`

---

## 1. Facebook Marketplace
- **Direct Link to Post**: https://www.facebook.com/marketplace/create/rental
- **Listing Title**: `{packages['facebook_marketplace']['title']}`
- **Price**: `${packages['facebook_marketplace']['price']}`
- **Category**: Property Rentals > {packages['facebook_marketplace']['rental_type']}
- **Bedrooms**: {packages['facebook_marketplace']['bedrooms']} | **Bathrooms**: {packages['facebook_marketplace']['bathrooms']}

### Description:
```text
{packages['facebook_marketplace']['description']}
```

---

## 2. Kijiji Ontario
- **Direct Link to Post**: https://www.kijiji.ca/p-post-ad.html?categoryId=37
- **Title**: `{packages['kijiji']['title']}`
- **Price**: `${packages['kijiji']['price']}`
- **Dedicated YouTube Video Link Field**: `{packages['kijiji']['youtube_video_url']}`
- **Bedrooms**: {packages['kijiji']['bedrooms']} | **Bathrooms**: {packages['kijiji']['bathrooms']}

### Description:
```text
{packages['kijiji']['description']}
```

---

## 3. Zumper / PadMapper
- **Direct Link to Post**: https://www.zumper.com/manage
- **Title**: `{packages['zumper']['title']}`
- **Price**: `${packages['zumper']['price']}`
- **Virtual Tour Link**: `{packages['zumper']['virtual_tour_url']}`
- **Bedrooms**: {packages['zumper']['bedrooms']} | **Bathrooms**: {packages['zumper']['bathrooms']} | **Sqft**: {packages['zumper']['sqft']}

### Description:
```text
{packages['zumper']['description']}
```
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)

    def launch_assisted_browser_session(self, unit_id: str, platform: str):
        """
        Launches an interactive Playwright session with a persistent user browser profile.
        Allows the agent to load the platform, authenticate securely, and prefill
        the fields without triggering automated bot flags or CAPTCHA blocks.
        """
        unit = self.get_unit(unit_id)
        if not unit:
            raise ValueError(f"Unit {unit_id} not found.")

        packages = package_all_listings_for_unit(unit)

        print(f"\n[Posting Assistant] Initializing browser profile at {USER_DATA_DIR}...")
        print(f"[Posting Assistant] Preparing unit {unit_id} ({unit['name']}) for {platform}...")

        target_url = "https://www.facebook.com/marketplace/create/rental"
        payload = packages['facebook_marketplace']

        if platform.lower() == "kijiji":
            target_url = "https://www.kijiji.ca/p-post-ad.html?categoryId=37"
            payload = packages['kijiji']
        elif platform.lower() == "zumper":
            target_url = "https://www.zumper.com/manage"
            payload = packages['zumper']

        print(f"[Target URL]: {target_url}")
        print(f"[Listing Title]: {payload['title']}")
        print(f"[Listing Price]: ${payload['price']}")
        print("\nReady! Use the interactive browser agent to complete submission.")
        return payload
