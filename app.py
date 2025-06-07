import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, render_template, session, redirect, url_for
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from database_helpers import fetch_all_entries
from functools import wraps

# Load environment variables
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize Flask and Slack apps
flask_app = Flask(__name__)
# A secret key is required for Flask session management
flask_app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "a-strong-default-secret-key-for-dev"
)

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


# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# --- Slack Bot Routes ---
@flask_app.route("/slack/events", methods=["POST"])
def slack_events_handler():
    """Handles incoming Slack events."""
    return handler.handle(request)


# --- Web Viewer Routes ---
@flask_app.route("/")
def index():
    """Redirects the root URL to the entries page."""
    return redirect(url_for("view_entries"))


@flask_app.route("/login", methods=["GET", "POST"])
def login():
    """Handles the login process."""
    error = None
    if request.method == "POST":
        # The password should be stored in an environment variable
        site_password = os.environ.get("SITE_PASSWORD")
        if request.form["password"] == site_password:
            session["logged_in"] = True
            return redirect(url_for("view_entries"))
        else:
            error = "Invalid password provided. Please try again."
    return render_template("login.html", error=error)


@flask_app.route("/entries")
@login_required
def view_entries():
    """Fetches all entries from the database and renders the webpage."""
    all_entries = fetch_all_entries()
    return render_template("entries.html", entries=all_entries)


@flask_app.route("/logout")
def logout():
    """Logs the user out."""
    session.pop("logged_in", None)
    return redirect(url_for("login"))


# Start the application for local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, debug=True)
