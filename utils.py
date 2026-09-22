"""
utils.py
=====================================================
Shared CLI helpers: screen/logo, success/error/info messages,
input validation, the 'back' cancel mechanism, and logging.
=====================================================
"""

import re
import hashlib
from datetime import datetime, date

LOG_FILE_PATH = "files/logs.txt"

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
    """Raised when the user types 'back', to cancel the current form."""
    pass


def _raise_if_back(value):
    """Raises GoBack if the given (already-stripped) value is the cancel keyword."""
    if value.lower() == BACK_COMMAND:
        raise GoBack()


def print_logo():
    """Prints the GoTravel ASCII logo."""
    print(APP_LOGO)


def print_header(title, show_back_hint=False):
    """Prints a consistent section header, with an optional 'back' hint."""
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
    """Asks a yes/no question and returns True/False. Typing 'back' cancels."""
    while True:
        choice = input(prompt).strip().lower()
        _raise_if_back(choice)
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'. (Or type 'back' to cancel.)")


def get_input(prompt, default=None):
    """Input wrapper: blank returns default, 'back' cancels the form."""
    value = input(prompt).strip()
    _raise_if_back(value)
    return value if value else default


def get_non_empty_input(prompt):
    """Keeps asking until a non-blank value is entered. 'back' cancels the form."""
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if value:
            return value
        print("This field cannot be empty. Please try again. (Or type 'back' to cancel.)")


def get_valid_email(prompt):
    """Keeps asking until a syntactically valid email is entered."""
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if EMAIL_PATTERN.match(value):
            return value
        print("Invalid email format. Example: name@example.com (Or type 'back' to cancel.)")


def get_valid_phone(prompt):
    """Keeps asking until a valid 10-digit phone number is entered."""
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if PHONE_PATTERN.match(value):
            return value
        print("Invalid phone number. Enter exactly 10 digits. (Or type 'back' to cancel.)")


def get_valid_date(prompt, allow_blank=False, disallow_past=False):
    """Keeps asking until a real YYYY-MM-DD date is entered (optionally not in the past)."""
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
    """Keeps asking until a password of at least min_length characters is entered."""
    while True:
        value = input(prompt).strip()
        _raise_if_back(value)
        if len(value) >= min_length:
            return value
        print(f"Password must be at least {min_length} characters long. (Or type 'back' to cancel.)")


def get_record_by_id(prompt, fetch_func, not_found_message="No matching record found."):
    """Asks for a whole-number ID and re-prompts until fetch_func(id) finds a match."""
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
    """Returns a SHA-256 hash of the password (never stored as plain text)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def print_table(headers, rows):
    """Prints a simple, evenly-spaced text table with the given headers/rows."""
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
    """Appends a timestamped line to files/logs.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except Exception:
        # Logging should never crash the application.
        pass