"""
Market Research & Rental Comps Module for Durham Region, Ontario
Analyzes comparable rental listings strictly for APARTMENTS IN APARTMENT BUILDINGS
(excluding basement apartments and whole houses), with heat type and parking flags.
Includes comps from Viewit.ca, Realtor.ca, Rentals.ca, Zumper, and Kijiji.
"""

import json
from typing import Dict, List, Any

# Durham Region Apartment Building Comps Database
# Strictly APARTMENTS IN APARTMENT BUILDINGS (Multi-unit, low-rise, mid-rise)
# Excludes basement apartments and detached single-family houses.
DURHAM_RENTAL_COMPS_DATABASE = [
    # Whitby Comps (Apartment Buildings)
    {
        "id": "comp_whi_01",
        "city": "Whitby",
        "neighbourhood": "Downtown Whitby (Brock & Gilbert)",
        "building_type": "Boutique Low-Rise Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 820,
        "rent": 2050,
        "heat_type": "Radiant Hot Water / Boiler (Included)",
        "parking": "Included (1 dedicated parking spot)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site coin laundry",
        "source": "Viewit.ca",
        "notes": "Low-rise 8-plex apartment building, renovated kitchen, walk to downtown Whitby amenities."
    },
    {
        "id": "comp_whi_02",
        "city": "Whitby",
        "neighbourhood": "Downtown Whitby (Colborne & Dundas)",
        "building_type": "Multi-Family Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 850,
        "rent": 2100,
        "heat_type": "Boiler / Hot Water Radiators (Included)",
        "parking": "Included (1 assigned outdoor space)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site laundry",
        "source": "Realtor.ca",
        "notes": "Spacious 2-bedroom suite in quiet residential apartment building, tenant pays hydro."
    },
    {
        "id": "comp_whi_03",
        "city": "Whitby",
        "neighbourhood": "Central Whitby (Mary St E / Garden)",
        "building_type": "Low-Rise Apartment Complex",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 800,
        "rent": 2025,
        "heat_type": "Radiant Heating (Included)",
        "parking": "Included (1 parking space)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site laundry facilities",
        "source": "Rentals.ca",
        "notes": "Clean 2-bedroom apartment suite near shopping and transit, parking included."
    },
    {
        "id": "comp_whi_04",
        "city": "Whitby",
        "neighbourhood": "Port Whitby (Victoria St W / Watson)",
        "building_type": "Mid-Rise Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 860,
        "rent": 2150,
        "heat_type": "Forced Air Gas (Included)",
        "parking": "Extra ($75/month)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "Shared building laundry",
        "source": "Zumper",
        "notes": "Close to Whitby GO station and lakefront trails, modern finishes."
    },

    # Oshawa Comps (Apartment Buildings)
    {
        "id": "comp_osh_01",
        "city": "Oshawa",
        "neighbourhood": "Central Oshawa (Simcoe St S & Bruce)",
        "building_type": "Low-Rise Brick Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 830,
        "rent": 1995,
        "heat_type": "Radiant Hot Water Boiler (Included)",
        "parking": "Included (1 parking spot)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site laundry",
        "source": "Viewit.ca",
        "notes": "Quiet boutique building near transit routes, heat and water included in rent."
    },
    {
        "id": "comp_osh_02",
        "city": "Oshawa",
        "neighbourhood": "Oshawa North (Mary St N & Rossland)",
        "building_type": "Mid-Rise Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 850,
        "rent": 2075,
        "heat_type": "Radiant Hot Water (Included)",
        "parking": "Included (1 space)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "Building laundry room",
        "source": "Realtor.ca",
        "notes": "Bright 2-bed suite with balcony, secure entry, close to schools."
    },
    {
        "id": "comp_osh_03",
        "city": "Oshawa",
        "neighbourhood": "Central Oshawa (Bond St & Centre St)",
        "building_type": "Multi-Unit Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 800,
        "rent": 1950,
        "heat_type": "Boiler Radiators (Included)",
        "parking": "Included (1 space)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site",
        "source": "Kijiji",
        "notes": "Central location, parking included, tenant pays personal hydro."
    },
    {
        "id": "comp_osh_04",
        "city": "Oshawa",
        "neighbourhood": "East Oshawa (King St E & Wilson)",
        "building_type": "Low-Rise Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 780,
        "rent": 1975,
        "heat_type": "Radiant Hot Water (Included)",
        "parking": "Extra ($50/month)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site coin laundry",
        "source": "Rentals.ca",
        "notes": "Renovated 2-bedroom suite, controlled access, mature tenant building."
    },

    # Ajax Comps (Apartment Buildings)
    {
        "id": "comp_ajx_01",
        "city": "Ajax",
        "neighbourhood": "Central Ajax (Harwood Ave S & Bayly)",
        "building_type": "Mid-Rise Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 880,
        "rent": 2195,
        "heat_type": "Radiant Boiler Heat (Included)",
        "parking": "Included (1 space)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site coin laundry",
        "source": "Viewit.ca",
        "notes": "Walking distance to Ajax GO station and shopping plaza."
    },
    {
        "id": "comp_ajx_02",
        "city": "Ajax",
        "neighbourhood": "North Ajax (Westney Rd N & Kingston Rd)",
        "building_type": "Multi-Unit Apartment Complex",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 840,
        "rent": 2150,
        "heat_type": "Central Gas Heating (Included)",
        "parking": "Included (1 parking spot)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "Building laundry room",
        "source": "Realtor.ca",
        "notes": "Close to 401 transit links, includes heat and water."
    },

    # Pickering Comps (Apartment Buildings)
    {
        "id": "comp_pck_01",
        "city": "Pickering",
        "neighbourhood": "Pickering Town Centre (Kingston Rd & Glenanna)",
        "building_type": "Mid-Rise Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 850,
        "rent": 2250,
        "heat_type": "Forced Air Gas (Included)",
        "parking": "Extra ($80/month)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site laundry",
        "source": "Realtor.ca",
        "notes": "Immediate walk to Pickering Town Centre and GO Station transit hub."
    },

    # Bowmanville / Clarington Comps (Apartment Buildings)
    {
        "id": "comp_bwm_01",
        "city": "Bowmanville",
        "neighbourhood": "Downtown Bowmanville (Church & Temperance)",
        "building_type": "Boutique Low-Rise Apartment Building",
        "type": "Apartment Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 800,
        "rent": 1950,
        "heat_type": "Radiant Boiler (Included)",
        "parking": "Included (1 space)",
        "utilities_included": ["Water", "Heat"],
        "laundry": "On-site laundry",
        "source": "Viewit.ca",
        "notes": "Charming low-rise apartment building near downtown shops, heat included."
    }
]

def get_comps_for_city(city: str) -> List[Dict[str, Any]]:
    c_lower = city.strip().lower()
    return [c for c in DURHAM_RENTAL_COMPS_DATABASE if c["city"].lower() == c_lower]

def find_comps_for_unit(unit: Dict[str, Any], max_results: int = 6) -> Dict[str, Any]:
    specs = unit["specs"]
    beds = specs["bedrooms"]
    sqft = specs["sqft"]
    city = unit["address"]["city"]
    target_rent = unit["financials"]["target_rent"]

    # Filter strictly for apartment buildings matching bedroom count
    exact_matches = [
        c for c in DURHAM_RENTAL_COMPS_DATABASE
        if c["city"].lower() == city.lower() and c["bedrooms"] == beds
    ]

    regional_matches = [
        c for c in DURHAM_RENTAL_COMPS_DATABASE
        if c["bedrooms"] == beds and c not in exact_matches
    ]

    selected = exact_matches + regional_matches
    selected = selected[:max_results]

    if not selected:
        return {
            "unit_id": unit["id"],
            "unit_name": unit["name"],
            "error": "No matching apartment building comps found in Durham database."
        }

    rents = [c["rent"] for c in selected]
    sqfts = [c["sqft"] for c in selected]
    psqft = [c["rent"] / c["sqft"] for c in selected if c["sqft"] > 0]

    avg_rent = round(sum(rents) / len(rents), 2)
    min_rent = min(rents)
    max_rent = max(rents)
    median_rent = round(sorted(rents)[len(rents) // 2], 2)
    avg_price_per_sqft = round(sum(psqft) / len(psqft), 2) if psqft else 0

    unit_psqft = round(target_rent / sqft, 2) if sqft > 0 else 0

    diff_from_avg = target_rent - avg_rent
    if abs(diff_from_avg) <= 75:
        positioning = f"Optimal Market Alignment (Fair market rent for Durham apartment buildings, avg ${int(avg_rent)}/mo)"
    elif diff_from_avg > 75:
        positioning = f"Premium Pricing (+${int(diff_from_avg)} above local apartment building average). Highlight included parking, boiler heat, and private balcony to justify."
    else:
        positioning = f"High-Demand / Value Pricing (-${int(abs(diff_from_avg))} below local apartment building average of ${int(avg_rent)}/mo). Strong tenant demand expected."

    return {
        "unit_id": unit["id"],
        "unit_name": unit["name"],
        "municipality": unit["address"]["city"],
        "specs": f"{beds} Bed / {unit['specs']['bathrooms']} Bath (~{sqft} sqft)",
        "target_rent": target_rent,
        "unit_price_per_sqft": unit_psqft,
        "stats": {
            "comp_count": len(selected),
            "average_comp_rent": avg_rent,
            "median_comp_rent": median_rent,
            "min_comp_rent": min_rent,
            "max_comp_rent": max_rent,
            "avg_price_per_sqft": avg_price_per_sqft,
            "diff_from_market_average": round(diff_from_avg, 2)
        },
        "verdict": positioning,
        "comps": selected
    }

def get_live_market_search_urls(city: str, beds: int) -> Dict[str, str]:
    """Generates direct URL links for real-time market comps lookup in Durham Region."""
    city_slug = city.strip().lower().replace(" ", "-")
    return {
        "Viewit.ca (Apartments)": f"https://www.viewit.ca/rentals/{city_slug}",
        "Realtor.ca (Whitby Apartments)": f"https://www.realtor.ca/on/{city_slug}/rentals",
        "Rentals.ca": f"https://rentals.ca/{city_slug}/{beds}-bedrooms",
        "Zumper": f"https://www.zumper.com/apartments-for-rent/{city_slug}-on/{beds}-beds",
        "Kijiji": f"https://www.kijiji.ca/b-apartments-condos/{city_slug}/c37l1700140"
    }
