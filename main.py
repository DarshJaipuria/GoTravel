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
import packages
import coupons
import booking
import wallet
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
    print("\nCurrent build: Stage 7 - Payments, Wallet & Coupons")
    utils.pause()


def show_help():
    utils.print_header("HELP")
    print("This is the GoTravel command line interface.")
    print("Use the number keys to navigate the menus shown on screen.")
    print("\nAvailable right now (Stage 7):")
    print("  1. Login")
    print("  2. Register")
    print("  3. Admin Login")
    print("  4. Test Database Connection")
    print("  5. Initialize Database")
    print("  6. About")
    print("  7. Help")
    print("  0. Exit")
    print("\nOnce logged in as a user, you can search Flights, Trains,")
    print("Hotels, Cabs, and Holiday Packages, then book them from the")
    print("Bookings menu (note the ID shown in search results, then use")
    print("it to book). At checkout you can optionally apply a coupon")
    print("code, then pay from your Wallet, or via simulated Card/UPI.")
    print("Top up your Wallet any time from the My Wallet menu. You can")
    print("also view or cancel your bookings from the Bookings menu -")
    print("cancelling always refunds the amount paid back to your")
    print("Wallet - and view/edit your profile. Admins can manage user")
    print("accounts, manage Flights/Trains/Hotels/Cabs/Packages/Coupons,")
    print("view all bookings, and load sample data from the admin")
    print("dashboard (first time only - use 'Load Sample Data').")
    print("\nTip: while filling in any form (login, registration, add/edit")
    print("forms, bookings, etc.), type 'back' at any prompt to cancel out")
    print("and return to the menu - you don't need to finish the form or")
    print("restart the program.")
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

    try:
        if not utils.confirm("Proceed? (y/n): "):
            utils.print_info("Initialization cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Cancelled.")
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
    elif message:
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
        if result:
            utils.print_error(result)
        utils.pause()
        return None


def bookings_menu(current_user):
    """
    Stage 6 submenu: book Flights/Trains/Hotels/Cabs/Packages,
    view booking history, or cancel a booking. Kept as its own
    submenu (like the admin management menus) so the main user
    dashboard doesn't get too crowded.
    """
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MY BOOKINGS")
        print("1. Book a Flight")
        print("2. Book a Train")
        print("3. Book a Hotel Room")
        print("4. Book a Cab")
        print("5. Book a Holiday Package")
        print("6. View My Bookings")
        print("7. Cancel a Booking")
        print("0. Back")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            booking.book_flight(current_user)
        elif choice == "2":
            booking.book_train(current_user)
        elif choice == "3":
            booking.book_hotel(current_user)
        elif choice == "4":
            booking.book_cab(current_user)
        elif choice == "5":
            booking.book_package(current_user)
        elif choice == "6":
            booking.view_my_bookings(current_user)
        elif choice == "7":
            booking.cancel_booking(current_user)
        elif choice == "0":
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def wallet_menu(current_user):
    """
    Stage 7 submenu: view wallet balance/transaction history or
    add funds (simulated top-up). Kept as its own submenu, like
    the Bookings submenu, so the main user dashboard doesn't get
    too crowded.
    """
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MY WALLET")
        print("1. View Wallet & Transaction History")
        print("2. Add Money to Wallet")
        print("0. Back")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            wallet.view_wallet(current_user)
        elif choice == "2":
            wallet.add_funds(current_user)
        elif choice == "0":
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def user_dashboard(current_user):
    """
    Menu shown after a successful login. Search features cover
    Flights/Trains (Stage 4), Hotels/Cabs (Stage 5), and Holiday
    Packages (Stage 6). Booking, viewing, and cancelling live in
    the Bookings submenu (Stage 6), which now also handles coupons
    and payment method selection at checkout (Stage 7). Wallet
    top-ups and history live in their own submenu (Stage 7).
    """
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header(f"WELCOME, {current_user['full_name'].upper()}")
        print("1. Search Flights")
        print("2. Search Trains")
        print("3. Search Hotels")
        print("4. Search Cabs")
        print("5. Search Holiday Packages")
        print("6. My Bookings (Book / View / Cancel)")
        print("7. My Wallet (View / Add Funds)")
        print("8. View My Profile")
        print("9. Edit My Profile")
        print("10. Change Password")
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
            packages.search_packages()
        elif choice == "6":
            bookings_menu(current_user)
        elif choice == "7":
            wallet_menu(current_user)
        elif choice == "8":
            user.view_profile(current_user)
        elif choice == "9":
            current_user = user.edit_profile(current_user)
        elif choice == "10":
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
        try:
            wants_bootstrap = utils.confirm(
                "Would you like to create the first admin account now? (y/n): "
            )
        except utils.GoBack:
            utils.print_info("Cancelled.")
            utils.pause()
            return None

        if wants_bootstrap:
            success, message = admin.register_admin(is_bootstrap=True)
            if success:
                utils.print_success(message + " Please log in now.")
            elif message:
                utils.print_error(message)
            utils.pause()
        return None

    success, result = admin.admin_login()
    if success:
        utils.print_success(f"Welcome, {result['admin_name']}!")
        utils.pause()
        return result
    else:
        if result:
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


def packages_management_menu():
    """Admin submenu for managing Holiday Packages (Stage 6)."""
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MANAGE HOLIDAY PACKAGES")
        print("1. View / Search Packages")
        print("2. Add New Package")
        print("3. Edit Package")
        print("4. Delete Package")
        print("0. Back to Admin Panel")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            packages.admin_view_packages()
        elif choice == "2":
            packages.admin_add_package()
        elif choice == "3":
            packages.admin_edit_package()
        elif choice == "4":
            packages.admin_delete_package()
        elif choice == "0":
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def coupons_management_menu():
    """Admin submenu for managing Coupons (Stage 7)."""
    while True:
        utils.clear_screen()
        utils.print_logo()
        utils.print_header("MANAGE COUPONS")
        print("1. View / Search Coupons")
        print("2. Add New Coupon")
        print("3. Edit Coupon")
        print("4. Delete Coupon")
        print("0. Back to Admin Panel")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            coupons.admin_view_coupons()
        elif choice == "2":
            coupons.admin_add_coupon()
        elif choice == "3":
            coupons.admin_edit_coupon()
        elif choice == "4":
            coupons.admin_delete_coupon()
        elif choice == "0":
            return
        else:
            utils.print_error("Invalid choice. Please select a valid menu option.")
            utils.pause()


def handle_load_sample_data():
    """Triggers seed_data.run_full_seed() and reports what happened."""
    utils.print_header("LOAD SAMPLE DATA")
    print("This loads sample Airports, Stations, Flights, Trains,")
    print("Hotels/Rooms, Cabs, Holiday Packages, and Coupons data.")
    print("Airports/Stations/Hotels/Rooms/Packages are only filled in")
    print("if they're currently empty - existing ones are left alone.")
    print("Flights, Trains, Cabs, and Coupons are different: since")
    print("their dates (travel date / expiry date) go stale over time,")
    print("those four are ALWAYS cleared out and freshly regenerated")
    print("every time you run this, dated from today onward. This also")
    print("removes any coupon you added yourself through Manage Coupons.")

    try:
        if not utils.confirm("Proceed? (y/n): "):
            utils.print_info("Cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Cancelled.")
        utils.pause()
        return

    print("\nLoading... this may take a few seconds.")
    summary = seed_data.run_full_seed()

    utils.print_success("Sample data loaded.")
    print(f"  Airports in database   : {summary['airports']}")
    print(f"  Stations in database   : {summary['stations']}")
    print(f"  Flights (refreshed)    : {summary['flights_inserted']}")
    print(f"  Trains (refreshed)     : {summary['trains_inserted']}")
    print(f"  Hotels newly added     : {summary['hotels_inserted'] or 'already had data, skipped'}")
    print(f"  Rooms newly added      : {summary['rooms_inserted'] or 'already had data, skipped'}")
    print(f"  Cabs (refreshed)       : {summary['cabs_inserted']}")
    print(f"  Packages newly added   : {summary['packages_inserted'] or 'already had data, skipped'}")
    print(f"  Coupons (refreshed)    : {summary['coupons_inserted']}")
    utils.pause()


def admin_dashboard(current_admin):
    """
    Menu shown after a successful admin login. Covers user account
    management (Stage 3), flight/train management (Stage 4),
    hotel/cab management (Stage 5), package management plus a
    read-only view of every booking (Stage 6), and coupon
    management (Stage 7). As more tables are added in later
    stages, this menu grows with them.
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
        print("10. Manage Holiday Packages")
        print("11. Manage Coupons")
        print("12. View All Bookings")
        print("13. Load Sample Data (Airports/Stations/Flights/Trains/Hotels/Cabs/Packages)")
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
            elif message:
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
            packages_management_menu()
        elif choice == "11":
            coupons_management_menu()
        elif choice == "12":
            admin.view_all_bookings()
        elif choice == "13":
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