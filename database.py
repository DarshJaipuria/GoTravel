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
    Reads sql/gotravel.sql and executes every statement in it, then
    calls _add_new_bookings_columns() to make sure a database that
    existed BEFORE Stage 7 also gets the three new Stage 7 columns
    on Bookings, WITHOUT deleting any existing users/bookings.

    Safe to run multiple times - 'CREATE DATABASE IF NOT EXISTS' and
    'CREATE TABLE IF NOT EXISTS' mean re-running this never drops or
    recreates anything that's already there.

    Returns:
        (success: bool, message: str)
    """
    if not os.path.exists(SQL_SCRIPT_PATH):
        return False, f"SQL script not found at: {SQL_SCRIPT_PATH}"

    try:
        with open(SQL_SCRIPT_PATH, "r") as file:
            sql_script = file.read()

        # Split into individual statements on ';' and drop empty ones.
        # NOTE: this is a simple split, so a ';' character must never
        # appear inside a comment line in gotravel.sql, or it will
        # chop that comment (and the statement after it) in half.
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

        _add_new_bookings_columns()

        utils.log_activity("Database initialized successfully.")
        return True, "Database and tables created/verified successfully."

    except Error as db_error:
        utils.log_activity(f"Database initialization failed: {db_error}")
        return False, f"Database initialization failed: {db_error}"
    except Exception as general_error:
        utils.log_activity(f"Unexpected error during initialization: {general_error}")
        return False, f"Unexpected error during initialization: {general_error}"


def _add_new_bookings_columns():
    """
    Stage 7 added three new columns to Bookings: payment_method,
    coupon_code, discount_amount. gotravel.sql's 'CREATE TABLE IF
    NOT EXISTS Bookings' already includes them for a brand new
    install, but does nothing at all if a Bookings table from
    BEFORE Stage 7 already exists - it can't add a column to a
    table that's already there.

    So this runs one ALTER TABLE ADD COLUMN per new column, which
    only adds the column and leaves every existing row exactly as
    it was (existing bookings simply get 'Wallet'/NULL/0 in the new
    columns, matching their column defaults). If a column already
    exists - which is the normal case on a fresh install, since the
    CREATE TABLE above already added it - MySQL raises an error for
    trying to add a duplicate column, and that's simply caught with
    try/except and ignored, since it just means there's nothing to
    do for that column.
    """
    new_columns = [
        "ALTER TABLE Bookings ADD COLUMN payment_method VARCHAR(10) DEFAULT 'Wallet'",
        "ALTER TABLE Bookings ADD COLUMN coupon_code VARCHAR(30)",
        "ALTER TABLE Bookings ADD COLUMN discount_amount DECIMAL(10,2) DEFAULT 0",
    ]

    conn = None
    try:
        conn = connection.get_connection(use_database=True)
        cursor = conn.cursor()
        for alter_statement in new_columns:
            try:
                cursor.execute(alter_statement)
                conn.commit()
            except Error:
                # Column already exists - nothing to do, move on.
                pass
        cursor.close()
    except Error as db_error:
        utils.log_activity(f"Could not add Stage 7 columns to Bookings: {db_error}")
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


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