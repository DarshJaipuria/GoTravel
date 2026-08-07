"""
user.py
=====================================================
Handles operations for an ALREADY logged-in user:
    - Viewing their profile
    - Editing their profile details
    - Changing their password

Authentication (login/registration) lives in login.py.
This module assumes a valid `user` dictionary (as returned
by login.login_user) is passed in by main.py.
=====================================================
"""

import database
import utils


def view_profile(user):
    """Displays the logged-in user's profile in a clean, formatted way."""
    utils.print_header("MY PROFILE")
    print(f"{'Full Name':<18}: {user['full_name']}")
    print(f"{'Email':<18}: {user['email']}")
    print(f"{'Phone':<18}: {user['phone']}")
    print(f"{'Gender':<18}: {user['gender'] or 'Not set'}")
    print(f"{'Date of Birth':<18}: {user['date_of_birth'] or 'Not set'}")
    print(f"{'Address':<18}: {user['address'] or 'Not set'}")
    print(f"{'Wallet Balance':<18}: Rs. {user['wallet_balance']}")
    print(f"{'Member Since':<18}: {user['created_at']}")
    utils.pause()


def edit_profile(user):
    """
    Lets the user update their name, phone, gender, date of birth,
    and address. Email is intentionally NOT editable here to keep
    it a stable login identifier.

    Returns the refreshed user dictionary (whether or not any
    field was actually changed).
    """
    utils.print_header("EDIT PROFILE")
    print("Press Enter on any field to keep its current value.\n")

    full_name = input(f"Full Name [{user['full_name']}]: ").strip() or user["full_name"]

    while True:
        phone = input(f"Phone Number [{user['phone']}]: ").strip() or user["phone"]
        if phone == user["phone"] or utils.PHONE_PATTERN.match(phone):
            existing = database.fetch_query(
                "SELECT user_id FROM Users WHERE phone = %s AND user_id != %s",
                (phone, user["user_id"]),
                fetch_one=True,
            )
            if existing:
                print("That phone number is already used by another account.")
                continue
            break
        print("Invalid phone number. Enter exactly 10 digits.")

    gender = input(f"Gender [{user['gender'] or 'Not set'}]: ").strip() or user["gender"]
    date_of_birth = (
        input(f"Date of Birth (YYYY-MM-DD) [{user['date_of_birth'] or 'Not set'}]: ").strip()
        or user["date_of_birth"]
    )
    address = input(f"Address [{user['address'] or 'Not set'}]: ").strip() or user["address"]

    query = """
        UPDATE Users
        SET full_name = %s, phone = %s, gender = %s, date_of_birth = %s, address = %s
        WHERE user_id = %s
    """
    params = (full_name, phone, gender, date_of_birth, address, user["user_id"])

    success, result = database.execute_query(query, params)

    if success:
        utils.print_success("Profile updated successfully.")
        utils.log_activity(f"Profile updated: {user['email']}")
        updated_user = database.fetch_query(
            "SELECT * FROM Users WHERE user_id = %s", (user["user_id"],), fetch_one=True
        )
        utils.pause()
        return updated_user
    else:
        utils.print_error(f"Could not update profile: {result}")
        utils.pause()
        return user


def change_password(user):
    """
    Lets the logged-in user change their password after verifying
    their current password. Returns nothing - the caller's `user`
    dict does not store the password, so no refresh is needed.
    """
    utils.print_header("CHANGE PASSWORD")

    current_password = input("Current Password: ").strip()
    if utils.hash_password(current_password) != user["password"]:
        utils.print_error("Current password is incorrect.")
        utils.pause()
        return

    new_password = utils.get_password("New Password (min 6 characters): ")
    confirm_password = input("Confirm New Password: ").strip()

    if new_password != confirm_password:
        utils.print_error("New passwords do not match.")
        utils.pause()
        return

    hashed_password = utils.hash_password(new_password)
    success, result = database.execute_query(
        "UPDATE Users SET password = %s WHERE user_id = %s",
        (hashed_password, user["user_id"]),
    )

    if success:
        utils.print_success("Password changed successfully.")
        utils.log_activity(f"Password changed: {user['email']}")
    else:
        utils.print_error(f"Could not change password: {result}")

    utils.pause()