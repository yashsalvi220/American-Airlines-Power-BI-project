"""
LinkedIn Lead Scraper — Tool (Layer 3)

Uses the Google Custom Search JSON API to find LinkedIn profiles
matching a given profession and location. Saves results to .tmp/.

Usage:
    python tools/linkedin_scraper.py --profession "Data Engineer" --location "Dallas, TX"
    python tools/linkedin_scraper.py --profession "Marketing Manager" --location "New York, NY" --max-results 20
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
TMP_DIR = PROJECT_ROOT / ".tmp"
OUTPUT_FILE = TMP_DIR / "linkedin_results.json"

SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_env() -> None:
    """Fail fast if required environment variables are missing."""
    missing = []
    if not GOOGLE_API_KEY:
        missing.append("GOOGLE_API_KEY")
    if not GOOGLE_CSE_ID:
        missing.append("GOOGLE_CSE_ID")
    if missing:
        sys.exit(
            f"[ERROR] Missing environment variables: {', '.join(missing)}\n"
            f"Copy .env.example to .env and fill in the values."
        )


def _extract_name_from_title(title: str) -> str:
    """Best-effort extraction of a person's name from a Google result title.

    LinkedIn titles typically look like:
        'Jane Doe - Data Engineer - Acme Corp | LinkedIn'
    """
    # Remove the trailing '| LinkedIn' or '- LinkedIn'
    cleaned = re.split(r"\s*[\|\-–—]\s*LinkedIn", title, flags=re.IGNORECASE)[0]
    # Take everything before the first separator (job title, company, etc.)
    name = re.split(r"\s*[\-–—]\s*", cleaned)[0].strip()
    return name


def _extract_email_from_snippet(snippet: str) -> str:
    """Return the first email address found in the snippet, or empty string."""
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", snippet)
    return match.group(0) if match else ""


# ---------------------------------------------------------------------------
# Core search
# ---------------------------------------------------------------------------


def search_linkedin_profiles(
    profession: str, location: str, max_results: int = 10
) -> list[dict]:
    """Query Google Custom Search for LinkedIn profiles and return parsed leads."""

    _check_env()
    TMP_DIR.mkdir(exist_ok=True)

    query = f'site:linkedin.com/in/ "{profession}" "{location}"'
    leads: list[dict] = []
    start_index = 1  # Google CSE uses 1-based paging

    while len(leads) < max_results:
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "start": start_index,
            "num": min(10, max_results - len(leads)),  # API max is 10 per page
        }

        try:
            resp = requests.get(SEARCH_URL, params=params, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if resp.status_code == 429:
                print("[WARN] Google API quota exceeded. Try again later or upgrade your quota.")
                break
            raise SystemExit(f"[ERROR] Google API returned {resp.status_code}: {exc}") from exc
        except requests.exceptions.ConnectionError:
            # One retry after 5 seconds
            print("[WARN] Connection error — retrying in 5 seconds …")
            time.sleep(5)
            try:
                resp = requests.get(SEARCH_URL, params=params, timeout=30)
                resp.raise_for_status()
            except Exception as retry_exc:
                raise SystemExit(f"[ERROR] Retry failed: {retry_exc}") from retry_exc

        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")

            # Only keep actual profile pages
            if "/in/" not in link:
                continue

            lead = {
                "name": _extract_name_from_title(title),
                "email": _extract_email_from_snippet(snippet),
                "linkedin_url": link,
                "profession": profession,
                "location": location,
                "date_found": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            }
            leads.append(lead)

            if len(leads) >= max_results:
                break

        # Move to next page
        next_page = data.get("queries", {}).get("nextPage")
        if not next_page:
            break
        start_index = next_page[0].get("startIndex", start_index + 10)

    return leads


def save_results(leads: list[dict]) -> Path:
    """Write leads to the intermediate JSON file and return the path."""
    TMP_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(leads, indent=2))
    return OUTPUT_FILE


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Search LinkedIn profiles via Google Custom Search")
    parser.add_argument("--profession", required=True, help='Job title to search for, e.g. "Data Engineer"')
    parser.add_argument("--location", required=True, help='Location to filter by, e.g. "Dallas, TX"')
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of leads to return (default: 10)")
    args = parser.parse_args()

    print(f"Searching for '{args.profession}' in '{args.location}' (max {args.max_results}) …")
    leads = search_linkedin_profiles(args.profession, args.location, args.max_results)

    if not leads:
        print("No leads found. Try broadening your search terms.")
        save_results([])
        return

    out = save_results(leads)
    print(f"Found {len(leads)} lead(s). Results saved to {out}")
    for lead in leads:
        email_info = f" | {lead['email']}" if lead["email"] else ""
        print(f"  • {lead['name']}{email_info} — {lead['linkedin_url']}")


if __name__ == "__main__":
    main()
