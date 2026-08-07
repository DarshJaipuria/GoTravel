"""
connection.py
=====================================================
Handles all MySQL connectivity for GoTravel.

Responsibilities:
    - Read database credentials from files/config.txt
    - Provide a function to open a new MySQL connection
    - Provide a function to open a connection WITHOUT
      selecting a database (used only when creating the
      database for the first time)

This module does NOT contain any business logic.
It is used by database.py and, indirectly, by every
feature module (flights.py, hotels.py, booking.py, etc.)
=====================================================
"""

import os
import mysql.connector
from mysql.connector import Error

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "files", "config.txt")


def read_config():
    """
    Reads files/config.txt and returns the settings as a dictionary.
    Lines starting with '#' or blank lines are ignored.
    Raises FileNotFoundError if the config file is missing.
    """
    if not os.path.exists(CONFIG_FILE_PATH):
        raise FileNotFoundError(
            f"Configuration file not found at: {CONFIG_FILE_PATH}\n"
            "Please make sure files/config.txt exists."
        )

    config = {}
    with open(CONFIG_FILE_PATH, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    return config


def get_connection(use_database=True):
    """
    Creates and returns a new MySQL connection object.

    Parameters:
        use_database (bool): If True, connects directly to the
            gotravel database. If False, connects to the MySQL
            server without selecting a database (used only during
            first-time database creation).

    Returns:
        A mysql.connector connection object, or None if the
        connection could not be established (error is printed
        to the caller via the raised exception).
    """
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
    """
    Attempts to connect to the MySQL server and the gotravel
    database. Returns a tuple: (success: bool, message: str)
    This function never raises an exception - it is meant to be
    called safely from menus.
    """
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