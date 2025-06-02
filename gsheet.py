import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = "1MtEOlfBOeKJcHLlKiM7b-rIchdPH6ZA7pGAJUnIXAII"
SAMPLE_RANGE_NAME = "Sheet1!A1"


def outreach_upload(valueData, client):
    creds = None
    # The file token.json stores the user's access and refresh tokens and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=3000)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Build the service
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Get the current data in the sheet to find the next available row
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1:A").execute()
        values = result.get('values', [])
        
        # Find the next available row
        next_row = len(values) + 1  # The next empty row
        next_range = f"Sheet1!A{next_row}"

        # Prepare the body for the update
        body = {
            "values": [valueData]
        }

        # Update the sheet with the new data
        result = (
            sheet.values()
            .update(spreadsheetId=SPREADSHEET_ID, range=next_range, valueInputOption="USER_ENTERED", body=body)
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated.")
        return result.get('updatedCells')

    except HttpError as err:
        print(err)
        return err



