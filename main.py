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
import admin
import flights
import trains
import hotels
import cabs
import seed_data


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
    print("\nCurrent build: Stage 5 - Hotels & Cabs")
    utils.pause()


def show_help():
    utils.print_header("HELP")
    print("This is the GoTravel command line interface.")
    print("Use the number keys to navigate the menus shown on screen.")
    print("\nAvailable right now (Stage 5):")
    print("  1. Login")
    print("  2. Register")
    print("  3. Admin Login")
    print("  4. Test Database Connection")
    print("  5. Initialize Database")
    print("  6. About")
    print("  7. Help")
    print("  0. Exit")
    print("\nOnce logged in as a user, you can search Flights, Trains,")
    print("Hotels, and Cabs, and view/edit your profile. Admins can")
    print("manage user accounts, manage Flights/Trains/Hotels/Cabs, and")
    print("load sample data from the admin dashboard (first time only -")
    print("use 'Load Sample Data').")
    print("\nBooking and Holiday Packages will appear automatically as")
    print("development continues.")
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
    Menu shown after a successful login. Search features (browse
    only - no booking yet) cover Flights/Trains (Stage 4) and
    Hotels/Cabs (Stage 5). Booking itself is added to this menu
    in Stage 6 without changing how it's reached.
    """
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header(f"WELCOME, {current_user['full_name'].upper()}")
        print("1. Search Flights")
        print("2. Search Trains")
        print("3. Search Hotels")
        print("4. Search Cabs")
        print("5. View My Profile")
        print("6. Edit My Profile")
        print("7. Change Password")
        print("0. Logout")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            flights.search_flights()
        elif choice == "2":
            trains.search_trains()
        elif choice == "3":
            hotels.search_hotels()
        elif choice == "4":
            cabs.search_cabs()
        elif choice == "5":
            user.view_profile(current_user)
        elif choice == "6":
            current_user = user.edit_profile(current_user)
        elif choice == "7":
            user.change_password(current_user)
        elif choice == "0":
            utils.log_activity(f"User logged out: {current_user['email']}")
            utils.print_info("You have been logged out.")
            utils.pause()
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def handle_admin_login():
    """
    Runs the admin login flow. If no admin accounts exist yet,
    offers to create the very first one instead (bootstrap).
    Returns the logged-in admin dict on success, or None.
    """
    if admin.get_admin_count() == 0:
        utils.print_info("No admin accounts exist yet.")
        if utils.confirm("Would you like to create the first admin account now? (y/n): "):
            success, message = admin.register_admin(is_bootstrap=True)
            if success:
                utils.print_success(message + " Please log in now.")
            else:
                utils.print_error(message)
            utils.pause()
        return None

    success, result = admin.admin_login()
    if success:
        utils.print_success(f"Welcome, {result['admin_name']}!")
        utils.pause()
        return result
    else:
        utils.print_error(result)
        utils.pause()
        return None


def flights_management_menu():
    """Admin submenu for managing Flights (Stage 4)."""
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MANAGE FLIGHTS")
        print("1. View / Search Flights")
        print("2. Add New Flight")
        print("3. Edit Flight")
        print("4. Delete Flight")
        print("0. Back to Admin Panel")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            flights.admin_view_flights()
        elif choice == "2":
            flights.admin_add_flight()
        elif choice == "3":
            flights.admin_edit_flight()
        elif choice == "4":
            flights.admin_delete_flight()
        elif choice == "0":
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def trains_management_menu():
    """Admin submenu for managing Trains (Stage 4)."""
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MANAGE TRAINS")
        print("1. View / Search Trains")
        print("2. Add New Train")
        print("3. Edit Train")
        print("4. Delete Train")
        print("0. Back to Admin Panel")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            trains.admin_view_trains()
        elif choice == "2":
            trains.admin_add_train()
        elif choice == "3":
            trains.admin_edit_train()
        elif choice == "4":
            trains.admin_delete_train()
        elif choice == "0":
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def hotels_management_menu():
    """Admin submenu for managing Hotels and Rooms (Stage 5)."""
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MANAGE HOTELS")
        print("1. View / Search Hotels")
        print("2. Add New Hotel")
        print("3. Edit Hotel")
        print("4. Delete Hotel")
        print("5. Manage Rooms for a Hotel")
        print("0. Back to Admin Panel")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            hotels.admin_view_hotels()
        elif choice == "2":
            hotels.admin_add_hotel()
        elif choice == "3":
            hotels.admin_edit_hotel()
        elif choice == "4":
            hotels.admin_delete_hotel()
        elif choice == "5":
            hotels.admin_manage_rooms()
        elif choice == "0":
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def cabs_management_menu():
    """Admin submenu for managing Cabs (Stage 5)."""
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MANAGE CABS")
        print("1. View / Search Cabs")
        print("2. Add New Cab")
        print("3. Edit Cab")
        print("4. Delete Cab")
        print("0. Back to Admin Panel")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            cabs.admin_view_cabs()
        elif choice == "2":
            cabs.admin_add_cab()
        elif choice == "3":
            cabs.admin_edit_cab()
        elif choice == "4":
            cabs.admin_delete_cab()
        elif choice == "0":
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def handle_load_sample_data():
    """Triggers seed_data.run_full_seed() and reports what happened."""
    utils.print_header("LOAD SAMPLE DATA")
    print("This loads sample Airports, Stations, Flights, Trains,")
    print("Hotels/Rooms, and Cabs data. Tables that already contain")
    print("data are left untouched.")

    if not utils.confirm("Proceed? (y/n): "):
        utils.print_info("Cancelled.")
        utils.pause()
        return

    print("\nLoading... this may take a few seconds.")
    summary = seed_data.run_full_seed()

    utils.print_success("Sample data check complete.")
    print(f"  Airports in database  : {summary['airports']}")
    print(f"  Stations in database   : {summary['stations']}")
    print(f"  Flights newly added    : {summary['flights_inserted'] or 'already had data, skipped'}")
    print(f"  Trains newly added     : {summary['trains_inserted'] or 'already had data, skipped'}")
    print(f"  Hotels newly added     : {summary['hotels_inserted'] or 'already had data, skipped'}")
    print(f"  Rooms newly added      : {summary['rooms_inserted'] or 'already had data, skipped'}")
    print(f"  Cabs newly added       : {summary['cabs_inserted'] or 'already had data, skipped'}")
    utils.pause()


def admin_dashboard(current_admin):
    """
    Menu shown after a successful admin login. Covers user account
    management (Stage 3), flight/train management (Stage 4), and
    hotel/cab management (Stage 5). As more tables are added in
    later stages, this menu grows with them.
    """
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header(f"ADMIN PANEL - {current_admin['admin_name'].upper()}")
        print("1. View All Users")
        print("2. Search Users")
        print("3. Activate / Deactivate User")
        print("4. Delete User")
        print("5. Add New Admin")
        print("6. Manage Flights")
        print("7. Manage Trains")
        print("8. Manage Hotels")
        print("9. Manage Cabs")
        print("10. Load Sample Data (Airports/Stations/Flights/Trains/Hotels/Cabs)")
        print("0. Logout")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            admin.view_all_users()
        elif choice == "2":
            admin.search_users()
        elif choice == "3":
            admin.toggle_user_status()
        elif choice == "4":
            admin.delete_user()
        elif choice == "5":
            success, message = admin.register_admin(is_bootstrap=False)
            if success:
                utils.print_success(message)
            else:
                utils.print_error(message)
            utils.pause()
        elif choice == "6":
            flights_management_menu()
        elif choice == "7":
            trains_management_menu()
        elif choice == "8":
            hotels_management_menu()
        elif choice == "9":
            cabs_management_menu()
        elif choice == "10":
            handle_load_sample_data()
        elif choice == "0":
            utils.log_activity(f"Admin logged out: {current_admin['email']}")
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
        print("3. Admin Login")
        print("4. Test Database Connection")
        print("5. Initialize Database")
        print("6. About")
        print("7. Help")
        print("0. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            logged_in_user = handle_login()
            if logged_in_user is not None:
                user_dashboard(logged_in_user)
        elif choice == "2":
            handle_register()
        elif choice == "3":
            logged_in_admin = handle_admin_login()
            if logged_in_admin is not None:
                admin_dashboard(logged_in_admin)
        elif choice == "4":
            handle_test_connection()
        elif choice == "5":
            handle_initialize_database()
        elif choice == "6":
            show_about()
        elif choice == "7":
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