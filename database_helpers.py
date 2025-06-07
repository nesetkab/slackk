import os
import psycopg2
import json


def connect_from_env():
    """
    Connects to the PostgreSQL database using credentials
    stored in environment variables, enforcing an SSL connection.
    """
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            sslmode="require",
        )
        print("Successfully connected to the PostgreSQL server.")
        return conn
    except Exception as error:
        print(f"Error connecting to PostgreSQL: {error}")
        raise error


def get_or_create_user_id(cursor, user_name):
    """
    Finds a user by name. If they don't exist, creates them.
    Returns the user's ID. Replaces the 'add_user' stored procedure.
    """
    cursor.execute("SELECT user_id FROM users WHERE user_name = %s;", (user_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        # User does not exist, create them with a default password
        cursor.execute(
            "INSERT INTO users (user_name, user_password) VALUES (%s, %s) RETURNING user_id;",
            (user_name, "default_pass"),
        )
        return cursor.fetchone()[0]


def enter_data(data_file, client, submitting_user):
    """
    Reads submission data and uses standard SQL transactions to insert it
    into the database, creating all necessary records and links.
    """
    conn = None
    try:
        conn = connect_from_env()
        with conn.cursor() as cur:
            with open(data_file, "r") as f:
                data = json.load(f)

            # Get IDs for all users involved, creating them if necessary
            all_user_names = set(
                data.get("selected_users", []) + [data.get("submitting_user")]
            )
            user_id_map = {
                name: get_or_create_user_id(cur, name) for name in all_user_names
            }

            # --- Insert the main entry ---
            # The 'data' column in the 'entries' table seems to expect a JSON-like array of strings
            entry_data_pg = [data.get("what_did", ""), data.get("what_learned", "")]

            cur.execute(
                """
                INSERT INTO entries (entry_data, is_milestone, creator_name)
                VALUES (%s, %s, %s) RETURNING entry_id;
                """,
                (
                    entry_data_pg,
                    data.get("milestone", False),
                    data.get("submitting_user"),
                ),
            )
            entry_id = cur.fetchone()[0]
            print(f"Created new entry with ID: {entry_id}")

            # --- Link authors to the new entry ---
            author_ids = [user_id_map[name] for name in data.get("selected_users", [])]
            for user_id in author_ids:
                cur.execute(
                    "INSERT INTO entry_author (entry_id, user_id) VALUES (%s, %s);",
                    (entry_id, user_id),
                )
            print(f"Linked {len(author_ids)} authors to entry {entry_id}")

            # --- Link tags (category) to the new entry ---
            category = data.get("category")
            if category:
                # Find tag by name, or create it if it doesn't exist
                cur.execute("SELECT tag_id FROM tags WHERE tag_name = %s;", (category,))
                tag_result = cur.fetchone()
                if tag_result:
                    tag_id = tag_result[0]
                else:
                    cur.execute(
                        "INSERT INTO tags (tag_name) VALUES (%s) RETURNING tag_id;",
                        (category,),
                    )
                    tag_id = cur.fetchone()[0]

                # Link the tag to the entry
                cur.execute(
                    "INSERT INTO entry_tags (entry_id, tag_id) VALUES (%s, %s);",
                    (entry_id, tag_id),
                )
                print(f"Linked tag '{category}' to entry {entry_id}")

            # --- Insert images and link them to the new entry ---
            for file_info in data.get("files", []):
                cur.execute(
                    "INSERT INTO img (img_name, img_data) VALUES (%s, %s) RETURNING img_id;",
                    (file_info.get("file_name"), file_info.get("file_url")),
                )
                img_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO entry_imgs (entry_id, img_id) VALUES (%s, %s);",
                    (entry_id, img_id),
                )
            print(
                f"Inserted and linked {len(data.get('files', []))} images to entry {entry_id}"
            )

            # --- Link entry to a project (simplified) ---
            # This assumes a project with the same name as the category exists
            project_name = data.get("project_name")
            if project_name:
                cur.execute(
                    "SELECT project_id FROM projects WHERE project_name = %s;",
                    (project_name,),
                )
                project_result = cur.fetchone()
                if project_result:
                    project_id = project_result[0]
                    cur.execute(
                        "INSERT INTO project_entries (project_id, entry_id) VALUES (%s, %s);",
                        (project_id, entry_id),
                    )
                    print(f"Linked entry {entry_id} to project '{project_name}'")

            # If all steps succeeded, commit the transaction
            conn.commit()
            print("Database transaction committed successfully.")

    except Exception as e:
        # If any error occurs, roll back the entire transaction
        if conn:
            conn.rollback()

        error_message = f"A database error occurred for an entry by {submitting_user}. The transaction has been rolled back.\n\n*Error:*\n```{e}```"
        print(f"Reporting error to Slack: {error_message}")
        if client:
            client.chat_postMessage(channel="#engineering-notebook", text=error_message)
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
