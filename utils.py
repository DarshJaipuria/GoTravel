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
    - The universal "type 'back' to cancel" mechanism
    - Activity logging to files/logs.txt

Keeping these in one place means every module prints
messages the same way, giving the CLI a consistent,
professional look.
=====================================================
"""

import os
import re
import hashlib
from datetime import datetime, date

LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "files", "logs.txt")

EMAIL_PATTERN = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^\d{10}$")  # any 10-digit number
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD

# The word a user types at ANY prompt to cancel whatever form they
# are currently filling in and return to the previous menu, instead
# of being forced to finish it (or restart the whole program).
BACK_COMMAND = "back"

APP_LOGO = r"""
   ______     ______                      __
  / ____/____/_  __/________ ____________/ /
 / / __ / __ \/ / / ___/ __ `/ | / / _ \/ /
/ /_/ // /_/ / / / /  / /_/ /| |/ /  __/ /
\____/ \____/_/ /_/   \__,_/ |___/\___/_/

        Your Complete Travel Companion
"""


class GoBack(Exception):
    """
    Raised whenever the user types 'back' at a prompt.

    Every multi-step form (registration, add/edit forms, booking
    forms, etc.) wraps its input-collection code in a single
    try/except GoBack block. Catching it there means the user can
    bail out at any point in the form and return to the menu - no
    database changes happen if a form is cancelled this way, since
    all inserts/updates happen only after every field is collected.
    """
    pass


def _raise_if_back(value):
    """Raises GoBack if the given (already-stripped) value is the cancel keyword."""
    if value.lower() == BACK_COMMAND:
        raise GoBack()


def clear_screen():
    """Clears the terminal screen on both Windows and Unix systems."""
    os.system("cls" if os.name == "nt" else "clear")


def print_logo():
    """Prints the GoTravel ASCII logo."""
    print(APP_LOGO)


def print_header(title, show_back_hint=False):
    """
    Prints a consistent section header, e.g. '=== LOGIN ==='.
    Pass show_back_hint=True for any multi-step form so the user
    is reminded they can type 'back' to cancel out of it.
    """
    line = "=" * 55
    print(f"\n{line}")
    print(f"{title.center(55)}")
    print(f"{line}")
    if show_back_hint:
        print("(Type 'back' at any prompt below to cancel and return to the menu.)")


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
    Typing 'back' raises GoBack, same as any other prompt.
    """
    while True:
        choice = input(prompt).strip().lower()
        _raise_if_back(choice)
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'. (Or type 'back' to cancel.)")


def get_input(prompt, default=None):
    """
    Generic single-value input wrapper, used in place of raw
    input() everywhere a field is optional or has a fallback
    ("press Enter to keep current value" edit prompts included).

    - Typing 'back' cancels the current form (raises GoBack).
    - Blank input returns `default` unchanged.
    - Anything else is returned stripped.
    """
    value = input(prompt).strip()
    _raise_if_back(value)
    return value if value else default


def get_non_empty_input(prompt):
    """
    Keeps asking until the user enters a non-blank value.
    Used everywhere a required text field is collected.
    Typing 'back' cancels the current form.
    """
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if value:
            return value
        print("This field cannot be empty. Please try again. (Or type 'back' to cancel.)")


def get_valid_email(prompt):
    """
    Keeps asking until a syntactically valid email is entered.
    Only checks format - uniqueness is checked separately by the caller.
    Typing 'back' cancels the current form.
    """
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if EMAIL_PATTERN.match(value):
            return value
        print("Invalid email format. Example: name@example.com (Or type 'back' to cancel.)")


def get_valid_phone(prompt):
    """
    Keeps asking until a valid 10-digit Indian mobile number is entered.
    Typing 'back' cancels the current form.
    """
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if PHONE_PATTERN.match(value):
            return value
        print("Invalid phone number. Enter exactly 10 digits. (Or type 'back' to cancel.)")


def get_valid_date(prompt, allow_blank=False, disallow_past=False):
    """
    Keeps asking until a real calendar date in YYYY-MM-DD format is
    entered - the format is checked first, then the value itself is
    parsed with datetime.strptime so something like '2026-05-92'
    (right shape, impossible day) is caught immediately instead of
    only failing later when MySQL rejects the INSERT.

    If allow_blank is True, an empty input returns None (used for
    optional fields like date of birth during profile edits).

    If disallow_past is True, any date earlier than today is
    rejected too - used for booking/travel dates, since you can't
    book a flight, train, cab, hotel stay, or package that already
    happened. Leave this False for fields like date of birth, where
    a past date is the whole point.

    Typing 'back' cancels the current form.
    """
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if allow_blank and value == "":
            return None
        if not DATE_PATTERN.match(value):
            print("Invalid date format. Please use YYYY-MM-DD (e.g. 2025-08-21). (Or type 'back' to cancel.)")
            continue
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            print("That's not a real calendar date - check the month/day. (Or type 'back' to cancel.)")
            continue
        if disallow_past and parsed_date < date.today():
            print("This date can't be in the past. Please enter today's date or later. (Or type 'back' to cancel.)")
            continue
        return value


def get_password(prompt, min_length=6):
    """
    Keeps asking until a password of at least min_length characters
    is entered. Kept simple and readable, in line with CBSE syllabus
    (no external validation libraries). Typing 'back' cancels the
    current form.
    """
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if len(value) >= min_length:
            return value
        print(f"Password must be at least {min_length} characters long. (Or type 'back' to cancel.)")


def get_record_by_id(prompt, fetch_func, not_found_message="No matching record found."):
    """
    Repeatedly asks for a whole-number ID and looks it up using
    fetch_func(id_as_int) until a matching record (any truthy value)
    is returned - instead of aborting the whole action the moment a
    non-existent or mistyped ID is entered once.

    Parameters:
        prompt (str): the input prompt shown each attempt
        fetch_func (callable): takes one int argument (the ID) and
            returns the matching record (dict, etc.) or a falsy
            value (None/False) if nothing matches
        not_found_message (str): shown when fetch_func returns falsy

    Typing 'back' cancels the current form (raises GoBack), same as
    any other prompt - so a user is never trapped here either.
    """
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if not value.isdigit():
            print("That must be a whole number. Please try again. (Or type 'back' to cancel.)")
            continue
        record = fetch_func(int(value))
        if record:
            return record
        print(f"{not_found_message} Please try again. (Or type 'back' to cancel.)")


def hash_password(password):
    """
    Returns a SHA-256 hash of the given password.
    Plain-text passwords are never stored in the database.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def print_table(headers, rows):
    """
    Prints a simple, evenly-spaced text table.

    Parameters:
        headers (list[str]): column titles
        rows (list[list]): each inner list is one row of values,
            in the same order as headers

    Used by admin.py (and, from later stages onward, by feature
    modules) so every listing in the app looks consistent.
    """
    if not rows:
        print("\nNo records found.")
        return

    str_rows = [[str(cell) for cell in row] for row in rows]

    col_widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-" * len(header_line)

    print(f"\n{header_line}")
    print(separator)
    for row in str_rows:
        print("  ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))


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