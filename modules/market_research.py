"""
Market Research & Rental Comps Module for Durham Region, Ontario
Analyzes comparable rental listings across Oshawa, Whitby, Ajax, Pickering, and Clarington.
"""

import json
from typing import Dict, List, Any

# Regional benchmarks based on GTA/Durham rental market data (CAD/month)
DURHAM_RENTAL_COMPS_DATABASE = [
    # Oshawa Comps
    {
        "id": "comp_osh_01",
        "city": "Oshawa",
        "neighbourhood": "Central Oshawa / Simcoe St N",
        "type": "Basement Apartment",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 800,
        "rent": 2050,
        "utilities_included": ["Water"],
        "parking": 1,
        "laundry": "In-unit",
        "source": "Rentals.ca",
        "notes": "Renovated 2024, laminate flooring, quartz kitchen"
    },
    {
        "id": "comp_osh_02",
        "city": "Oshawa",
        "neighbourhood": "North Oshawa (near Ontario Tech)",
        "type": "Basement Apartment",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 900,
        "rent": 2150,
        "utilities_included": ["Water", "Heat", "Hydro"],
        "parking": 1,
        "laundry": "Shared",
        "source": "Kijiji",
        "notes": "All inclusive, egress windows, near transit"
    },
    {
        "id": "comp_osh_03",
        "city": "Oshawa",
        "neighbourhood": "Oshawa Waterfront / South",
        "type": "Basement Apartment",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 850,
        "rent": 1975,
        "utilities_included": ["Water"],
        "parking": 1,
        "laundry": "In-unit",
        "source": "Facebook Marketplace",
        "notes": "Private entrance, 40% utilities"
    },
    {
        "id": "comp_osh_04",
        "city": "Oshawa",
        "neighbourhood": "Central Oshawa",
        "type": "Main Floor House",
        "bedrooms": 3,
        "bathrooms": 1.5,
        "sqft": 1300,
        "rent": 2800,
        "utilities_included": ["Water"],
        "parking": 2,
        "laundry": "In-unit",
        "source": "Zumper",
        "notes": "Large backyard, private garage, stainless appliances"
    },
    {
        "id": "comp_osh_05",
        "city": "Oshawa",
        "neighbourhood": "East Oshawa",
        "type": "Main Floor House",
        "bedrooms": 3,
        "bathrooms": 1,
        "sqft": 1200,
        "rent": 2650,
        "utilities_included": [],
        "parking": 2,
        "laundry": "In-unit",
        "source": "Kijiji",
        "notes": "Tenant pays 60% utilities, walkout deck"
    },
    # Whitby Comps
    {
        "id": "comp_whi_01",
        "city": "Whitby",
        "neighbourhood": "Downtown Whitby",
        "type": "Apartment Suite",
        "bedrooms": 1,
        "bathrooms": 1,
        "sqft": 620,
        "rent": 1825,
        "utilities_included": ["Water", "Heat"],
        "parking": 1,
        "laundry": "On-site",
        "source": "Rentals.ca",
        "notes": "Walk to restaurants, 5 min drive to Whitby GO"
    },
    {
        "id": "comp_whi_02",
        "city": "Whitby",
        "neighbourhood": "Port Whitby",
        "type": "Condo Suite",
        "bedrooms": 1,
        "bathrooms": 1,
        "sqft": 680,
        "rent": 1950,
        "utilities_included": ["Water"],
        "parking": 1,
        "laundry": "In-unit",
        "source": "Zumper",
        "notes": "Steps to Whitby GO station and waterfront trails"
    },
    {
        "id": "comp_whi_03",
        "city": "Whitby",
        "neighbourhood": "Taunton North",
        "type": "Basement Apartment",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 900,
        "rent": 2200,
        "utilities_included": ["Water", "Heat", "Hydro"],
        "parking": 1,
        "laundry": "In-unit",
        "source": "Facebook Marketplace",
        "notes": "Brand new legal suite, quartz counters"
    },
    # Ajax Comps
    {
        "id": "comp_ajx_01",
        "city": "Ajax",
        "neighbourhood": "Central Ajax / Kingston Rd",
        "type": "Townhouse",
        "bedrooms": 2,
        "bathrooms": 2,
        "sqft": 1100,
        "rent": 2450,
        "utilities_included": [],
        "parking": 1,
        "laundry": "In-unit",
        "source": "Rentals.ca",
        "notes": "Multi-level townhouse, garage parking, near Ajax GO"
    },
    {
        "id": "comp_ajx_02",
        "city": "Ajax",
        "neighbourhood": "South Ajax / Lake",
        "type": "Townhouse",
        "bedrooms": 2,
        "bathrooms": 1.5,
        "sqft": 1000,
        "rent": 2350,
        "utilities_included": ["Water"],
        "parking": 1,
        "laundry": "In-unit",
        "source": "Zumper",
        "notes": "Balcony, open layout, walking distance to schools"
    },
    # Pickering Comps
    {
        "id": "comp_pck_01",
        "city": "Pickering",
        "neighbourhood": "Town Centre / Bayly St",
        "type": "Condo / Suite",
        "bedrooms": 1.5,
        "bathrooms": 1,
        "sqft": 680,
        "rent": 2250,
        "utilities_included": ["Water", "Heat"],
        "parking": 1,
        "laundry": "In-unit",
        "source": "Zumper",
        "notes": "San Francisco by the Bay, walk to Pickering GO, balcony"
    },
    {
        "id": "comp_pck_02",
        "city": "Pickering",
        "neighbourhood": "Liverpool",
        "type": "Basement Suite",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 850,
        "rent": 2150,
        "utilities_included": ["Water", "Heat"],
        "parking": 1,
        "laundry": "Shared",
        "source": "Facebook Marketplace",
        "notes": "Quick highway 401 access, separate entrance"
    },
    # Bowmanville / Clarington Comps
    {
        "id": "comp_bwm_01",
        "city": "Bowmanville",
        "neighbourhood": "Downtown Bowmanville",
        "type": "Upper Level House",
        "bedrooms": 3,
        "bathrooms": 1,
        "sqft": 1150,
        "rent": 2475,
        "utilities_included": ["Water"],
        "parking": 2,
        "laundry": "In-unit",
        "source": "Kijiji",
        "notes": "Upper 2 floors of duplex, yard access, quiet street"
    },
    {
        "id": "comp_bwm_02",
        "city": "Bowmanville",
        "neighbourhood": "North Bowmanville",
        "type": "Townhouse",
        "bedrooms": 3,
        "bathrooms": 2.5,
        "sqft": 1400,
        "rent": 2650,
        "utilities_included": [],
        "parking": 2,
        "laundry": "In-unit",
        "source": "Rentals.ca",
        "notes": "Full modern townhouse, master ensuite, tenant pays all utilities"
    }
]

def find_comps_for_unit(unit: Dict[str, Any], max_results: int = 5) -> Dict[str, Any]:
    """
    Finds and analyzes comparable listings in Durham Region based on:
    - Municipality / City
    - Bedroom count (exact or +/- 0.5)
    - Unit type (Basement, Apartment, Townhouse, House)
    - Square footage similarity
    """
    city = unit["address"]["city"].lower()
    beds = unit["specs"]["bedrooms"]
    sqft = unit["specs"]["sqft"]
    target_rent = unit["financials"]["target_rent"]
    unit_type = unit["type"].lower()

    scored_comps = []
    for comp in DURHAM_RENTAL_COMPS_DATABASE:
        score = 0
        comp_city = comp["city"].lower()

        # Location matching
        if comp_city in city or city in comp_city:
            score += 40
        else:
            # Regional neighbor in Durham
            score += 15

        # Bedroom matching
        bed_diff = abs(comp["bedrooms"] - beds)
        if bed_diff == 0:
            score += 35
        elif bed_diff <= 0.5:
            score += 25
        elif bed_diff <= 1:
            score += 10
        else:
            continue  # Don't compare 1-bed with 4-bed

        # Type matching
        if ("basement" in unit_type and "basement" in comp["type"].lower()) or \
           ("townhouse" in unit_type and "townhouse" in comp["type"].lower()) or \
           ("condo" in unit_type and "condo" in comp["type"].lower()) or \
           ("house" in unit_type and "house" in comp["type"].lower()):
            score += 15

        # Sqft proximity
        sqft_diff_pct = abs(comp["sqft"] - sqft) / max(sqft, 1)
        if sqft_diff_pct < 0.15:
            score += 10
        elif sqft_diff_pct < 0.30:
            score += 5

        scored_comps.append((score, comp))

    scored_comps.sort(key=lambda x: x[0], reverse=True)
    selected = [c[1] for c in scored_comps[:max_results]]

    if not selected:
        return {
            "unit_id": unit["id"],
            "unit_name": unit["name"],
            "comps": [],
            "stats": {}
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

    # Positioning recommendation
    diff_from_avg = target_rent - avg_rent
    if abs(diff_from_avg) <= 75:
        positioning = "Optimal Market Alignment (Fair market rent, expect high quality tenant inquiries quickly)"
    elif diff_from_avg > 75:
        positioning = f"Premium Pricing (+${int(diff_from_avg)} above local comp average). Ensure video walkthrough highlights high-end finishes, parking, or utilities included to justify premium."
    else:
        positioning = f"High-Demand / Value Pricing (-${int(abs(diff_from_avg))} below local comp average). Anticipate rapid tenant response; recommend rigorous screening."

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
        "Rentals.ca": f"https://rentals.ca/{city_slug}/{beds}-bedrooms",
        "Zumper": f"https://www.zumper.com/apartments-for-rent/{city_slug}-on/{beds}-beds",
        "Kijiji": f"https://www.kijiji.ca/b-apartments-condos/{city_slug}/c37l1700140"
    }
