"""
SQLite Database Layer for Durham Rental Portfolio
Manages property units, photo & video media catalogs, and platform posting history.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

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
        platform TEXT NOT NULL CHECK(platform IN ('facebook', 'kijiji', 'zumper', 'rentals_ca')),
        status TEXT NOT NULL CHECK(status IN ('draft', 'in_progress', 'posted', 'failed')),
        external_url TEXT,
        last_posted_at TIMESTAMP,
        log_output TEXT,
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

                # Insert Media: Cloud Photos (Google Drive & Cover)
                drive_folder = cloud_media.get("google_drive_photos_folder")
                cover_url = cloud_media.get("cover_photo_url") or "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800"

                cur.execute("""
                INSERT INTO media (unit_id, media_type, file_path, web_url, caption, is_cover, sort_order)
                VALUES (?, 'photo', ?, ?, 'Google Drive Photo Assets', 1, 1)
                """, (p["id"], drive_folder, cover_url))

                # Initialize Default Posting Records
                for plat in ['facebook', 'kijiji', 'zumper', 'rentals_ca']:
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
    """Updates the status of a posting (e.g. 'in_progress', 'posted', 'failed')."""
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

if __name__ == "__main__":
    init_db()
    seed_from_sample_if_empty()
    units = get_all_units()
    print(f"Initialized Database with {len(units)} units and full media tables.")
