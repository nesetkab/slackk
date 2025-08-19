import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from database_helpers import (
    get_db_connection,
    get_all_entries,
    get_entry_by_id,
    update_entry_in_db,
    delete_entry_from_db,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "a_default_secret_key")
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Define allowed extensions for file uploads, now including video formats
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "mkv", "webm"}

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check against environment variables
        env_username = os.environ.get("FLASK_USERNAME")
        env_password_hash = os.environ.get("FLASK_PASSWORD_HASH")

        if username == env_username and check_password_hash(
            env_password_hash, password
        ):
            session["logged_in"] = True
            return redirect(url_for("entries"))
        else:
            flash("Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Handle user logout."""
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
def index():
    """Redirect to login page if not logged in, otherwise show entries."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return redirect(url_for("entries"))


@app.route("/entries")
def entries():
    """Display all entries."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    sort_by = request.args.get("sort_by", "timestamp")
    sort_order = request.args.get("sort_order", "desc")

    all_entries = get_all_entries(sort_by, sort_order)
    return render_template(
        "entries.html", entries=all_entries, sort_by=sort_by, sort_order=sort_order
    )


@app.route("/edit/<int:entry_id>", methods=["GET", "POST"])
def edit_entry(entry_id):
    """Handle editing of a specific entry."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    entry = get_entry_by_id(entry_id)
    if not entry:
        return "Entry not found", 404

    if request.method == "POST":
        author_name = request.form["author_name"]
        entry_text = request.form["entry_text"]
        image_filename = entry["image_filename"]

        # Handle file upload
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename != "" and allowed_file(file.filename):
                # If a new file is uploaded, save it and update the filename
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_filename = filename
            elif file and file.filename != "" and not allowed_file(file.filename):
                flash(
                    "Invalid file type. Allowed types are: "
                    + ", ".join(ALLOWED_EXTENSIONS)
                )
                return render_template("edit_entry.html", entry=entry)

        update_entry_in_db(entry_id, author_name, entry_text, image_filename)
        return redirect(url_for("entries"))

    return render_template("edit_entry.html", entry=entry)


@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):
    """Handle deletion of a specific entry."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    delete_entry_from_db(entry_id)
    return redirect(url_for("entries"))


if __name__ == "__main__":
    app.run(debug=True)
