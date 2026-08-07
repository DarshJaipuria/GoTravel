"""
utils.py
=====================================================
Shared helper functions used across the whole GoTravel
application (CLI and, later, the GUI).

Responsibilities:
    - Screen clearing
    - ASCII logo / welcome screen
    - Consistent success / error / info messages
    - Simple confirmation prompts
    - Activity logging to files/logs.txt

Keeping these in one place means every module prints
messages the same way, giving the CLI a consistent,
professional look.
=====================================================
"""

import os
import re
import hashlib
from datetime import datetime

LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "files", "logs.txt")

EMAIL_PATTERN = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^\d{10}$")  # any 10-digit number
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD

APP_LOGO = r"""
   ______     ______                     __
  / ____/____/_  __/________ ___veL_____/ /
 / / __ / __ \/ / / ___/ __ `/ | / / _ \/ /
/ /_/ // /_/ / / / /  / /_/ /| |/ /  __/ /
\____/ \____/_/ /_/   \__,_/ |___/\___/_/

        Your Complete Travel Companion
"""


def clear_screen():
    """Clears the terminal screen on both Windows and Unix systems."""
    os.system("cls" if os.name == "nt" else "clear")


def print_logo():
    """Prints the GoTravel ASCII logo."""
    print(APP_LOGO)


def print_header(title):
    """Prints a consistent section header, e.g. '=== LOGIN ==='."""
    line = "=" * 55
    print(f"\n{line}")
    print(f"{title.center(55)}")
    print(f"{line}")


def print_success(message):
    print(f"\n[SUCCESS] {message}")


def print_error(message):
    print(f"\n[ERROR] {message}")


def print_info(message):
    print(f"\n[INFO] {message}")


def pause():
    """Pauses execution until the user presses Enter."""
    input("\nPress Enter to continue...")


def confirm(prompt="Are you sure? (y/n): "):
    """
    Asks a yes/no question and returns True/False.
    Keeps asking until a valid response ('y' or 'n') is given.
    """
    while True:
        choice = input(prompt).strip().lower()
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


def get_non_empty_input(prompt):
    """
    Keeps asking until the user enters a non-blank value.
    Used everywhere a required text field is collected.
    """
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty. Please try again.")


def get_valid_email(prompt):
    """
    Keeps asking until a syntactically valid email is entered.
    Only checks format - uniqueness is checked separately by the caller.
    """
    while True:
        value = input(prompt).strip()
        if EMAIL_PATTERN.match(value):
            return value
        print("Invalid email format. Example: name@example.com")


def get_valid_phone(prompt):
    """
    Keeps asking until a valid 10-digit Indian mobile number is entered.
    """
    while True:
        value = input(prompt).strip()
        if PHONE_PATTERN.match(value):
            return value
        print("Invalid phone number. Enter exactly 10 digits.")


def get_valid_date(prompt, allow_blank=False):
    """
    Keeps asking until a date in YYYY-MM-DD format is entered.
    If allow_blank is True, an empty input returns None (used for
    optional fields like date of birth during profile edits).
    """
    while True:
        value = input(prompt).strip()
        if allow_blank and value == "":
            return None
        if DATE_PATTERN.match(value):
            return value
        print("Invalid date format. Please use YYYY-MM-DD (e.g. 2005-08-21).")


def get_password(prompt, min_length=6):
    """
    Keeps asking until a password of at least min_length characters
    is entered. Kept simple and readable, in line with CBSE syllabus
    (no external validation libraries).
    """
    while True:
        value = input(prompt).strip()
        if len(value) >= min_length:
            return value
        print(f"Password must be at least {min_length} characters long.")


def hash_password(password):
    """
    Returns a SHA-256 hash of the given password.
    Plain-text passwords are never stored in the database.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def log_activity(message):
    """
    Appends a timestamped line to files/logs.txt.
    Used by database.py and other modules to keep an
    audit trail of important events (DB init, errors, etc.)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except Exception:
        # Logging should never crash the application.
        pass