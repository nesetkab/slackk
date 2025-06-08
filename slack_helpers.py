from datetime import datetime, timezone, timedelta
from ftc_scout_api import ftc
from database_helpers import fetch_all_projects

# --- Message Sending Functions ---


def send_confirmation_message(client, channel_id, text):
    """Sends a generic confirmation or status message."""
    client.chat_postMessage(channel=channel_id, text=text)


def _create_progress_message_blocks(
    project_name, user_info, what_you_did, what_you_learned, file_info
):
    """A helper function to build the Block Kit structure for progress messages."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"New Entry for: {project_name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Who Was There:*\n{', '.join(user_info)}"}
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*What was done:*\n{what_you_did}"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*What was learned:*\n{what_you_learned}",
            },
        },
    ]
    if file_info:
        blocks.append({"type": "divider"})
        for image_url in file_info:
            blocks.append(
                {
                    "type": "image",
                    "image_url": image_url,
                    "alt_text": "User-uploaded image for the engineering notebook entry.",
                }
            )
    return blocks


def send_mechanical_update(
    client, project_name, user_info, what_you_did, what_you_learned, file_info
):
    """Sends a richly formatted update message for a mechanical entry."""
    blocks = _create_progress_message_blocks(
        project_name, user_info, what_you_did, what_you_learned, file_info
    )
    client.chat_postMessage(
        channel="C07GPKUFGQL",
        text=f"New Mechanical Entry for {project_name}",
        blocks=blocks,
    )


def send_programming_update(
    client, project_name, user_info, what_you_did, what_you_learned, file_info
):
    """Sends a richly formatted update message for a programming entry, with optional images."""
    blocks = _create_progress_message_blocks(
        project_name, user_info, what_you_did, what_you_learned, file_info
    )
    client.chat_postMessage(
        channel="C07H9UN6VMW",
        text=f"New Programming Entry for {project_name}",
        blocks=blocks,
    )


def send_done_message(client, sub_usr, sub_time):
    """Sends a message confirming an engineering notebook entry."""
    confirm_msg = f"{sub_usr} made an Engineering Notebook entry at {sub_time}"
    client.chat_postMessage(channel="C07QFDDS9QW", text=confirm_msg)


# --- Modal Helper Functions ---


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
            "title": {"type": "plain_text", "text": "Create New Entry"},
            "submit": {"type": "plain_text", "text": "Next"},
            "blocks": [
                {
                    "type": "section",
                    "block_id": "category_selection_block",
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


def open_mech_modal(trigger_id, client):
    """Opens the modal for a mechanical entry."""
    projects = fetch_all_projects()
    project_options = [
        {"text": {"type": "plain_text", "text": p}, "value": p} for p in projects
    ]
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "mech-modal-identifier",
            "title": {"type": "plain_text", "text": "New Mechanical Entry"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "project_block",
                    "label": {"type": "plain_text", "text": "Project"},
                    "element": {
                        "type": "static_select",
                        "action_id": "project_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a project",
                        },
                        "options": project_options
                        + [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Create New Project...",
                                },
                                "value": "_new_",
                            }
                        ],
                    },
                },
                {
                    "type": "input",
                    "block_id": "new_project_block",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "New Project Name"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "new_project_name",
                    },
                },
                {
                    "type": "input",
                    "block_id": "users_block",
                    "label": {"type": "plain_text", "text": "Who Was There?"},
                    "element": {
                        "type": "multi_users_select",
                        "action_id": "users_select",
                        "placeholder": {"type": "plain_text", "text": "Select People"},
                    },
                },
                {
                    "type": "input",
                    "block_id": "did_block",
                    "label": {"type": "plain_text", "text": "What You Did:"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "did_input",
                        "multiline": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "learned_block",
                    "label": {"type": "plain_text", "text": "What You Learned:"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "learned_input",
                        "multiline": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "files_block",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "Upload Images"},
                    "element": {
                        "type": "file_input",
                        "action_id": "file_input",
                        "filetypes": ["jpg", "png", "jpeg", "heic"],
                        "max_files": 10,
                    },
                },
            ],
        },
    )


def open_prog_modal(trigger_id, client):
    """Opens the modal for a programming entry."""
    projects = fetch_all_projects()
    project_options = [
        {"text": {"type": "plain_text", "text": p}, "value": p} for p in projects
    ]
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "prog-modal-identifier",
            "title": {"type": "plain_text", "text": "New Programming Entry"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "project_block",
                    "label": {"type": "plain_text", "text": "Project"},
                    "element": {
                        "type": "static_select",
                        "action_id": "project_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a project",
                        },
                        "options": project_options
                        + [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Create New Project...",
                                },
                                "value": "_new_",
                            }
                        ],
                    },
                },
                {
                    "type": "input",
                    "block_id": "new_project_block",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "New Project Name"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "new_project_name",
                    },
                },
                {
                    "type": "input",
                    "block_id": "users_block",
                    "label": {"type": "plain_text", "text": "Who Was There?"},
                    "element": {
                        "type": "multi_users_select",
                        "action_id": "users_select",
                        "placeholder": {"type": "plain_text", "text": "Select People"},
                    },
                },
                {
                    "type": "input",
                    "block_id": "did_block",
                    "label": {"type": "plain_text", "text": "What You Did:"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "did_input",
                        "multiline": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "learned_block",
                    "label": {"type": "plain_text", "text": "What You Learned:"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "learned_input",
                        "multiline": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "files_block",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "Upload Images"},
                    "element": {
                        "type": "file_input",
                        "action_id": "file_input",
                        "filetypes": ["jpg", "png", "jpeg", "heic"],
                        "max_files": 10,
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


def send_ftc_team_info(body, client):
    """Fetches and sends information about a specific FTC team."""
    team_number = body["text"]
    team_data = ftc(team_number)
    if team_data and team_data.get("data") and team_data["data"].get("teamByNumber"):
        team = team_data["data"]["teamByNumber"]
        location = team.get("location", {})
        quick_stats = team.get("quickStats", {}).get("tot", {})
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Team Info: {team_number} - {team['name']}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*School:*\n{team.get('schoolName', 'N/A')}",
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
                        "text": f"*Location:*\n{location.get('city', 'N/A')}, {location.get('state', 'N/A')}, {location.get('country', 'N/A')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*OPR / Rank:*\n{round(quick_stats.get('value', 0), 2)} / #{quick_stats.get('rank', 'N/A')}",
                    },
                ],
            },
        ]
        client.chat_postMessage(
            channel=body["channel_id"], text=f"Team Info: {team_number}", blocks=blocks
        )
    else:
        client.chat_postMessage(
            channel=body["channel_id"],
            text=f"Could not find data for team {team_number}",
        )
