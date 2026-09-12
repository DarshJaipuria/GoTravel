"""
flights.py
=====================================================
Everything related to Flights:
    - search_flights()      - used by logged-in users (browse only,
                               booking itself lives in booking.py)
    - Admin management: view/search all flights, add, edit, delete

Depends on the Airports table (reference data) which is
populated by seed_data.py.

Every function below lets the user type 'back' at any prompt
to cancel out and return to the menu (see utils.GoBack).
=====================================================
"""

from datetime import date

import database
import utils


def get_all_airports():
    """Returns every airport as a list of dicts, ordered by city."""
    return database.fetch_query("SELECT * FROM Airports ORDER BY city") or []


def _print_airport_reference():
    """Prints a compact code -> city reference table for prompts."""
    airports = get_all_airports()
    if not airports:
        print("\nNo airports found. Ask an admin to load sample data first.")
        return
    rows = [[a["airport_code"], a["city"], a["airport_name"]] for a in airports]
    utils.print_table(["Code", "City", "Airport Name"], rows)


FLIGHT_SEARCH_QUERY = """
    SELECT
        f.flight_id, f.flight_number, f.airline_name,
        f.travel_date, f.departure_time, f.arrival_time, f.duration_minutes,
        f.price, f.available_seats, f.status,
        a1.city AS source_city, a1.airport_code AS source_code,
        a2.city AS destination_city, a2.airport_code AS destination_code
    FROM Flights f
    JOIN Airports a1 ON f.source_airport_id = a1.airport_id
    JOIN Airports a2 ON f.destination_airport_id = a2.airport_id
    WHERE LOWER(a1.city) LIKE %s AND LOWER(a2.city) LIKE %s
"""


def _format_flight_rows(flights):
    return [
        [
            f["flight_id"], f["flight_number"], f["airline_name"],
            f"{f['source_city']} ({f['source_code']})",
            f"{f['destination_city']} ({f['destination_code']})",
            str(f["travel_date"]), str(f["departure_time"])[:5], str(f["arrival_time"])[:5],
            f"Rs. {f['price']}", f["available_seats"], f["status"],
        ]
        for f in flights
    ]


def search_flights():
    """
    User-facing flight search. Asks for source city, destination
    city, and an optional travel date. Shows matching upcoming
    flights. Browse only - booking is done from the Bookings menu.
    """
    utils.print_header("SEARCH FLIGHTS", show_back_hint=True)
    _print_airport_reference()

    try:
        source_city = utils.get_non_empty_input("\nFrom (city): ")
        destination_city = utils.get_non_empty_input("To (city): ")
        travel_date_input = utils.get_valid_date(
            "Travel Date (YYYY-MM-DD, press Enter for any upcoming date): ", allow_blank=True
        )
    except utils.GoBack:
        utils.print_info("Search cancelled.")
        utils.pause()
        return

    query = FLIGHT_SEARCH_QUERY
    params = [f"%{source_city.lower()}%", f"%{destination_city.lower()}%"]

    if travel_date_input:
        query += " AND f.travel_date = %s"
        params.append(travel_date_input)
    else:
        query += " AND f.travel_date >= %s"
        params.append(date.today())

    query += " AND f.status = 'Scheduled' ORDER BY f.travel_date, f.departure_time LIMIT 30"

    flights = database.fetch_query(query, tuple(params))

    if flights is None:
        utils.print_error("Search failed.")
    elif not flights:
        utils.print_info("No flights found matching your search.")
    else:
        utils.print_header(f"{len(flights)} FLIGHT(S) FOUND (showing up to 30)")
        utils.print_table(
            ["ID", "Flight No.", "Airline", "From", "To", "Date", "Dep.", "Arr.", "Price", "Seats", "Status"],
            _format_flight_rows(flights),
        )

    utils.pause()


# ---------------------------------------------------------
# Admin management
# ---------------------------------------------------------

def admin_view_flights():
    """
    Admin flight listing with optional filters. Blank inputs mean
    'no filter on this field'. Shows up to 40 results at a time.
    """
    utils.print_header("VIEW / SEARCH FLIGHTS", show_back_hint=True)
    try:
        source_city = utils.get_input("From (city, optional): ", default="")
        destination_city = utils.get_input("To (city, optional): ", default="")
    except utils.GoBack:
        utils.print_info("Cancelled.")
        utils.pause()
        return

    query = FLIGHT_SEARCH_QUERY
    params = [f"%{source_city.lower()}%", f"%{destination_city.lower()}%"]
    query += " ORDER BY f.travel_date, f.departure_time LIMIT 40"

    flights = database.fetch_query(query, tuple(params))

    if not flights:
        utils.print_info("No flights found.")
    else:
        utils.print_header(f"{len(flights)} FLIGHT(S) (showing up to 40)")
        utils.print_table(
            ["ID", "Flight No.", "Airline", "From", "To", "Date", "Dep.", "Arr.", "Price", "Seats", "Status"],
            _format_flight_rows(flights),
        )
    utils.pause()


def admin_add_flight():
    """Collects details for a new flight and inserts it."""
    utils.print_header("ADD NEW FLIGHT", show_back_hint=True)
    _print_airport_reference()

    airports = {a["airport_code"]: a for a in get_all_airports()}
    if not airports:
        utils.print_error("No airports available. Load sample data first.")
        utils.pause()
        return

    try:
        flight_number = utils.get_non_empty_input("\nFlight Number (e.g. 6E203): ")
        airline_name = utils.get_non_empty_input("Airline Name: ")

        while True:
            source_code = utils.get_non_empty_input("Source Airport Code: ").upper()
            if source_code in airports:
                break
            print("Unknown airport code. Please use one from the list above.")

        while True:
            dest_code = utils.get_non_empty_input("Destination Airport Code: ").upper()
            if dest_code == source_code:
                print("Destination must be different from source.")
                continue
            if dest_code in airports:
                break
            print("Unknown airport code. Please use one from the list above.")

        travel_date_input = utils.get_valid_date("Travel Date (YYYY-MM-DD): ", disallow_past=True)
        departure_time = utils.get_non_empty_input("Departure Time (HH:MM, 24-hour): ")
        arrival_time = utils.get_non_empty_input("Arrival Time (HH:MM, 24-hour): ")
    except utils.GoBack:
        utils.print_info("Add cancelled. No flight was added.")
        utils.pause()
        return

    try:
        dep_h, dep_m = map(int, departure_time.split(":"))
        arr_h, arr_m = map(int, arrival_time.split(":"))
        duration_minutes = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)
        if duration_minutes <= 0:
            duration_minutes += 24 * 60  # arrival is next day
    except ValueError:
        utils.print_error("Invalid time format. Flight not added.")
        utils.pause()
        return

    try:
        price = float(utils.get_non_empty_input("Price (Rs.): "))
        total_seats = int(utils.get_non_empty_input("Total Seats: "))
    except utils.GoBack:
        utils.print_info("Add cancelled. No flight was added.")
        utils.pause()
        return
    except ValueError:
        utils.print_error("Price and seats must be numbers. Flight not added.")
        utils.pause()
        return

    success, result = database.execute_query(
        """
        INSERT INTO Flights (
            flight_number, airline_name, source_airport_id, destination_airport_id,
            travel_date, departure_time, arrival_time, duration_minutes,
            price, total_seats, available_seats, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Scheduled')
        """,
        (
            flight_number, airline_name, airports[source_code]["airport_id"],
            airports[dest_code]["airport_id"], travel_date_input, departure_time,
            arrival_time, duration_minutes, price, total_seats, total_seats,
        ),
    )

    if success:
        utils.print_success(f"Flight {flight_number} added successfully (ID: {result}).")
        utils.log_activity(f"Admin added flight: {flight_number}")
    else:
        utils.print_error(f"Could not add flight: {result}")
    utils.pause()


def _fetch_flight_by_id(flight_id):
    """Looks up a flight by ID (any status)."""
    return database.fetch_query(
        "SELECT * FROM Flights WHERE flight_id = %s", (flight_id,), fetch_one=True
    )


def admin_edit_flight():
    """Edits an existing flight's price, seats, or status by ID."""
    utils.print_header("EDIT FLIGHT", show_back_hint=True)
    try:
        flight = utils.get_record_by_id(
            "Enter Flight ID: ",
            _fetch_flight_by_id,
            "No flight found with that ID.",
        )

        print(f"\nEditing Flight {flight['flight_number']} - press Enter to keep current value.\n")

        price_input = utils.get_input(f"Price [Rs. {flight['price']}]: ")
        price = float(price_input) if price_input else flight["price"]

        seats_input = utils.get_input(f"Available Seats [{flight['available_seats']}]: ")
        available_seats = int(seats_input) if seats_input else flight["available_seats"]

        status = utils.get_input(
            f"Status [{flight['status']}] (Scheduled/Delayed/Cancelled): ", default=flight["status"]
        )
    except utils.GoBack:
        utils.print_info("Edit cancelled. No changes were made.")
        utils.pause()
        return

    success, result = database.execute_query(
        "UPDATE Flights SET price = %s, available_seats = %s, status = %s WHERE flight_id = %s",
        (price, available_seats, status, flight["flight_id"]),
    )

    if success:
        utils.print_success("Flight updated successfully.")
        utils.log_activity(f"Admin edited flight ID {flight['flight_id']}")
    else:
        utils.print_error(f"Could not update flight: {result}")
    utils.pause()


def admin_delete_flight():
    """Deletes a flight by ID, after confirmation."""
    utils.print_header("DELETE FLIGHT", show_back_hint=True)
    try:
        flight = utils.get_record_by_id(
            "Enter Flight ID: ",
            _fetch_flight_by_id,
            "No flight found with that ID.",
        )

        print(f"\nYou are about to delete flight {flight['flight_number']} "
              f"on {flight['travel_date']}.")
        if not utils.confirm("This cannot be undone. Continue? (y/n): "):
            utils.print_info("Deletion cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    success, result = database.execute_query(
        "DELETE FROM Flights WHERE flight_id = %s", (flight["flight_id"],)
    )

    if success:
        utils.print_success("Flight deleted successfully.")
        utils.log_activity(f"Admin deleted flight ID {flight['flight_id']}")
    else:
        utils.print_error(f"Could not delete flight: {result}")
    utils.pause()