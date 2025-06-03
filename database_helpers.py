import psycopg2
from configparser import ConfigParser
import json


def load_db_config(filename="database.ini", section="postgresql"):
    """Loads database configuration from a file."""
    parser = ConfigParser()
    parser.read(filename)
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f"Section {section} not found in the {filename} file")
    return config


def connect_to_db():
    """Connects to the PostgreSQL database."""
    try:
        config = load_db_config()
        print("Connecting to the PostgreSQL server...")
        conn = psycopg2.connect(**config)
        print("Connected to the PostgreSQL server.")
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
        return None


def enter_data_into_db(data_file):
    """Enters data from a JSON file into the database."""
    conn = connect_to_db()
    if not conn:
        return

    with open(data_file, "r") as f:
        data_json = json.load(f)

    cur = conn.cursor()
    # ... (The rest of your database insertion logic from client_functions.py)
    # This would include the logic for creating projects, adding users, creating entries, etc.
    conn.commit()
    cur.close()
    conn.close()


# You can also move other database-related helper functions from client_functions.py here.
