import os
import psycopg2
import json


def connect_from_env():
    """Connects to the PostgreSQL database from environment variables."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            sslmode="require",
        )
        return conn
    except Exception as error:
        print(f"Error connecting to PostgreSQL: {error}")
        raise error


def get_or_create_user_id(cursor, user_name):
    """Finds or creates a user and returns their ID."""
    cursor.execute("SELECT user_id FROM users WHERE user_name = %s;", (user_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute(
            "INSERT INTO users (user_name, user_password) VALUES (%s, %s) RETURNING user_id;",
            (user_name, "default_pass"),
        )
        return cursor.fetchone()[0]


def get_or_create_project_id(cursor, project_name):
    """Finds or creates a project and returns its ID."""
    cursor.execute(
        "SELECT project_id FROM projects WHERE project_name = %s;", (project_name,)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute(
            "INSERT INTO projects (project_name) VALUES (%s) RETURNING project_id;",
            (project_name,),
        )
        return cursor.fetchone()[0]


def enter_data(data, client, submitting_user):
    """Inserts a new entry into the database using a dictionary of data."""
    conn = None
    try:
        conn = connect_from_env()
        with conn.cursor() as cur:
            all_user_names = set(
                data.get("selected_users", []) + [data.get("submitting_user")]
            )
            user_id_map = {
                name: get_or_create_user_id(cur, name) for name in all_user_names
            }

            project_id = get_or_create_project_id(cur, data["project_name"])

            entry_data_pg = [data.get("what_did", ""), data.get("what_learned", "")]
            cur.execute(
                "INSERT INTO entries (entry_data, creator_name) VALUES (%s, %s) RETURNING entry_id;",
                (entry_data_pg, data.get("submitting_user")),
            )
            entry_id = cur.fetchone()[0]

            author_ids = [user_id_map[name] for name in data.get("selected_users", [])]
            for user_id in author_ids:
                cur.execute(
                    "INSERT INTO entry_author (entry_id, user_id) VALUES (%s, %s);",
                    (entry_id, user_id),
                )

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

            cur.execute(
                "INSERT INTO project_entries (project_id, entry_id) VALUES (%s, %s);",
                (project_id, entry_id),
            )
            conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        error_message = f"DB Error by {submitting_user}: Transaction rolled back.\n*Error:*\n```{e}```"
        if client:
            client.chat_postMessage(channel="#engineering-notebook", text=error_message)
    finally:
        if conn:
            conn.close()


def fetch_all_entries():
    """Fetches all entries and their related data for the website."""
    conn = None
    try:
        conn = connect_from_env()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.entry_id, e.entry_data, e.creator_name, e.created_at, p.project_name,
                       array_agg(DISTINCT u.user_name) FILTER (WHERE u.user_name IS NOT NULL) as authors,
                       array_agg(DISTINCT i.img_data) FILTER (WHERE i.img_data IS NOT NULL) as images
                FROM entries e
                LEFT JOIN project_entries pe ON e.entry_id = pe.entry_id
                LEFT JOIN projects p ON pe.project_id = p.project_id
                LEFT JOIN entry_author ea ON e.entry_id = ea.entry_id
                LEFT JOIN users u ON ea.user_id = u.user_id
                LEFT JOIN entry_imgs ei ON e.entry_id = ei.entry_id
                LEFT JOIN img i ON ei.img_id = i.img_id
                GROUP BY e.entry_id, p.project_name
                ORDER BY e.created_at DESC;
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "data": row[1],
                    "creator": row[2],
                    "created_at": row[3].strftime("%B %d, %Y - %I:%M %p"),
                    "project": row[4],
                    "authors": row[5] or [],
                    "images": row[6] or [],
                }
                for row in rows
            ]
    except Exception as e:
        print(f"An error occurred while fetching entries: {e}")
        return []
    finally:
        if conn:
            conn.close()


def fetch_all_projects():
    """Fetches a list of all project names."""
    conn = None
    try:
        conn = connect_from_env()
        with conn.cursor() as cur:
            cur.execute("SELECT project_name FROM projects ORDER BY project_name;")
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"An error occurred while fetching projects: {e}")
        return []
    finally:
        if conn:
            conn.close()


def delete_entry(entry_id):
    """Deletes a specific entry and its linked data from the database."""
    conn = None
    try:
        conn = connect_from_env()
        with conn.cursor() as cur:
            # The ON DELETE CASCADE in the schema will handle cleaning up junction tables.
            cur.execute("DELETE FROM entries WHERE entry_id = %s;", (entry_id,))
            conn.commit()
    except Exception as e:
        print(f"Error deleting entry {entry_id}: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
