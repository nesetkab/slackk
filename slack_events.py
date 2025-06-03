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
    send_done_message,
    send_confirmation_message,
    send_programming_update,
    send_mechanical_update,
    handle_scout_submission as process_scout_submission,
    handle_outreach_submission as process_outreach_submission,
)


def register_events(app):
    """
    Registers all Slack event handlers.
    """

    @app.action("category_action_id")
    def handle_category_action(ack, body, logger):
        """Handles the category selection action."""
        ack()
        logger.info(body)

    @app.view("modal-identifier")
    def handle_modal_submission(ack, body, logger, client):
        """Handles the submission of the initial new entry modal."""
        ack()
        trigger_id = body["trigger_id"]
        submitted_data = body["view"]["state"]["values"]
        category = ""
        for block_id, block_data in submitted_data.items():
            for action_id, action_data in block_data.items():
                if action_data["type"] == "radio_buttons":
                    category = action_data["selected_option"]["value"]

        if category == "mech":
            open_mech_categories(trigger_id, client)
        elif category == "prog":
            open_prog_categories(trigger_id, client)
        elif category == "outreach":
            open_outreach_modal(trigger_id, client)

    @app.view("outreach-modal-identifier")
    def handle_outreach_submission(ack, body, logger, client):
        """Handles the submission of the outreach modal."""
        ack()
        process_outreach_submission(body, client)

    @app.view("prog-categories-identifier")
    def handle_prog_categories_submission(ack, body, logger, client):
        """Handles the submission of the programming categories modal."""
        ack()
        trigger_id = body["trigger_id"]
        submitted_data = body["view"]["state"]["values"]
        p_category = ""
        for block_id, block_data in submitted_data.items():
            for action_id, action_data in block_data.items():
                if action_data["type"] == "static_select":
                    p_category = action_data["selected_option"]["value"]
        open_prog_modal(trigger_id, client, p_category)

    @app.action("p_button")
    def handle_p_button_action(ack, body, logger, client):
        """Handles the new programming category button action."""
        ack()
        # In a real application, you might open a new modal here to create a new category.
        logger.info("New programming category button clicked.")

    @app.view("prog-modal-identifier")
    def handle_prog_modal_submission(ack, body, logger, client):
        """Handles the submission of the programming entry modal."""
        ack()
        user_id = body["user"]["id"]
        submitted_data = body["view"]["state"]["values"]
        entry_number = hkl.load("entrys") + 1
        hkl.dump(entry_number, "entrys")
        entry_time = datetime.now(timezone(timedelta(hours=-7))).strftime("%c")
        user_response = client.users_info(user=user_id)
        submitting_user = (
            user_response["user"]["real_name"] if user_response["ok"] else ""
        )

        user_ids = []
        for block_id, block_data in submitted_data.items():
            for action_id, action_data in block_data.items():
                if action_data["type"] == "multi_users_select":
                    user_ids = action_data["selected_users"]

        user_info = [
            client.users_info(user=uid)["user"]["real_name"]
            for uid in user_ids
            if client.users_info(user=uid)["ok"]
        ]

        text_responses = [
            action_data["value"]
            for block_id, block_data in submitted_data.items()
            for action_id, action_data in block_data.items()
            if action_data["type"] == "plain_text_input"
        ]
        what_you_did, what_you_learned = text_responses

        milestone = False
        for block_id, block_data in submitted_data.items():
            for action_id, action_data in block_data.items():
                if action_data["type"] == "radio_buttons":
                    milestone = action_data["selected_option"]["value"] == "yes"

        submission = {
            "is_new_project": False,  # This seems to be hardcoded or from a global variable before
            "project_name": "default_prog_category",  # This should be passed from the previous modal
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

        with open("submission_data.json", "w") as f:
            json.dump(submission, f, indent=4)

        send_done_message(client, submitting_user, entry_time)
        run_upload()
        send_confirmation_message(client)
        send_programming_update(client, user_info, what_you_did, [])

    @app.view("mech-categories-identifier")
    def handle_mech_categories_submission(ack, body, logger, client):
        """Handles the submission of the mechanical categories modal."""
        ack()
        trigger_id = body["trigger_id"]
        submitted_data = body["view"]["state"]["values"]
        m_category = ""
        for block_id, block_data in submitted_data.items():
            for action_id, action_data in block_data.items():
                if action_data["type"] == "static_select":
                    m_category = action_data["selected_option"]["value"]
        open_mech_modal(trigger_id, client, m_category)

    @app.action("m_button")
    def handle_m_button_action(ack, body, logger, client):
        """Handles the new mechanical category button action."""
        ack()
        # In a real application, you might open a new modal here to create a new category.
        logger.info("New mechanical category button clicked.")

    @app.view("mech-modal-identifier")
    def handle_mech_modal_submission(ack, body, logger, client):
        """Handles the submission of the mechanical entry modal."""
        ack()
        user_id = body["user"]["id"]
        submitted_data = body["view"]["state"]["values"]
        entry_number = hkl.load("entrys") + 1
        hkl.dump(entry_number, "entrys")
        entry_time = datetime.now(timezone(timedelta(hours=-7))).strftime("%c")
        user_response = client.users_info(user=user_id)
        submitting_user = (
            user_response["user"]["real_name"] if user_response["ok"] else ""
        )

        user_ids = []
        for block_id, block_data in submitted_data.items():
            for action_id, action_data in block_data.items():
                if action_data["type"] == "multi_users_select":
                    user_ids = action_data["selected_users"]

        user_info = [
            client.users_info(user=uid)["user"]["real_name"]
            for uid in user_ids
            if client.users_info(user=uid)["ok"]
        ]

        text_responses = [
            action_data["value"]
            for block_id, block_data in submitted_data.items()
            for action_id, action_data in block_data.items()
            if action_data["type"] == "plain_text_input"
        ]
        what_you_did, what_you_learned = text_responses

        milestone = False
        for block_id, block_data in submitted_data.items():
            for action_id, action_data in block_data.items():
                if action_data["type"] == "radio_buttons":
                    milestone = action_data["selected_option"]["value"] == "yes"

        files = submitted_data["input_block_id"]["file_input_action_id_1"]["files"]

        submission = {
            "is_new_project": False,  # This seems to be hardcoded or from a global variable before
            "project_name": "default_mech_category",  # This should be passed from the previous modal
            "category": "mechanical",
            "entry_id": entry_number,
            "entry_time": entry_time,
            "submitting_user": submitting_user,
            "selected_users": user_info,
            "what_did": what_you_did,
            "what_learned": what_you_learned,
            "milestone": milestone,
            "files": [
                {"file_name": f["name"], "file_url": f["url_private"]} for f in files
            ],
        }

        with open("submission_data.json", "w") as f:
            json.dump(submission, f, indent=4)

        send_done_message(client, submitting_user, entry_time)
        run_upload()
        send_confirmation_message(client)
        send_mechanical_update(
            client, user_info, what_you_did, [f["url_private"] for f in files]
        )

    @app.view("scout-modal-identifier")
    def handle_scout_submission_event(ack, body, logger, client):
        """Handles the submission of the scout modal."""
        ack()
        process_scout_submission(body, logger, client)
