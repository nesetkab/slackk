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
        return conn
    except Exception as error:
        print(f"Error connecting to PostgreSQL: {error}")
        raise error


def get_or_create_user_id(cursor, user_name):
    """
    Finds a user by name. If they don't exist, creates them.
    Returns the user's ID.
    """
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

            all_user_names = set(
                data.get("selected_users", []) + [data.get("submitting_user")]
            )
            user_id_map = {
                name: get_or_create_user_id(cur, name) for name in all_user_names
            }

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

            author_ids = [user_id_map[name] for name in data.get("selected_users", [])]
            for user_id in author_ids:
                cur.execute(
                    "INSERT INTO entry_author (entry_id, user_id) VALUES (%s, %s);",
                    (entry_id, user_id),
                )

            category = data.get("category")
            if category:
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

                cur.execute(
                    "INSERT INTO entry_tags (entry_id, tag_id) VALUES (%s, %s);",
                    (entry_id, tag_id),
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
            conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()

        error_message = f"A database error occurred for an entry by {submitting_user}. The transaction has been rolled back.\n\n*Error:*\n```{e}```"
        if client:
            client.chat_postMessage(channel="#engineering-notebook", text=error_message)
    finally:
        if conn:
            conn.close()


def fetch_all_entries():
    """
    Fetches all entries and their related data (authors, tags, images)
    from the database for display on the website.
    """
    conn = None
    entries = []
    try:
        conn = connect_from_env()
        with conn.cursor() as cur:
            # This query joins all tables and aggregates related data into arrays.
            cur.execute("""
                SELECT
                    e.entry_id,
                    e.entry_data,
                    e.is_milestone,
                    e.creator_name,
                    e.created_at,
                    p.project_name,
                    array_agg(DISTINCT u.user_name) FILTER (WHERE u.user_name IS NOT NULL) as authors,
                    array_agg(DISTINCT t.tag_name) FILTER (WHERE t.tag_name IS NOT NULL) as tags,
                    array_agg(DISTINCT i.img_data) FILTER (WHERE i.img_data IS NOT NULL) as images
                FROM
                    entries e
                LEFT JOIN project_entries pe ON e.entry_id = pe.entry_id
                LEFT JOIN projects p ON pe.project_id = p.project_id
                LEFT JOIN entry_author ea ON e.entry_id = ea.entry_id
                LEFT JOIN users u ON ea.user_id = u.user_id
                LEFT JOIN entry_tags et ON e.entry_id = et.entry_id
                LEFT JOIN tags t ON et.tag_id = t.tag_id
                LEFT JOIN entry_imgs ei ON e.entry_id = ei.entry_id
                LEFT JOIN img i ON ei.img_id = i.img_id
                GROUP BY
                    e.entry_id, p.project_name
                ORDER BY
                    e.created_at DESC;
            """)

            # Fetch all rows from the query
            rows = cur.fetchall()

            # Process rows into a list of dictionaries
            for row in rows:
                entries.append(
                    {
                        "id": row[0],
                        "data": row[1],
                        "is_milestone": row[2],
                        "creator": row[3],
                        "created_at": row[4].strftime("%B %d, %Y - %I:%M %p"),
                        "project": row[5],
                        "authors": row[6] or [],
                        "tags": row[7] or [],
                        "images": row[8] or [],
                    }
                )
        return entries
    except Exception as e:
        print(f"An error occurred while fetching entries: {e}")
        return []  # Return an empty list on error
    finally:
        if conn:
            conn.close()
