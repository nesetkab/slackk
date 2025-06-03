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
)
from gsheet import outreach_upload


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
        # ... (logic from original app.py)

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
        logger.info("New programming category button clicked.")

    @app.view("prog-modal-identifier")
    def handle_prog_modal_submission(ack, body, logger, client):
        """Handles the submission of the programming entry modal."""
        ack()
        # ... (logic from original app.py)

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
        logger.info("New mechanical category button clicked.")

    @app.view("mech-modal-identifier")
    def handle_mech_modal_submission(ack, body, logger, client):
        """Handles the submission of the mechanical entry modal."""
        ack()
        # ... (logic from original app.py)

    @app.view("scout-modal-identifier")
    def handle_scout_submission_event(ack, body, logger, client):
        """Handles the submission of the scout modal."""
        ack()
        # ... (logic from original app.py)
