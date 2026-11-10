#!/usr/bin/env python3
"""
REST API & Web Agent Backend Server
Serves the web dashboard, manages SQLite media & posting records,
and executes 1-click automated posting to Facebook, Kijiji, and Zumper.
"""

import http.server
import socketserver
import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from data.database import (
    get_all_units,
    get_unit_by_id,
    add_media_asset,
    update_posting_status,
    init_db,
    seed_from_sample_if_empty,
    get_all_applicants,
    upsert_applicant
)
from modules.automated_poster import AutomatedPoster
from modules.content_generator import package_all_listings_for_unit
from modules.tenant_screening import analyze_tenant_application, generate_gmail_compose_url

PORT = int(os.environ.get("PORT", 8000))
DOCS_DIR = Path(__file__).parent / "docs"
MEDIA_DIR = Path(__file__).parent / "media"
REPORTS_DIR = Path(__file__).parent / "reports"

class AgentAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/units":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            units = get_all_units()
            self.wfile.write(json.dumps({"success": True, "properties": units}).encode("utf-8"))
            return

        elif path == "/api/applicants":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            applicants = get_all_applicants()
            self.wfile.write(json.dumps({"success": True, "applicants": applicants}).encode("utf-8"))
            return

        elif path.startswith("/api/units/") and path.endswith("/package"):
            # e.g. /api/units/unit_1/package
            unit_id = path.split("/")[3]
            unit = get_unit_by_id(unit_id)
            if not unit:
                self.send_error(404, "Unit not found")
                return
            pkg = package_all_listings_for_unit(unit)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "package": pkg}).encode("utf-8"))
            return

        # Serve static media files if requested
        elif path.startswith("/media/"):
            rel_path = path[len("/media/"):]
            file_path = MEDIA_DIR / rel_path
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self._set_cors_headers()
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        data = json.loads(body) if body else {}

        # 1-Click Automated Poster Endpoint
        if path == "/api/post-unit":
            unit_id = data.get("unit_id")
            platform = data.get("platform")
            headless = data.get("headless", False)

            if not unit_id or not platform:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "unit_id and platform required"}).encode("utf-8"))
                return

            print(f"\n[API 1-Click Trigger] Running automated poster for {unit_id} -> {platform}...")
            poster = AutomatedPoster(unit_id=unit_id, platform=platform, headless=headless)
            result = poster.run()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        # Add Media to Unit Endpoint
        elif path == "/api/media":
            unit_id = data.get("unit_id")
            media_type = data.get("media_type", "photo")
            web_url = data.get("web_url")
            file_path = data.get("file_path")
            caption = data.get("caption", "")
            is_cover = data.get("is_cover", False)

            if not unit_id or (not web_url and not file_path):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "unit_id and web_url or file_path required"}).encode("utf-8"))
                return

            add_media_asset(unit_id, media_type, file_path=file_path, web_url=web_url, caption=caption, is_cover=is_cover)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Media asset added to database"}).encode("utf-8"))
            return

        # Save or Update Applicant Endpoint
        elif path == "/api/applicants":
            saved = upsert_applicant(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "applicant": saved}).encode("utf-8"))
            return

        # AI Credit & Income Analysis Endpoint
        elif path == "/api/analyze-credit":
            unit_id = data.get("unit_id", "unit_3")
            unit = get_unit_by_id(unit_id) or {"name": "315 Kent St", "financials": {"target_rent": 2075}}
            analysis = analyze_tenant_application(data, unit)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "analysis": analysis}).encode("utf-8"))
            return

        self.send_error(404, "Endpoint not found")

def run_server():
    init_db()
    seed_from_sample_if_empty()
    os.chdir(Path(__file__).parent)
    with socketserver.TCPServer(("", PORT), AgentAPIHandler) as httpd:
        print(f"\n[Durham Rental Agent Server] Live on http://localhost:{PORT}")
        print(" • Serving dashboard from /docs")
        print(" • REST API & 1-Click Posting Engine active")
        print("Press Ctrl+C to terminate.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()
