"""
SQLite Database Layer for Durham Rental Portfolio
Manages property units, photo & video media catalogs, and platform posting history.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent / "rental_portfolio.db"
SAMPLE_JSON_PATH = Path(__file__).parent / "units" / "sample_units.json"

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = DB_PATH):
    """Initializes tables for units, media (photos/videos), and posting history."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Units Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS units (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        street TEXT NOT NULL,
        city TEXT NOT NULL,
        region TEXT DEFAULT 'Durham Region',
        postal_code TEXT,
        unit_type TEXT NOT NULL,
        bedrooms REAL NOT NULL,
        bathrooms REAL NOT NULL,
        sqft INTEGER NOT NULL,
        parking_spots INTEGER DEFAULT 1,
        target_rent REAL NOT NULL,
        utilities_included TEXT, -- JSON Array
        utilities_extra TEXT,    -- JSON Array
        lease_term_months INTEGER DEFAULT 12,
        available_date TEXT,
        amenities TEXT,          -- JSON Array
        pet_policy TEXT,
        smoking_policy TEXT,
        notes TEXT,
        ad_active INTEGER DEFAULT 1,
        last_refreshed_at TIMESTAMP,
        next_refresh_at TIMESTAMP,
        refresh_interval_days INTEGER DEFAULT 7,
        master_title TEXT,
        master_description TEXT,
        master_price REAL,
        master_avail_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Safe Schema Migrations for existing DBs
    for col_def in [
        ("ad_active", "INTEGER DEFAULT 1"),
        ("last_refreshed_at", "TIMESTAMP"),
        ("next_refresh_at", "TIMESTAMP"),
        ("refresh_interval_days", "INTEGER DEFAULT 7"),
        ("master_title", "TEXT"),
        ("master_description", "TEXT"),
        ("master_price", "REAL"),
        ("master_avail_date", "TEXT"),
    ]:
        try:
            cur.execute(f"ALTER TABLE units ADD COLUMN {col_def[0]} {col_def[1]}")
        except Exception:
            pass  # column already exists

    # Media Table (Photos & Videos)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_id TEXT NOT NULL,
        media_type TEXT NOT NULL CHECK(media_type IN ('photo', 'video')),
        file_path TEXT,
        web_url TEXT,
        caption TEXT,
        is_cover INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
    );
    """)

    # Posting History Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS posting_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_id TEXT NOT NULL,
        platform TEXT NOT NULL CHECK(platform IN ('facebook', 'kijiji', 'zumper', 'rentals_ca', 'liv_rent')),
        status TEXT NOT NULL CHECK(status IN ('draft', 'in_progress', 'posted', 'failed', 'inactive')),
        external_url TEXT,
        last_posted_at TIMESTAMP,
        log_output TEXT,
        FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
    );
    """)

    # Applicants & Tenant Screening Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applicants (
        id TEXT PRIMARY KEY,
        unit_id TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        source_platform TEXT DEFAULT 'Google Form',
        stage TEXT DEFAULT 'New Inquiry',
        desired_move_in TEXT,
        occupants INTEGER DEFAULT 1,
        monthly_income REAL DEFAULT 0,
        employment_status TEXT DEFAULT 'Full-Time Permanent',
        employment_months INTEGER DEFAULT 12,
        employer_name TEXT,
        credit_score INTEGER DEFAULT 0,
        credit_utilization REAL DEFAULT 25,
        late_payments INTEGER DEFAULT 0,
        collections_or_insolvency INTEGER DEFAULT 0,
        has_pets INTEGER DEFAULT 0,
        smokes INTEGER DEFAULT 0,
        landlord_ref_verified INTEGER DEFAULT 0,
        showing_slot TEXT,
        ai_score INTEGER DEFAULT 0,
        ai_verdict TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
    );
    """)

    # Ad Performance & Engagement Analytics Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ad_analytics (
        unit_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        views_count INTEGER DEFAULT 0,
        inquiries_count INTEGER DEFAULT 0,
        applications_count INTEGER DEFAULT 0,
        ad_status TEXT DEFAULT 'live',
        listing_url TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(unit_id, platform),
        FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

def seed_from_sample_if_empty(db_path: Path = DB_PATH):
    """Seeds the SQLite database from sample_units.json if units table is empty."""
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM units")
    count = cur.fetchone()[0]
    if count == 0 and SAMPLE_JSON_PATH.exists():
        with open(SAMPLE_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            properties = data.get("properties", [])

            for p in properties:
                # Insert Unit
                cur.execute("""
                INSERT INTO units (
                    id, name, street, city, region, postal_code, unit_type,
                    bedrooms, bathrooms, sqft, parking_spots, target_rent,
                    utilities_included, utilities_extra, lease_term_months,
                    available_date, amenities, pet_policy, smoking_policy, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["id"],
                    p["name"],
                    p["address"]["street"],
                    p["address"]["city"],
                    p["address"].get("region", "Durham Region"),
                    p["address"].get("postal_code", ""),
                    p["type"],
                    p["specs"]["bedrooms"],
                    p["specs"]["bathrooms"],
                    p["specs"]["sqft"],
                    p["specs"].get("parking_spots", 1),
                    p["financials"]["target_rent"],
                    json.dumps(p["financials"].get("utilities_included", [])),
                    json.dumps(p["financials"].get("utilities_extra", [])),
                    p["financials"].get("lease_term_months", 12),
                    p["financials"].get("available_date", ""),
                    json.dumps(p.get("amenities", [])),
                    p.get("pet_policy", ""),
                    p.get("smoking_policy", ""),
                    p.get("notes", "")
                ))

                # Insert Media: Cloud Video (YouTube)
                cloud_media = p.get("cloud_media", {})
                video_url = cloud_media.get("youtube_video_url") or p.get("media", {}).get("video_walkthrough_url")
                if video_url:
                    cur.execute("""
                    INSERT INTO media (unit_id, media_type, file_path, web_url, caption, is_cover, sort_order)
                    VALUES (?, 'video', NULL, ?, 'YouTube Walkthrough Tour', 0, 0)
                    """, (p["id"], video_url))

                # Insert Media: Cloud Photos (Google Drive Unit Folder & Building Exterior)
                drive_folder = cloud_media.get("google_drive_photos_folder")
                building_folder = cloud_media.get("building_exterior_folder") or "https://drive.google.com/drive/folders/1kll_JpcjeQ3KHYk8WtLOjuFmH2Bl9Cy0"
                building_photo = cloud_media.get("building_exterior_photo") or "Screenshot 2026-09-10 12.54.46 PM.png"

                # 1. Building exterior photo (required for every posting)
                cur.execute("""
                INSERT INTO media (unit_id, media_type, file_path, web_url, caption, is_cover, sort_order)
                VALUES (?, 'photo', ?, ?, 'Building Exterior Photo (Google Drive - Required on all posts)', 1, 1)
                """, (p["id"], building_folder, f"{building_folder} - {building_photo}"))

                # 2. Unit-specific photo collection
                cur.execute("""
                INSERT INTO media (unit_id, media_type, file_path, web_url, caption, is_cover, sort_order)
                VALUES (?, 'photo', ?, ?, 'Unit Photo Collection (Google Drive)', 0, 2)
                """, (p["id"], drive_folder, drive_folder))

                # Initialize Default Posting Records
                for plat in ['facebook', 'kijiji', 'zumper', 'rentals_ca', 'liv_rent']:
                    cur.execute("""
                    INSERT INTO posting_history (unit_id, platform, status, external_url, last_posted_at, log_output)
                    VALUES (?, ?, 'draft', NULL, NULL, 'Ready for automated posting')
                    """, (p["id"], plat))

        conn.commit()
    conn.close()

def get_all_units(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Returns all units with their nested media assets and posting statuses."""
    seed_from_sample_if_empty(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT * FROM units ORDER BY id ASC")
    units_rows = cur.fetchall()

    results = []
    for u in units_rows:
        unit_id = u["id"]
        # Fetch Media
        cur.execute("SELECT * FROM media WHERE unit_id = ? ORDER BY sort_order ASC", (unit_id,))
        media_rows = cur.fetchall()
        media_list = [dict(m) for m in media_rows]

        # Fetch Posting Status
        cur.execute("SELECT * FROM posting_history WHERE unit_id = ?", (unit_id,))
        posting_rows = cur.fetchall()
        posting_dict = {p["platform"]: dict(p) for p in posting_rows}

        # Extract cloud media for modern UI
        cloud_media = {
            "building_exterior_folder": "https://drive.google.com/drive/folders/1kll_JpcjeQ3KHYk8WtLOjuFmH2Bl9Cy0",
            "building_exterior_direct_url": "https://drive.google.com/file/d/185EGZHPUiw_bkYOQPyqds8ZvSH6qJ6JZ/view",
            "building_exterior_photo": "Screenshot 2026-09-10 12.54.46 PM.png",
            "youtube_playlist": "https://www.youtube.com/playlist?list=PLLwTe84kfw7U"
        }
        for m in media_list:
            if m["media_type"] == "video":
                cloud_media["youtube_video_url"] = m["web_url"]
            elif m["media_type"] == "photo":
                if "Building" in (m.get("caption") or ""):
                    cloud_media["building_exterior_folder"] = m["file_path"]
                else:
                    cloud_media["google_drive_photos_folder"] = m["file_path"]

        u_dict = dict(u)
        ad_active = u_dict.get("ad_active", 1) == 1
        last_ref = u_dict.get("last_refreshed_at") or datetime.now().isoformat()
        next_ref = u_dict.get("next_refresh_at") or (datetime.now() + timedelta(days=7)).isoformat()

        results.append({
            "id": u["id"],
            "name": u["name"],
            "address": {
                "street": u["street"],
                "city": u["city"],
                "region": u["region"],
                "postal_code": u["postal_code"]
            },
            "type": u["unit_type"],
            "specs": {
                "bedrooms": u["bedrooms"],
                "bathrooms": u["bathrooms"],
                "sqft": u["sqft"],
                "parking_spots": u["parking_spots"]
            },
            "financials": {
                "target_rent": u["target_rent"],
                "utilities_included": json.loads(u["utilities_included"] or "[]"),
                "utilities_extra": json.loads(u["utilities_extra"] or "[]"),
                "lease_term_months": u["lease_term_months"],
                "available_date": u["available_date"]
            },
            "amenities": json.loads(u["amenities"] or "[]"),
            "pet_policy": u["pet_policy"],
            "smoking_policy": u["smoking_policy"],
            "notes": u["notes"],
            "ad_active": ad_active,
            "last_refreshed_at": last_ref,
            "next_refresh_at": next_ref,
            "refresh_interval_days": u_dict.get("refresh_interval_days", 7),
            "master_title": u_dict.get("master_title"),
            "master_description": u_dict.get("master_description"),
            "master_price": u_dict.get("master_price", u["target_rent"]),
            "master_avail_date": u_dict.get("master_avail_date", u["available_date"]),
            "cloud_media": cloud_media,
            "media_assets": media_list,
            "postings": posting_dict
        })

    conn.close()
    return results

def get_unit_by_id(unit_id: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    units = get_all_units(db_path)
    for u in units:
        if u["id"] == unit_id:
            return u
    return None

def update_posting_status(unit_id: str, platform: str, status: str, external_url: str = None, log: str = "", db_path: Path = DB_PATH):
    """Updates the status of a posting (e.g. 'in_progress', 'posted', 'failed', 'inactive')."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute("""
    UPDATE posting_history
    SET status = ?, external_url = COALESCE(?, external_url), last_posted_at = ?, log_output = ?
    WHERE unit_id = ? AND platform = ?
    """, (status, external_url, now, log, unit_id, platform))
    conn.commit()
    conn.close()

def update_unit_master_content(unit_id: str, title: str = None, price: float = None, avail_date: str = None, description: str = None, db_path: Path = DB_PATH) -> bool:
    """Updates the unit's master listing copy so all platforms pull from the same single source of truth."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute("""
    UPDATE units
    SET master_title = COALESCE(?, master_title),
        target_rent = COALESCE(?, target_rent),
        master_price = COALESCE(?, master_price),
        available_date = COALESCE(?, available_date),
        master_avail_date = COALESCE(?, master_avail_date),
        master_description = COALESCE(?, master_description),
        updated_at = ?
    WHERE id = ?
    """, (title, price, price, avail_date, avail_date, description, now, unit_id))
    conn.commit()
    conn.close()
    return True

def add_media_asset(unit_id: str, media_type: str, file_path: str = None, web_url: str = None, caption: str = "", is_cover: bool = False, db_path: Path = DB_PATH):
    """Adds a photo or video record to the unit's media catalog."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO media (unit_id, media_type, file_path, web_url, caption, is_cover, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM media WHERE unit_id = ?))
    """, (unit_id, media_type, file_path, web_url, caption, 1 if is_cover else 0, unit_id))
    conn.commit()
    conn.close()


def get_all_applicants(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM applicants ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_applicant(app_data: Dict[str, Any], db_path: Path = DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    app_id = app_data.get("id") or f"app_{int(datetime.now().timestamp())}"
    cur.execute("""
    INSERT OR REPLACE INTO applicants (
        id, unit_id, full_name, email, phone, source_platform, stage,
        desired_move_in, occupants, monthly_income, employment_status,
        employment_months, employer_name, credit_score, credit_utilization,
        late_payments, collections_or_insolvency, has_pets, smokes,
        landlord_ref_verified, showing_slot, ai_score, ai_verdict, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        app_id,
        app_data.get("unit_id", "unit_3"),
        app_data.get("full_name", "New Applicant"),
        app_data.get("email", ""),
        app_data.get("phone", ""),
        app_data.get("source_platform", "Google Form"),
        app_data.get("stage", "New Inquiry"),
        app_data.get("desired_move_in", "Immediate"),
        int(app_data.get("occupants") or 1),
        float(app_data.get("monthly_income") or 0),
        app_data.get("employment_status", "Full-Time Permanent"),
        int(app_data.get("employment_months") or 12),
        app_data.get("employer_name", ""),
        int(app_data.get("credit_score") or 0),
        float(app_data.get("credit_utilization") or 25),
        int(app_data.get("late_payments") or 0),
        1 if app_data.get("collections_or_insolvency") else 0,
        1 if app_data.get("has_pets") else 0,
        1 if app_data.get("smokes") else 0,
        1 if app_data.get("landlord_ref_verified") else 0,
        app_data.get("showing_slot", ""),
        int(app_data.get("ai_score") or 0),
        app_data.get("ai_verdict", ""),
        app_data.get("notes", "")
    ))
    conn.commit()
    conn.close()
    app_data["id"] = app_id
    return app_data

def get_ad_analytics(unit_id: Optional[str] = None, db_path: Path = DB_PATH) -> list:
    """Retrieves live ad engagement metrics across platforms."""
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Seed default sample data if table is completely empty
    cur.execute("SELECT COUNT(*) FROM ad_analytics")
    if cur.fetchone()[0] == 0:
        sample_rows = [
            ("unit_3", "facebook", 842, 48, 8, "live", "https://www.facebook.com/marketplace/item/315kent-unit3"),
            ("unit_3", "kijiji", 420, 26, 4, "live", "https://www.kijiji.ca/v-apartments-condos/oshawa-durham-region/315-kent-street-unit-3/16849102"),
            ("unit_3", "zumper", 280, 12, 2, "live", "https://www.zumper.com/apartments-for-rent/whitby-on/315-kent-st"),
            ("unit_3", "rentals_ca", 195, 6, 0, "live", "https://rentals.ca/whitby/315-kent-st-unit-3"),
            ("unit_3", "liv_rent", 105, 2, 0, "live", "https://liv.rent/rental-listings/whitby-315-kent"),
            ("unit_1", "facebook", 610, 31, 5, "live", "https://www.facebook.com/marketplace/item/315kent-unit1"),
            ("unit_1", "kijiji", 340, 19, 3, "live", "https://www.kijiji.ca/v-apartments-condos/oshawa-durham-region/315-kent-street-unit-1/16849101"),
            ("unit_1", "zumper", 180, 7, 1, "live", "https://www.zumper.com/apartments-for-rent/whitby-on/315-kent-st-1"),
        ]
        for row in sample_rows:
            cur.execute("""
            INSERT OR REPLACE INTO ad_analytics (unit_id, platform, views_count, inquiries_count, applications_count, ad_status, listing_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, row)
        conn.commit()

    if unit_id:
        cur.execute("SELECT * FROM ad_analytics WHERE unit_id = ? ORDER BY views_count DESC", (unit_id,))
    else:
        cur.execute("SELECT * FROM ad_analytics ORDER BY unit_id, views_count DESC")

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def upsert_ad_analytics(data: dict, db_path: Path = DB_PATH) -> dict:
    """Updates or logs new views/inquiries for an ad."""
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    unit_id = data.get("unit_id", "unit_3")
    platform = data.get("platform", "facebook").lower()
    views = int(data.get("views_count") or 0)
    inquiries = int(data.get("inquiries_count") or 0)
    applications = int(data.get("applications_count") or 0)
    ad_status = data.get("ad_status", "live")
    listing_url = data.get("listing_url", "")

    cur.execute("""
    INSERT INTO ad_analytics (unit_id, platform, views_count, inquiries_count, applications_count, ad_status, listing_url, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(unit_id, platform) DO UPDATE SET
        views_count = excluded.views_count,
        inquiries_count = excluded.inquiries_count,
        applications_count = excluded.applications_count,
        ad_status = excluded.ad_status,
        listing_url = CASE WHEN excluded.listing_url != '' THEN excluded.listing_url ELSE ad_analytics.listing_url END,
        last_updated = CURRENT_TIMESTAMP
    """, (unit_id, platform, views, inquiries, applications, ad_status, listing_url))

    conn.commit()
    conn.close()
    return data

if __name__ == "__main__":
    init_db()
    seed_from_sample_if_empty()
    units = get_all_units()
    print(f"Initialized Database with {len(units)} units and full media tables.")
