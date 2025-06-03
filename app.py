import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# Load environment variables
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize Flask and Slack apps
flask_app = Flask(__name__)
app = App(
    token=os.environ.get("SLACK_TOKEN"),
    signing_secret=os.environ.get("SIGNING_SECRET"),
)
handler = SlackRequestHandler(app)

application = flask_app

# Import and register handlers
from slack_commands import register_commands
from slack_events import register_events

register_commands(app)
register_events(app)


# Flask routes
@flask_app.route("/slack/events", methods=["POST"])
def slack_events_handler():
    """Handles incoming Slack events."""
    return handler.handle(request)


@flask_app.route("/", methods=["POST", "GET"])
def health_check():
    """A simple health check endpoint."""
    return "OK", 200


# Start the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, debug=True)
