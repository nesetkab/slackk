import os
import psycopg2


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


def initialize_database():
    """
    Connects to the database and creates all necessary tables and relations
    if they don't already exist.
    """
    commands = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            user_name TEXT NOT NULL UNIQUE,
            user_password TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS entries (
            entry_id SERIAL PRIMARY KEY,
            entry_data TEXT[],
            is_milestone BOOLEAN DEFAULT FALSE,
            creator_name TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS tags (
            tag_id SERIAL PRIMARY KEY,
            tag_name TEXT NOT NULL UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS img (
            img_id SERIAL PRIMARY KEY,
            img_name TEXT,
            img_data TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS projects (
            project_id SERIAL PRIMARY KEY,
            project_name TEXT NOT NULL UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS status_ (
            status_id SERIAL PRIMARY KEY,
            status_name TEXT NOT NULL UNIQUE
        );
        """,
        # --- Junction Tables ---
        """
        CREATE TABLE IF NOT EXISTS entry_author (
            entry_id INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
            PRIMARY KEY (entry_id, user_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS entry_tags (
            entry_id INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(tag_id) ON DELETE CASCADE,
            PRIMARY KEY (entry_id, tag_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS entry_imgs (
            entry_id INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE,
            img_id INTEGER REFERENCES img(img_id) ON DELETE CASCADE,
            PRIMARY KEY (entry_id, img_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS project_entries (
            project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
            entry_id INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE,
            PRIMARY KEY (project_id, entry_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS project_tags (
            project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(tag_id) ON DELETE CASCADE,
            PRIMARY KEY (project_id, tag_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS project_status (
            project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
            status_id INTEGER REFERENCES status_(status_id) ON DELETE CASCADE,
            PRIMARY KEY (project_id, status_id)
        );
        """,
    ]

    conn = None
    try:
        conn = connect_from_env()
        with conn.cursor() as cur:
            print("Connected to the database. Creating tables...")
            for command in commands:
                cur.execute(command)
            conn.commit()
            print("Database schema initialized successfully.")
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    initialize_database()
