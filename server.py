#!/usr/bin/env python3
"""
Simple Web Agent Server for Local or GitHub Codespaces Execution.
Serves the interactive web dashboard from the docs/ directory.
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = int(os.environ.get("PORT", 8000))
DOCS_DIR = Path(__file__).parent / "docs"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"\n[Rental Agent Web Server] Serving dashboard at: {url}")
        print("Press Ctrl+C to stop the server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
