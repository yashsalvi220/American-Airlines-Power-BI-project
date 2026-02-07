"""
Google Sheets Exporter — Tool (Layer 3)

Reads leads from .tmp/linkedin_results.json and appends them to a Google Sheet,
skipping duplicates based on LinkedIn URL.

Usage:
    python tools/google_sheets.py
    python tools/google_sheets.py --input .tmp/linkedin_results.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

import gspread
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
DEFAULT_INPUT = PROJECT_ROOT / ".tmp" / "linkedin_results.json"

HEADER_ROW = ["Name", "Email", "LinkedIn URL", "Profession", "Location", "Date Found"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_env() -> None:
    """Fail fast if required environment variables are missing."""
    missing = []
    if not GOOGLE_SHEET_ID:
        missing.append("GOOGLE_SHEET_ID")

    # Resolve service account path relative to project root if not absolute
    sa_path = Path(SERVICE_ACCOUNT_FILE)
    if not sa_path.is_absolute():
        sa_path = PROJECT_ROOT / sa_path
    if not sa_path.exists():
        missing.append(f"GOOGLE_SERVICE_ACCOUNT_FILE (file not found: {sa_path})")

    if missing:
        sys.exit(
            f"[ERROR] Missing configuration: {', '.join(missing)}\n"
            f"See .env.example for setup instructions."
        )


def _resolve_sa_path() -> Path:
    """Return the absolute path to the service account JSON file."""
    sa_path = Path(SERVICE_ACCOUNT_FILE)
    if not sa_path.is_absolute():
        sa_path = PROJECT_ROOT / sa_path
    return sa_path


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def load_leads(input_file: Path) -> list[dict]:
    """Load leads from the intermediate JSON file."""
    if not input_file.exists():
        sys.exit(f"[ERROR] Input file not found: {input_file}\nRun linkedin_scraper.py first.")

    with open(input_file) as f:
        leads = json.load(f)

    if not isinstance(leads, list):
        sys.exit("[ERROR] Expected a JSON array in the input file.")

    return leads


def export_to_sheet(leads: list[dict]) -> int:
    """Append leads to the Google Sheet, skipping duplicates. Returns count of new rows."""

    _check_env()

    sa_path = _resolve_sa_path()
    gc = gspread.service_account(filename=str(sa_path))

    try:
        spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)
    except gspread.exceptions.SpreadsheetNotFound:
        sys.exit(
            f"[ERROR] Sheet not found. Make sure the sheet with ID '{GOOGLE_SHEET_ID}' "
            f"is shared with the service account email in {sa_path.name}."
        )

    worksheet = spreadsheet.sheet1

    # Ensure header row exists
    existing = worksheet.get_all_values()
    if not existing or existing[0] != HEADER_ROW:
        worksheet.insert_row(HEADER_ROW, index=1)
        existing = [HEADER_ROW]

    # Collect existing LinkedIn URLs for duplicate detection
    existing_urls = set()
    for row in existing[1:]:  # skip header
        if len(row) >= 3:
            existing_urls.add(row[2])  # LinkedIn URL is column 3

    new_rows = []
    for lead in leads:
        url = lead.get("linkedin_url", "")
        if url in existing_urls:
            continue
        new_rows.append([
            lead.get("name", ""),
            lead.get("email", ""),
            url,
            lead.get("profession", ""),
            lead.get("location", ""),
            lead.get("date_found", ""),
        ])

    if new_rows:
        worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")

    return len(new_rows)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Export LinkedIn leads to Google Sheets")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the JSON file with leads (default: .tmp/linkedin_results.json)",
    )
    args = parser.parse_args()

    leads = load_leads(args.input)
    if not leads:
        print("No leads to export.")
        return

    print(f"Exporting {len(leads)} lead(s) to Google Sheet …")
    written = export_to_sheet(leads)
    print(f"Done. {written} new row(s) written ({len(leads) - written} duplicate(s) skipped).")


if __name__ == "__main__":
    main()
