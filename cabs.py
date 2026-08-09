"""
cabs.py
=====================================================
Everything related to Cabs:
    - search_cabs()      - used by logged-in users (browse only,
                            booking is added in Stage 6)
    - Admin management: view/search all cabs, add, edit, delete

Unlike Flights/Trains, a cab is a single vehicle booked as a
whole (not sold seat-by-seat), so availability is tracked with
a simple status: 'Available' or 'Booked'.
=====================================================
"""

from datetime import date

import database
import utils


def _format_cab_rows(cabs):
    return [
        [
            c["cab_id"], c["cab_number"], c["cab_type"], c["driver_name"],
            c["source_city"], c["destination_city"], str(c["travel_date"]),
            str(c["departure_time"])[:5], f"Rs. {c['price']}", c["seats_capacity"], c["status"],
        ]
        for c in cabs
    ]


def search_cabs():
    """
    User-facing cab search. Asks for source city, destination
    city, and an optional travel date. Shows matching available
    cabs. Browse only - no booking yet (added in Stage 6).
    """
    utils.print_header("SEARCH CABS")

    source_city = utils.get_non_empty_input("From (city): ")
    destination_city = utils.get_non_empty_input("To (city): ")
    travel_date_input = utils.get_valid_date(
        "Travel Date (YYYY-MM-DD, press Enter for any upcoming date): ", allow_blank=True
    )

    query = (
        "SELECT * FROM Cabs WHERE source_city LIKE %s AND destination_city LIKE %s "
        "AND status = 'Available'"
    )
    params = [f"%{source_city}%", f"%{destination_city}%"]

    if travel_date_input:
        query += " AND travel_date = %s"
        params.append(travel_date_input)
    else:
        query += " AND travel_date >= %s"
        params.append(date.today())

    query += " ORDER BY travel_date, departure_time LIMIT 30"

    cabs = database.fetch_query(query, tuple(params))

    if cabs is None:
        utils.print_error("Search failed.")
    elif not cabs:
        utils.print_info("No cabs found matching your search.")
    else:
        utils.print_header(f"{len(cabs)} CAB(S) FOUND (showing up to 30)")
        utils.print_table(
            ["ID", "Cab No.", "Type", "Driver", "From", "To", "Date", "Time", "Price", "Seats", "Status"],
            _format_cab_rows(cabs),
        )

    utils.pause()


# ---------------------------------------------------------
# Admin management
# ---------------------------------------------------------

def admin_view_cabs():
    """Admin cab listing with optional route filters."""
    utils.print_header("VIEW / SEARCH CABS")
    source_city = input("From (city, optional): ").strip()
    destination_city = input("To (city, optional): ").strip()

    query = "SELECT * FROM Cabs WHERE source_city LIKE %s AND destination_city LIKE %s"
    params = [f"%{source_city}%", f"%{destination_city}%"]
    query += " ORDER BY travel_date, departure_time LIMIT 40"

    cabs = database.fetch_query(query, tuple(params))

    if not cabs:
        utils.print_info("No cabs found.")
    else:
        utils.print_header(f"{len(cabs)} CAB(S) (showing up to 40)")
        utils.print_table(
            ["ID", "Cab No.", "Type", "Driver", "From", "To", "Date", "Time", "Price", "Seats", "Status"],
            _format_cab_rows(cabs),
        )
    utils.pause()


def admin_add_cab():
    """Collects details for a new cab and inserts it."""
    utils.print_header("ADD NEW CAB")

    cab_number = utils.get_non_empty_input("Cab Registration Number: ")
    cab_type = utils.get_non_empty_input("Cab Type (Hatchback/Sedan/SUV/Mini Van): ")
    driver_name = utils.get_non_empty_input("Driver Name: ")
    source_city = utils.get_non_empty_input("Source City: ")

    while True:
        destination_city = utils.get_non_empty_input("Destination City: ")
        if destination_city.strip().lower() != source_city.strip().lower():
            break
        print("Destination must be different from source.")

    travel_date_input = utils.get_valid_date("Travel Date (YYYY-MM-DD): ")
    departure_time = input("Departure Time (HH:MM, 24-hour): ").strip()

    try:
        price = float(utils.get_non_empty_input("Price (Rs.): "))
        seats_capacity = int(utils.get_non_empty_input("Seat Capacity: "))
    except ValueError:
        utils.print_error("Price and seat capacity must be numbers. Cab not added.")
        utils.pause()
        return

    success, result = database.execute_query(
        """
        INSERT INTO Cabs (
            cab_number, cab_type, driver_name, source_city, destination_city,
            travel_date, departure_time, price, seats_capacity, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Available')
        """,
        (
            cab_number, cab_type, driver_name, source_city, destination_city,
            travel_date_input, departure_time, price, seats_capacity,
        ),
    )

    if success:
        utils.print_success(f"Cab {cab_number} added successfully (ID: {result}).")
        utils.log_activity(f"Admin added cab: {cab_number}")
    else:
        utils.print_error(f"Could not add cab: {result}")
    utils.pause()


def admin_edit_cab():
    """Edits an existing cab's price or status by ID."""
    utils.print_header("EDIT CAB")
    cab_id_input = utils.get_non_empty_input("Enter Cab ID: ")
    if not cab_id_input.isdigit():
        utils.print_error("Cab ID must be a number.")
        utils.pause()
        return

    cab = database.fetch_query(
        "SELECT * FROM Cabs WHERE cab_id = %s", (int(cab_id_input),), fetch_one=True
    )
    if cab is None:
        utils.print_error("No cab found with that ID.")
        utils.pause()
        return

    print(f"\nEditing Cab {cab['cab_number']} - press Enter to keep current value.\n")

    price_input = input(f"Price [Rs. {cab['price']}]: ").strip()
    price = float(price_input) if price_input else cab["price"]

    status = input(f"Status [{cab['status']}] (Available/Booked): ").strip() or cab["status"]

    success, result = database.execute_query(
        "UPDATE Cabs SET price = %s, status = %s WHERE cab_id = %s",
        (price, status, cab["cab_id"]),
    )

    if success:
        utils.print_success("Cab updated successfully.")
        utils.log_activity(f"Admin edited cab ID {cab['cab_id']}")
    else:
        utils.print_error(f"Could not update cab: {result}")
    utils.pause()


def admin_delete_cab():
    """Deletes a cab by ID, after confirmation."""
    utils.print_header("DELETE CAB")
    cab_id_input = utils.get_non_empty_input("Enter Cab ID: ")
    if not cab_id_input.isdigit():
        utils.print_error("Cab ID must be a number.")
        utils.pause()
        return

    cab = database.fetch_query(
        "SELECT * FROM Cabs WHERE cab_id = %s", (int(cab_id_input),), fetch_one=True
    )
    if cab is None:
        utils.print_error("No cab found with that ID.")
        utils.pause()
        return

    print(f"\nYou are about to delete cab {cab['cab_number']} ({cab['driver_name']}).")
    if not utils.confirm("This cannot be undone. Continue? (y/n): "):
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    success, result = database.execute_query(
        "DELETE FROM Cabs WHERE cab_id = %s", (cab["cab_id"],)
    )

    if success:
        utils.print_success("Cab deleted successfully.")
        utils.log_activity(f"Admin deleted cab ID {cab['cab_id']}")
    else:
        utils.print_error(f"Could not delete cab: {result}")
    utils.pause()