"""
login.py
=====================================================
Handles user REGISTRATION and LOGIN (authentication only).

Responsibilities:
    - Collect and validate registration details
    - Ensure email/phone are unique before creating an account
    - Verify login credentials against the Users table
    - Hash passwords (never store plain text)

Profile viewing/editing and password changes for an
ALREADY logged-in user live in user.py, not here - this
module's job ends the moment a session starts or fails.
=====================================================
"""

import database
import utils


def _email_exists(email):
    """Returns True if a user with this email already exists."""
    result = database.fetch_query(
        "SELECT user_id FROM Users WHERE email = %s", (email,), fetch_one=True
    )
    return result is not None


def _phone_exists(phone):
    """Returns True if a user with this phone number already exists."""
    result = database.fetch_query(
        "SELECT user_id FROM Users WHERE phone = %s", (phone,), fetch_one=True
    )
    return result is not None


def register_user():
    """
    Runs the full registration flow: collects details, validates
    them, checks for duplicates, hashes the password, and inserts
    the new user into the database.

    Returns:
        (success: bool, message: str)
    """
    utils.print_header("CREATE A NEW ACCOUNT")

    full_name = utils.get_non_empty_input("Full Name: ")

    while True:
        email = utils.get_valid_email("Email: ")
        if _email_exists(email):
            print("An account with this email already exists. Try logging in instead.")
            continue
        break

    while True:
        phone = utils.get_valid_phone("Phone Number (10 digits): ")
        if _phone_exists(phone):
            print("An account with this phone number already exists.")
            continue
        break

    while True:
        password = utils.get_password("Password (min 6 characters): ")
        confirm_password = input("Confirm Password: ").strip()
        if password != confirm_password:
            print("Passwords do not match. Please try again.")
            continue
        break

    gender = input("Gender (Male/Female/Other, optional): ").strip() or None
    date_of_birth = utils.get_valid_date(
        "Date of Birth (YYYY-MM-DD, optional, press Enter to skip): ", allow_blank=True
    )
    address = input("Address (optional): ").strip() or None

    hashed_password = utils.hash_password(password)

    query = """
        INSERT INTO Users (full_name, email, phone, password, gender, date_of_birth, address)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (full_name, email, phone, hashed_password, gender, date_of_birth, address)

    success, result = database.execute_query(query, params)

    if success:
        utils.log_activity(f"New user registered: {email}")
        return True, "Account created successfully! You can now log in."
    else:
        utils.log_activity(f"Registration failed for {email}: {result}")
        return False, f"Registration failed: {result}"


def login_user():
    """
    Runs the login flow: asks for email/phone + password, verifies
    them against the database, and returns the user record on success.

    Returns:
        (success: bool, user_dict_or_message)
        - On success: (True, user_dict)
        - On failure: (False, error_message)
    """
    utils.print_header("LOGIN TO YOUR ACCOUNT")

    identifier = utils.get_non_empty_input("Email or Phone Number: ")
    password = input("Password: ").strip()

    if not password:
        return False, "Password cannot be empty."

    hashed_password = utils.hash_password(password)

    user = database.fetch_query(
        """
        SELECT * FROM Users
        WHERE (email = %s OR phone = %s) AND password = %s
        """,
        (identifier, identifier, hashed_password),
        fetch_one=True,
    )

    if user is None:
        utils.log_activity(f"Failed login attempt for: {identifier}")
        return False, "Invalid credentials. Please check your email/phone and password."

    if not user.get("is_active", 1):
        return False, "This account has been deactivated. Please contact support."

    utils.log_activity(f"User logged in: {user['email']}")
    return True, user