"""
Rental Listing Content Generator
Crafts tailored, high-converting rental listings formatted for Facebook Marketplace, Kijiji, and Zumper/PadMapper.
"""

from typing import Dict, Any

def _get_media(unit: Dict[str, Any]) -> Dict[str, str]:
    cloud = unit.get("cloud_media", {})
    legacy = unit.get("media", {})
    return {
        "video_url": cloud.get("youtube_video_url") or legacy.get("video_walkthrough_url") or "Contact for YouTube link",
        "drive_folder": cloud.get("google_drive_photos_folder") or legacy.get("photos_dir") or "Google Drive",
        "cover_photo": cloud.get("cover_photo_url") or "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800"
    }

def generate_facebook_marketplace_listing(unit: Dict[str, Any]) -> Dict[str, str]:
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)

    title = f"{specs['bedrooms']} Bed {specs['bathrooms']} Bath - {unit['type']} | {address['city']}"
    if len(title) > 100:
        title = title[:97] + "..."

    utilities_inc = ", ".join(financials['utilities_included']) if financials['utilities_included'] else "None (Tenant pays utilities)"
    utilities_ext = ", ".join(financials['utilities_extra']) if financials['utilities_extra'] else "Included in rent"

    description = f"""✨ BEAUTIFULLY MAINTAINED {specs['bedrooms']} BEDROOM RENTAL IN {address['city'].upper()}, ON ✨

📍 LOCATION: {address['street']}, {address['city']} ({address['region']})
💰 RENT: ${financials['target_rent']:,}/month
📅 MOVE-IN DATE: {financials['available_date']}

🎥 YOUTUBE WALKTHROUGH TOUR:
{media_info['video_url']}

🏢 UNIT HIGHLIGHTS & SPECS:
• Bedrooms: {specs['bedrooms']}
• Bathrooms: {specs['bathrooms']}
• Approximate Size: ~{specs['sqft']} sq. ft.
• Parking: {specs['parking_spots']} dedicated parking spot(s)
• Type: {unit['type']}

🌟 FEATURES & AMENITIES:
"""
    for a in unit.get("amenities", []):
        description += f"• {a}\n"

    description += f"""
💡 UTILITIES & LEASE TERMS:
• Included: {utilities_inc}
• Extra: {utilities_ext}
• Lease: {financials['lease_term_months']} Month Standard Ontario Residential Tenancy Agreement
• Pets: {unit.get('pet_policy', 'Pets considered (Ontario standard)')}
• Smoking: {unit.get('smoking_policy', 'Strictly non-smoking unit')}

🚇 COMMUTE & TRANSIT:
{unit.get('notes', 'Conveniently located near public transit, shopping, and major highways.')}

📋 REQUIREMENTS FOR APPLICATION:
1. Proof of income / recent paystubs & employment letter
2. Credit check / Equifax score report
3. Photo ID & references

📩 TO BOOK A SHOWING:
Please message directly with a brief introduction about yourself and anyone who would be living with you, your target move-in date, and reason for moving.
"""

    return {
        "platform": "Facebook Marketplace",
        "title": title,
        "price": str(financials['target_rent']),
        "category": "Property Rentals",
        "rental_type": unit['type'],
        "bedrooms": str(specs['bedrooms']),
        "bathrooms": str(specs['bathrooms']),
        "description": description.strip(),
        "video_link": media_info['video_url'],
        "drive_folder": media_info['drive_folder']
    }

def generate_kijiji_listing(unit: Dict[str, Any]) -> Dict[str, str]:
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)

    title = f"{specs['bedrooms']} Bedroom {unit['type']} for Rent in {address['city']} - Video Tour Available"
    if len(title) > 70:
        title = f"{specs['bedrooms']} Bed {unit['type']} in {address['city']} - Video Tour"

    utilities_inc = ", ".join(financials['utilities_included']) if financials['utilities_included'] else "None"
    utilities_ext = ", ".join(financials['utilities_extra']) if financials['utilities_extra'] else "Included"

    description = f"""FOR RENT: Spacious & Clean {specs['bedrooms']} Bed / {specs['bathrooms']} Bath Unit in {address['city']}

Watch the full YouTube walkthrough tour here:
{media_info['video_url']}

UNIT DETAILS:
- Address: {address['street']}, {address['city']}, ON ({address['postal_code']})
- Rent: ${financials['target_rent']:,}/month
- Bedrooms: {specs['bedrooms']}
- Bathrooms: {specs['bathrooms']}
- Square Footage: approx. {specs['sqft']} sqft
- Parking: {specs['parking_spots']} space(s) included
- Move-In Availability: {financials['available_date']}

AMENITIES & HIGHLIGHTS:
"""
    for a in unit.get("amenities", []):
        description += f"- {a}\n"

    description += f"""
UTILITY BREAKDOWN:
- Utilities Included: {utilities_inc}
- Utilities Extra: {utilities_ext}

LEASE TERMS & VETTING:
- 1-Year Ontario Standard Lease Agreement
- First & last month's rent deposit required upon lease signing
- Required: Credit check, letter of employment, recent pay stubs, reference check

LOCATION HIGHLIGHTS:
{unit.get('notes', 'Close to GO Station, 401, parks, and shopping.')}

Interested? Send a message with your intended move-in date and a short introduction.
"""

    return {
        "platform": "Kijiji Ontario",
        "title": title,
        "price": str(financials['target_rent']),
        "category": "Apartments & Condos for Rent",
        "bedrooms": str(specs['bedrooms']),
        "bathrooms": str(specs['bathrooms']),
        "youtube_video_url": media_info['video_url'],
        "description": description.strip(),
        "drive_folder": media_info['drive_folder']
    }

def generate_zumper_listing(unit: Dict[str, Any]) -> Dict[str, str]:
    specs = unit["specs"]
    financials = unit["financials"]
    address = unit["address"]
    media_info = _get_media(unit)

    title = f"{address['street']}, Unit - {specs['bedrooms']} Bed / {specs['bathrooms']} Bath in {address['city']}"

    amenities_list = "\n".join([f"• {a}" for a in unit.get("amenities", [])])

    description = f"""Welcome to this modern {specs['bedrooms']}-bedroom, {specs['bathrooms']}-bathroom rental located at {address['street']} in desirable {address['city']}, Durham Region.

Key Unit Features:
- Living Area: Approximately {specs['sqft']} sq ft
- Parking: {specs['parking_spots']} spot(s)
- Available Date: {financials['available_date']}
- Lease Duration: {financials['lease_term_months']} months

Amenities:
{amenities_list}

YouTube Virtual Walkthrough:
{media_info['video_url']}

Lease Terms:
Standard Ontario Tenancy Agreement. Full application, credit evaluation, and employment verification required.
"""

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
        "description": description.strip(),
        "drive_folder": media_info['drive_folder']
    }

def package_all_listings_for_unit(unit: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "unit_id": unit["id"],
        "unit_name": unit["name"],
        "facebook_marketplace": generate_facebook_marketplace_listing(unit),
        "kijiji": generate_kijiji_listing(unit),
        "zumper": generate_zumper_listing(unit)
    }
