import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, render_template
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from database_helpers import fetch_all_entries

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

# --- Slack Bot Routes ---


@flask_app.route("/slack/events", methods=["POST"])
def slack_events_handler():
    """Handles incoming Slack events."""
    return handler.handle(request)


# --- Web Viewer Routes ---


@flask_app.route("/")
def index():
    """Redirects the root URL to the entries page."""
    from flask import redirect, url_for

    return redirect(url_for("view_entries"))


@flask_app.route("/entries")
def view_entries():
    """Fetches all entries from the database and renders the webpage."""
    all_entries = fetch_all_entries()
    return render_template("entries.html", entries=all_entries)


# Start the application for local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, debug=True)
