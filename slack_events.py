from datetime import datetime, timezone, timedelta
import json
import hickle as hkl
from upload import main as run_upload
from slack_helpers import (
    open_mech_categories,
    open_prog_categories,
    open_outreach_modal,
    open_prog_modal,
    open_mech_modal,
    open_scout_modal,
    send_done_message,
    send_confirmation_message,
    send_programming_update,
    send_mechanical_update,
)
from gsheet import outreach_upload
from google_sheets_client import append_scout_data, get_all_teams


def register_events(app):
    """
    Registers all Slack event handlers.
    """

    @app.view("modal-identifier")
    def handle_initial_category_submission(ack, body, logger, client):
        """Handles the submission of the initial new entry modal."""
        ack()
        try:
            trigger_id = body["trigger_id"]
            values = body["view"]["state"]["values"]

            # Directly access the value from the known block_id and action_id
            category = values["category_selection_block"]["category_action_id"][
                "selected_option"
            ]["value"]

            if category == "mech":
                open_mech_categories(trigger_id, client)
            elif category == "prog":
                open_prog_categories(trigger_id, client)
            elif category == "outreach":
                open_outreach_modal(trigger_id, client)
        except (KeyError, TypeError) as e:
            logger.error(
                f"Error parsing initial category submission: {e}\n{body['view']['state']['values']}"
            )

    @app.view("mech-categories-identifier")
    def handle_mech_categories_submission(ack, body, logger, client):
        """Handles submission of the mechanical category selection."""
        ack()
        try:
            trigger_id = body["trigger_id"]
            values = body["view"]["state"]["values"]
            m_category = values["mech_category_block"]["mech_category_select_action"][
                "selected_option"
            ]["value"]
            open_mech_modal(trigger_id, client, m_category)
        except (KeyError, TypeError) as e:
            logger.error(
                f"Error parsing mech category submission: {e}\n{body['view']['state']['values']}"
            )

    @app.view("prog-categories-identifier")
    def handle_prog_categories_submission(ack, body, logger, client):
        """Handles submission of the programming category selection."""
        ack()
        try:
            trigger_id = body["trigger_id"]
            values = body["view"]["state"]["values"]
            p_category = values["prog_category_block"]["prog_category_select_action"][
                "selected_option"
            ]["value"]
            open_prog_modal(trigger_id, client, p_category)
        except (KeyError, TypeError) as e:
            logger.error(
                f"Error parsing prog category submission: {e}\n{body['view']['state']['values']}"
            )

    @app.view("mech-modal-identifier")
    def handle_mech_modal_submission(ack, body, logger, client):
        """Handles the submission of the mechanical entry modal."""
        ack()
        try:
            entry_number = hkl.load("entrys")
            entry_number += 1
            hkl.dump(entry_number, "entrys")

            submitting_user_id = body["user"]["id"]
            values = body["view"]["state"]["values"]

            m_category = body["view"]["private_metadata"]

            user_ids = values["users_block"]["multi_users_select-action"][
                "selected_users"
            ]
            what_you_did = values["did_block"]["did_input"]["value"]
            what_you_learned = values["learned_block"]["learned_input"]["value"]
            milestone = (
                values["milestone_block"]["radio_buttons-action"]["selected_option"][
                    "value"
                ]
                == "yes"
            )
            files = values["files_block"]["file_input_action"].get(
                "files", []
            )  # Use .get for safety

            user_info_list = [
                client.users_info(user=uid)["user"]["real_name"]
                for uid in user_ids
                if client.users_info(user=uid)["ok"]
            ]
            submitting_user_name = client.users_info(user=submitting_user_id)["user"][
                "real_name"
            ]

            entry_time = datetime.now(timezone(timedelta(hours=-7))).strftime("%c")

            submission_data = {
                "is_new_project": False,
                "project_name": m_category,
                "category": "mechanical",
                "entry_id": entry_number,
                "entry_time": entry_time,
                "submitting_user": submitting_user_name,
                "selected_users": user_info_list,
                "what_did": what_you_did,
                "what_learned": what_you_learned,
                "milestone": milestone,
                "files": [
                    {"file_name": f["name"], "file_url": f["url_private"]}
                    for f in files
                ],
            }

            with open("submission_data.json", "w") as f:
                json.dump(submission_data, f, indent=4)

            send_done_message(client, submitting_user_name, entry_time)
            run_upload()
            send_confirmation_message(client, "C07QFDDS9QW", "API Upload successful :)")
            send_mechanical_update(
                client, user_info_list, what_you_did, [f["url_private"] for f in files]
            )
        except Exception as e:
            logger.error(f"Error handling mechanical submission: {e}")
            send_confirmation_message(
                client, body["user"]["id"], f"An error occurred: {e}"
            )

    @app.view("prog-modal-identifier")
    def handle_prog_modal_submission(ack, body, logger, client):
        """Handles the submission of the programming entry modal."""
        ack()
        try:
            entry_number = hkl.load("entrys")
            entry_number += 1
            hkl.dump(entry_number, "entrys")

            submitting_user_id = body["user"]["id"]
            values = body["view"]["state"]["values"]

            p_category = body["view"]["private_metadata"]

            user_ids = values["users_block"]["multi_users_select-action"][
                "selected_users"
            ]
            what_you_did = values["did_block"]["did_input"]["value"]
            what_you_learned = values["learned_block"]["learned_input"]["value"]
            milestone = (
                values["milestone_block"]["radio_buttons-action"]["selected_option"][
                    "value"
                ]
                == "yes"
            )

            user_info_list = [
                client.users_info(user=uid)["user"]["real_name"]
                for uid in user_ids
                if client.users_info(user=uid)["ok"]
            ]
            submitting_user_name = client.users_info(user=submitting_user_id)["user"][
                "real_name"
            ]

            entry_time = datetime.now(timezone(timedelta(hours=-7))).strftime("%c")

            submission_data = {
                "is_new_project": False,
                "project_name": p_category,
                "category": "programming",
                "entry_id": entry_number,
                "entry_time": entry_time,
                "submitting_user": submitting_user_name,
                "selected_users": user_info_list,
                "what_did": what_you_did,
                "what_learned": what_you_learned,
                "milestone": milestone,
                "files": [],
            }

            with open("submission_data.json", "w") as f:
                json.dump(submission_data, f, indent=4)

            send_done_message(client, submitting_user_name, entry_time)
            run_upload()
            send_confirmation_message(client, "C07QFDDS9QW", "API Upload successful :)")
            send_programming_update(client, user_info_list, what_you_did)
        except Exception as e:
            logger.error(f"Error handling programming submission: {e}")
            send_confirmation_message(
                client, body["user"]["id"], f"An error occurred: {e}"
            )

    @app.view("outreach-modal-identifier")
    def handle_outreach_submission(ack, body, logger, client):
        """Handles the submission of the outreach modal."""
        ack()
        values = body["view"]["state"]["values"]

        name = values["name_block"]["name_input"]["value"]
        date = values["date_block"]["datepicker"]["selected_date"]
        user_ids = values["users_block"]["multi_users_select-action"]["selected_users"]
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

        try:
            result = outreach_upload(submission_data, client)
            send_confirmation_message(
                client,
                "C07QFDDS9QW",
                f"Outreach event '{name}' logged successfully. Cells updated: {result}",
            )
        except Exception as e:
            logger.error(f"Error in outreach submission: {e}")
            send_confirmation_message(
                client, "C07QFDDS9QW", f"Error logging outreach event: {e}"
            )

    @app.view("scout-modal-identifier")
    def handle_scout_submission(ack, body, logger, client):
        """Handles the submission of the scouting modal."""
        ack()
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

        all_teams = get_all_teams()
        team_name = next(
            (team[0] for team in all_teams if team[1] == team_number), "Unknown Team"
        )

        new_row = [
            submitting_user,
            team_number,
            team_name,
            values["robot_type_block"]["robot_type_action"]["selected_option"]["value"],
            values["spec_auto_block"]["spec_auto_action"]["selected_option"]["value"],
            values["sample_auto_block"]["sample_auto_action"]["selected_option"][
                "value"
            ],
            values["spec_tele_block"]["spec_tele_action"]["selected_option"]["value"],
            values["sample_tele_block"]["sample_tele_action"]["selected_option"][
                "value"
            ],
            values["ascent_block"]["ascent_action"]["selected_option"]["value"],
            values["contact_block"]["contact_action"]["value"],
            values["notes_block"]["notes_action"]["value"],
        ]

        try:
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
                "C07QFDDS9QW",
                f"Error saving scout data for team {team_number}: {e}",
            )
