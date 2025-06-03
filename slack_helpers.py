import time
from datetime import datetime, timezone, timedelta
from ftc_scout_api import fetch_team_stats, get_best_stats, ftc
from google_sheets_client import (
    init_google_sheets,
    get_all_teams,
    get_scouted_teams,
    append_scout_data,
    update_opr_sheet,
)

# --- Message Sending Functions ---


def send_confirmation_message(client):
    """Sends a generic API upload success message."""
    client.chat_postMessage(channel="C07QFDDS9QW", text="API Upload successful :)")


def send_mechanical_update(client, user_info, what_you_did, file_info):
    """Sends an update message for a mechanical entry."""
    attachments = [
        {"fallback": "Image attachment", "image_url": file} for file in file_info
    ]
    client.chat_postMessage(
        channel="C07GPKUFGQL",
        text=f"**New Entry**:\n{', '.join(user_info)}\n- **What:** {what_you_did}\n**Images:** {','.join(file_info)}",
        attachments=attachments,
    )


def send_programming_update(client, user_info, what_you_did, file_info):
    """Sends an update message for a programming entry."""
    attachments = [
        {"fallback": "Image attachment", "image_url": file} for file in file_info
    ]
    client.chat_postMessage(
        channel="C07H9UN6VMW",
        text=f"**New Entry**:\n{', '.join(user_info)}\n- **What:** {what_you_did}\n**Images:** {','.join(file_info)}",
        attachments=attachments,
    )


def send_outreach_response(client, err):
    """Sends a response after an outreach submission."""
    client.chat_postMessage(channel="C07QFDDS9QW", text=f"Outreach: {err}")


def send_done_message(client, sub_usr, sub_time):
    """Sends a message confirming an engineering notebook entry."""
    confirm_msg = f"{sub_usr} made an Engineering Notebook entry at {sub_time}"
    client.chat_postMessage(channel="C07QFDDS9QW", text=confirm_msg)
    upload_submission_data(client)


def upload_submission_data(client):
    """Uploads the submission_data.json file to Slack."""
    try:
        client.files_upload_v2(
            file="submission_data.json",
            title="Submission Data",
            initial_comment="Submission Data",
            channel="C07QFDDS9QW",
        )
    except Exception as e:
        print(f"Error uploading submission data: {e}")


# --- Modal Opening Functions ---


def open_new_entry_modal(trigger_id, client):
    """Opens the initial modal for creating a new entry."""
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "modal-identifier",
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "submit": {"type": "plain_text", "text": "Next"},
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


def open_mech_categories(trigger_id, client):
    """Opens the modal for selecting a mechanical category."""
    client.views_open(
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
            ],
        },
    )


def open_prog_categories(trigger_id, client):
    """Opens the modal for selecting a programming category."""
    client.views_open(
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
            ],
        },
    )


def open_mech_modal(trigger_id, client, category):
    """Opens the modal for a mechanical entry."""
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "mech-modal-identifier",
            "private_metadata": category,
            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "blocks": [
                # ... (blocks for mech_modal)
            ],
        },
    )


def open_prog_modal(trigger_id, client, category):
    """Opens the modal for a programming entry."""
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "prog-modal-identifier",
            "private_metadata": category,
            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "blocks": [
                # ... (blocks for prog_modal)
            ],
        },
    )


def open_outreach_modal(trigger_id, client):
    """Opens the modal for logging an outreach event."""
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "outreach-modal-identifier",
            "title": {"type": "plain_text", "text": "New Outreach Event"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                # ... (modal blocks for outreach)
            ],
        },
    )


def open_scout_modal(trigger_id, client, logger):
    """Opens the scouting modal."""
    # ... (logic for opening the scout modal, including fetching teams from Google Sheets)


# --- Command Logic Functions ---
def update_oprs_and_notify(body, logger, client):
    """Fetches and updates OPRs, then notifies the channel."""
    try:
        if not init_google_sheets():
            raise ConnectionError("Failed to initialize Google Sheets.")

        all_teams = get_all_teams()
        if not all_teams:
            raise ValueError("Spreadsheet is empty or could not be read.")

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

        updated_rows = []
        errors = []
        for row in all_teams:
            team_number = row[1].strip()
            if not team_number:
                continue

            stats = fetch_team_stats(team_number)
            if not stats or not stats.get("events"):
                errors.append(f"No stats found for team {team_number}")
                continue

            best_stats = get_best_stats(stats["events"])
            new_row = [
                stats["name"],
                team_number,
                best_stats["totalPointsNp"],
                best_stats["autoSamplePoints"],
                best_stats["autoSpecimenPoints"],
                best_stats["autoPoints"],
                best_stats["dcSamplePoints"],
                best_stats["dcSpecimenPoints"],
                best_stats["dcPoints"],
                best_stats["dcParkPointsIndividual"],
            ]
            updated_rows.append(new_row)
            time.sleep(0.2)  # Avoid rate limiting

        update_opr_sheet(header_row, updated_rows)
        message = f"Successfully updated OPR stats for {len(updated_rows)} teams!"
        if errors:
            message += f"\nEncountered {len(errors)} errors:\n" + "\n".join(errors[:5])
        client.chat_postMessage(channel=body["channel_id"], text=message)

    except Exception as e:
        logger.error(f"Error updating OPRs: {e}")
        client.chat_postMessage(
            channel=body["channel_id"], text=f"Error updating OPRs: {e}"
        )


def send_ftc_team_info(body, client):
    """Sends information about a specific FTC team."""
    team_data = ftc(body["text"])
    if team_data and team_data.get("data") and team_data["data"].get("teamByNumber"):
        team = team_data["data"]["teamByNumber"]
        location = team.get("location", {})
        quick_stats = team.get("quickStats", {}).get("tot", {})

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Team Info: {body['text']}"},
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
            # ... (more blocks for team info)
        ]
        client.chat_postMessage(
            channel=body["channel_id"], text=f"Team Info: {body['text']}", blocks=blocks
        )
    else:
        client.chat_postMessage(
            channel=body["channel_id"],
            text=f"Could not find data for team {body['text']}",
        )


def handle_scout_submission(body, logger, client):
    """Handles the submission of the scouting modal."""
    # ... (logic for processing the scout submission and saving to Google Sheets)
