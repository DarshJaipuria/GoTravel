"""
packages.py
=====================================================
Everything related to Holiday Packages:
    - search_packages()      - used by logged-in users (browse only,
                                booking itself lives in booking.py)
    - Admin management: view/search all packages, add, edit, delete

A holiday package is a fixed itinerary (destination + number of
days + price) with a limited number of slots, similar in spirit
to how Cabs track a simple availability count rather than
individual seats.

Every function below lets the user type 'back' at any prompt
to cancel out and return to the menu (see utils.GoBack).
=====================================================
"""

import database
import utils


def _format_package_rows(packages):
    return [
        [
            p["package_id"], p["package_name"], p["destination"],
            f"{p['duration_days']}D/{max(p['duration_days'] - 1, 1)}N",
            f"Rs. {p['price']}", p["available_slots"], p["status"],
        ]
        for p in packages
    ]


def search_packages():
    """
    User-facing package search. Asks for a destination (optional)
    and shows matching active packages with slots still available.
    Browse only - booking is done from the Bookings menu.
    """
    utils.print_header("SEARCH HOLIDAY PACKAGES", show_back_hint=True)

    try:
        destination = utils.get_input("Destination (optional, press Enter to see all): ", default="")
    except utils.GoBack:
        utils.print_info("Search cancelled.")
        utils.pause()
        return

    query = (
        "SELECT * FROM Packages WHERE LOWER(destination) LIKE %s "
        "AND status = 'Active' AND available_slots > 0"
    )
    params = [f"%{destination.lower()}%"]
    query += " ORDER BY destination, price LIMIT 30"

    packages = database.fetch_query(query, tuple(params))

    if packages is None:
        utils.print_error("Search failed.")
    elif not packages:
        utils.print_info("No packages found matching your search.")
    else:
        utils.print_header(f"{len(packages)} PACKAGE(S) FOUND (showing up to 30)")
        utils.print_table(
            ["ID", "Package Name", "Destination", "Duration", "Price", "Slots Left", "Status"],
            _format_package_rows(packages),
        )
        for p in packages:
            if p.get("description"):
                print(f"  #{p['package_id']}: {p['description']}")

    utils.pause()


# ---------------------------------------------------------
# Admin management
# ---------------------------------------------------------

def admin_view_packages():
    """Admin package listing with an optional destination filter."""
    utils.print_header("VIEW / SEARCH PACKAGES", show_back_hint=True)
    try:
        destination = utils.get_input("Destination (optional): ", default="")
    except utils.GoBack:
        utils.print_info("Cancelled.")
        utils.pause()
        return

    query = "SELECT * FROM Packages WHERE LOWER(destination) LIKE %s ORDER BY destination LIMIT 40"
    packages = database.fetch_query(query, (f"%{destination.lower()}%",))

    if packages is None:
        utils.print_error("Search failed. Check files/logs.txt for the database error "
                           "(e.g. the Packages table may not exist yet - try Initialize Database).")
    elif not packages:
        utils.print_info("No packages found.")
    else:
        utils.print_header(f"{len(packages)} PACKAGE(S) (showing up to 40)")
        utils.print_table(
            ["ID", "Package Name", "Destination", "Duration", "Price", "Slots Left", "Status"],
            _format_package_rows(packages),
        )
    utils.pause()


def admin_add_package():
    """Collects details for a new holiday package and inserts it."""
    utils.print_header("ADD NEW HOLIDAY PACKAGE", show_back_hint=True)

    try:
        package_name = utils.get_non_empty_input("Package Name: ")
        destination = utils.get_non_empty_input("Destination (city): ")

        while True:
            duration_input = utils.get_non_empty_input("Duration (days): ")
            if duration_input.isdigit() and int(duration_input) > 0:
                duration_days = int(duration_input)
                break
            print("Duration must be a positive whole number.")

        description = utils.get_input("Description (what's included, optional): ")

        while True:
            price_input = utils.get_non_empty_input("Price per person (Rs.): ")
            try:
                price = float(price_input)
                break
            except ValueError:
                print("Price must be a number.")

        while True:
            slots_input = utils.get_non_empty_input("Total Slots (travellers it can take): ")
            if slots_input.isdigit() and int(slots_input) > 0:
                total_slots = int(slots_input)
                break
            print("Total slots must be a positive whole number.")
    except utils.GoBack:
        utils.print_info("Add cancelled. No package was added.")
        utils.pause()
        return

    success, result = database.execute_query(
        """
        INSERT INTO Packages (
            package_name, destination, duration_days, price,
            description, total_slots, available_slots, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
        """,
        (package_name, destination, duration_days, price, description, total_slots, total_slots),
    )

    if success:
        utils.print_success(f"Package '{package_name}' added successfully (ID: {result}).")
        utils.log_activity(f"Admin added package: {package_name}")
    else:
        utils.print_error(f"Could not add package: {result}")
    utils.pause()


def _fetch_package_by_id(package_id):
    """Looks up a package by ID (any status)."""
    return database.fetch_query(
        "SELECT * FROM Packages WHERE package_id = %s", (package_id,), fetch_one=True
    )


def admin_edit_package():
    """Edits an existing package's price, slots, or status by ID."""
    utils.print_header("EDIT PACKAGE", show_back_hint=True)
    try:
        package = utils.get_record_by_id(
            "Enter Package ID: ",
            _fetch_package_by_id,
            "No package found with that ID.",
        )

        print(f"\nEditing {package['package_name']} - press Enter to keep current value.\n")

        price_input = utils.get_input(f"Price [Rs. {package['price']}]: ")
        price = float(price_input) if price_input else package["price"]

        slots_input = utils.get_input(f"Available Slots [{package['available_slots']}]: ")
        available_slots = int(slots_input) if slots_input else package["available_slots"]

        status = utils.get_input(
            f"Status [{package['status']}] (Active/Inactive): ", default=package["status"]
        )
    except utils.GoBack:
        utils.print_info("Edit cancelled. No changes were made.")
        utils.pause()
        return

    success, result = database.execute_query(
        "UPDATE Packages SET price = %s, available_slots = %s, status = %s WHERE package_id = %s",
        (price, available_slots, status, package["package_id"]),
    )

    if success:
        utils.print_success("Package updated successfully.")
        utils.log_activity(f"Admin edited package ID {package['package_id']}")
    else:
        utils.print_error(f"Could not update package: {result}")
    utils.pause()


def admin_delete_package():
    """Deletes a package by ID, after confirmation."""
    utils.print_header("DELETE PACKAGE", show_back_hint=True)
    try:
        package = utils.get_record_by_id(
            "Enter Package ID: ",
            _fetch_package_by_id,
            "No package found with that ID.",
        )

        print(f"\nYou are about to delete package '{package['package_name']}' ({package['destination']}).")
        if not utils.confirm("This cannot be undone. Continue? (y/n): "):
            utils.print_info("Deletion cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    success, result = database.execute_query(
        "DELETE FROM Packages WHERE package_id = %s", (package["package_id"],)
    )

    if success:
        utils.print_success("Package deleted successfully.")
        utils.log_activity(f"Admin deleted package ID {package['package_id']}")
    else:
        utils.print_error(f"Could not delete package: {result}")
    utils.pause()