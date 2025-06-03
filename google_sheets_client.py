import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Globals for caching ---
gc = None
teams_sheet = None
scouting_sheet = None


def init_google_sheets():
    """
    Initializes the Google Sheets client and worksheets.
    Caches the client and sheets for subsequent calls.
    """
    global gc, teams_sheet, scouting_sheet
    if gc and teams_sheet and scouting_sheet:
        return True

    try:
        print("Initializing Google Sheets connection...")
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            raise FileNotFoundError(
                "Google credentials not found in environment variables"
            )

        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gc = gspread.authorize(creds)

        spreadsheet = gc.open("Worlds Scouting Spreadsheet 2025")
        teams_sheet = spreadsheet.worksheet("FRANKLIN OPRs")
        scouting_sheet = spreadsheet.sheet1
        return True

    except Exception as e:
        print(f"Error initializing Google Sheets: {e}")
        return False


def get_all_teams():
    """
    Fetches all teams from the 'FRANKLIN OPRs' worksheet.
    """
    if not init_google_sheets():
        return []
    return teams_sheet.get_all_values()[1:]  # Skip header


def get_scouted_teams():
    """
    Fetches all scouted teams from the main scouting sheet.
    """
    if not init_google_sheets():
        return set()
    scouted_data = scouting_sheet.get_all_values()
    return {row[1] for row in scouted_data[1:]} if scouted_data else set()


def append_scout_data(new_row):
    """
    Appends a new row of scouting data to the sheet.
    """
    if not init_google_sheets():
        raise ConnectionError("Could not connect to Google Sheets.")
    scouting_sheet.append_row(new_row)


def update_opr_sheet(header, rows):
    """
    Updates the OPR sheet with new data.
    """
    if not init_google_sheets():
        raise ConnectionError("Could not connect to Google Sheets.")
    sheet = gc.open("Worlds Scouting Spreadsheet 2025").sheet1
    sheet.update("A1:J1", [header])
    for i, row in enumerate(rows, start=2):
        sheet.update(f"A{i}:J{i}", [row])
