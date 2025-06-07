import os
import psycopg2


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


def drop_all_tables(conn):
    """Drops all tables in the correct order to respect dependencies."""
    tables_to_drop = [
        "project_status",
        "project_tags",
        "project_entries",
        "entry_imgs",
        "entry_tags",
        "entry_author",
        "projects",
        "img",
        "tags",
        "entries",
        "users",
        "status_",
    ]
    with conn.cursor() as cur:
        for table in tables_to_drop:
            try:
                print(f"Dropping table {table}...")
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            except psycopg2.Error as e:
                print(f"Could not drop table {table}. It might not exist. Error: {e}")
        conn.commit()
        print("All existing tables dropped successfully.")


def initialize_database(conn):
    """Creates all necessary tables with the updated schema."""
    # Note: 'is_milestone' has been removed from the 'entries' table.
    commands = [
        """CREATE TABLE IF NOT EXISTS users (user_id SERIAL PRIMARY KEY, user_name TEXT NOT NULL UNIQUE, user_password TEXT NOT NULL);""",
        """CREATE TABLE IF NOT EXISTS entries (entry_id SERIAL PRIMARY KEY, entry_data TEXT[], creator_name TEXT, created_at TIMESTAMPTZ DEFAULT NOW());""",
        """CREATE TABLE IF NOT EXISTS tags (tag_id SERIAL PRIMARY KEY, tag_name TEXT NOT NULL UNIQUE);""",
        """CREATE TABLE IF NOT EXISTS img (img_id SERIAL PRIMARY KEY, img_name TEXT, img_data TEXT, created_at TIMESTAMPTZ DEFAULT NOW());""",
        """CREATE TABLE IF NOT EXISTS projects (project_id SERIAL PRIMARY KEY, project_name TEXT NOT NULL UNIQUE);""",
        """CREATE TABLE IF NOT EXISTS status_ (status_id SERIAL PRIMARY KEY, status_name TEXT NOT NULL UNIQUE);""",
        """CREATE TABLE IF NOT EXISTS entry_author (entry_id INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE, user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE, PRIMARY KEY (entry_id, user_id));""",
        """CREATE TABLE IF NOT EXISTS entry_tags (entry_id INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE, tag_id INTEGER REFERENCES tags(tag_id) ON DELETE CASCADE, PRIMARY KEY (entry_id, tag_id));""",
        """CREATE TABLE IF NOT EXISTS entry_imgs (entry_id INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE, img_id INTEGER REFERENCES img(img_id) ON DELETE CASCADE, PRIMARY KEY (entry_id, img_id));""",
        """CREATE TABLE IF NOT EXISTS project_entries (project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE, entry_id INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE, PRIMARY KEY (project_id, entry_id));""",
        """CREATE TABLE IF NOT EXISTS project_tags (project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE, tag_id INTEGER REFERENCES tags(tag_id) ON DELETE CASCADE, PRIMARY KEY (project_id, tag_id));""",
        """CREATE TABLE IF NOT EXISTS project_status (project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE, status_id INTEGER REFERENCES status_(status_id) ON DELETE CASCADE, PRIMARY KEY (project_id, status_id));""",
    ]
    with conn.cursor() as cur:
        print("Creating new tables...")
        for command in commands:
            cur.execute(command)
        conn.commit()
        print("Database schema initialized successfully.")


if __name__ == "__main__":
    if (
        input(
            "Are you sure you want to completely WIPE and RESET the database? (yes/no): "
        ).lower()
        == "yes"
    ):
        conn = None
        try:
            conn = connect_from_env()
            drop_all_tables(conn)
            initialize_database(conn)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if conn:
                conn.close()
    else:
        print("Database reset cancelled.")
