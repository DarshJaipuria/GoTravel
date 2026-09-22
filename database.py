"""
=====================================================
database.py
=====================================================
Runs the schema file and provides execute_query()/fetch_query()
helpers used by every other module to talk to MySQL.
=====================================================
"""

from mysql.connector import Error
import connection
import utils

SQL_SCRIPT_PATH = "sql/gotravel.sql"


def initialize_database():
    """Runs sql/gotravel.sql to create the database and tables. Safe to run again."""
    try:
        with open(SQL_SCRIPT_PATH, "r") as file:
            sql_script = file.read()

        # Split the script into separate SQL statements on ';'.
        statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]

        # First statement creates the database, so no database is selected yet.
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

    except FileNotFoundError:
        return False, f"SQL script not found at: {SQL_SCRIPT_PATH}"
    except Error as db_error:
        utils.log_activity(f"Database initialization failed: {db_error}")
        return False, f"Database initialization failed: {db_error}"
    except Exception as general_error:
        utils.log_activity(f"Unexpected error during initialization: {general_error}")
        return False, f"Unexpected error during initialization: {general_error}"


def _add_new_bookings_columns():
    """Adds payment_method/coupon_code/discount_amount to Bookings if missing."""
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
    """Runs an INSERT/UPDATE/DELETE query. Returns (success, last_insert_id_or_error)."""
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
    """Runs the same INSERT/UPDATE query for many rows at once (used by seed_data.py)."""
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
    """Runs a SELECT query. Returns one row (dict) if fetch_one, else a list of rows."""
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