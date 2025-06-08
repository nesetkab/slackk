import time
from slack_helpers import (
    open_new_entry_modal,
    open_outreach_modal,
    send_ftc_team_info,
)
from ftc_scout_api import fetch_team_stats, get_best_stats
from google_sheets_client import (
    init_google_sheets,
    get_all_teams,
    get_scouted_teams,
    update_opr_sheet,
)


def open_scout_modal(trigger_id, client, logger):
    """Opens or updates the scouting modal with team data."""
    loading_view = {
        "type": "modal",
        "callback_id": "loading-modal",
        "title": {"type": "plain_text", "text": "Loading Teams"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Loading available teams..."},
            }
        ],
    }
    try:
        loading_response = client.views_open(trigger_id=trigger_id, view=loading_view)
        view_id = loading_response["view"]["id"]

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
        ][:100]

        from slack_helpers import (
            get_spec_auto_options,
            get_sample_auto_options,
            get_tele_options,
        )

        view_payload = {
            "type": "modal",
            "callback_id": "scout-modal-identifier",
            "title": {"type": "plain_text", "text": "Scout Team"},
            "submit": {"type": "plain_text", "text": "Submit"},
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
        client.views_update(view_id=view_id, view=view_payload)
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
        if "view_id" in locals():
            client.views_update(view_id=view_id, view=error_view)


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
            time.sleep(0.2)

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


def register_commands(app):
    """Registers all Slack command handlers."""

    @app.command("/help")
    def handle_help_command(ack, body, client):
        ack()
        client.chat_postMessage(channel=body["channel_id"], text="Help is on the way!")

    @app.command("/updateoprs")
    def handle_update_oprs_command(ack, body, logger, client):
        ack()
        update_oprs_and_notify(body, logger, client)

    @app.command("/scout")
    def handle_scout_command(ack, body, logger, client):
        ack()
        open_scout_modal(body["trigger_id"], client, logger)

    @app.command("/ftc")
    def handle_ftc_command(ack, body, client):
        ack()
        send_ftc_team_info(body, client)

    @app.command("/en")
    def handle_en_command(ack, body, client):
        ack()
        open_new_entry_modal(body["trigger_id"], client)

    @app.command("/outreach")
    def handle_outreach_command(ack, body, client):
        ack()
        open_outreach_modal(body["trigger_id"], client)
