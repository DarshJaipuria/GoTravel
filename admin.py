"""
admin.py
=====================================================
Handles the admin side of GoTravel:
    - Admin login
    - First-time "bootstrap" admin creation (only when
      the Admins table is empty - there is no public
      admin registration for security reasons)
    - Adding further admins (only usable by an already
      logged-in admin, from the admin dashboard)
    - User management: view, search, activate/deactivate,
      and delete user accounts

As more tables are added in later stages (Flights, Hotels,
Bookings, etc.), this module gains more management functions,
but the login/bootstrap logic here does not change.
=====================================================
"""

import database
import utils


def get_admin_count():
    """Returns how many admin accounts currently exist."""
    result = database.fetch_query("SELECT COUNT(*) AS total FROM Admins", fetch_one=True)
    return result["total"] if result else 0


def _email_exists(email):
    """Returns True if an admin with this email already exists."""
    result = database.fetch_query(
        "SELECT admin_id FROM Admins WHERE email = %s", (email,), fetch_one=True
    )
    return result is not None


def register_admin(is_bootstrap=False):
    """
    Creates a new admin account.

    Parameters:
        is_bootstrap (bool): True when this is the very first
            admin account being created (no login required).
            False when an existing admin is adding a colleague.

    Returns:
        (success: bool, message: str)
    """
    if is_bootstrap:
        utils.print_header("FIRST-TIME ADMIN SETUP")
        print("No admin accounts exist yet. Let's create the first one.\n")
    else:
        utils.print_header("ADD NEW ADMIN")

    admin_name = utils.get_non_empty_input("Admin Name: ")

    while True:
        email = utils.get_valid_email("Email: ")
        if _email_exists(email):
            print("An admin with this email already exists.")
            continue
        break

    while True:
        password = utils.get_password("Password (min 6 characters): ")
        confirm_password = input("Confirm Password: ").strip()
        if password != confirm_password:
            print("Passwords do not match. Please try again.")
            continue
        break

    hashed_password = utils.hash_password(password)

    success, result = database.execute_query(
        "INSERT INTO Admins (admin_name, email, password) VALUES (%s, %s, %s)",
        (admin_name, email, hashed_password),
    )

    if success:
        utils.log_activity(f"Admin account created: {email}")
        return True, "Admin account created successfully."
    else:
        utils.log_activity(f"Admin creation failed for {email}: {result}")
        return False, f"Admin creation failed: {result}"


def admin_login():
    """
    Runs the admin login flow.

    Returns:
        (success: bool, admin_dict_or_message)
    """
    utils.print_header("ADMIN LOGIN")

    email = utils.get_non_empty_input("Admin Email: ")
    password = input("Password: ").strip()

    if not password:
        return False, "Password cannot be empty."

    hashed_password = utils.hash_password(password)

    admin = database.fetch_query(
        "SELECT * FROM Admins WHERE email = %s AND password = %s",
        (email, hashed_password),
        fetch_one=True,
    )

    if admin is None:
        utils.log_activity(f"Failed admin login attempt for: {email}")
        return False, "Invalid credentials."

    utils.log_activity(f"Admin logged in: {admin['email']}")
    return True, admin


# ---------------------------------------------------------
# User management (available to logged-in admins)
# ---------------------------------------------------------

def view_all_users():
    """Displays every registered user in a table."""
    utils.print_header("ALL REGISTERED USERS")
    users = database.fetch_query(
        "SELECT user_id, full_name, email, phone, is_active FROM Users ORDER BY user_id"
    )
    if users is None:
        utils.print_error("Could not fetch users.")
        utils.pause()
        return

    rows = [
        [u["user_id"], u["full_name"], u["email"], u["phone"],
         "Active" if u["is_active"] else "Inactive"]
        for u in users
    ]
    utils.print_table(["ID", "Full Name", "Email", "Phone", "Status"], rows)
    utils.pause()


def search_users():
    """Searches users by name, email, or phone (partial match)."""
    utils.print_header("SEARCH USERS")
    keyword = utils.get_non_empty_input("Enter name, email, or phone to search: ")
    like_pattern = f"%{keyword}%"

    users = database.fetch_query(
        """
        SELECT user_id, full_name, email, phone, is_active
        FROM Users
        WHERE full_name LIKE %s OR email LIKE %s OR phone LIKE %s
        ORDER BY user_id
        """,
        (like_pattern, like_pattern, like_pattern),
    )

    if users is None:
        utils.print_error("Search failed.")
        utils.pause()
        return

    rows = [
        [u["user_id"], u["full_name"], u["email"], u["phone"],
         "Active" if u["is_active"] else "Inactive"]
        for u in users
    ]
    utils.print_table(["ID", "Full Name", "Email", "Phone", "Status"], rows)
    utils.pause()


def toggle_user_status():
    """Activates or deactivates a user account by ID."""
    utils.print_header("ACTIVATE / DEACTIVATE USER")
    view_all_users_inline()

    user_id_input = utils.get_non_empty_input("\nEnter User ID: ")
    if not user_id_input.isdigit():
        utils.print_error("User ID must be a number.")
        utils.pause()
        return

    target_user = database.fetch_query(
        "SELECT * FROM Users WHERE user_id = %s", (int(user_id_input),), fetch_one=True
    )
    if target_user is None:
        utils.print_error("No user found with that ID.")
        utils.pause()
        return

    current_status = "Active" if target_user["is_active"] else "Inactive"
    new_status = 0 if target_user["is_active"] else 1
    new_status_label = "Inactive" if target_user["is_active"] else "Active"

    print(f"\n{target_user['full_name']} is currently {current_status}.")
    if not utils.confirm(f"Change status to {new_status_label}? (y/n): "):
        utils.print_info("No changes made.")
        utils.pause()
        return

    success, result = database.execute_query(
        "UPDATE Users SET is_active = %s WHERE user_id = %s",
        (new_status, target_user["user_id"]),
    )

    if success:
        utils.print_success(f"User status updated to {new_status_label}.")
        utils.log_activity(f"Admin set user {target_user['email']} to {new_status_label}")
    else:
        utils.print_error(f"Could not update status: {result}")
    utils.pause()


def delete_user():
    """Permanently deletes a user account by ID, after confirmation."""
    utils.print_header("DELETE USER")
    view_all_users_inline()

    user_id_input = utils.get_non_empty_input("\nEnter User ID to delete: ")
    if not user_id_input.isdigit():
        utils.print_error("User ID must be a number.")
        utils.pause()
        return

    target_user = database.fetch_query(
        "SELECT * FROM Users WHERE user_id = %s", (int(user_id_input),), fetch_one=True
    )
    if target_user is None:
        utils.print_error("No user found with that ID.")
        utils.pause()
        return

    print(f"\nYou are about to permanently delete: {target_user['full_name']} ({target_user['email']})")
    if not utils.confirm("This cannot be undone. Continue? (y/n): "):
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    success, result = database.execute_query(
        "DELETE FROM Users WHERE user_id = %s", (target_user["user_id"],)
    )

    if success:
        utils.print_success("User deleted successfully.")
        utils.log_activity(f"Admin deleted user: {target_user['email']}")
    else:
        utils.print_error(f"Could not delete user: {result}")
    utils.pause()


def view_all_users_inline():
    """
    Same as view_all_users() but without a header/pause - used to
    show the user list right before asking for a User ID, so the
    admin doesn't have to look it up separately.
    """
    users = database.fetch_query(
        "SELECT user_id, full_name, email, is_active FROM Users ORDER BY user_id"
    )
    if not users:
        print("\nNo users to display.")
        return
    rows = [
        [u["user_id"], u["full_name"], u["email"], "Active" if u["is_active"] else "Inactive"]
        for u in users
    ]
    utils.print_table(["ID", "Full Name", "Email", "Status"], rows)