# LinkedIn Lead Scraper Workflow

## Objective

Find professional contacts on LinkedIn based on **profession** and **location**, then store their lead information (name, email, LinkedIn profile URL) in a Google Sheet.

## Required Inputs

| Input | Source | Example |
|-------|--------|---------|
| Profession / job title | User-provided | `"Data Engineer"` |
| Location | User-provided | `"Dallas, TX"` |
| Max results | User-provided (default: 10) | `10` |
| Google Sheet ID | `.env` → `GOOGLE_SHEET_ID` | — |
| Google API key | `.env` → `GOOGLE_API_KEY` | — |
| Google CSE ID | `.env` → `GOOGLE_CSE_ID` | — |
| Service account creds | `.env` → `GOOGLE_SERVICE_ACCOUNT_FILE` | — |

## Tool Sequence

### Step 1: Search for LinkedIn profiles

**Tool:** `tools/linkedin_scraper.py`

- Uses the Google Custom Search JSON API to query `site:linkedin.com/in/` with the profession and location as search terms.
- Parses results to extract: **name**, **LinkedIn profile URL**, and any visible **email** or description text.
- Saves raw results to `.tmp/linkedin_results.json`.

### Step 2: Export leads to Google Sheets

**Tool:** `tools/google_sheets.py`

- Reads `.tmp/linkedin_results.json`.
- Connects to the target Google Sheet via the `gspread` library and a service-account credential.
- Appends each lead as a new row: `Name | Email | LinkedIn URL | Profession | Location | Date Found`.
- Creates the header row if the sheet is empty.

### Step 3 (optional): Run full pipeline

**Tool:** `tools/lead_pipeline.py`

- Orchestrates Step 1 → Step 2 in a single command.
- Usage: `python tools/lead_pipeline.py --profession "Data Engineer" --location "Dallas, TX" --max-results 10`

## Expected Outputs

- `.tmp/linkedin_results.json` — intermediate JSON file with scraped leads.
- Google Sheet updated with new rows containing lead data.
- Console summary: number of leads found, number written to sheet.

## Edge Cases

| Scenario | Handling |
|----------|----------|
| No results from Google search | Log a warning; write zero rows; exit cleanly. |
| Google API quota exhausted | Catch `HttpError 429`; log the error; suggest waiting or upgrading quota. |
| Google Sheet not shared with service account | Catch `gspread.exceptions.SpreadsheetNotFound`; print sharing instructions. |
| Duplicate leads | Check LinkedIn URL against existing sheet rows before appending. |
| Missing `.env` variables | Fail fast with a clear message listing which variables are missing. |
| Network timeout | Retry once after 5 seconds; fail with a descriptive error if retry fails. |
