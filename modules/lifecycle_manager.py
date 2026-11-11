#!/usr/bin/env python3
"""
Lifecycle Manager for 315 Kent Street Rental Postings
Handles automated 7-day take-down and re-post cycles,
active/inactive status toggles, and master content synchronization.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from data.database import (
    get_connection,
    get_all_units,
    get_unit_by_id,
    update_posting_status,
    DB_PATH
)
from modules.content_generator import (
    generate_facebook_marketplace_listing,
    generate_kijiji_listing,
    generate_zumper_listing,
    generate_rentals_ca_listing
)

REFRESH_CYCLE_DAYS = 7

def get_lifecycle_overview(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Returns the 7-day auto-refresh and active/inactive status for all units."""
    units = get_all_units(db_path)
    now = datetime.now()
    results = []

    for u in units:
        unit_id = u["id"]
        ad_active = u.get("ad_active", 1) == 1
        last_refreshed_str = u.get("last_refreshed_at")
        next_refresh_str = u.get("next_refresh_at")

        if not last_refreshed_str:
            last_refreshed = now
            last_refreshed_str = last_refreshed.isoformat()
        else:
            try:
                last_refreshed = datetime.fromisoformat(last_refreshed_str)
            except Exception:
                last_refreshed = now

        if not next_refresh_str:
            next_refresh = last_refreshed + timedelta(days=REFRESH_CYCLE_DAYS)
            next_refresh_str = next_refresh.isoformat()
        else:
            try:
                next_refresh = datetime.fromisoformat(next_refresh_str)
            except Exception:
                next_refresh = last_refreshed + timedelta(days=REFRESH_CYCLE_DAYS)

        time_remaining = next_refresh - now
        days_remaining = max(0, time_remaining.days)
        hours_remaining = max(0, int(time_remaining.seconds / 3600))
        is_due = (now >= next_refresh) and ad_active

        results.append({
            "unit_id": unit_id,
            "unit_name": u["name"],
            "ad_active": ad_active,
            "status_label": "Active (7-Day Auto-Refresh)" if ad_active else "Inactive (Taken Down)",
            "is_due_for_refresh": is_due,
            "last_refreshed_at": last_refreshed_str,
            "last_refreshed_display": last_refreshed.strftime("%b %d, %Y"),
            "next_refresh_at": next_refresh_str,
            "next_refresh_display": next_refresh.strftime("%b %d, %Y"),
            "days_remaining": days_remaining,
            "hours_remaining": hours_remaining,
            "countdown_label": f"Refreshes in {days_remaining}d {hours_remaining}h" if ad_active else "Campaign Inactive"
        })

    return results

def toggle_posting_active(unit_id: str, is_active: bool, db_path: Path = DB_PATH) -> Dict[str, Any]:
    """
    Activates or deactivates a unit's rental ads.
    When deactivated: Takes down active postings and pauses 7-day auto-refresh.
    When activated: Re-posts the ads immediately and starts a fresh 7-day cycle.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now()
    next_refresh = now + timedelta(days=REFRESH_CYCLE_DAYS)

    if is_active:
        # Activate and reset 7-day cycle
        cur.execute("""
        UPDATE units
        SET ad_active = 1,
            last_refreshed_at = ?,
            next_refresh_at = ?,
            updated_at = ?
        WHERE id = ?
        """, (now.isoformat(), next_refresh.isoformat(), now.isoformat(), unit_id))

        for plat in ['facebook', 'kijiji', 'zumper', 'rentals_ca']:
            cur.execute("""
            UPDATE posting_history
            SET status = 'posted',
                last_posted_at = ?,
                log_output = ?
            WHERE unit_id = ? AND platform = ?
            """, (now.isoformat(), f"Active: 7-day refresh scheduled for {next_refresh.strftime('%b %d')}", unit_id, plat))
            cur.execute("""
            UPDATE ad_analytics
            SET ad_status = 'live', last_updated = CURRENT_TIMESTAMP
            WHERE unit_id = ? AND platform = ?
            """, (unit_id, plat))

        action_msg = f"Unit {unit_id} postings activated and 7-day auto-renewal scheduled! Next refresh on {next_refresh.strftime('%b %d, %Y')}."
    else:
        # Deactivate and take down listings
        cur.execute("""
        UPDATE units
        SET ad_active = 0,
            updated_at = ?
        WHERE id = ?
        """, (now.isoformat(), unit_id))

        for plat in ['facebook', 'kijiji', 'zumper', 'rentals_ca']:
            cur.execute("""
            UPDATE posting_history
            SET status = 'inactive',
                log_output = ?
            WHERE unit_id = ? AND platform = ?
            """, (f"Taken down by landlord at {now.strftime('%b %d, %Y %I:%M %p')}", unit_id, plat))
            cur.execute("""
            UPDATE ad_analytics
            SET ad_status = 'inactive', last_updated = CURRENT_TIMESTAMP
            WHERE unit_id = ? AND platform = ?
            """, (unit_id, plat))

        action_msg = f"Unit {unit_id} postings deactivated and taken down from all platforms. Auto-refresh paused."

    conn.commit()
    conn.close()

    return {
        "success": True,
        "unit_id": unit_id,
        "is_active": is_active,
        "message": action_msg,
        "next_refresh_at": next_refresh.isoformat() if is_active else None
    }


def delete_unit_posting(
    unit_id: str,
    platform: str = "all",
    run_bot: bool = False,
    headless: bool = False,
    db_path: Path = DB_PATH
) -> Dict[str, Any]:
    """
    Deletes / takes down a specific platform's posting or all postings for a unit.
    Optionally launches the Playwright browser bot to remove the ad on the external site.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now()
    platform_clean = platform.lower().replace(".", "_")

    platforms_to_delete = (
        ['facebook', 'kijiji', 'zumper', 'rentals_ca']
        if platform_clean == "all"
        else [platform_clean]
    )

    if platform_clean == "all":
        cur.execute("UPDATE units SET ad_active = 0, updated_at = ? WHERE id = ?", (now.isoformat(), unit_id))

    for plat in platforms_to_delete:
        cur.execute("""
        UPDATE posting_history
        SET status = 'inactive',
            log_output = ?
        WHERE unit_id = ? AND platform = ?
        """, (f"Deleted / taken down on {now.strftime('%b %d, %Y %I:%M %p')}", unit_id, plat))
        cur.execute("""
        UPDATE ad_analytics
        SET ad_status = 'inactive', last_updated = CURRENT_TIMESTAMP
        WHERE unit_id = ? AND platform = ?
        """, (unit_id, plat))

    conn.commit()
    conn.close()

    bot_result = None
    if run_bot:
        from modules.automated_poster import AutomatedPoster
        poster = AutomatedPoster(unit_id=unit_id, platform=platform_clean, headless=headless)
        bot_result = poster.delete_posting()

    target_label = "ALL 5 platforms" if platform_clean == "all" else platform_clean.upper()
    return {
        "success": True,
        "unit_id": unit_id,
        "platform": platform_clean,
        "bot_executed": run_bot,
        "bot_details": bot_result,
        "message": f"Posting for {unit_id} on {target_label} has been deleted / taken down."
    }


def execute_7day_refresh(
    unit_id: str,
    platform: str = "all",
    run_bot: bool = False,
    headless: bool = False,
    db_path: Path = DB_PATH
) -> Dict[str, Any]:
    """
    Takes the current ad down and immediately re-posts it fresh to gain top ranking/new views.
    Resets the 7-day timer.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now()
    next_refresh = now + timedelta(days=REFRESH_CYCLE_DAYS)

    unit = get_unit_by_id(unit_id, db_path)
    if not unit:
        conn.close()
        return {"success": False, "error": f"Unit {unit_id} not found"}

    # Update database timestamps
    cur.execute("""
    UPDATE units
    SET ad_active = 1,
        last_refreshed_at = ?,
        next_refresh_at = ?,
        updated_at = ?
    WHERE id = ?
    """, (now.isoformat(), next_refresh.isoformat(), now.isoformat(), unit_id))

    platform_clean = platform.lower().replace(".", "_")
    platforms_to_refresh = (
        ['facebook', 'kijiji', 'zumper', 'rentals_ca']
        if platform_clean == "all"
        else [platform_clean]
    )

    for plat in platforms_to_refresh:
        cur.execute("""
        UPDATE posting_history
        SET status = 'posted',
            last_posted_at = ?,
            log_output = ?
        WHERE unit_id = ? AND platform = ?
        """, (now.isoformat(), f"7-Day Auto-Refresh: Previous post archived & fresh ad published on {now.strftime('%b %d')}", unit_id, plat))
        cur.execute("""
        UPDATE ad_analytics
        SET ad_status = 'live', last_updated = CURRENT_TIMESTAMP
        WHERE unit_id = ? AND platform = ?
        """, (unit_id, plat))

    conn.commit()
    conn.close()

    bot_result = None
    if run_bot:
        from modules.automated_poster import AutomatedPoster
        poster = AutomatedPoster(unit_id=unit_id, platform=platform_clean, headless=headless)
        bot_result = poster.renew_posting()

    return {
        "success": True,
        "unit_id": unit_id,
        "platform": platform_clean,
        "bot_executed": run_bot,
        "bot_details": bot_result,
        "message": f"Successfully took down previous ad and re-posted fresh for {unit['name']}. Next 7-day auto-renewal scheduled for {next_refresh.strftime('%b %d, %Y')}.",
        "last_refreshed_at": now.isoformat(),
        "next_refresh_at": next_refresh.isoformat(),
        "next_refresh_display": next_refresh.strftime("%b %d, %Y")
    }

def check_and_run_all_due_refreshes(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Checks all active units and executes 7-day refresh on any that are due."""
    units = get_all_units(db_path)
    now = datetime.now()
    refreshed = []

    for u in units:
        ad_active = u.get("ad_active", 1) == 1
        if not ad_active:
            continue

        next_refresh_str = u.get("next_refresh_at")
        if not next_refresh_str:
            continue

        try:
            next_refresh = datetime.fromisoformat(next_refresh_str)
            if now >= next_refresh:
                res = execute_7day_refresh(u["id"], db_path)
                refreshed.append(res)
        except Exception as e:
            print(f"[Lifecycle Refresh Error] Unit {u['id']}: {e}")

    return refreshed
