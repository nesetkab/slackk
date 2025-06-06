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


def send_confirmation_message(client, channel_id, text):
    """Sends a generic confirmation or status message."""
    client.chat_postMessage(channel=channel_id, text=text)


def send_mechanical_update(client, user_info, what_you_did, file_info):
    """Sends an update message for a mechanical entry."""
    attachments = [
        {"fallback": "Image attachment", "image_url": file} for file in file_info
    ]
    client.chat_postMessage(
        channel="C07GPKUFGQL",  # Mechanical Progress Channel
        text=f"**New Entry**:\n{', '.join(user_info)}\n- **What:** {what_you_did}",
        attachments=attachments,
    )


def send_programming_update(client, user_info, what_you_did):
    """Sends an update message for a programming entry."""
    client.chat_postMessage(
        channel="C07H9UN6VMW",  # Programming Progress Channel
        text=f"**New Entry**:\n{', '.join(user_info)}\n- **What:** {what_you_did}",
    )


def send_done_message(client, sub_usr, sub_time):
    """Sends a message confirming an engineering notebook entry."""
    confirm_msg = f"{sub_usr} made an Engineering Notebook entry at {sub_time}"
    client.chat_postMessage(
        channel="C07QFDDS9QW", text=confirm_msg
    )  # General Bot Channel
    upload_submission_data(client)


def upload_submission_data(client):
    """Uploads the submission_data.json file to Slack."""
    try:
        client.files_upload_v2(
            file="submission_data.json",
            title="Submission Data",
            initial_comment="Submission Data",
            channel="C07QFDDS9QW",  # General Bot Channel
        )
    except Exception as e:
        print(f"Error uploading submission data: {e}")


# --- Modal Helper Functions ---


def get_spec_auto_options():
    """Returns options for specimen auto performance."""
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
    """Returns options for sample auto performance."""
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
    """Returns options for teleop performance."""
    options = [{"text": {"type": "plain_text", "text": "None"}, "value": "0"}]
    options.extend(
        [
            {"text": {"type": "plain_text", "text": str(i)}, "value": str(i)}
            for i in range(1, 21)
        ]
    )
    return options


# --- Modal Opening Functions ---


def open_new_entry_modal(trigger_id, client):
    """Opens the initial modal for creating a new entry."""
    client.views_open(
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


def open_mech_categories(trigger_id, client):
    """Opens the modal for selecting a mechanical category."""
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "mech-categories-identifier",
            "submit": {"type": "plain_text", "text": "Next"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Mechanical Category"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a category",
                        },
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


def open_prog_categories(trigger_id, client):
    """Opens the modal for selecting a programming category."""
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "prog-categories-identifier",
            "submit": {"type": "plain_text", "text": "Next"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Programming Category"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a category",
                        },
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
            "title": {
                "type": "plain_text",
                "text": f"New Mechanical Entry: {category.capitalize()}",
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "users_block",
                    "element": {
                        "type": "multi_users_select",
                        "placeholder": {"type": "plain_text", "text": "Select People"},
                        "action_id": "multi_users_select-action",
                    },
                    "label": {"type": "plain_text", "text": "Who Was There?"},
                },
                {
                    "type": "input",
                    "block_id": "did_block",
                    "element": {"type": "plain_text_input", "action_id": "did_input"},
                    "label": {"type": "plain_text", "text": "What You Did:"},
                },
                {
                    "type": "input",
                    "block_id": "learned_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "learned_input",
                    },
                    "label": {"type": "plain_text", "text": "What You Learned:"},
                },
                {
                    "type": "input",
                    "block_id": "milestone_block",
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
                    "block_id": "files_block",
                    "label": {"type": "plain_text", "text": "Upload Images"},
                    "element": {
                        "type": "file_input",
                        "action_id": "file_input_action",
                        "filetypes": ["jpg", "png", "jpeg", "heic"],
                        "max_files": 10,
                    },
                },
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
            "title": {
                "type": "plain_text",
                "text": f"New Programming Entry: {category.capitalize()}",
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "users_block",
                    "element": {
                        "type": "multi_users_select",
                        "placeholder": {"type": "plain_text", "text": "Select People"},
                        "action_id": "multi_users_select-action",
                    },
                    "label": {"type": "plain_text", "text": "Who Was There?"},
                },
                {
                    "type": "input",
                    "block_id": "did_block",
                    "element": {"type": "plain_text_input", "action_id": "did_input"},
                    "label": {"type": "plain_text", "text": "What You Did:"},
                },
                {
                    "type": "input",
                    "block_id": "learned_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "learned_input",
                    },
                    "label": {"type": "plain_text", "text": "What You Learned:"},
                },
                {
                    "type": "input",
                    "block_id": "milestone_block",
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
                {
                    "type": "input",
                    "block_id": "name_block",
                    "element": {"type": "plain_text_input", "action_id": "name_input"},
                    "label": {"type": "plain_text", "text": "Name of outreach"},
                },
                {
                    "type": "input",
                    "block_id": "date_block",
                    "element": {"type": "datepicker", "action_id": "datepicker"},
                    "label": {"type": "plain_text", "text": "Date:"},
                },
                {
                    "type": "input",
                    "block_id": "users_block",
                    "element": {
                        "type": "multi_users_select",
                        "placeholder": {"type": "plain_text", "text": "Select People"},
                        "action_id": "multi_users_select-action",
                    },
                    "label": {"type": "plain_text", "text": "Which students?"},
                },
                {
                    "type": "input",
                    "block_id": "hours_block",
                    "element": {
                        "type": "number_input",
                        "is_decimal_allowed": True,
                        "action_id": "hours_input",
                    },
                    "label": {"type": "plain_text", "text": "How Many Hours?"},
                },
                {
                    "type": "input",
                    "block_id": "people_block",
                    "element": {
                        "type": "number_input",
                        "is_decimal_allowed": False,
                        "action_id": "people_input",
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


def open_scout_modal(trigger_id, view_id, client, logger):
    """Opens or updates the scouting modal with team data."""
    try:
        # Initialize Google Sheets
        if not init_google_sheets():
            raise ConnectionError("Could not connect to Google Sheets.")

        all_teams = get_all_teams()
        scouted_teams = get_scouted_teams()

        team_options = [
            {
                "text": {"type": "plain_text", "text": f"{team[1]} - {team[0]}"},
                "value": str(team[1]),
            }
            for team in all_teams
            if str(team[1]) not in scouted_teams
        ][:100]  # Slack's 100 option limit

        view_payload = {
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
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select robot type",
                        },
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
            ],
        }

        if view_id:
            client.views_update(view_id=view_id, view=view_payload)
        else:
            client.views_open(trigger_id=trigger_id, view=view_payload)

    except Exception as e:
        logger.error(f"Error creating scout modal: {e}")
        error_view = {
            "type": "modal",
            "title": {"type": "plain_text", "text": "Error"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"An error occurred: {e}"},
                }
            ],
        }
        if view_id:
            client.views_update(view_id=view_id, view=error_view)
        # If there's no view_id, we can't update anything, so we just log it.
