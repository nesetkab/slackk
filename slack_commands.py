from slack_helpers import (
    open_outreach_modal,
    open_new_entry_modal,
    send_ftc_team_info,
    update_oprs_and_notify,
    open_scout_modal,
)


def register_commands(app):
    """
    Registers all Slack command handlers.
    """

    @app.command("/help")
    def handle_help_command(ack, body, client):
        """Handles the /help command."""
        ack()
        client.chat_postMessage(channel=body["channel_id"], text="Help is on the way!")

    @app.command("/updateoprs")
    def handle_update_oprs_command(ack, body, logger, client):
        """Handles the /updateoprs command to update team OPRs."""
        ack()
        update_oprs_and_notify(body, logger, client)

    @app.command("/scout")
    def handle_scout_command(ack, body, logger, client):
        """Handles the /scout command to open the scouting modal."""
        ack()
        open_scout_modal(body["trigger_id"], client, logger)

    @app.command("/ftc")
    def handle_ftc_command(ack, body, logger, client):
        """Handles the /ftc command to get information about an FTC team."""
        ack()
        send_ftc_team_info(body, client)

    @app.command("/en")
    def handle_en_command(ack, body, logger, client):
        """Handles the /en command to create a new engineering notebook entry."""
        ack()
        open_new_entry_modal(body["trigger_id"], client)

    @app.command("/outreach")
    def handle_outreach_command(ack, body, logger, client):
        """Handles the /outreach command for logging outreach events."""
        ack()
        open_outreach_modal(body["trigger_id"], client)
