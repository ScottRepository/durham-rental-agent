"""
Posting Automation & Assistant Engine
Coordinates browser automation (via Playwright) and structured listing dispatch
for Facebook Marketplace, Kijiji, Zumper, Rentals.ca, and Liv.rent.
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
        with open(self.units_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {u["id"]: u for u in data.get("properties", [])}

    def get_unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        return self.units.get(unit_id)

    def export_unit_listing_dossier(self, unit_id: str, output_dir: str = "reports/dossiers") -> str:
        """
        Exports a complete ready-to-copy posting packet with all platform listings,
        media checklist, video walkthrough, and Google Form intake link.
        """
        unit = self.get_unit(unit_id)
        if not unit:
            raise ValueError(f"Unit {unit_id} not found.")

        packages = package_all_listings_for_unit(unit)
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{unit_id}_listing_dossier.md"

        media = unit.get("cloud_media") or unit.get("media") or {}
        video_url = media.get("youtube_video_url") or media.get("video_walkthrough_url", "N/A")
        photos_folder = media.get("google_drive_photos_folder") or media.get("photos_dir", "N/A")
        intake_form = unit.get("intake_form_url") or "https://forms.gle/UZSrP8PUSh9GsdLX8"

        content = f"""# Rental Listing Packet: {unit['name']}
**Property Address**: {unit['address']['street']}, {unit['address']['city']}, {unit['address']['region']}
**Target Rent**: ${unit['financials']['target_rent']:,} CAD/mo | **Move-in**: {unit['financials']['available_date']}
**Applicant Intake Form**: {intake_form}
**YouTube Walkthrough Video**: {video_url}
**Google Drive Photos Folder**: `{photos_folder}`

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

---

## 4. Rentals.ca
- **Direct Link to Post**: https://rentals.ca/landlord
- **Title**: `{packages['rentals_ca']['title']}`
- **Price**: `${packages['rentals_ca']['price']}`
- **Virtual Tour Link**: `{packages['rentals_ca']['virtual_tour_url']}`
- **Bedrooms**: {packages['rentals_ca']['bedrooms']} | **Bathrooms**: {packages['rentals_ca']['bathrooms']}

### Description:
```text
{packages['rentals_ca']['description']}
```

---

## 5. Liv.rent
- **Direct Link to Post**: https://liv.rent/landlords
- **Title**: `{packages['liv_rent']['title']}`
- **Price**: `${packages['liv_rent']['price']}`
- **Virtual Tour Link**: `{packages['liv_rent']['virtual_tour_url']}`
- **Bedrooms**: {packages['liv_rent']['bedrooms']} | **Bathrooms**: {packages['liv_rent']['bathrooms']}

### Description:
```text
{packages['liv_rent']['description']}
```
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)

    def export_all_dossiers(self) -> Dict[str, str]:
        results = {}
        for unit_id in self.units.keys():
            results[unit_id] = self.export_unit_listing_dossier(unit_id)
        return results
