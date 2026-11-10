"""
Rental Listing Content Generator
Crafts tailored, high-converting rental listings formatted for Facebook Marketplace,
Kijiji, Zumper/PadMapper, Rentals.ca, and Liv.rent.
Replicated authentically from owner's standard 315 Kent Street listing template.
"""

from typing import Dict, Any

DEFAULT_INTAKE_FORM_URL = "https://forms.gle/UZSrP8PUSh9GsdLX8"

def _get_media(unit: Dict[str, Any]) -> Dict[str, str]:
    cloud = unit.get("cloud_media", {})
    legacy = unit.get("media", {})
    return {
        "video_url": cloud.get("youtube_video_url") or legacy.get("video_walkthrough_url") or "https://www.youtube.com/playlist?list=PLLwTe84kfw7U",
        "drive_folder": cloud.get("google_drive_photos_folder") or legacy.get("photos_dir") or "https://drive.google.com/drive/folders/1TAeTgXcOFydiAh6xYD7hBCZ0oAjXrqTt?usp=sharing",
        "cover_photo": cloud.get("cover_photo_url") or "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800",
        "intake_form": unit.get("intake_form_url") or DEFAULT_INTAKE_FORM_URL
    }

def get_unit_specific_bullet(unit: Dict[str, Any]) -> str:
    """Returns unit-specific floor/feature description bullet."""
    uid = unit.get("id", "")
    if uid == "unit_1":
        return "* Lower Level Unit 1 is half above ground and half below. Lots of light\n* The second bedroom is smaller so it would be suitable for an office, spare bedroom, small bedroom or den."
    elif uid == "unit_2":
        return "* Lower Level Unit 2 is half above ground and half below. Generous natural daylight and comfortable layout."
    elif uid == "unit_3":
        return "* Upper Level Unit 3 features a private walkout balcony overlooking the property grounds.\n* Full 2 bedroom layout with spacious living room."
    elif uid == "unit_4":
        return "* Unit 4 features clean modern laminate/hardwood style flooring in a quiet, peaceful building setting."
    elif uid == "unit_5":
        return "* Upper Level Unit 5 with expansive picture windows and elevated views.\n* Full kitchen with ample cabinet storage."
    elif uid == "unit_6":
        return "* Upper Level Unit 6 is a quiet corner suite offering maximum privacy and bright living spaces."
    else:
        return f"* {unit.get('notes', 'Well-maintained boutique apartment suite.')}"

def generate_standard_description(unit: Dict[str, Any], include_emojis: bool = False) -> str:
    """
    Standard description replicating the owner's Google Doc template.
    """
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)
    unit_bullet = get_unit_specific_bullet(unit)
    unit_label = unit.get("name", f"Unit {unit['id']}")

    rent_str = f"${financials['target_rent']:,}"
    form_link = media_info["intake_form"]
    video_link = media_info["video_url"]

    header_icon = "✨ " if include_emojis else ""
    point_prefix = "• " if include_emojis else "* "

    desc = f"""Whitby Central, Renovated 2-Bed, Great Location, Most Utilities - {unit_label}

FILL OUT FORM TO SET SHOWING DATE/TIME:
{form_link}

Very clean and comfortable 2 bedroom (or 1 bed + den) available for rent immediately. Just a 5-minute walk to downtown Whitby, shopping, transit, grocery stores, 401, GO Transit, schools, and many other great amenities!

Includes one parking space with laundry on-site. The property has a beautiful yard and great neighbours. Located in a safe neighbourhood and in a small six unit apartment building.

🎥 YouTube Walkthrough Tour:
{video_link}

KEY HIGHLIGHTS:
{point_prefix}Kent St off Brock, Whitby
{unit_bullet}
{point_prefix}Includes heat, on-site coin laundry, water and one parking space
{point_prefix}Renovated & very clean
{point_prefix}Five minute walk to everything including 401 and GO Train
{point_prefix}{rent_str} per month includes heat and water. Tenant pays hydro
{point_prefix}No Marijuana Growing / No Smoking of any kind in unit
{point_prefix}No Pets
{point_prefix}Suitable for Professional, retired or mature student
{point_prefix}Owners have many past references from previous tenants providing quality service
{point_prefix}Available Immediately

FILL OUT FORM TO SET SHOWING DATE/TIME:
{form_link}

We will contact qualified candidates for a showing. DO NOT EMAIL, USE THE FORM PLEASE."""
    return desc.strip()

def generate_facebook_marketplace_listing(unit: Dict[str, Any]) -> Dict[str, str]:
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)

    title = f"{specs['bedrooms']} Bed {specs['bathrooms']} Bath - {unit['name']} | Whitby Central"
    if len(title) > 100:
        title = title[:97] + "..."

    description = generate_standard_description(unit, include_emojis=True)

    return {
        "platform": "Facebook Marketplace",
        "title": title,
        "price": str(financials['target_rent']),
        "category": "Property Rentals",
        "rental_type": unit['type'],
        "bedrooms": str(specs['bedrooms']),
        "bathrooms": str(specs['bathrooms']),
        "description": description,
        "video_link": media_info['video_url'],
        "drive_folder": media_info['drive_folder'],
        "intake_form": media_info['intake_form']
    }

def generate_kijiji_listing(unit: Dict[str, Any]) -> Dict[str, str]:
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)

    unit_label = unit.get("name", f"Unit {unit['id']}")
    title = f"Whitby Central Renovated 2-Bed Apt ({unit_label}) - Most Utilities"
    if len(title) > 70:
        title = f"Whitby Central 2-Bed Apt - Most Utilities ({unit['id']})"

    description = generate_standard_description(unit, include_emojis=False)

    return {
        "platform": "Kijiji Ontario",
        "title": title,
        "price": str(financials['target_rent']),
        "category": "Apartments & Condos for Rent",
        "bedrooms": str(specs['bedrooms']),
        "bathrooms": str(specs['bathrooms']),
        "youtube_video_url": media_info['video_url'],
        "description": description,
        "drive_folder": media_info['drive_folder'],
        "intake_form": media_info['intake_form']
    }

def generate_zumper_listing(unit: Dict[str, Any]) -> Dict[str, str]:
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)

    unit_label = unit.get("name", f"Unit {unit['id']}")
    title = f"{address['street']} - 2 Bed / 1 Bath Boutique Suite | Whitby"

    description = generate_standard_description(unit, include_emojis=False)

    return {
        "platform": "Zumper & PadMapper",
        "title": title,
        "price": str(financials['target_rent']),
        "street_address": address['street'],
        "city": address['city'],
        "postal_code": address['postal_code'],
        "bedrooms": str(specs['bedrooms']),
        "bathrooms": str(specs['bathrooms']),
        "sqft": str(specs['sqft']),
        "virtual_tour_url": media_info['video_url'],
        "description": description,
        "drive_folder": media_info['drive_folder'],
        "intake_form": media_info['intake_form']
    }

def generate_rentals_ca_listing(unit: Dict[str, Any]) -> Dict[str, str]:
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)

    unit_label = unit.get("name", f"Unit {unit['id']}")
    title = f"Whitby Central - Renovated 2-Bed Apartment ({unit_label})"

    description = generate_standard_description(unit, include_emojis=False)

    return {
        "platform": "Rentals.ca",
        "title": title,
        "price": str(financials['target_rent']),
        "bedrooms": str(specs['bedrooms']),
        "bathrooms": str(specs['bathrooms']),
        "sqft": str(specs['sqft']),
        "virtual_tour_url": media_info['video_url'],
        "description": description,
        "drive_folder": media_info['drive_folder'],
        "intake_form": media_info['intake_form']
    }

def generate_liv_rent_listing(unit: Dict[str, Any]) -> Dict[str, str]:
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)

    unit_label = unit.get("name", f"Unit {unit['id']}")
    title = f"Whitby Central 2-Bedroom Suite - {unit_label}"

    description = generate_standard_description(unit, include_emojis=False)

    return {
        "platform": "Liv.rent",
        "title": title,
        "price": str(financials['target_rent']),
        "bedrooms": str(specs['bedrooms']),
        "bathrooms": str(specs['bathrooms']),
        "sqft": str(specs['sqft']),
        "virtual_tour_url": media_info['video_url'],
        "description": description,
        "drive_folder": media_info['drive_folder'],
        "intake_form": media_info['intake_form']
    }

def package_all_listings_for_unit(unit: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "unit_id": unit["id"],
        "unit_name": unit["name"],
        "facebook_marketplace": generate_facebook_marketplace_listing(unit),
        "kijiji": generate_kijiji_listing(unit),
        "zumper": generate_zumper_listing(unit),
        "rentals_ca": generate_rentals_ca_listing(unit),
        "liv_rent": generate_liv_rent_listing(unit)
    }
