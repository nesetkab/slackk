from pathlib import Path
from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

import json, time, ssl, csv, os, hickle as hkl, requests, gspread
from datetime import datetime, timezone, timedelta
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from gsheet import outreach_upload
from upload import main
from oauth2client.service_account import ServiceAccountCredentials

global gc, teams_sheet, scouting_sheet
gc = None
teams_sheet = None
scouting_sheet = None

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED
flask_app = Flask(__name__)
app = App(
    token=os.environ["SLACK_TOKEN"],
    signing_secret=os.environ["SIGNING_SECRET"],
    # ssl = ssl_context
)
handler = SlackRequestHandler(app)
m_category = "default"
p_category = "deafult"


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/", methods=["POST"])
def health():
    return "OK", 200


# SEND MESSAGES
def send_confirm_msg(client):
    res = client.chat_postMessage(channel="C07QFDDS9QW", text="API Upload succesful :)")


def send_m_update_msg(client, user_info, what_you_did, file_info):
    attachments = []
    for file in file_info:
        attachment = {
            "fallback": "Image attachment",
            "image_url": file,  # Use the URL directly here
        }
        attachments.append(attachment)
    res = client.chat_postMessage(
        channel="C07GPKUFGQL",
        text="**New Entry**:\n"
        + ", ".join(user_info)
        + "\n- **What:** "
        + str(what_you_did)
        + "\n**Images:** "
        + ",".join(file_info),
        attachments=attachments,
    )


def send_p_update_msg(client, user_info, what_you_did, file_info):
    attachments = []
    for file in file_info:
        attachment = {
            "fallback": "Image attachment",
            "image_url": file,  # Use the URL directly here
        }
        attachments.append(attachment)
    res = client.chat_postMessage(
        channel="C07H9UN6VMW",
        text="**New Entry**:\n"
        + ", ".join(user_info)
        + "\n- **What:** "
        + str(what_you_did)
        + "\n**Images:** "
        + ",".join(file_info),
        attachments=attachments,
    )


def outreach_response(client, err):
    res = client.chat_postMessage(channel="C07QFDDS9QW", text="Outreach:" + str(err))


def send_done_msg(client, sub_usr, sub_time):
    confirm_msg = sub_usr + " made an Engineering Notebook entry at " + sub_time
    res = client.chat_postMessage(channel="C07QFDDS9QW", text=confirm_msg)
    upload_subdata(client)


def upload_subdata(client):
    res = client.files_upload_v2(
        file="submission_data.json",
        title="My file",
        initial_comment="Submission Data",
        channel="C07QFDDS9QW",
    )


@app.command("/help")
def handle_command(ack, body, logger, client):
    ack()
    print(body)
    trigger_id = body["trigger_id"]
    res = client.chat_postMessage(channel="C07QFDDS9QW", text="help")


def fetch_team_stats(team_number):
    query = (
        """
	query {
		teamByNumber(number: %s) {
			name
			events(season: 2024) {
				stats {
					__typename
					... on TeamEventStats2024 {
						opr {
							autoSamplePoints
							autoSpecimenPoints
							dcSamplePoints
							dcSpecimenPoints
							autoPoints
							dcPoints
							totalPointsNp
							dcParkPointsIndividual
						}
					}
				}
			}
		}
	}
	"""
        % team_number
    )

    try:
        response = requests.post(
            "https://api.ftcscout.org/graphql", json={"query": query}
        )
        data = response.json()
        return data["data"]["teamByNumber"]
    except Exception as e:
        print(f"Error fetching stats for team {team_number}: {e}")
        return None


def get_best_stats(stats_list):
    try:
        print(f"Processing stats: {json.dumps(stats_list, indent=2)}")

        best_stats = {
            "totalPointsNp": 0,
            "autoSamplePoints": 0,
            "autoSpecimenPoints": 0,
            "autoPoints": 0,
            "dcSamplePoints": 0,
            "dcSpecimenPoints": 0,
            "dcPoints": 0,
            "dcParkPointsIndividual": 0,
        }

        for event in stats_list:
            if event.get("stats") and event["stats"].get("opr"):
                opr = event["stats"]["opr"]
                print(f"Processing OPR data: {json.dumps(opr, indent=2)}")
                for key in best_stats:
                    if opr.get(key) is not None:
                        best_stats[key] = max(best_stats[key], float(opr[key]))

        return {key: round(value, 2) for key, value in best_stats.items()}

    except Exception as e:
        print(f"Error in get_best_stats: {e}")
        raise


@app.command("/updateoprs")
def handle_update_oprs(ack, body, logger, client):
    try:
        ack()
        print("Update OPRs command received")

        # Initialize Google Sheets connection
        global gc
        if not gc:
            print("Initializing Google Sheets connection...")
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]

            creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            if creds_json:
                creds = ServiceAccountCredentials.from_json_keyfile_dict(
                    json.loads(creds_json), scope
                )
                gc = gspread.authorize(creds)
            else:
                raise FileNotFoundError(
                    "Google credentials not found in environment variables"
                )

        # Get sheet
        print("Opening spreadsheet...")
        sheet = gc.open("Worlds Scouting Spreadsheet 2025").sheet1
        all_values = sheet.get_all_values()

        if not all_values:
            raise ValueError("Spreadsheet is empty")

        print(f"Found {len(all_values)} rows in spreadsheet")

        header_row = [
            "Name",
            "Number",
            "NP OPR",
            "Auto Sample OPR",
            "Auto Spec OPR",
            "Auto OPR",
            "DC Sample OPR",
            "DC Specimen OPR",
            "DC OPR",
            "Ascent",
        ]

        # Update header row
        sheet.update("A1:J1", [header_row])

        # Update each team's stats
        updated_teams = 0
        errors = []

        for row_idx, row in enumerate(all_values[1:], start=2):
            try:
                team_number = row[1].strip()  # Column B has team numbers
                if not team_number:
                    continue

                print(f"Fetching stats for team {team_number}...")

                stats = fetch_team_stats(team_number)
                if not stats:
                    errors.append(f"No stats found for team {team_number}")
                    continue

                if not stats.get("events"):
                    errors.append(f"No events found for team {team_number}")
                    continue

                # Get best stats across all events
                best_stats = get_best_stats(stats["events"])
                if not best_stats:
                    errors.append(f"No valid stats for team {team_number}")
                    continue

                # Create new row with updated stats
                new_row = [
                    stats["name"],  # Name
                    team_number,  # Number
                    best_stats["totalPointsNp"],  # NP OPR
                    best_stats["autoSamplePoints"],  # Auto Sample OPR
                    best_stats["autoSpecimenPoints"],  # Auto Spec OPR
                    best_stats["autoPoints"],  # Auto OPR
                    best_stats["dcSamplePoints"],  # DC Sample OPR
                    best_stats["dcSpecimenPoints"],  # DC Specimen OPR
                    best_stats["dcPoints"],  # DC OPR
                    best_stats["dcParkPointsIndividual"],  # Ascent
                ]

                # Update row in spreadsheet
                sheet.update(f"A{row_idx}:J{row_idx}", [new_row])
                updated_teams += 1
                print(f"Updated team {team_number}")

                # Sleep briefly to avoid rate limiting
                time.sleep(0.2)

            except Exception as e:
                error_msg = f"Error processing team {team_number}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Send confirmation message
        message = f"Successfully updated OPR stats for {updated_teams} teams!"
        if errors:
            message += f"\nEncountered {len(errors)} errors:"
            for error in errors[:5]:  # Show first 5 errors
                message += f"\n• {error}"
            if len(errors) > 5:
                message += f"\n...and {len(errors) - 5} more errors"

        client.chat_postMessage(channel=body["channel_id"], text=message)

    except Exception as e:
        error_msg = f"Err updating OPRs: {str(e)}"
        logger.error(error_msg)
        client.chat_postMessage(channel=body["channel_id"], text=error_msg)


def init_google_sheets():
    global gc, teams_sheet, scouting_sheet
    try:
        if not gc:
            print("Initializing Google Sheets connection...")
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]

            creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            if creds_json:
                creds = ServiceAccountCredentials.from_json_keyfile_dict(
                    json.loads(creds_json), scope
                )
                gc = gspread.authorize(creds)
            else:
                raise FileNotFoundError(
                    "Google credentials not found in environment variables"
                )

        if not teams_sheet or not scouting_sheet:
            teams_sheet = gc.open("Worlds Scouting Spreadsheet 2025").worksheet(
                "FRANKLIN OPRs"
            )
            franklin_sheet = gc.open("Worlds Scouting Spreadsheet 2025").worksheet(
                "FRANKLIN OPRs"
            )
            sheet = gc.open("Worlds Scouting Spreadsheet 2025")
            scouting_sheet = sheet.sheet1

        return True
    except Exception as e:
        print(f"Error initializing Google Sheets: {e}")
        return False


@app.command("/scout")
def handle_command(ack, body, logger, client):
    try:
        ack()
        trigger_id = body["trigger_id"]

        # Show loading modal first
        loading_response = client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "loading-modal",
                "title": {"type": "plain_text", "text": "Loading Teams"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Loading available teams...\n_wait patiently >:(_",
                        },
                    }
                ],
            },
        )

        # Get view ID from loading modal
        view_id = loading_response["view"]["id"]

        # Initialize Google Sheets
        if not init_google_sheets():
            client.views_update(
                view_id=view_id,
                view={
                    "type": "modal",
                    "title": {"type": "plain_text", "text": "Error"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Could not connect to Google Sheets",
                            },
                        }
                    ],
                },
            )
            return

        # Now load the actual scout modal
        try:
            # Get team data
            all_teams = teams_sheet.get_all_values()[1:]  # Skip header
            scouted_data = (
                scouting_sheet.get_all_values()[1:]
                if scouting_sheet.get_all_values()
                else []
            )
            scouted_teams = {row[1] for row in scouted_data}

            # Create team options
            team_options = [
                {
                    "text": {"type": "plain_text", "text": f"{team[1]} - {team[0]}"},
                    "value": str(team[1]),
                }
                for team in all_teams
                if str(team[1]) not in scouted_teams
            ][:100]  # Slack's 100 option limit

            # Update the loading modal with the scout modal
            client.views_update(
                view_id=view_id,
                view={
                    "type": "modal",
                    "callback_id": "scout-modal-identifier",
                    "title": {"type": "plain_text", "text": "Scout Team"},
                    "submit": {"type": "plain_text", "text": "Submit"},
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "team_block",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select a team",
                                },
                                "options": team_options,
                                "action_id": "team_select_action",
                            },
                            "label": {"type": "plain_text", "text": "Select Team"},
                        },
                        {
                            "type": "input",
                            "block_id": "robot_type_block",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select robot type",
                                },
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Specimen",
                                        },
                                        "value": "specimen",
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Sample",
                                        },
                                        "value": "sample",
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "Both"},
                                        "value": "both",
                                    },
                                ],
                                "action_id": "robot_type_action",
                            },
                            "label": {"type": "plain_text", "text": "Robot Type"},
                        },
                        {
                            "type": "input",
                            "block_id": "spec_auto_block",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select Specimen Auto",
                                },
                                "options": get_spec_auto_options(),
                                "action_id": "spec_auto_action",
                            },
                            "label": {"type": "plain_text", "text": "Specimen Auto"},
                        },
                        {
                            "type": "input",
                            "block_id": "sample_auto_block",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select Sample Auto",
                                },
                                "options": get_sample_auto_options(),
                                "action_id": "sample_auto_action",
                            },
                            "label": {"type": "plain_text", "text": "Sample Auto"},
                        },
                        {
                            "type": "input",
                            "block_id": "spec_tele_block",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select Specimen Teleop",
                                },
                                "options": get_tele_options(),
                                "action_id": "spec_tele_action",
                            },
                            "label": {"type": "plain_text", "text": "Specimen Teleop"},
                        },
                        {
                            "type": "input",
                            "block_id": "sample_tele_block",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select Sample Teleop",
                                },
                                "options": get_tele_options(),
                                "action_id": "sample_tele_action",
                            },
                            "label": {"type": "plain_text", "text": "Sample Teleop"},
                        },
                        {
                            "type": "input",
                            "block_id": "ascent_block",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select ascent level",
                                },
                                "options": [
                                    {
                                        "text": {"type": "plain_text", "text": "None"},
                                        "value": "none",
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "L1"},
                                        "value": "l1",
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "L2"},
                                        "value": "l2",
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "L3"},
                                        "value": "l3",
                                    },
                                ],
                                "action_id": "ascent_action",
                            },
                            "label": {"type": "plain_text", "text": "Ascent Level"},
                        },
                        {
                            "type": "input",
                            "block_id": "contact_block",
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "contact_action",
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "Contact Information",
                            },
                        },
                        {
                            "type": "input",
                            "block_id": "notes_block",
                            "element": {
                                "type": "plain_text_input",
                                "multiline": True,
                                "action_id": "notes_action",
                            },
                            "label": {"type": "plain_text", "text": "Additional Notes"},
                        },
                    ],
                },
            )

        except Exception as modal_error:
            logger.error(f"Failed to load teams: {str(modal_error)}")
            client.views_update(
                view_id=view_id,
                view={
                    "type": "modal",
                    "title": {"type": "plain_text", "text": "Error"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"Err loading teams: {str(modal_error)}",
                            },
                        }
                    ],
                },
            )
            raise

    except Exception as e:
        logger.error(f"Error handling scout command: {str(e)}")
        client.chat_postMessage(channel=body["channel_id"], text=f"Error: {str(e)}")


@app.view("scout-modal-identifier")
def handle_scout_submission(ack, body, logger, client):
    try:
        ack()
        print("Processing scout submission...")

        # Initialize Google Sheets connection
        if not init_google_sheets():
            raise Exception("Failed to initialize Google Sheets")

        # Extract submitted data
        submitted_data = body["view"]["state"]["values"]
        submission_time = datetime.now(timezone(timedelta(hours=-7))).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Extract data from submission
        team_info = None
        team_name = None
        robot_type = None
        spec_auto = None
        sample_auto = None
        spec_tele = None
        sample_tele = None
        ascent_level = None
        contact_info = None
        notes = None

        # Parse submitted data
        for block_id, block_data in submitted_data.items():
            for action_id, action_data in block_data.items():
                if action_id == "team_select_action":
                    team_info = action_data["selected_option"]["value"]
                    # Get team name
                    for team in teams_sheet.get_all_values():
                        if team[1] == team_info:
                            team_name = team[0]
                            break
                elif action_id == "robot_type_action":
                    robot_type = action_data["selected_option"]["value"]
                elif action_id == "spec_auto_action":
                    spec_auto = action_data["selected_option"]["value"]
                elif action_id == "sample_auto_action":
                    sample_auto = action_data["selected_option"]["value"]
                elif action_id == "spec_tele_action":
                    spec_tele = action_data["selected_option"]["value"]
                elif action_id == "sample_tele_action":
                    sample_tele = action_data["selected_option"]["value"]
                elif action_id == "ascent_action":
                    ascent_level = action_data["selected_option"]["value"]
                elif action_id == "contact_action":
                    contact_info = action_data["value"]
                elif action_id == "notes_action":
                    notes = action_data["value"]

        user_id = body["user"]["id"]
        user_response = client.users_info(user=user_id)
        if user_response["ok"]:
            submitting_user = user_response["user"]["real_name"]

        # Create new row data
        new_row = [
            submitting_user,  # A: person responsible
            team_info,  # B: Team Number
            team_name,  # C: Team Name
            robot_type,  # D: Robot Type
            spec_auto,  # E: Specimen Auto
            sample_auto,  # F: Sample Auto
            spec_tele,  # G: Specimen Teleop
            sample_tele,  # H: Sample Teleop
            ascent_level,  # I: Ascent Level
            contact_info,  # J: Contact Information
            notes,  # K: Additional Notes
        ]

        # print(new_row)
        # Append to scouting sheet
        print(f"Appending data for team {team_info} to sheet...")
        scouting_sheet.append_row(new_row)
        print("Successfully added scout data to sheet")

        # Send confirmation message

        fallback_text = f"New scouted Team {team_info} - {team_name}"
        client.chat_postMessage(
            channel="C07QFDDS9QW",
            text=fallback_text,
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Team Scouted: {team_info} - {team_name}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Robot Type:* {robot_type}"}
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Auto:*\nSpecimen: {spec_auto}\nSample: {sample_auto}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Teleop:*\nSpecimen: {spec_tele}\nSample: {sample_tele}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Ascent:* {ascent_level}"},
                        {"type": "mrkdwn", "text": f"*Contact:* {contact_info}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Notes:*\n{notes}"},
                },
            ],
        )

    except Exception as e:
        error_msg = f"Error saving scout data: {str(e)}"
        logger.error(error_msg)
        client.chat_postMessage(channel="C07QFDDS9QW", text=error_msg)
        raise


def get_spec_auto_options():
    return [
        {"text": {"type": "plain_text", "text": "None"}, "value": "none"},
        {"text": {"type": "plain_text", "text": "1+0"}, "value": "1+0"},
        {"text": {"type": "plain_text", "text": "2+0"}, "value": "2+0"},
        {"text": {"type": "plain_text", "text": "3+0"}, "value": "3+0"},
        {"text": {"type": "plain_text", "text": "4+0"}, "value": "4+0"},
        {"text": {"type": "plain_text", "text": "5+0"}, "value": "5+0"},
        {"text": {"type": "plain_text", "text": "5+1"}, "value": "5+1"},
        {"text": {"type": "plain_text", "text": "6+0"}, "value": "6+0"},
        {"text": {"type": "plain_text", "text": "7+0"}, "value": "7+0"},
    ]


def get_sample_auto_options():
    return [
        {"text": {"type": "plain_text", "text": "None"}, "value": "none"},
        {"text": {"type": "plain_text", "text": "0+1"}, "value": "0+1"},
        {"text": {"type": "plain_text", "text": "0+2"}, "value": "0+2"},
        {"text": {"type": "plain_text", "text": "0+3"}, "value": "0+3"},
        {"text": {"type": "plain_text", "text": "0+4"}, "value": "0+4"},
        {"text": {"type": "plain_text", "text": "0+5"}, "value": "0+5"},
        {"text": {"type": "plain_text", "text": "0+6"}, "value": "0+6"},
        {"text": {"type": "plain_text", "text": "0+7"}, "value": "0+7"},
        {"text": {"type": "plain_text", "text": "0+8"}, "value": "0+8"},
    ]


def get_tele_options():
    options = [{"text": {"type": "plain_text", "text": "None"}, "value": "0"}]

    options.extend(
        [
            {"text": {"type": "plain_text", "text": str(i)}, "value": str(i)}
            for i in range(1, 21)  # 1-20 inclusive
        ]
    )

    return options


def scout_modal(trigger_id, client):
    try:
        # Get teams and filter out scouted ones
        all_teams = teams_sheet.get_all_values()[1:]  # Skip header
        scouted_data = (
            scouting_sheet.get_all_values()[1:]
            if scouting_sheet.get_all_values()
            else []
        )
        scouted_teams = {row[1] for row in scouted_data}

        # Create team options
        team_options = [
            {
                "text": {"type": "plain_text", "text": f"{team[1]} - {team[0]}"},
                "value": str(team[1]),
            }
            for team in all_teams
            if str(team[1]) not in scouted_teams
        ][:100]  # Slack's 100 option limit

        print(f"Found {len(team_options)} available teams")

        # Rest of your modal code...
        blocks = [
            {
                "type": "input",
                "block_id": "team_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "Select a team"},
                    "options": team_options,
                    "action_id": "team_select_action",
                },
                "label": {"type": "plain_text", "text": "Select Team"},
            },
            {
                "type": "input",
                "block_id": "robot_type_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "Select robot type"},
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "Specimen"},
                            "value": "specimen",
                        },
                        {
                            "text": {"type": "plain_text", "text": "Sample"},
                            "value": "sample",
                        },
                        {
                            "text": {"type": "plain_text", "text": "Both"},
                            "value": "both",
                        },
                    ],
                    "action_id": "robot_type_action",
                },
                "label": {"type": "plain_text", "text": "Robot Type"},
            },
            {
                "type": "input",
                "block_id": "spec_auto_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select Specimen Auto",
                    },
                    "options": get_spec_auto_options(),
                    "action_id": "spec_auto_action",
                },
                "label": {"type": "plain_text", "text": "Specimen Auto"},
            },
            {
                "type": "input",
                "block_id": "sample_auto_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "Select Sample Auto"},
                    "options": get_sample_auto_options(),
                    "action_id": "sample_auto_action",
                },
                "label": {"type": "plain_text", "text": "Sample Auto"},
            },
            {
                "type": "input",
                "block_id": "spec_tele_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select Specimen Teleop",
                    },
                    "options": get_tele_options(),
                    "action_id": "spec_tele_action",
                },
                "label": {"type": "plain_text", "text": "Specimen Teleop"},
            },
            {
                "type": "input",
                "block_id": "sample_tele_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select Sample Teleop",
                    },
                    "options": get_tele_options(),
                    "action_id": "sample_tele_action",
                },
                "label": {"type": "plain_text", "text": "Sample Teleop"},
            },
            {
                "type": "input",
                "block_id": "ascent_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select ascent level",
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "None"},
                            "value": "none",
                        },
                        {"text": {"type": "plain_text", "text": "L1"}, "value": "l1"},
                        {"text": {"type": "plain_text", "text": "L2"}, "value": "l2"},
                        {"text": {"type": "plain_text", "text": "L3"}, "value": "l3"},
                    ],
                    "action_id": "ascent_action",
                },
                "label": {"type": "plain_text", "text": "Ascent Level"},
            },
            {
                "type": "input",
                "block_id": "contact_block",
                "element": {"type": "plain_text_input", "action_id": "contact_action"},
                "label": {"type": "plain_text", "text": "Contact Information"},
            },
            {
                "type": "input",
                "block_id": "notes_block",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "notes_action",
                },
                "label": {"type": "plain_text", "text": "Additional Notes"},
            },
        ]

        # print(blocks)

        res = client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "scout-modal-identifier",
                "title": {"type": "plain_text", "text": "Scout Team"},
                "submit": {"type": "plain_text", "text": "Submit"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "blocks": blocks,
            },
        )

        return res
    except Exception as e:
        print(f"Error creating scout modal: {str(e)}")
        raise


def ftc(teamNum):
    url = "https://api.ftcscout.org/graphql"
    body = (
        """
	query {
		teamByNumber(number: %s) {
			name
			schoolName
			location {
				city, state, country
			}
			rookieYear
			quickStats(season:2024) {
				tot {
				  value
				  rank
				}
			}
		}
	}
	"""
        % teamNum
    )

    response = requests.post(url=url, json={"query": body})
    if response.status_code == 200:
        return json.loads(response.content)
    return None


@app.command("/ftc")
def handle_command(ack, body, logger, client):
    ack()
    trigger_id = body["trigger_id"]
    team_data = ftc(body["text"])

    if team_data and team_data.get("data") and team_data["data"].get("teamByNumber"):
        team = team_data["data"]["teamByNumber"]
        location = team.get("location", {})
        quick_stats = team.get("quickStats", {}).get("tot", {})

        res = client.chat_postMessage(
            channel=body["channel_id"],
            text=f"Team Info: Team {body['text']}",  # Fallback text
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Team Info: Team {body['text']}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Team Name:*\n{team['name']}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*School:*\n{team.get('schoolName', 'N/A')}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Location:*\n{location.get('city', 'N/A')}, {location.get('state', 'N/A')}, {location.get('country', 'N/A')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Rookie Year:*\n{team.get('rookieYear', 'N/A')}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*OPR:*\n{round(quick_stats.get('value', 0), 2)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Rank:*\n#{quick_stats.get('rank', 'N/A')}",
                        },
                    ],
                },
            ],
        )
    else:
        client.chat_postMessage(
            channel=body["channel_id"],
            text=f"Could not find data for team {body['text']}",
        )


# #########     ####			####
# ###     ###    ####			####
#   ###########    ####			####
#   ###     ###    ####	      	####
#   ###     ###    #########    ##########


def open_modal(trigger_id, client):
    res = client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "modal-identifier",
            "submit": {"type": "plain_text", "text": "Next"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "plain_text", "text": "Choose the category:"},
                    "accessory": {
                        "type": "radio_buttons",
                        "action_id": "category_action_id",
                        "options": [
                            {
                                "value": "mech",
                                "text": {"type": "plain_text", "text": "Mechanical"},
                            },
                            {
                                "value": "prog",
                                "text": {"type": "plain_text", "text": "Programming"},
                            },
                            {
                                "value": "outreach",
                                "text": {"type": "plain_text", "text": "Outreach"},
                            },
                        ],
                    },
                }
            ],
        },
    )
    return res


# #######
# #######
# ######
# ####
# ####
# ####
# ####
# ####
# ####


def mech_categories(trigger_id, client):
    res = client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "mech-categories-identifier",
            "submit": {"type": "plain_text", "text": "Next"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "static_select",
                        "placeholder": {"type": "plain_text", "text": "Select an item"},
                        "options": [
                            {
                                "value": "drivetrain",
                                "text": {"type": "plain_text", "text": "Drivetrain"},
                            },
                            {
                                "value": "intake",
                                "text": {"type": "plain_text", "text": "Intake"},
                            },
                        ],
                        "action_id": "static_select-action",
                    },
                    "label": {"type": "plain_text", "text": "Choose a category:"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "My category isn't there: DM Nes'et (this is hardcoded)",
                    },
                },
            ],
        },
    )
    return res


# OLD CODE, CATS ARE HARDCODED NOW !!!
"""
def new_mech_category(view_id, client):
	res = client.views_update(
		view_id=view_id,
	view={
		"type": "modal",
		"callback_id": "n_mech_cat_identifier",
		"submit": {
			"type": "plain_text",
			"text": "Next"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [ 
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Enter New Category Below:"
				}
			}
		]
	}
	)
	return res
"""


def mech_modal(trigger_id, client):
    res = client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "mech-modal-identifier",
            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "multi_users_select",
                        "placeholder": {"type": "plain_text", "text": "Select People"},
                        "action_id": "multi_users_select-action",
                    },
                    "label": {"type": "plain_text", "text": "Who Was There?"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "plain_text_input-action",
                    },
                    "label": {"type": "plain_text", "text": "What You Did:"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "plain_text_input-action",
                    },
                    "label": {"type": "plain_text", "text": "What You Learned:"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "radio_buttons",
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "Yes"},
                                "value": "yes",
                            },
                            {
                                "text": {"type": "plain_text", "text": "No"},
                                "value": "no",
                            },
                        ],
                        "action_id": "radio_buttons-action",
                    },
                    "label": {"type": "plain_text", "text": "Milestone?"},
                },
                {
                    "type": "input",
                    "block_id": "input_block_id",
                    "label": {"type": "plain_text", "text": "Upload Images"},
                    "element": {
                        "type": "file_input",
                        "action_id": "file_input_action_id_1",
                        "filetypes": ["jpg", "png", "jpeg", "heic"],
                        "max_files": 10,
                    },
                },
            ],
        },
    )
    return res


# ####
# 	##  ##
#   #####
#   ##
#   ##


def prog_categories(trigger_id, client):
    res = client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "prog-categories-identifier",
            "submit": {"type": "plain_text", "text": "Next"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "static_select",
                        "placeholder": {"type": "plain_text", "text": "Select an item"},
                        "options": [
                            {
                                "value": "limelight",
                                "text": {"type": "plain_text", "text": "Limelight"},
                            },
                            {
                                "value": "roadrunner",
                                "text": {"type": "plain_text", "text": "Roadrunner"},
                            },
                            {
                                "value": "autonomous",
                                "text": {"type": "plain_text", "text": "Autonomous"},
                            },
                        ],
                        "action_id": "static_select-action",
                    },
                    "label": {"type": "plain_text", "text": "Choose a category:"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "My category isn't there: DM Nes'et (this is hardcoded)",
                    },
                },
            ],
        },
    )
    return res


# OLD CODE, CATS ARE HARDCODED NOW !!!
"""
def new_prog_category(view_id, client):
	res = client.views_update(
		view_id=view_id,
	view={
		"type": "modal",
		"callback_id": "n_prog_cat_identifier",
		"submit": {
			"type": "plain_text",
			"text": "Next"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [ 
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Enter New Category Below:"
				}
			}
		]
	}
	)
	return res
"""


def prog_modal(trigger_id, client):
    res = client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "prog-modal-identifier",
            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "multi_users_select",
                        "placeholder": {"type": "plain_text", "text": "Select People"},
                        "action_id": "multi_users_select-action",
                    },
                    "label": {"type": "plain_text", "text": "Who Was There?"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "plain_text_input-action",
                    },
                    "label": {"type": "plain_text", "text": "What You Did:"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "plain_text_input-action",
                    },
                    "label": {"type": "plain_text", "text": "What You Learned:"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "radio_buttons",
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "Yes"},
                                "value": "yes",
                            },
                            {
                                "text": {"type": "plain_text", "text": "No"},
                                "value": "no",
                            },
                        ],
                        "action_id": "radio_buttons-action",
                    },
                    "label": {"type": "plain_text", "text": "Milestone?"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "If you have any images: send to #programming-progress",
                    },
                },
                # {
                # "type": "input",
                # "optional": true,
                # "block_id": "input_block_id",
                # "label": {
                # "type": "plain_text",
                # "text": "Upload Images"
                # },
                # "element": {
                # "action_id": "file_input_action_id_1",
                # "filetypes": [
                # "jpg",
                # "png",
                # "jpeg",
                # "heic"
                # ],
                # "max_files": 10
                # }
                # }
            ],
        },
    )
    return res


def outreach_modal(trigger_id, client):
    res = client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "outreach-modal-identifier",
            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "New Outreach Event"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "plain_text_input-action",
                    },
                    "label": {"type": "plain_text", "text": "Name of outreach"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "datepicker",
                        "action_id": "datepicker",
                        "placeholder": {"type": "plain_text", "text": "What Day?"},
                    },
                    "label": {"type": "plain_text", "text": "Date:"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "multi_users_select",
                        "placeholder": {"type": "plain_text", "text": "Select People"},
                        "action_id": "multi_users_select-action",
                    },
                    "label": {"type": "plain_text", "text": "Which students?"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "number_input",
                        "is_decimal_allowed": True,
                        "action_id": "number_input-action",
                    },
                    "label": {"type": "plain_text", "text": "How Many Hours?"},
                },
                {
                    "type": "input",
                    "element": {
                        "type": "number_input",
                        "is_decimal_allowed": False,
                        "action_id": "number_input-action",
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "How Many People Affected?",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "If you have any images, send them to #outreach-pics!",
                    },
                },
            ],
        },
    )
    return res


# Command
@app.command("/en")
def handle_command(ack, body, logger, client):
    ack()
    print(body)
    trigger_id = body["trigger_id"]
    open_modal(trigger_id, client)


@app.command("/outreach")
def handle_command(ack, body, logger, client):
    ack()
    print(body)
    trigger_id = body["trigger_id"]
    outreach_modal(trigger_id, client)


# Button handler
@app.action("category_action_id")
def handle_some_action(ack, body, logger):
    ack()
    print(body)


@app.view("modal-identifier")
def handle_view_submission_events(ack, body, logger, client):
    ack()
    print(body)
    trigger_id = body["trigger_id"]
    submitted_data = body["view"]["state"]["values"]
    global new_prog_cat_made
    new_prog_cat_made = False
    global new_mech_cat_made
    new_mech_cat_made = False
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "radio_buttons":
                category = action_data["selected_option"]["value"]
                print(category)
    if category == "mech":
        mech_categories(trigger_id, client)
    elif category == "prog":
        prog_categories(trigger_id, client)
    elif category == "outreach":
        outreach_modal(trigger_id, client)


@app.view("outreach-modal-identifier")
def handle_view_submission(ack, body, logger, client):
    ack()
    print(body)
    user_id = body["user"]["id"]
    submitted_data = body["view"]["state"]["values"]
    print(submitted_data)

    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "plain_text_input":
                what_you_did = action_data["value"]

    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "datepicker":
                date = action_data["selected_date"]

    user_ids = []
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "multi_users_select":
                user_ids = action_data["selected_users"]

    user_info = []
    for user_id in user_ids:
        response = client.users_info(user=user_id)
        if response["ok"]:
            user_info.append(response["user"]["real_name"])

    num_inputs = []
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "number_input":
                num_inputs.append(action_data["value"])
    indiv_hours = num_inputs[0]
    affected = num_inputs[1]

    team_hours = int(len(user_info)) * int(indiv_hours)

    members = ""
    for i in range(len(user_info)):
        members = members + user_info[i] + ","
    submission_data = [what_you_did, date, members, indiv_hours, team_hours, affected]

    outreach_result = outreach_upload(submission_data, client)
    outreach_response(client, outreach_result)


@app.view("prog-categories-identifier")
def handle_view_submission(ack, body, logger, client):
    ack()
    print(body)
    trigger_id = body["trigger_id"]
    global p_category
    submitted_data = body["view"]["state"]["values"]
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "static_select":
                p_category = action_data["selected_option"]["value"]
    prog_modal(trigger_id, client)


# New category button
@app.action("p_button")
def handle_some_action(ack, body, logger, client):
    ack()
    print(body)
    view_id = body["view"]["id"]
    global new_prog_cat_made
    new_prog_cat_made = True
    # new_prog_category(view_id, client)


# Entry
@app.view("prog-modal-identifier")
def handle_view_submission(ack, body, logger, client):
    ack()
    print(body)
    # print(body)
    user_id = body["user"]["id"]
    submitted_data = body["view"]["state"]["values"]

    # Keeping track of how many entries
    entry_number = hkl.load("entrys")
    entry_number += 1
    hkl.dump(entry_number, "entrys")

    # Time when entry was submitted
    entry_time = datetime.now(timezone(timedelta(hours=-7)))
    entry_time = entry_time.strftime("%c")

    user_response = client.users_info(user=user_id)
    if user_response["ok"]:
        submitting_user = user_response["user"]["real_name"]

    user_ids = []
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "multi_users_select":
                user_ids = action_data["selected_users"]

    user_info = []
    for user_id in user_ids:
        response = client.users_info(user=user_id)
        if response["ok"]:
            user_info.append(response["user"]["real_name"])

    text_reponses = []
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "plain_text_input":
                text_reponses.append(action_data["value"])

    what_you_did = text_reponses[0]
    what_you_learned = text_reponses[1]

    milestone = "no"
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "radio_buttons":
                milestone = action_data["selected_option"]["value"]
    if milestone == "yes":
        milestone = True
    elif milestone == "no":
        milestone = False

    # files = submitted_data['input_block_id']['file_input_action_id_1']['files']
    submission_data = {
        "is_new_project": new_prog_cat_made,
        "project_name": p_category,
        "category": "programming",
        "entry_id": entry_number,
        "entry_time": entry_time,
        "submitting_user": submitting_user,
        "selected_users": user_info,
        "what_did": what_you_did,
        "what_learned": what_you_learned,
        "milestone": milestone,
        "files": [],
    }

    # for file in files:
    # file_info = {
    # "file_name": file['name'],
    # "file_type": file['filetype'],
    # "file_url": file['url_private']
    # }
    # submission_data["files"].append(file_info)

    def convert_sets_to_lists(obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: convert_sets_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_sets_to_lists(elem) for elem in obj]
        else:
            return obj

    submission_data = convert_sets_to_lists(submission_data)
    # existing_data = []

    # if os.path.exists("submission_data.json"):
    # with open('submission_data.json', 'r') as json_file:
    # existing_data.clear()
    # existing_data.append(json.load(json_file))
    # else:
    # existing_data = []

    # existing_data.append(submission_data)

    # write data to json file
    with open("submission_data.json", "w") as json_file:
        json.dump(submission_data, json_file, indent=4)

    # Send confirmation message
    send_done_msg(client, submitting_user, entry_time)

    # api
    main()
    send_files = []
    # api worked
    send_confirm_msg(client)
    send_p_update_msg(client, user_info, what_you_did, send_files)


# MMM    MMM
# 		MM  MM MM  MM
#     MM     MM     MM
#   MMM              MMM


# Categories
@app.view("mech-categories-identifier")
def handle_view_submission(ack, body, logger, client):
    ack()
    print(body)
    trigger_id = body["trigger_id"]
    global m_category
    submitted_data = body["view"]["state"]["values"]
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "static_select":
                m_category = action_data["selected_option"]["value"]
    mech_modal(trigger_id, client)


# New category button
@app.action("m_button")
def handle_some_action(ack, body, logger, client):
    ack()
    print(body)
    view_id = body["view"]["id"]
    global new_mech_cat_made
    new_mech_cat_made = True
    # new_mech_category(view_id, client)


"""
# New category function
@app.view("n_mech_cat_identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	print(body)
	trigger_id = body["trigger_id"]
	submitted_data = body['view']['state']['values']
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'plain_text_input':
				new_cat = action_data['value']
	mech_options = hkl.load('mech_cat')
	new_value = new_cat.lower()
	new_label = new_cat.capitalize()
	new_append = {
					"value": new_value,
					"text": {
						"type": "plain_text",
						"text": new_label
					}
				}
	mech_options.append(new_append)
	hkl.dump(mech_options, 'mech_cat')
	mech_categories(trigger_id, client)
"""


# Entry
@app.view("mech-modal-identifier")
def handle_view_submission(ack, body, logger, client):
    ack()
    print(body)
    user_id = body["user"]["id"]
    submitted_data = body["view"]["state"]["values"]

    # Keeping track of how many entries
    entry_number = hkl.load("entrys")
    entry_number += 1
    hkl.dump(entry_number, "entrys")

    # Time when entry was submitted
    entry_time = datetime.now(timezone(timedelta(hours=-7)))
    entry_time = entry_time.strftime("%c")

    user_response = client.users_info(user=user_id)
    if user_response["ok"]:
        submitting_user = user_response["user"]["real_name"]

    user_ids = []
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "multi_users_select":
                user_ids = action_data["selected_users"]

    user_info = []
    for user_id in user_ids:
        response = client.users_info(user=user_id)
        if response["ok"]:
            user_info.append(response["user"]["real_name"])

    # category = submitted_data['WYrS1']['static_select-action']['selected_option']['text']['text']
    text_reponses = []
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "plain_text_input":
                text_reponses.append(action_data["value"])

    what_you_did = text_reponses[0]
    what_you_learned = text_reponses[1]

    milestone = "no"
    for block_id, block_data in submitted_data.items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "radio_buttons":
                milestone = action_data["selected_option"]["value"]
    if milestone == "yes":
        milestone = True
    elif milestone == "no":
        milestone = False

    files = submitted_data["input_block_id"]["file_input_action_id_1"]["files"]

    submission_data = {
        "is_new_project": new_mech_cat_made,
        "project_name": m_category,
        "category": "mechanical",
        "entry_id": entry_number,
        "entry_time": entry_time,
        "submitting_user": submitting_user,
        "selected_users": user_info,
        "what_did": what_you_did,
        "what_learned": what_you_learned,
        "milestone": milestone,
        "files": [],
    }
    send_files = []
    for file in files:
        send_files.append(file["url_private"])
    for file in files:
        file_info = {"file_name": file["name"], "file_url": file["url_private"]}
        submission_data["files"].append(file_info)

    def convert_sets_to_lists(obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: convert_sets_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_sets_to_lists(elem) for elem in obj]
        else:
            return obj

    submission_data = convert_sets_to_lists(submission_data)

    # write data to json file
    with open("submission_data.json", "w") as json_file:
        json.dump(submission_data, json_file, indent=4)

    # Send confirmation message
    send_done_msg(client, submitting_user, entry_time)

    # api
    main()

    # api worked
    send_confirm_msg(client)
    send_m_update_msg(client, user_info, what_you_did, send_files)


application = flask_app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, debug=True)
