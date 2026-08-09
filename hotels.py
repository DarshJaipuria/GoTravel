"""
hotels.py
=====================================================
Everything related to Hotels and Rooms:
    - search_hotels()       - used by logged-in users (browse only,
                               booking is added in Stage 6)
    - Admin management: view/search hotels, add/edit/delete hotels,
      and manage each hotel's room types

A hotel can have several room types (Single, Double, Deluxe,
Suite), each with its own price and availability - so hotel
management and room management are handled as two related but
separate sets of functions.
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
    types and prices. Browse only - no booking yet (Stage 6).
    """
    utils.print_header("SEARCH HOTELS")

    city = utils.get_non_empty_input("City: ")
    min_rating_input = input("Minimum Star Rating (1-5, optional): ").strip()

    query = "SELECT * FROM Hotels WHERE city LIKE %s"
    params = [f"%{city}%"]

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
    utils.print_header("VIEW / SEARCH HOTELS")
    city = input("City (optional): ").strip()

    query = "SELECT * FROM Hotels WHERE city LIKE %s ORDER BY city, hotel_name LIMIT 40"
    hotels = database.fetch_query(query, (f"%{city}%",))

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
    utils.print_header("ADD NEW HOTEL")

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

    if utils.confirm("Add a room type for this hotel now? (y/n): "):
        _add_room_type(hotel_id)

    utils.pause()


def _add_room_type(hotel_id):
    """Collects one room type's details and inserts it for the given hotel."""
    print("\nRoom Types: Single, Double, Deluxe, Suite (or your own label)")
    room_type = utils.get_non_empty_input("Room Type: ")

    try:
        price_per_night = float(utils.get_non_empty_input("Price per Night (Rs.): "))
        total_rooms = int(utils.get_non_empty_input("Total Rooms of this type: "))
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
    utils.print_header("EDIT HOTEL")
    hotel_id_input = utils.get_non_empty_input("Enter Hotel ID: ")
    if not hotel_id_input.isdigit():
        utils.print_error("Hotel ID must be a number.")
        utils.pause()
        return

    hotel = database.fetch_query(
        "SELECT * FROM Hotels WHERE hotel_id = %s", (int(hotel_id_input),), fetch_one=True
    )
    if hotel is None:
        utils.print_error("No hotel found with that ID.")
        utils.pause()
        return

    print(f"\nEditing {hotel['hotel_name']} - press Enter to keep current value.\n")

    rating_input = input(f"Star Rating [{hotel['star_rating']}]: ").strip()
    star_rating = int(rating_input) if rating_input.isdigit() else hotel["star_rating"]

    contact_number = input(f"Contact Number [{hotel['contact_number']}]: ").strip() or hotel["contact_number"]

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
    utils.print_header("DELETE HOTEL")
    hotel_id_input = utils.get_non_empty_input("Enter Hotel ID: ")
    if not hotel_id_input.isdigit():
        utils.print_error("Hotel ID must be a number.")
        utils.pause()
        return

    hotel = database.fetch_query(
        "SELECT * FROM Hotels WHERE hotel_id = %s", (int(hotel_id_input),), fetch_one=True
    )
    if hotel is None:
        utils.print_error("No hotel found with that ID.")
        utils.pause()
        return

    print(f"\nYou are about to delete '{hotel['hotel_name']}' and all its room types.")
    if not utils.confirm("This cannot be undone. Continue? (y/n): "):
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
    utils.print_header("MANAGE ROOMS")
    hotel_id_input = utils.get_non_empty_input("Enter Hotel ID: ")
    if not hotel_id_input.isdigit():
        utils.print_error("Hotel ID must be a number.")
        utils.pause()
        return

    hotel = database.fetch_query(
        "SELECT * FROM Hotels WHERE hotel_id = %s", (int(hotel_id_input),), fetch_one=True
    )
    if hotel is None:
        utils.print_error("No hotel found with that ID.")
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
    room_id_input = utils.get_non_empty_input("Enter Room ID to edit: ")
    if not room_id_input.isdigit():
        utils.print_error("Room ID must be a number.")
        utils.pause()
        return

    room = database.fetch_query(
        "SELECT * FROM Rooms WHERE room_id = %s", (int(room_id_input),), fetch_one=True
    )
    if room is None:
        utils.print_error("No room found with that ID.")
        utils.pause()
        return

    price_input = input(f"Price per Night [Rs. {room['price_per_night']}]: ").strip()
    price_per_night = float(price_input) if price_input else room["price_per_night"]

    available_input = input(f"Available Rooms [{room['available_rooms']}]: ").strip()
    available_rooms = int(available_input) if available_input else room["available_rooms"]

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
    room_id_input = utils.get_non_empty_input("Enter Room ID to delete: ")
    if not room_id_input.isdigit():
        utils.print_error("Room ID must be a number.")
        utils.pause()
        return

    room = database.fetch_query(
        "SELECT * FROM Rooms WHERE room_id = %s", (int(room_id_input),), fetch_one=True
    )
    if room is None:
        utils.print_error("No room found with that ID.")
        utils.pause()
        return

    if not utils.confirm(f"Delete room type '{room['room_type']}'? (y/n): "):
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