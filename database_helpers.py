import os
import psycopg2
import json


def connect_from_env():
    """
    Connects to the PostgreSQL database using credentials
    stored in environment variables, enforcing an SSL connection.
    """
    try:
        # Heroku requires SSL connections for its Postgres databases.
        # sslmode='require' ensures that the connection is encrypted.
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            sslmode="require",
        )
        print("Successfully connected to the PostgreSQL server.")
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"Error connecting to PostgreSQL: {error}")
        # Return the error object to be handled by the calling function
        raise error


def convert_array_to_pg_format(arr):
    """Converts a Python list to a PostgreSQL array string format."""
    return "{" + ",".join(f'"{item}"' for item in arr) + "}"


def enter_data(data_file, client, submitting_user):
    """
    Reads a submission data JSON file and inserts the data into the database.
    Reports errors back to a Slack channel.
    """
    conn = None
    try:
        conn = connect_from_env()
        if not conn:
            # The exception from connect_from_env will be caught by the outer block
            return

        with open(data_file, "r") as f:
            data_json = json.load(f)

        with conn.cursor() as cur:
            if data_json.get("is_new_project"):
                command = "SELECT create_project(%s::text, %s::text[]);"
                category_array = convert_array_to_pg_format(
                    [data_json.get("category", "general")]
                )
                cur.execute(command, (data_json["project_name"], category_array))

            for user in data_json.get("selected_users", []):
                cur.execute("SELECT add_user(%s, 'pass');", (user,))

            command = """
                SELECT create_entry(
                    %s::text, %s::text[], %s::text[],
                    %s::text[], %s::text[], %s::text, %s::boolean
                );
            """
            selected_users_pg = convert_array_to_pg_format(data_json["selected_users"])
            tags_pg = convert_array_to_pg_format([data_json.get("category")])
            files_pg = [
                [f.get("file_name"), f.get("file_url")]
                for f in data_json.get("files", [])
            ]
            data_pg = convert_array_to_pg_format(
                [data_json["what_did"], data_json["what_learned"]]
            )

            cur.execute(
                command,
                (
                    data_json["submitting_user"],
                    selected_users_pg,
                    tags_pg,
                    files_pg,
                    data_pg,
                    data_json["project_name"],
                    data_json["milestone"],
                ),
            )
            conn.commit()
            print("Successfully executed create_entry command.")

    except Exception as e:
        error_message = f"An error occurred during the database upload process for an entry by {submitting_user}.\n\n*Error:*\n```{e}```"
        print(f"Reporting error to Slack: {error_message}")
        if client:
            client.chat_postMessage(channel="#engineering-notebook", text=error_message)
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
