#!/usr/bin/env python3
"""
Durham Region Property Management Posting & Market Comps Agent
Command-Line Interface and Agent Core.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from modules.durham_platforms import get_recommended_platforms
from modules.market_research import find_comps_for_unit, get_live_market_search_urls
from modules.content_generator import package_all_listings_for_unit
from modules.posting_engine import PostingEngine

console = Console()
DEFAULT_UNITS_PATH = Path(__file__).parent / "data" / "units" / "sample_units.json"

def load_units(path: Path = DEFAULT_UNITS_PATH):
    if not path.exists():
        console.print(f"[bold red]Error: Units data file not found at {path}[/bold red]")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("properties", [])

def cmd_list(args):
    units = load_units()
    table = Table(title="Durham Rental Portfolio - 6 Units Overview", show_header=True, header_style="bold cyan")
    table.add_column("Unit ID", style="bold yellow")
    table.add_column("Property Name", style="white")
    table.add_column("City", style="green")
    table.add_column("Type", style="magenta")
    table.add_column("Beds/Baths", justify="center")
    table.add_column("Sq Ft", justify="right")
    table.add_column("Target Rent", justify="right", style="bold green")
    table.add_column("Video Tour", style="blue")

    for u in units:
        has_video = "✅ Yes" if u.get("media", {}).get("video_walkthrough_url") else "❌ Missing"
        table.add_row(
            u["id"],
            u["name"],
            u["address"]["city"],
            u["type"],
            f"{u['specs']['bedrooms']}b / {u['specs']['bathrooms']}ba",
            f"{u['specs']['sqft']} sqft",
            f"${u['financials']['target_rent']:,}/mo",
            has_video
        )

    console.print(table)
    console.print("[dim]Edit 'data/units/sample_units.json' to customize your unit details, pictures, and video links.[/dim]")

def cmd_comps(args):
    units = load_units()
    selected_units = [u for u in units if u["id"] == args.unit] if args.unit else units

    if not selected_units:
        console.print(f"[bold red]Unit ID '{args.unit}' not found.[/bold red]")
        return

    for u in selected_units:
        res = find_comps_for_unit(u)
        stats = res.get("stats", {})

        console.print(Panel(
            f"[bold cyan]{u['name']} ({u['address']['city']})[/bold cyan]\n"
            f"Type: {u['type']} | Specs: {res['specs']} | Target Rent: [bold green]${u['financials']['target_rent']:,}/mo[/bold green] (${res['unit_price_per_sqft']}/sqft)\n"
            f"[bold]Market Comp Analysis:[/bold]\n"
            f" • Average Comp Rent: [bold]${stats.get('average_comp_rent'):,}[/bold] (Range: ${stats.get('min_comp_rent'):,} - ${stats.get('max_comp_rent'):,})\n"
            f" • Market $/sqft Benchmark: ${stats.get('avg_price_per_sqft')}/sqft\n"
            f" • Delta vs Market Average: {'+' if stats.get('diff_from_market_average', 0) >= 0 else ''}${stats.get('diff_from_market_average', 0)}/mo\n"
            f" • Pricing Verdict: [bold italic yellow]{res['verdict']}[/bold italic yellow]",
            title=f"Market Comps: {u['id']}",
            border_style="cyan"
        ))

        # Show table of individual comps
        comp_table = Table(show_header=True, header_style="bold magenta")
        comp_table.add_column("Comp ID", style="dim")
        comp_table.add_column("Neighbourhood")
        comp_table.add_column("Type")
        comp_table.add_column("Beds/Baths", justify="center")
        comp_table.add_column("Sqft", justify="right")
        comp_table.add_column("Rent", justify="right", style="bold green")
        comp_table.add_column("Utilities Inc.", style="cyan")
        comp_table.add_column("Source", style="dim")

        for c in res.get("comps", []):
            comp_table.add_row(
                c["id"],
                c["neighbourhood"],
                c["type"],
                f"{c['bedrooms']}b / {c['bathrooms']}ba",
                f"{c['sqft']}",
                f"${c['rent']:,}",
                ", ".join(c["utilities_included"]) if c["utilities_included"] else "None",
                c["source"]
            )
        console.print(comp_table)

        # Show live check links
        urls = get_live_market_search_urls(u['address']['city'], u['specs']['bedrooms'])
        console.print("[bold]Direct Live Market Comps Links:[/bold]")
        for platform_name, link in urls.items():
            console.print(f" • [cyan]{platform_name}[/cyan]: {link}")
        console.print("\n" + "="*70 + "\n")

def cmd_platforms(args):
    platforms = get_recommended_platforms()
    table = Table(title="Durham Region Rental Posting Platforms (Free Tiers & High Traffic)", show_header=True, header_style="bold blue")
    table.add_column("Platform", style="bold white")
    table.add_column("Cost / Tier", style="green")
    table.add_column("Durham Local Strength", style="yellow")
    table.add_column("Walkthrough Video Support", style="cyan")
    table.add_column("Action / Direct URL", style="blue")

    for p in platforms:
        table.add_row(
            p["name"],
            p["cost"],
            p["local_strength"],
            p["media_support"]["video_walkthrough"],
            p["url"]
        )
    console.print(table)

def cmd_package(args):
    engine = PostingEngine(str(DEFAULT_UNITS_PATH))
    units = load_units()
    selected_units = [u for u in units if u["id"] == args.unit] if args.unit else units

    if not selected_units:
        console.print(f"[bold red]Unit ID '{args.unit}' not found.[/bold red]")
        return

    for u in selected_units:
        dossier_path = engine.export_unit_listing_dossier(u["id"])
        console.print(f"[bold green]✔ Packaged listings for {u['name']}[/bold green] -> [cyan]{dossier_path}[/cyan]")

    console.print(f"\n[bold]Ready![/bold] All dossiers generated in 'reports/dossiers/'. You can open and copy directly or trigger automated posting.")

def main():
    parser = argparse.ArgumentParser(description="Durham Region Property Management Posting & Market Comps Agent")
    subparsers = parser.add_subparsers(dest="command", help="Agent Commands")

    # list
    subparsers.add_parser("list", help="List all 6 units in the portfolio")

    # comps
    comps_p = subparsers.add_parser("comps", help="Run market rent comps research")
    comps_p.add_argument("--unit", type=str, help="Specific unit ID (e.g. unit_1), or omit for all")

    # platforms
    subparsers.add_parser("platforms", help="Display all Durham Region free rental platforms guide")

    # package
    pkg_p = subparsers.add_parser("package", help="Generate platform listing packages & dossiers")
    pkg_p.add_argument("--unit", type=str, help="Specific unit ID (e.g. unit_1), or omit for all")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "list":
        cmd_list(args)
    elif args.command == "comps":
        cmd_comps(args)
    elif args.command == "platforms":
        cmd_platforms(args)
    elif args.command == "package":
        cmd_package(args)

if __name__ == "__main__":
    main()
