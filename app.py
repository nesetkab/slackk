import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, render_template, session, redirect, url_for, flash
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from database_helpers import (
    fetch_all_entries,
    delete_entry as db_delete_entry,
    fetch_single_entry,
    update_entry,
    fetch_all_projects,
)
from functools import wraps

# Load environment variables
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize Flask and Slack apps
flask_app = Flask(__name__)
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
    return handler.handle(request)


# --- Web Viewer Routes ---
@flask_app.route("/")
def index():
    return redirect(url_for("view_entries"))


@flask_app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
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
    all_entries = fetch_all_entries()
    entry_count = len(all_entries)
    return render_template("entries.html", entries=all_entries, entry_count=entry_count)


@flask_app.route("/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry_route(entry_id):
    db_delete_entry(entry_id)
    flash("Entry successfully deleted.", "success")
    return redirect(url_for("view_entries"))


@flask_app.route("/edit/<int:entry_id>")
@login_required
def edit_entry_route(entry_id):
    entry = fetch_single_entry(entry_id)
    projects = fetch_all_projects()
    if entry:
        return render_template("edit_entry.html", entry=entry, projects=projects)
    else:
        flash("Entry not found.", "error")
        return redirect(url_for("view_entries"))


@flask_app.route("/update/<int:entry_id>", methods=["POST"])
@login_required
def update_entry_route(entry_id):
    updated_data = {
        "what_did": request.form["what_did"],
        "what_learned": request.form["what_learned"],
        "project_name": request.form["project_name"],
    }
    update_entry(entry_id, updated_data)
    flash("Entry successfully updated.", "success")
    return redirect(url_for("view_entries"))


@flask_app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, debug=True)
