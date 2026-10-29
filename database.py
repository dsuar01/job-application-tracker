"""Database connection helpers.

Connection settings are read from environment variables (or from a local ``.env``
file) so that the password is never stored in the code or pushed to GitHub.
See ``.env.example`` for the variable names.
"""
import os

import mysql.connector
from mysql.connector import Error


def _load_env_file(path=".env"):
    """Tiny .env reader (KEY=value per line) so no extra package is needed."""
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if not os.path.exists(full_path):
        return
    with open(full_path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "job_tracker"),
}


def get_db_connection():
    """Return a MySQL connection, or None if the connection fails."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Database connection error: {e}")
        return None


def test_connection():
    """Print whether the database connection works."""
    connection = get_db_connection()

    if connection is not None and connection.is_connected():
        print(f"Successfully connected to MySQL database: {DB_CONFIG['database']}")
        connection.close()
    else:
        print("Failed to connect to the database. Check your .env settings.")


if __name__ == "__main__":
    test_connection()
