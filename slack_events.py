from datetime import datetime, timezone, timedelta
import json
import hickle as hkl
from slack_helpers import (
    open_prog_modal,
    open_mech_modal,
    open_outreach_modal,
    send_done_message,
    send_confirmation_message,
    send_programming_update,
    send_mechanical_update,
)
from gsheet import outreach_upload
from google_sheets_client import append_scout_data, get_all_teams
from database_helpers import enter_data as run_db_upload


def process_entry_submission(body, logger, client, category):
    """A generic function to process both mech and prog submissions."""
    try:
        entry_number = hkl.load("entrys") + 1
        hkl.dump(entry_number, "entrys")

        values = body["view"]["state"]["values"]
        submitting_user_info = client.users_info(user=body["user"]["id"])
        submitting_user_name = submitting_user_info["user"]["real_name"]

        project_selection = values["project_block"]["project_select"]["selected_option"]
        project_name = ""
        if project_selection and project_selection["value"] == "_new_":
            project_name = values["new_project_block"]["new_project_name"]["value"]
            if not project_name:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="Error: You selected 'Create New Project' but did not provide a name.",
                )
                return
        elif project_selection:
            project_name = project_selection["value"]
        else:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="Error: You must select a project or create a new one.",
            )
            return

        user_ids = values["users_block"]["users_select"]["selected_users"]
        what_you_did = values["did_block"]["did_input"]["value"]
        what_you_learned = values["learned_block"]["learned_input"]["value"]
        files = values["files_block"]["file_input"].get("files", [])

        user_info_list = [
            client.users_info(user=uid)["user"]["real_name"] for uid in user_ids
        ]

        submission_data = {
            "project_name": project_name,
            "category": category,
            "entry_id": entry_number,
            "entry_time": datetime.now(timezone(timedelta(hours=-7))).strftime("%c"),
            "submitting_user": submitting_user_name,
            "selected_users": user_info_list,
            "what_did": what_you_did,
            "what_learned": what_you_learned,
            "files": [
                {"file_name": f["name"], "file_url": f["url_private"]} for f in files
            ],
        }

        run_db_upload(submission_data, client, submitting_user_name)

        send_done_message(client, submitting_user_name, submission_data["entry_time"])
        send_confirmation_message(
            client,
            "C07QFDDS9QW",
            f"New {category} entry for '{project_name}' submitted to database.",
        )

        if category == "mechanical":
            send_mechanical_update(
                client, user_info_list, what_you_did, [f["url_private"] for f in files]
            )
        else:  # Handles programming
            send_programming_update(
                client, user_info_list, what_you_did, [f["url_private"] for f in files]
            )

    except Exception as e:
        logger.error(f"Error processing {category} submission: {e}")
        client.chat_postMessage(
            channel=body["user"]["id"], text=f"An error occurred: {e}"
        )


def register_events(app):
    @app.action("category_action_id")
    def handle_category_clicks(ack):
        ack()

    @app.view("modal-identifier")
    def handle_initial_category_submission(ack, body, logger, client):
        ack()
        try:
            trigger_id = body["trigger_id"]
            values = body["view"]["state"]["values"]
            category = values["category_selection_block"]["category_action_id"][
                "selected_option"
            ]["value"]

            if category == "mech":
                open_mech_modal(trigger_id, client)
            elif category == "prog":
                open_prog_modal(trigger_id, client)
            elif category == "outreach":
                open_outreach_modal(trigger_id, client)
        except Exception as e:
            logger.error(f"Error parsing initial category submission: {e}")

    @app.view("mech-modal-identifier")
    def handle_mech_modal_submission(ack, body, logger, client):
        ack()
        process_entry_submission(body, logger, client, "mechanical")

    @app.view("prog-modal-identifier")
    def handle_prog_modal_submission(ack, body, logger, client):
        ack()
        process_entry_submission(body, logger, client, "programming")

    @app.view("outreach-modal-identifier")
    def handle_outreach_submission(ack, body, logger, client):
        """Handles the submission of the outreach modal."""
        ack()
        try:
            values = body["view"]["state"]["values"]

            name = values["name_block"]["name_input"]["value"]
            date = values["date_block"]["datepicker"]["selected_date"]
            user_ids = values["users_block"]["multi_users_select-action"][
                "selected_users"
            ]
            indiv_hours = values["hours_block"]["hours_input"]["value"]
            affected_people = values["people_block"]["people_input"]["value"]

            user_info_list = [
                client.users_info(user=uid)["user"]["real_name"]
                for uid in user_ids
                if client.users_info(user=uid)["ok"]
            ]
            team_hours = len(user_info_list) * float(indiv_hours)

            submission_data = [
                name,
                date,
                ",".join(user_info_list),
                indiv_hours,
                str(team_hours),
                affected_people,
            ]

            result = outreach_upload(submission_data, client)
            send_confirmation_message(
                client,
                "C07QFDDS9QW",
                f"Outreach event '{name}' logged successfully. Cells updated: {result}",
            )
        except Exception as e:
            logger.error(f"Error in outreach submission: {e}")
            send_confirmation_message(
                client, body["user"]["id"], f"Error logging outreach event: {e}"
            )

    @app.view("scout-modal-identifier")
    def handle_scout_submission(ack, body, logger, client):
        """Handles the submission of the scouting modal."""
        ack()
        try:
            values = body["view"]["state"]["values"]
            submitting_user_info = client.users_info(user=body["user"]["id"])
            submitting_user = (
                submitting_user_info["user"]["real_name"]
                if submitting_user_info["ok"]
                else "Unknown User"
            )

            team_number = values["team_block"]["team_select_action"]["selected_option"][
                "value"
            ]

            # This requires google_sheets_client to be initialized
            all_teams = get_all_teams()
            team_name = next(
                (team[0] for team in all_teams if team[1] == team_number),
                "Unknown Team",
            )

            new_row = [
                submitting_user,
                team_number,
                team_name,
                values["robot_type_block"]["robot_type_action"]["selected_option"][
                    "value"
                ],
                values["spec_auto_block"]["spec_auto_action"]["selected_option"][
                    "value"
                ],
                values["sample_auto_block"]["sample_auto_action"]["selected_option"][
                    "value"
                ],
                values["spec_tele_block"]["spec_tele_action"]["selected_option"][
                    "value"
                ],
                values["sample_tele_block"]["sample_tele_action"]["selected_option"][
                    "value"
                ],
                values["ascent_block"]["ascent_action"]["selected_option"]["value"],
                values["contact_block"]["contact_action"]["value"],
                values["notes_block"]["notes_action"]["value"],
            ]

            append_scout_data(new_row)
            send_confirmation_message(
                client,
                "C07QFDDS9QW",
                f"Successfully scouted team {team_number} - {team_name}.",
            )
        except Exception as e:
            logger.error(f"Error saving scout data: {e}")
            send_confirmation_message(
                client,
                body["user"]["id"],
                f"Error saving scout data for team {team_number}: {e}",
            )
