"""
main.py
=====================================================
Entry point for the GoTravel application.

Behaviour:
    - If gui.py exists in the project folder, it is
      launched automatically (Tkinter GUI mode).
    - If gui.py does NOT exist, the application falls
      back to CLI mode automatically.

Stage 1 note:
    gui.py does not exist yet (it is built in Stage 10),
    so this will always run in CLI mode for now. The
    fallback logic is already in place so nothing needs
    to change later.

Run with:  python main.py
=====================================================
"""

import os
import sys

import utils
import database
import connection
import login
import user


def launch_gui():
    """Imports and launches the Tkinter GUI, if available."""
    import gui  # only imported when gui.py actually exists
    gui.run_app()


def show_about():
    utils.print_header("ABOUT GOTRAVEL")
    print("GoTravel - A Complete Travel Booking & Management System")
    print("Inspired by Goibibo, built entirely in Python.")
    print("\nFeatures (rolled out across development stages):")
    print("  - Flights, Trains, Hotels, Cabs & Holiday Packages")
    print("  - Secure Login & User Profiles")
    print("  - Booking, Payments, Wallet & Coupons")
    print("  - Reviews, Invoices & Booking History")
    print("  - Admin Panel & Travel Analytics")
    print("\nCurrent build: Stage 2 - User Authentication & Profile")
    utils.pause()


def show_help():
    utils.print_header("HELP")
    print("This is the GoTravel command line interface.")
    print("Use the number keys to navigate the menus shown on screen.")
    print("\nAvailable right now (Stage 2):")
    print("  1. Login")
    print("  2. Register")
    print("  3. Test Database Connection")
    print("  4. Initialize Database")
    print("  5. About")
    print("  6. Help")
    print("  0. Exit")
    print("\nOnce logged in, you can view/edit your profile and")
    print("change your password. Booking features (flights, trains,")
    print("hotels, cabs, packages) will appear in your dashboard")
    print("automatically as development continues.")
    utils.pause()


def handle_test_connection():
    utils.print_header("DATABASE CONNECTION TEST")
    print("Connecting to MySQL...")
    success, message = connection.test_connection()
    if success:
        utils.print_success(message)
    else:
        utils.print_error(message)
        print("\nTip: Check files/config.txt and make sure MySQL is running.")
    utils.pause()


def handle_initialize_database():
    utils.print_header("INITIALIZE DATABASE")
    print("This will create the 'gotravel' database and required")
    print("tables if they do not already exist. Existing data is")
    print("never deleted by this operation.")

    if not utils.confirm("Proceed? (y/n): "):
        utils.print_info("Initialization cancelled.")
        utils.pause()
        return

    success, message = database.initialize_database()
    if success:
        utils.print_success(message)
    else:
        utils.print_error(message)
    utils.pause()


def handle_register():
    success, message = login.register_user()
    if success:
        utils.print_success(message)
    else:
        utils.print_error(message)
    utils.pause()


def handle_login():
    """
    Runs the login flow. Returns the logged-in user dict on
    success, or None if login failed / was cancelled.
    """
    success, result = login.login_user()
    if success:
        utils.print_success(f"Welcome back, {result['full_name']}!")
        utils.pause()
        return result
    else:
        utils.print_error(result)
        utils.pause()
        return None


def user_dashboard(current_user):
    """
    Menu shown after a successful login. Currently offers the
    features available as of Stage 2 (profile management).
    Booking-related features are added to this menu in later
    stages without changing how it is reached.
    """
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header(f"WELCOME, {current_user['full_name'].upper()}")
        print("1. View My Profile")
        print("2. Edit My Profile")
        print("3. Change Password")
        print("0. Logout")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            user.view_profile(current_user)
        elif choice == "2":
            current_user = user.edit_profile(current_user)
        elif choice == "3":
            user.change_password(current_user)
        elif choice == "0":
            utils.log_activity(f"User logged out: {current_user['email']}")
            utils.print_info("You have been logged out.")
            utils.pause()
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def main_menu():
    """The main guest-facing CLI menu loop (before login)."""
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MAIN MENU")
        print("1. Login")
        print("2. Register")
        print("3. Test Database Connection")
        print("4. Initialize Database")
        print("5. About")
        print("6. Help")
        print("0. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            logged_in_user = handle_login()
            if logged_in_user is not None:
                user_dashboard(logged_in_user)
        elif choice == "2":
            handle_register()
        elif choice == "3":
            handle_test_connection()
        elif choice == "4":
            handle_initialize_database()
        elif choice == "5":
            show_about()
        elif choice == "6":
            show_help()
        elif choice == "0":
            print("\nThank you for using GoTravel. Safe travels!\n")
            sys.exit(0)
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def run_cli():
    """Runs the CLI version of the application."""
    utils.clear_screen()
    utils.print_logo()
    print("Welcome to GoTravel - A Complete Travel Booking & Management System")
    utils.pause()
    main_menu()


if __name__ == "__main__":
    gui_file_path = os.path.join(os.path.dirname(__file__), "gui.py")

    if os.path.exists(gui_file_path):
        try:
            launch_gui()
        except Exception as gui_error:
            utils.print_error(f"GUI failed to launch: {gui_error}")
            print("Falling back to CLI mode...\n")
            run_cli()
    else:
        run_cli()