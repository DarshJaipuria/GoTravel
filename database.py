"""
database.py
=====================================================
Database setup and low-level query helpers for GoTravel.

Responsibilities:
    - Initialize the database using sql/gotravel.sql
    - Provide generic execute_query() / fetch_query() helpers
      so that feature modules never write raw connection
      handling code themselves

All feature modules (flights.py, hotels.py, booking.py, etc.)
should use execute_query() and fetch_query() from this file
instead of talking to connection.py directly.
=====================================================
"""

import os
from mysql.connector import Error
import connection
import utils

SQL_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "sql", "gotravel.sql")


def initialize_database():
    """
    Reads sql/gotravel.sql and executes every statement in it.
    Safe to run multiple times because the script uses
    'CREATE DATABASE IF NOT EXISTS' and 'CREATE TABLE IF NOT EXISTS'.

    Returns:
        (success: bool, message: str)
    """
    if not os.path.exists(SQL_SCRIPT_PATH):
        return False, f"SQL script not found at: {SQL_SCRIPT_PATH}"

    try:
        with open(SQL_SCRIPT_PATH, "r") as file:
            sql_script = file.read()

        # Split into individual statements on ';' and drop empty ones.
        statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]

        # First statement creates the database, so connect WITHOUT
        # selecting a database yet.
        conn = connection.get_connection(use_database=False)
        cursor = conn.cursor()

        for statement in statements:
            cursor.execute(statement)

        conn.commit()
        cursor.close()
        conn.close()

        utils.log_activity("Database initialized successfully.")
        return True, "Database and tables created/verified successfully."

    except Error as db_error:
        utils.log_activity(f"Database initialization failed: {db_error}")
        return False, f"Database initialization failed: {db_error}"
    except Exception as general_error:
        utils.log_activity(f"Unexpected error during initialization: {general_error}")
        return False, f"Unexpected error during initialization: {general_error}"


def execute_query(query, params=None):
    """
    Executes an INSERT / UPDATE / DELETE query safely.

    Parameters:
        query (str): SQL query with %s placeholders
        params (tuple): values to substitute into the query

    Returns:
        (success: bool, message_or_lastrowid)
    """
    conn = None
    try:
        conn = connection.get_connection(use_database=True)
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return True, last_id
    except Error as db_error:
        utils.log_activity(f"Query execution failed: {db_error}")
        return False, str(db_error)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def execute_many(query, param_list):
    """
    Executes the same INSERT/UPDATE query for many rows at once
    using cursor.executemany() - far faster than calling
    execute_query() in a loop when inserting hundreds of rows
    (used by seed_data.py to load sample Airports/Stations/
    Flights/Trains data).

    Parameters:
        query (str): SQL query with %s placeholders
        param_list (list[tuple]): one tuple of values per row

    Returns:
        (success: bool, rows_affected_or_error_message)
    """
    conn = None
    try:
        conn = connection.get_connection(use_database=True)
        cursor = conn.cursor()
        cursor.executemany(query, param_list)
        conn.commit()
        row_count = cursor.rowcount
        cursor.close()
        conn.close()
        return True, row_count
    except Error as db_error:
        utils.log_activity(f"Bulk insert failed: {db_error}")
        return False, str(db_error)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def fetch_query(query, params=None, fetch_one=False):
    """
    Executes a SELECT query safely.

    Parameters:
        query (str): SQL query with %s placeholders
        params (tuple): values to substitute into the query
        fetch_one (bool): if True, returns a single row (dict) or None
                           if False, returns a list of rows (dicts)

    Returns:
        On success: the fetched data (dict, list of dicts, or None)
        On failure: None
    """
    conn = None
    try:
        conn = connection.get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()

        cursor.close()
        conn.close()
        return result
    except Error as db_error:
        utils.log_activity(f"Query fetch failed: {db_error}")
        return None
    finally:
        if conn is not None and conn.is_connected():
            conn.close()