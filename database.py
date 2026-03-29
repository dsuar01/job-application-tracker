import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Darien@15",
    "database": "job_tracker"
}


def get_db_connection():
    """
    Create and return a connection to the MySQL database.
    Returns None if the connection fails.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None


def test_connection():
    """
    Test whether the database connection works.
    """
    connection = get_db_connection()

    if connection is not None and connection.is_connected():
        print("Successfully connected to MySQL database: job_tracker")
        connection.close()
    else:
        print("Failed to connect to the database.")


if __name__ == "__main__":
    test_connection()
