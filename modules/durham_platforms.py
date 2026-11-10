"""
Durham Region Rental Platform Directory & Strategy Guide
Identifies the best free and high-converting channels in Durham Region (Oshawa, Whitby, Ajax, Pickering, Clarington).
"""

DURHAM_PLATFORMS = [
    {
        "id": "fb_marketplace",
        "name": "Facebook Marketplace & Durham Rental Groups",
        "category": "Social / Classifieds",
        "cost": "100% Free",
        "local_strength": "Very High (#1 inquiry volume across Durham)",
        "durham_focus": "Reaches commuters, local families, and college/university students. Can cross-post into local groups like 'Durham Region Rentals', 'Oshawa Apartments & Houses for Rent', 'Ajax/Whitby Rentals'.",
        "media_support": {
            "max_photos": 50,
            "video_walkthrough": "Direct video upload supported (MP4/MOV) + clickable link in description",
            "recommended_dimensions": "1:1 square or 4:5 vertical"
        },
        "url": "https://www.facebook.com/marketplace/create/rental",
        "key_tips": [
            "Always state closest GO station (Pickering, Ajax, Whitby, Oshawa) or Highway 401/407 exit.",
            "Screen profiles before replying to weed out fake accounts.",
            "Add video walkthrough link prominently in first 3 lines."
        ]
    },
    {
        "id": "kijiji",
        "name": "Kijiji Ontario (Durham Region / Oshawa / Ajax / Whitby)",
        "category": "General Classifieds",
        "cost": "Free (1-2 active rental ads per account free; upgrade packages optional)",
        "local_strength": "Very High (Standard staple for suburban GTA rentals & basement apartments)",
        "durham_focus": "Huge for basement apartments, duplexes, and single-family home rentals across Oshawa, Courtice, Bowmanville, and Whitby.",
        "media_support": {
            "max_photos": 10,
            "video_walkthrough": "Native YouTube URL embed field (video plays directly inside Kijiji listing)",
            "recommended_dimensions": "Landscape 4:3 or 16:9"
        },
        "url": "https://www.kijiji.ca/p-post-ad.html?categoryId=37",
        "key_tips": [
            "Use the dedicated YouTube link field so prospective tenants see the video badge on search results.",
            "Fill in exact bedroom, bathroom, and parking counts for search filters.",
            "Repost/refresh every 3-4 days to stay at the top of the feed."
        ]
    },
    {
        "id": "zumper",
        "name": "Zumper (Syndicates to PadMapper & Walk Score)",
        "category": "Dedicated Rental Portal",
        "cost": "Free basic listings via Landlord Dashboard",
        "local_strength": "High (Preferred by young professionals and commuters moving from Toronto to Durham)",
        "durham_focus": "Excellent for condos, townhomes, and professionally managed units near transit hubs.",
        "media_support": {
            "max_photos": 30,
            "video_walkthrough": "Virtual tour / 3D tour / YouTube link field",
            "recommended_dimensions": "High-res horizontal"
        },
        "url": "https://www.zumper.com/manage",
        "key_tips": [
            "Posting once on Zumper automatically feeds into PadMapper.",
            "Includes built-in digital screening and credit check options if desired."
        ]
    },
    {
        "id": "rentals_ca",
        "name": "Rentals.ca",
        "category": "Dedicated Rental Portal",
        "cost": "Free (Up to 3 listings free for individual landlords)",
        "local_strength": "High (Top Google organic rank for 'Durham apartments for rent')",
        "durham_focus": "Very popular among renters searching specifically for Oshawa and Pickering rentals.",
        "media_support": {
            "max_photos": 25,
            "video_walkthrough": "Video URL / 3D tour link supported",
            "recommended_dimensions": "High resolution landscape"
        },
        "url": "https://rentals.ca/landlord",
        "key_tips": [
            "Highlight included utilities and exact square footage for best search ranking.",
            "Free tier is perfect for managing a multi-unit rotation."
        ]
    },
    {
        "id": "liv_rent",
        "name": "Liv.rent",
        "category": "Rental Platform & Tenant Verification",
        "cost": "Free plan (Up to 2 active listings simultaneously)",
        "local_strength": "Medium-High (Rapidly growing in the GTA, built-in digital lease & vetting)",
        "durham_focus": "Attracts verified renters who want a secure, scam-free leasing process.",
        "media_support": {
            "max_photos": 20,
            "video_walkthrough": "Virtual tour link & video link integration",
            "recommended_dimensions": "Standard landscape"
        },
        "url": "https://liv.rent/landlord",
        "key_tips": [
            "Pre-screens tenants with Trust Score (credit report and income verification built-in)."
        ]
    },
    {
        "id": "places4students",
        "name": "Places4Students (Oshawa / Durham College & Ontario Tech)",
        "category": "Student Housing Portal",
        "cost": "Free to low-cost partner postings depending on campus season",
        "local_strength": "Extreme (Best channel if units are in North or Central Oshawa)",
        "durham_focus": "Official off-campus housing partner for Ontario Tech University & Durham College students and staff.",
        "media_support": {
            "max_photos": 15,
            "video_walkthrough": "Video link in listing description",
            "recommended_dimensions": "Standard photos"
        },
        "url": "https://www.places4students.com/",
        "key_tips": [
            "Only relevant if units are within reasonable bus commute to North Campus or Downtown Oshawa campus."
        ]
    },
    {
        "id": "craigslist_toronto",
        "name": "Craigslist (Toronto & Eastern Suburbs)",
        "category": "Classifieds",
        "cost": "100% Free",
        "local_strength": "Medium (Solid for out-of-province / newcomer renters looking in the GTA)",
        "durham_focus": "Free coverage under the 'suburbs / durham' filter.",
        "media_support": {
            "max_photos": 24,
            "video_walkthrough": "Direct link in description",
            "recommended_dimensions": "Standard"
        },
        "url": "https://toronto.craigslist.org/",
        "key_tips": [
            "Include 'Durham Region', 'Oshawa', 'Whitby', 'Ajax' in the title for sub-region searches."
        ]
    }
]

def get_recommended_platforms():
    return DURHAM_PLATFORMS
