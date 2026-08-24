"""
hotels.py
=====================================================
Everything related to Hotels and Rooms:
    - search_hotels()       - used by logged-in users (browse only,
                               booking itself lives in booking.py)
    - Admin management: view/search hotels, add/edit/delete hotels,
      and manage each hotel's room types

A hotel can have several room types (Single, Double, Deluxe,
Suite), each with its own price and availability - so hotel
management and room management are handled as two related but
separate sets of functions.

Every function below lets the user type 'back' at any prompt
to cancel out and return to the menu (see utils.GoBack).
=====================================================
"""

import database
import utils


def get_rooms_for_hotel(hotel_id):
    """Returns every room type belonging to one hotel."""
    return database.fetch_query(
        "SELECT * FROM Rooms WHERE hotel_id = %s ORDER BY price_per_night",
        (hotel_id,),
    ) or []


def _format_hotel_with_rooms(hotel):
    """Prints one hotel's details followed by a table of its rooms."""
    stars = "*" * (hotel["star_rating"] or 0)
    print(f"\n{hotel['hotel_name']} ({stars}) - {hotel['city']}")
    print(f"  {hotel['address']}")
    print(f"  Contact: {hotel['contact_number']}")

    rooms = get_rooms_for_hotel(hotel["hotel_id"])
    if rooms:
        rows = [
            [r["room_type"], f"Rs. {r['price_per_night']} / night", r["available_rooms"]]
            for r in rooms
        ]
        utils.print_table(["Room Type", "Price", "Available Rooms"], rows)
    else:
        print("  No room types listed for this hotel.")


def search_hotels():
    """
    User-facing hotel search. Asks for a city and an optional
    minimum star rating. Shows matching hotels with their room
    types and prices. Browse only - booking is done from the
    Bookings menu.
    """
    utils.print_header("SEARCH HOTELS", show_back_hint=True)

    try:
        city = utils.get_non_empty_input("City: ")
        min_rating_input = utils.get_input("Minimum Star Rating (1-5, optional): ", default="")
    except utils.GoBack:
        utils.print_info("Search cancelled.")
        utils.pause()
        return

    query = "SELECT * FROM Hotels WHERE LOWER(city) LIKE %s"
    params = [f"%{city.lower()}%"]

    if min_rating_input.isdigit():
        query += " AND star_rating >= %s"
        params.append(int(min_rating_input))

    query += " ORDER BY star_rating DESC, hotel_name LIMIT 20"

    hotels = database.fetch_query(query, tuple(params))

    if hotels is None:
        utils.print_error("Search failed.")
    elif not hotels:
        utils.print_info("No hotels found matching your search.")
    else:
        utils.print_header(f"{len(hotels)} HOTEL(S) FOUND (showing up to 20)")
        for hotel in hotels:
            _format_hotel_with_rooms(hotel)

    utils.pause()


# ---------------------------------------------------------
# Admin management - Hotels
# ---------------------------------------------------------

def admin_view_hotels():
    """Admin hotel listing with an optional city filter."""
    utils.print_header("VIEW / SEARCH HOTELS", show_back_hint=True)
    try:
        city = utils.get_input("City (optional): ", default="")
    except utils.GoBack:
        utils.print_info("Cancelled.")
        utils.pause()
        return

    query = "SELECT * FROM Hotels WHERE LOWER(city) LIKE %s ORDER BY city, hotel_name LIMIT 40"
    hotels = database.fetch_query(query, (f"%{city.lower()}%",))

    if not hotels:
        utils.print_info("No hotels found.")
    else:
        rows = [
            [h["hotel_id"], h["hotel_name"], h["city"], h["star_rating"], h["contact_number"]]
            for h in hotels
        ]
        utils.print_header(f"{len(hotels)} HOTEL(S) (showing up to 40)")
        utils.print_table(["ID", "Hotel Name", "City", "Stars", "Contact"], rows)
    utils.pause()


def admin_add_hotel():
    """Adds a new hotel, then immediately prompts for its room types."""
    utils.print_header("ADD NEW HOTEL", show_back_hint=True)

    try:
        hotel_name = utils.get_non_empty_input("Hotel Name: ")
        city = utils.get_non_empty_input("City: ")
        address = utils.get_non_empty_input("Address: ")

        while True:
            star_input = utils.get_non_empty_input("Star Rating (1-5): ")
            if star_input.isdigit() and 1 <= int(star_input) <= 5:
                star_rating = int(star_input)
                break
            print("Please enter a number from 1 to 5.")

        contact_number = utils.get_valid_phone("Contact Number (10 digits): ")
    except utils.GoBack:
        utils.print_info("Add cancelled. No hotel was added.")
        utils.pause()
        return

    success, result = database.execute_query(
        "INSERT INTO Hotels (hotel_name, city, address, star_rating, contact_number) "
        "VALUES (%s, %s, %s, %s, %s)",
        (hotel_name, city, address, star_rating, contact_number),
    )

    if not success:
        utils.print_error(f"Could not add hotel: {result}")
        utils.pause()
        return

    hotel_id = result
    utils.print_success(f"Hotel '{hotel_name}' added successfully (ID: {hotel_id}).")
    utils.log_activity(f"Admin added hotel: {hotel_name}")

    try:
        if utils.confirm("Add a room type for this hotel now? (y/n): "):
            _add_room_type(hotel_id)
    except utils.GoBack:
        utils.print_info("Skipped adding a room type.")

    utils.pause()


def _add_room_type(hotel_id):
    """Collects one room type's details and inserts it for the given hotel."""
    print("\nRoom Types: Single, Double, Deluxe, Suite (or your own label)")
    print("(Type 'back' at any prompt to skip adding this room type.)")
    try:
        room_type = utils.get_non_empty_input("Room Type: ")
        price_per_night = float(utils.get_non_empty_input("Price per Night (Rs.): "))
        total_rooms = int(utils.get_non_empty_input("Total Rooms of this type: "))
    except utils.GoBack:
        utils.print_info("Room type not added.")
        return
    except ValueError:
        utils.print_error("Price and room count must be numbers. Room type not added.")
        return

    success, result = database.execute_query(
        "INSERT INTO Rooms (hotel_id, room_type, price_per_night, total_rooms, available_rooms) "
        "VALUES (%s, %s, %s, %s, %s)",
        (hotel_id, room_type, price_per_night, total_rooms, total_rooms),
    )

    if success:
        utils.print_success(f"Room type '{room_type}' added.")
    else:
        utils.print_error(f"Could not add room type: {result}")


def admin_edit_hotel():
    """Edits a hotel's star rating and contact number by ID."""
    utils.print_header("EDIT HOTEL", show_back_hint=True)
    try:
        hotel = utils.get_record_by_id(
            "Enter Hotel ID: ",
            lambda hid: database.fetch_query(
                "SELECT * FROM Hotels WHERE hotel_id = %s", (hid,), fetch_one=True
            ),
            "No hotel found with that ID.",
        )

        print(f"\nEditing {hotel['hotel_name']} - press Enter to keep current value.\n")

        rating_input = utils.get_input(f"Star Rating [{hotel['star_rating']}]: ")
        star_rating = int(rating_input) if rating_input and rating_input.isdigit() else hotel["star_rating"]

        contact_number = utils.get_input(
            f"Contact Number [{hotel['contact_number']}]: ", default=hotel["contact_number"]
        )
    except utils.GoBack:
        utils.print_info("Edit cancelled. No changes were made.")
        utils.pause()
        return

    success, result = database.execute_query(
        "UPDATE Hotels SET star_rating = %s, contact_number = %s WHERE hotel_id = %s",
        (star_rating, contact_number, hotel["hotel_id"]),
    )

    if success:
        utils.print_success("Hotel updated successfully.")
        utils.log_activity(f"Admin edited hotel ID {hotel['hotel_id']}")
    else:
        utils.print_error(f"Could not update hotel: {result}")
    utils.pause()


def admin_delete_hotel():
    """Deletes a hotel AND all its room types by ID, after confirmation."""
    utils.print_header("DELETE HOTEL", show_back_hint=True)
    try:
        hotel = utils.get_record_by_id(
            "Enter Hotel ID: ",
            lambda hid: database.fetch_query(
                "SELECT * FROM Hotels WHERE hotel_id = %s", (hid,), fetch_one=True
            ),
            "No hotel found with that ID.",
        )

        print(f"\nYou are about to delete '{hotel['hotel_name']}' and all its room types.")
        if not utils.confirm("This cannot be undone. Continue? (y/n): "):
            utils.print_info("Deletion cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    database.execute_query("DELETE FROM Rooms WHERE hotel_id = %s", (hotel["hotel_id"],))
    success, result = database.execute_query(
        "DELETE FROM Hotels WHERE hotel_id = %s", (hotel["hotel_id"],)
    )

    if success:
        utils.print_success("Hotel and its room types deleted successfully.")
        utils.log_activity(f"Admin deleted hotel ID {hotel['hotel_id']}")
    else:
        utils.print_error(f"Could not delete hotel: {result}")
    utils.pause()


# ---------------------------------------------------------
# Admin management - Rooms
# ---------------------------------------------------------

def admin_manage_rooms():
    """Lets an admin view a hotel's rooms and add/edit/delete room types."""
    utils.print_header("MANAGE ROOMS", show_back_hint=True)
    try:
        hotel = utils.get_record_by_id(
            "Enter Hotel ID: ",
            lambda hid: database.fetch_query(
                "SELECT * FROM Hotels WHERE hotel_id = %s", (hid,), fetch_one=True
            ),
            "No hotel found with that ID.",
        )
    except utils.GoBack:
        utils.print_info("Cancelled.")
        utils.pause()
        return

    rooms = get_rooms_for_hotel(hotel["hotel_id"])
    utils.print_header(f"ROOMS AT {hotel['hotel_name']}")
    if rooms:
        rows = [
            [r["room_id"], r["room_type"], f"Rs. {r['price_per_night']}",
             r["total_rooms"], r["available_rooms"]]
            for r in rooms
        ]
        utils.print_table(["Room ID", "Type", "Price/Night", "Total", "Available"], rows)
    else:
        print("\nNo room types yet for this hotel.")

    print("\n1. Add Room Type")
    print("2. Edit Room Type")
    print("3. Delete Room Type")
    print("0. Back")
    choice = input("\nEnter your choice: ").strip()

    if choice == "1":
        _add_room_type(hotel["hotel_id"])
        utils.pause()
    elif choice == "2":
        _edit_room_type()
    elif choice == "3":
        _delete_room_type()
    # choice "0" or anything else simply returns


def _edit_room_type():
    try:
        room = utils.get_record_by_id(
            "Enter Room ID to edit: ",
            lambda rid: database.fetch_query(
                "SELECT * FROM Rooms WHERE room_id = %s", (rid,), fetch_one=True
            ),
            "No room found with that ID.",
        )

        price_input = utils.get_input(f"Price per Night [Rs. {room['price_per_night']}]: ")
        price_per_night = float(price_input) if price_input else room["price_per_night"]

        available_input = utils.get_input(f"Available Rooms [{room['available_rooms']}]: ")
        available_rooms = int(available_input) if available_input else room["available_rooms"]
    except utils.GoBack:
        utils.print_info("Edit cancelled. No changes were made.")
        utils.pause()
        return

    success, result = database.execute_query(
        "UPDATE Rooms SET price_per_night = %s, available_rooms = %s WHERE room_id = %s",
        (price_per_night, available_rooms, room["room_id"]),
    )

    if success:
        utils.print_success("Room type updated successfully.")
        utils.log_activity(f"Admin edited room ID {room['room_id']}")
    else:
        utils.print_error(f"Could not update room type: {result}")
    utils.pause()


def _delete_room_type():
    try:
        room = utils.get_record_by_id(
            "Enter Room ID to delete: ",
            lambda rid: database.fetch_query(
                "SELECT * FROM Rooms WHERE room_id = %s", (rid,), fetch_one=True
            ),
            "No room found with that ID.",
        )

        if not utils.confirm(f"Delete room type '{room['room_type']}'? (y/n): "):
            utils.print_info("Deletion cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    success, result = database.execute_query(
        "DELETE FROM Rooms WHERE room_id = %s", (room["room_id"],)
    )

    if success:
        utils.print_success("Room type deleted successfully.")
        utils.log_activity(f"Admin deleted room ID {room['room_id']}")
    else:
        utils.print_error(f"Could not delete room type: {result}")
    utils.pause()