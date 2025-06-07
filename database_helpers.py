import os
import psycopg2
import json


def connect_from_env():
    """
    Connects to the PostgreSQL database using credentials
    stored in environment variables.
    """
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
        )
        print("Successfully connected to the PostgreSQL server.")
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"Error connecting to PostgreSQL: {error}")
        return None


def convert_array_to_pg_format(arr):
    """Converts a Python list to a PostgreSQL array string format."""
    return "{" + ",".join(f'"{item}"' for item in arr) + "}"


def enter_data(data_file="submission_data.json"):
    """
    Reads a submission data JSON file and inserts the data into the database.
    """
    conn = connect_from_env()
    if not conn:
        print("Database connection failed. Aborting data entry.")
        return

    try:
        with open(data_file, "r") as f:
            data_json = json.load(f)

        with conn.cursor() as cur:
            # Note: The original app had logic for creating a new project.
            # This is hardcoded to False for now as per the simplified flow.
            if data_json.get("is_new_project"):
                command = "SELECT create_project(%s::text, %s::text[]);"
                # The category needs to be in PostgreSQL array format
                category_array = convert_array_to_pg_format(
                    [data_json.get("category", "general")]
                )
                cur.execute(command, (data_json["project_name"], category_array))

            # Add users if they don't exist (original app assumed this)
            for user in data_json.get("selected_users", []):
                # This is a simplified version of the original app's user creation
                # A more robust version would check if the user exists first.
                cur.execute("SELECT add_user(%s, 'pass');", (user,))

            # Create the main engineering notebook entry
            command = """
                SELECT create_entry(
                    %s::text,
                    %s::text[],
                    %s::text[],
                    %s::text[],
                    %s::text[],
                    %s::text,
                    %s::boolean
                );
            """

            # Prepare arrays for the stored procedure
            selected_users_pg = convert_array_to_pg_format(data_json["selected_users"])
            # The original app had a separate 'category' and project 'tags'
            # We'll use the main category for both for simplicity in this refactor.
            tags_pg = convert_array_to_pg_format([data_json.get("category")])

            # The files array should be a list of lists/tuples for the stored proc
            # e.g., [['file1.jpg', 'url1'], ['file2.png', 'url2']]
            files_pg = [
                [f.get("file_name"), f.get("file_url")]
                for f in data_json.get("files", [])
            ]

            # The data array contains 'what you did' and 'what you learned'
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
        print(f"An error occurred during data entry: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
