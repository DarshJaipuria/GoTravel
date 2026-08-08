"""
trains.py
=====================================================
Everything related to Trains:
    - search_trains()       - used by logged-in users (browse only,
                               booking is added in Stage 6)
    - Admin management: view/search all trains, add, edit, delete

Depends on the Stations table (reference data) which is
populated by seed_data.py.
=====================================================
"""

from datetime import date

import database
import utils


def get_all_stations():
    """Returns every station as a list of dicts, ordered by city."""
    return database.fetch_query("SELECT * FROM Stations ORDER BY city") or []


def _print_station_reference():
    """Prints a compact code -> city reference table for prompts."""
    stations = get_all_stations()
    if not stations:
        print("\nNo stations found. Ask an admin to load sample data first.")
        return
    rows = [[s["station_code"], s["city"], s["station_name"]] for s in stations]
    utils.print_table(["Code", "City", "Station Name"], rows)


TRAIN_SEARCH_QUERY = """
    SELECT
        t.train_id, t.train_number, t.train_name,
        t.travel_date, t.departure_time, t.arrival_time, t.duration_minutes,
        t.price, t.available_seats, t.status,
        s1.city AS source_city, s1.station_code AS source_code,
        s2.city AS destination_city, s2.station_code AS destination_code
    FROM Trains t
    JOIN Stations s1 ON t.source_station_id = s1.station_id
    JOIN Stations s2 ON t.destination_station_id = s2.station_id
    WHERE s1.city LIKE %s AND s2.city LIKE %s
"""


def _format_train_rows(trains):
    return [
        [
            t["train_id"], t["train_number"], t["train_name"],
            f"{t['source_city']} ({t['source_code']})",
            f"{t['destination_city']} ({t['destination_code']})",
            str(t["travel_date"]), str(t["departure_time"])[:5], str(t["arrival_time"])[:5],
            f"Rs. {t['price']}", t["available_seats"], t["status"],
        ]
        for t in trains
    ]


def search_trains():
    """
    User-facing train search. Asks for source city, destination
    city, and an optional travel date. Shows matching upcoming
    trains. Browse only - no booking yet (added in Stage 6).
    """
    utils.print_header("SEARCH TRAINS")
    _print_station_reference()

    source_city = utils.get_non_empty_input("\nFrom (city): ")
    destination_city = utils.get_non_empty_input("To (city): ")
    travel_date_input = utils.get_valid_date(
        "Travel Date (YYYY-MM-DD, press Enter for any upcoming date): ", allow_blank=True
    )

    query = TRAIN_SEARCH_QUERY
    params = [f"%{source_city}%", f"%{destination_city}%"]

    if travel_date_input:
        query += " AND t.travel_date = %s"
        params.append(travel_date_input)
    else:
        query += " AND t.travel_date >= %s"
        params.append(date.today())

    query += " AND t.status = 'Scheduled' ORDER BY t.travel_date, t.departure_time LIMIT 30"

    trains = database.fetch_query(query, tuple(params))

    if trains is None:
        utils.print_error("Search failed.")
    elif not trains:
        utils.print_info("No trains found matching your search.")
    else:
        utils.print_header(f"{len(trains)} TRAIN(S) FOUND (showing up to 30)")
        utils.print_table(
            ["ID", "Train No.", "Train Name", "From", "To", "Date", "Dep.", "Arr.", "Price", "Seats", "Status"],
            _format_train_rows(trains),
        )

    utils.pause()


# ---------------------------------------------------------
# Admin management
# ---------------------------------------------------------

def admin_view_trains():
    """
    Admin train listing with optional filters. Blank inputs mean
    'no filter on this field'. Shows up to 40 results at a time.
    """
    utils.print_header("VIEW / SEARCH TRAINS")
    source_city = input("From (city, optional): ").strip()
    destination_city = input("To (city, optional): ").strip()

    query = TRAIN_SEARCH_QUERY
    params = [f"%{source_city}%", f"%{destination_city}%"]
    query += " ORDER BY t.travel_date, t.departure_time LIMIT 40"

    trains = database.fetch_query(query, tuple(params))

    if not trains:
        utils.print_info("No trains found.")
    else:
        utils.print_header(f"{len(trains)} TRAIN(S) (showing up to 40)")
        utils.print_table(
            ["ID", "Train No.", "Train Name", "From", "To", "Date", "Dep.", "Arr.", "Price", "Seats", "Status"],
            _format_train_rows(trains),
        )
    utils.pause()


def admin_add_train():
    """Collects details for a new train and inserts it."""
    utils.print_header("ADD NEW TRAIN")
    _print_station_reference()

    stations = {s["station_code"]: s for s in get_all_stations()}
    if not stations:
        utils.print_error("No stations available. Load sample data first.")
        utils.pause()
        return

    train_number = utils.get_non_empty_input("\nTrain Number (5 digits): ")
    train_name = utils.get_non_empty_input("Train Name: ")

    while True:
        source_code = utils.get_non_empty_input("Source Station Code: ").upper()
        if source_code in stations:
            break
        print("Unknown station code. Please use one from the list above.")

    while True:
        dest_code = utils.get_non_empty_input("Destination Station Code: ").upper()
        if dest_code == source_code:
            print("Destination must be different from source.")
            continue
        if dest_code in stations:
            break
        print("Unknown station code. Please use one from the list above.")

    travel_date_input = utils.get_valid_date("Travel Date (YYYY-MM-DD): ")
    departure_time = input("Departure Time (HH:MM, 24-hour): ").strip()
    arrival_time = input("Arrival Time (HH:MM, 24-hour): ").strip()

    try:
        dep_h, dep_m = map(int, departure_time.split(":"))
        arr_h, arr_m = map(int, arrival_time.split(":"))
        duration_minutes = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)
        if duration_minutes <= 0:
            duration_minutes += 24 * 60  # arrival is next day (or later)
    except ValueError:
        utils.print_error("Invalid time format. Train not added.")
        utils.pause()
        return

    try:
        price = float(utils.get_non_empty_input("Price (Rs.): "))
        total_seats = int(utils.get_non_empty_input("Total Seats: "))
    except ValueError:
        utils.print_error("Price and seats must be numbers. Train not added.")
        utils.pause()
        return

    success, result = database.execute_query(
        """
        INSERT INTO Trains (
            train_number, train_name, source_station_id, destination_station_id,
            travel_date, departure_time, arrival_time, duration_minutes,
            price, total_seats, available_seats, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Scheduled')
        """,
        (
            train_number, train_name, stations[source_code]["station_id"],
            stations[dest_code]["station_id"], travel_date_input, departure_time,
            arrival_time, duration_minutes, price, total_seats, total_seats,
        ),
    )

    if success:
        utils.print_success(f"Train {train_number} added successfully (ID: {result}).")
        utils.log_activity(f"Admin added train: {train_number}")
    else:
        utils.print_error(f"Could not add train: {result}")
    utils.pause()


def admin_edit_train():
    """Edits an existing train's price, seats, or status by ID."""
    utils.print_header("EDIT TRAIN")
    train_id_input = utils.get_non_empty_input("Enter Train ID: ")
    if not train_id_input.isdigit():
        utils.print_error("Train ID must be a number.")
        utils.pause()
        return

    train = database.fetch_query(
        "SELECT * FROM Trains WHERE train_id = %s", (int(train_id_input),), fetch_one=True
    )
    if train is None:
        utils.print_error("No train found with that ID.")
        utils.pause()
        return

    print(f"\nEditing Train {train['train_number']} - press Enter to keep current value.\n")

    price_input = input(f"Price [Rs. {train['price']}]: ").strip()
    price = float(price_input) if price_input else train["price"]

    seats_input = input(f"Available Seats [{train['available_seats']}]: ").strip()
    available_seats = int(seats_input) if seats_input else train["available_seats"]

    status = input(f"Status [{train['status']}] (Scheduled/Delayed/Cancelled): ").strip() or train["status"]

    success, result = database.execute_query(
        "UPDATE Trains SET price = %s, available_seats = %s, status = %s WHERE train_id = %s",
        (price, available_seats, status, train["train_id"]),
    )

    if success:
        utils.print_success("Train updated successfully.")
        utils.log_activity(f"Admin edited train ID {train['train_id']}")
    else:
        utils.print_error(f"Could not update train: {result}")
    utils.pause()


def admin_delete_train():
    """Deletes a train by ID, after confirmation."""
    utils.print_header("DELETE TRAIN")
    train_id_input = utils.get_non_empty_input("Enter Train ID: ")
    if not train_id_input.isdigit():
        utils.print_error("Train ID must be a number.")
        utils.pause()
        return

    train = database.fetch_query(
        "SELECT * FROM Trains WHERE train_id = %s", (int(train_id_input),), fetch_one=True
    )
    if train is None:
        utils.print_error("No train found with that ID.")
        utils.pause()
        return

    print(f"\nYou are about to delete train {train['train_number']} "
          f"on {train['travel_date']}.")
    if not utils.confirm("This cannot be undone. Continue? (y/n): "):
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    success, result = database.execute_query(
        "DELETE FROM Trains WHERE train_id = %s", (train["train_id"],)
    )

    if success:
        utils.print_success("Train deleted successfully.")
        utils.log_activity(f"Admin deleted train ID {train['train_id']}")
    else:
        utils.print_error(f"Could not delete train: {result}")
    utils.pause()