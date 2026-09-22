"""
connection.py
=====================================================
Reads files/config.txt and opens a MySQL connection.
Used by database.py, not directly by feature modules.
=====================================================
"""

import mysql.connector
from mysql.connector import Error

# The program is always run from inside the GoTravel folder,
# so this simple relative path is enough.
CONFIG_FILE_PATH = "files/config.txt"


def read_config():
    config = {}
    try:
        with open(CONFIG_FILE_PATH, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Configuration file not found at: {CONFIG_FILE_PATH}\n"
            "Please make sure files/config.txt exists."
        )

    return config


def get_connection(use_database=True):

    config = read_config()

    connection_params = {
        "host": config.get("DB_HOST", "localhost"),
        "port": int(config.get("DB_PORT", 3306)),
        "user": config.get("DB_USER", "root"),
        "password": config.get("DB_PASSWORD", ""),
    }

    if use_database:
        connection_params["database"] = config.get("DB_NAME", "gotravel")

    connection = mysql.connector.connect(**connection_params)
    return connection


def test_connection():
    try:
        connection = get_connection(use_database=True)
        if connection.is_connected():
            db_info = connection.get_server_info()
            connection.close()
            return True, f"Connected successfully. MySQL server version {db_info}"
    except FileNotFoundError as fnf_error:
        return False, str(fnf_error)
    except Error as db_error:
        return False, f"Database connection failed: {db_error}"
    except Exception as general_error:
        return False, f"Unexpected error while connecting: {general_error}"

    return False, "Connection could not be established."