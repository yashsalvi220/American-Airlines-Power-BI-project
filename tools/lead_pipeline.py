"""
Lead Pipeline — Tool (Layer 3)

Orchestrates the full LinkedIn-to-Google-Sheets pipeline:
    1. Search for LinkedIn profiles (linkedin_scraper.py)
    2. Export results to Google Sheets (google_sheets.py)

Usage:
    python tools/lead_pipeline.py --profession "Data Engineer" --location "Dallas, TX"
    python tools/lead_pipeline.py --profession "Marketing Manager" --location "New York, NY" --max-results 20
"""

import argparse

from linkedin_scraper import save_results, search_linkedin_profiles
from google_sheets import export_to_sheet, load_leads


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find LinkedIn leads and export them to Google Sheets"
    )
    parser.add_argument("--profession", required=True, help='Job title, e.g. "Data Engineer"')
    parser.add_argument("--location", required=True, help='Location, e.g. "Dallas, TX"')
    parser.add_argument("--max-results", type=int, default=10, help="Max leads to fetch (default: 10)")
    args = parser.parse_args()

    # Step 1 — scrape
    print(f"\n=== Step 1: Searching LinkedIn for '{args.profession}' in '{args.location}' ===\n")
    leads = search_linkedin_profiles(args.profession, args.location, args.max_results)

    if not leads:
        print("No leads found. Try different search terms.")
        return

    out = save_results(leads)
    print(f"Found {len(leads)} lead(s). Intermediate file: {out}\n")

    for lead in leads:
        email_info = f" | {lead['email']}" if lead["email"] else ""
        print(f"  • {lead['name']}{email_info} — {lead['linkedin_url']}")

    # Step 2 — export
    print(f"\n=== Step 2: Exporting to Google Sheet ===\n")
    written = export_to_sheet(leads)
    print(f"Done. {written} new row(s) written ({len(leads) - written} duplicate(s) skipped).")

    # Summary
    print(f"\n=== Summary ===")
    print(f"  Leads found:   {len(leads)}")
    print(f"  Rows written:  {written}")
    print(f"  Duplicates:    {len(leads) - written}")


if __name__ == "__main__":
    main()
