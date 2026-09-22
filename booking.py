"""
booking.py
=====================================================
The booking engine: book/view/cancel Flights, Trains, Hotels,
Cabs, and Packages, all stored in one Bookings table. Checkout
also handles coupons and payment (Wallet/Card/UPI).
=====================================================
"""

import coupons
import database
import invoices
import utils
import wallet

PAYMENT_METHODS = ["Wallet", "Card", "UPI"]


# ---------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------

def _insert_booking(user_id, booking_type, item_id, item_label,
                     travel_date, quantity, nights, unit_price, total_amount,
                     payment_method, coupon_code, discount_amount):
    """Inserts one row into Bookings. Returns (success, booking_id_or_error)."""
    return database.execute_query(
        """
        INSERT INTO Bookings (
            user_id, booking_type, item_id, item_label, travel_date,
            quantity, nights, unit_price, total_amount, booking_status,
            payment_method, coupon_code, discount_amount
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed', %s, %s, %s)
        """,
        (user_id, booking_type, item_id, item_label, travel_date,
         quantity, nights, unit_price, total_amount,
         payment_method, coupon_code, discount_amount),
    )


def _fetch_bookable_flight(flight_id):
    """Looks up a Scheduled flight by ID, with its source/destination city names."""
    return database.fetch_query(
        """
        SELECT f.*, a1.city AS source_city, a2.city AS destination_city
        FROM Flights f
        JOIN Airports a1 ON f.source_airport_id = a1.airport_id
        JOIN Airports a2 ON f.destination_airport_id = a2.airport_id
        WHERE f.flight_id = %s AND f.status = 'Scheduled'
        """,
        (flight_id,), fetch_one=True,
    )


def _fetch_bookable_train(train_id):
    """Looks up a Scheduled train by ID, with its source/destination city names."""
    return database.fetch_query(
        """
        SELECT t.*, s1.city AS source_city, s2.city AS destination_city
        FROM Trains t
        JOIN Stations s1 ON t.source_station_id = s1.station_id
        JOIN Stations s2 ON t.destination_station_id = s2.station_id
        WHERE t.train_id = %s AND t.status = 'Scheduled'
        """,
        (train_id,), fetch_one=True,
    )


def _fetch_hotel_by_id(hotel_id):
    """Looks up a hotel by ID."""
    return database.fetch_query(
        "SELECT * FROM Hotels WHERE hotel_id = %s", (hotel_id,), fetch_one=True
    )


def _fetch_available_cab(cab_id):
    """Looks up a still-Available cab by ID."""
    return database.fetch_query(
        "SELECT * FROM Cabs WHERE cab_id = %s AND status = 'Available'", (cab_id,), fetch_one=True
    )


def _fetch_active_package(package_id):
    """Looks up an Active package by ID."""
    return database.fetch_query(
        "SELECT * FROM Packages WHERE package_id = %s AND status = 'Active'", (package_id,), fetch_one=True
    )


def _apply_coupon(subtotal):
    """Shows applicable coupons and lets the user apply one by code."""
    available = coupons.get_applicable_coupons(subtotal)
    if available:
        rows = [
            [
                c["code"],
                f"{c['discount_value']}%" if c["discount_type"] == "Percentage" else f"Rs. {c['discount_value']}",
                f"Rs. {c['min_booking_amount']}",
                str(c["expiry_date"]) if c["expiry_date"] else "No expiry",
            ]
            for c in available
        ]
        print("\nCoupons you can apply to this booking:")
        utils.print_table(["Code", "Discount", "Min. Booking", "Expiry"], rows)
    else:
        print("\nNo coupons are currently applicable to this booking.")
        return None, 0

    if not utils.confirm("Apply one of these coupons? (y/n): "):
        return None, 0

    while True:
        code = utils.get_non_empty_input("Enter Coupon Code: ")
        valid, coupon_or_message, discount = coupons.validate_coupon(code, subtotal)
        if valid:
            print(f"\nCoupon '{coupon_or_message['code']}' applied - you save Rs. {discount}.")
            return coupon_or_message, discount
        print(coupon_or_message)
        if not utils.confirm("Try a different code? (y/n): "):
            return None, 0


def _choose_payment_method(user, amount_due):
    """Asks for Wallet/Card/UPI; loops back if Wallet balance is too low."""
    while True:
        print("\nPayment Method:")
        for i, method in enumerate(PAYMENT_METHODS, start=1):
            label = method
            if method == "Wallet":
                label += f" (Balance: Rs. {wallet.get_wallet_balance(user['user_id'])})"
            print(f"  {i}. {label}")

        choice = utils.get_non_empty_input("Choose a payment method (number): ")
        if not (choice.isdigit() and 1 <= int(choice) <= len(PAYMENT_METHODS)):
            print("Please enter a valid option number.")
            continue

        method = PAYMENT_METHODS[int(choice) - 1]
        if method == "Wallet" and wallet.get_wallet_balance(user["user_id"]) < amount_due:
            print("Insufficient wallet balance for this amount. "
                  "Top up your wallet from the main menu, or choose Card/UPI instead.")
            continue
        return method


def _checkout(user, subtotal):
    """Runs coupon + payment steps and returns a dict with the final checkout details."""
    coupon, discount_amount = _apply_coupon(subtotal)
    final_amount = round(subtotal - discount_amount, 2)

    print(f"\nSubtotal: Rs. {subtotal}")
    if discount_amount:
        print(f"Discount: -Rs. {discount_amount}")
    print(f"Total Payable: Rs. {final_amount}")

    payment_method = _choose_payment_method(user, final_amount)

    return {
        "coupon": coupon,
        "coupon_code": coupon["code"] if coupon else None,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "payment_method": payment_method,
    }


def _finalize_payment(user, checkout_info, booking_id):
    """Debits the wallet if used, and marks the coupon as used, after booking succeeds."""
    if checkout_info["payment_method"] == "Wallet" and checkout_info["final_amount"] > 0:
        wallet.debit_wallet(
            user["user_id"], checkout_info["final_amount"],
            f"Payment for Booking #{booking_id}",
        )
    if checkout_info["coupon"]:
        coupons.mark_coupon_used(checkout_info["coupon"]["coupon_id"])


def _generate_documents(user, booking_id):
    """Auto-generates the invoice and refreshes the CSV export for a new booking."""
    try:
        fresh_booking = database.fetch_query(
            "SELECT * FROM Bookings WHERE booking_id = %s", (booking_id,), fetch_one=True
        )
        if fresh_booking:
            invoices.generate_invoice_text(fresh_booking, user)
            invoices.export_bookings_csv(user)
    except Exception as file_error:
        utils.log_activity(f"Could not auto-generate invoice/CSV for booking {booking_id}: {file_error}")


# ---------------------------------------------------------
# Book: Flight
# ---------------------------------------------------------

def book_flight(user):
    utils.print_header("BOOK A FLIGHT", show_back_hint=True)
    print("Tip: use 'Search Flights' first to find a Flight ID.\n")

    try:
        flight = utils.get_record_by_id(
            "Enter Flight ID: ",
            _fetch_bookable_flight,
            "No bookable flight found with that ID (it may not exist, or may be Delayed/Cancelled).",
        )
        flight_id = flight["flight_id"]

        print(f"\n{flight['flight_number']} ({flight['airline_name']}): "
              f"{flight['source_city']} -> {flight['destination_city']} on {flight['travel_date']}")
        print(f"Price: Rs. {flight['price']} per seat | Seats available: {flight['available_seats']}")

        while True:
            seats_input = utils.get_non_empty_input("Number of seats to book: ")
            if seats_input.isdigit() and int(seats_input) > 0:
                seats = int(seats_input)
                break
            print("Number of seats must be a positive whole number.")

        if seats > flight["available_seats"]:
            utils.print_error(f"Only {flight['available_seats']} seat(s) available.")
            utils.pause()
            return

        subtotal = float(flight["price"]) * seats
        checkout_info = _checkout(user, subtotal)

        if not utils.confirm("Confirm booking? (y/n): "):
            utils.print_info("Booking cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Booking cancelled. No changes were made.")
        utils.pause()
        return

    label = f"{flight['flight_number']} {flight['source_city']} -> {flight['destination_city']}"
    success, result = _insert_booking(
        user["user_id"], "Flight", flight_id, label,
        flight["travel_date"], seats, 1, flight["price"], checkout_info["final_amount"],
        checkout_info["payment_method"], checkout_info["coupon_code"], checkout_info["discount_amount"],
    )
    if not success:
        utils.print_error(f"Booking failed: {result}")
        utils.pause()
        return

    database.execute_query(
        "UPDATE Flights SET available_seats = available_seats - %s WHERE flight_id = %s",
        (seats, flight_id),
    )
    _finalize_payment(user, checkout_info, result)
    _generate_documents(user, result)
    utils.print_success(f"Flight booked! Booking ID: {result}")
    utils.log_activity(f"User {user['email']} booked flight {flight['flight_number']} x{seats}")
    utils.pause()


# ---------------------------------------------------------
# Book: Train
# ---------------------------------------------------------

def book_train(user):
    utils.print_header("BOOK A TRAIN", show_back_hint=True)
    print("Tip: use 'Search Trains' first to find a Train ID.\n")

    try:
        train = utils.get_record_by_id(
            "Enter Train ID: ",
            _fetch_bookable_train,
            "No bookable train found with that ID (it may not exist, or may be Delayed/Cancelled).",
        )
        train_id = train["train_id"]

        print(f"\n{train['train_number']} ({train['train_name']}): "
              f"{train['source_city']} -> {train['destination_city']} on {train['travel_date']}")
        print(f"Price: Rs. {train['price']} per seat | Seats available: {train['available_seats']}")

        while True:
            seats_input = utils.get_non_empty_input("Number of seats to book: ")
            if seats_input.isdigit() and int(seats_input) > 0:
                seats = int(seats_input)
                break
            print("Number of seats must be a positive whole number.")

        if seats > train["available_seats"]:
            utils.print_error(f"Only {train['available_seats']} seat(s) available.")
            utils.pause()
            return

        subtotal = float(train["price"]) * seats
        checkout_info = _checkout(user, subtotal)

        if not utils.confirm("Confirm booking? (y/n): "):
            utils.print_info("Booking cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Booking cancelled. No changes were made.")
        utils.pause()
        return

    label = f"{train['train_number']} {train['source_city']} -> {train['destination_city']}"
    success, result = _insert_booking(
        user["user_id"], "Train", train_id, label,
        train["travel_date"], seats, 1, train["price"], checkout_info["final_amount"],
        checkout_info["payment_method"], checkout_info["coupon_code"], checkout_info["discount_amount"],
    )
    if not success:
        utils.print_error(f"Booking failed: {result}")
        utils.pause()
        return

    database.execute_query(
        "UPDATE Trains SET available_seats = available_seats - %s WHERE train_id = %s",
        (seats, train_id),
    )
    _finalize_payment(user, checkout_info, result)
    _generate_documents(user, result)
    utils.print_success(f"Train booked! Booking ID: {result}")
    utils.log_activity(f"User {user['email']} booked train {train['train_number']} x{seats}")
    utils.pause()


# ---------------------------------------------------------
# Book: Hotel (room type)
# ---------------------------------------------------------

def book_hotel(user):
    utils.print_header("BOOK A HOTEL ROOM", show_back_hint=True)
    print("Tip: use 'Search Hotels' first to find a Hotel ID.\n")

    try:
        hotel = utils.get_record_by_id(
            "Enter Hotel ID: ",
            _fetch_hotel_by_id,
            "No hotel found with that ID.",
        )
        hotel_id = hotel["hotel_id"]

        rooms = database.fetch_query(
            "SELECT * FROM Rooms WHERE hotel_id = %s ORDER BY price_per_night", (hotel_id,)
        )
        if not rooms:
            utils.print_info("This hotel has no room types listed.")
            utils.pause()
            return

        print(f"\n{hotel['hotel_name']} - {hotel['city']}")
        rows = [
            [r["room_id"], r["room_type"], f"Rs. {r['price_per_night']} / night", r["available_rooms"]]
            for r in rooms
        ]
        utils.print_table(["Room ID", "Type", "Price", "Available"], rows)

        def _find_room(room_id):
            """Finds a room from the list already fetched for this hotel."""
            for r in rooms:
                if r["room_id"] == room_id:
                    return r
            return None

        room = utils.get_record_by_id(
            "\nEnter Room ID to book: ",
            _find_room,
            "That Room ID does not belong to this hotel.",
        )

        check_in = utils.get_valid_date("Check-in Date (YYYY-MM-DD): ", disallow_past=True)

        while True:
            nights_input = utils.get_non_empty_input("Number of Nights: ")
            rooms_input = utils.get_non_empty_input("Number of Rooms: ")
            if (nights_input.isdigit() and int(nights_input) > 0
                    and rooms_input.isdigit() and int(rooms_input) > 0):
                nights = int(nights_input)
                num_rooms = int(rooms_input)
                break
            print("Nights and rooms must both be positive whole numbers.")

        if num_rooms > room["available_rooms"]:
            utils.print_error(f"Only {room['available_rooms']} room(s) of this type available.")
            utils.pause()
            return

        subtotal = float(room["price_per_night"]) * nights * num_rooms
        checkout_info = _checkout(user, subtotal)

        if not utils.confirm("Confirm booking? (y/n): "):
            utils.print_info("Booking cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Booking cancelled. No changes were made.")
        utils.pause()
        return

    label = f"{hotel['hotel_name']} ({room['room_type']}) - {hotel['city']}"
    success, result = _insert_booking(
        user["user_id"], "Hotel", room["room_id"], label,
        check_in, num_rooms, nights, room["price_per_night"], checkout_info["final_amount"],
        checkout_info["payment_method"], checkout_info["coupon_code"], checkout_info["discount_amount"],
    )
    if not success:
        utils.print_error(f"Booking failed: {result}")
        utils.pause()
        return

    database.execute_query(
        "UPDATE Rooms SET available_rooms = available_rooms - %s WHERE room_id = %s",
        (num_rooms, room["room_id"]),
    )
    _finalize_payment(user, checkout_info, result)
    _generate_documents(user, result)
    utils.print_success(f"Hotel room booked! Booking ID: {result}")
    utils.log_activity(f"User {user['email']} booked {hotel['hotel_name']} x{num_rooms} room(s)")
    utils.pause()


# ---------------------------------------------------------
# Book: Cab (whole vehicle)
# ---------------------------------------------------------

def book_cab(user):
    utils.print_header("BOOK A CAB", show_back_hint=True)
    print("Tip: use 'Search Cabs' first to find a Cab ID.\n")

    try:
        cab = utils.get_record_by_id(
            "Enter Cab ID: ",
            _fetch_available_cab,
            "No available cab found with that ID (it may not exist, or may already be booked).",
        )
        cab_id = cab["cab_id"]

        print(f"\n{cab['cab_type']} ({cab['cab_number']}), Driver: {cab['driver_name']}")
        print(f"{cab['source_city']} -> {cab['destination_city']} on {cab['travel_date']}")
        print(f"Price: Rs. {cab['price']} (whole vehicle, up to {cab['seats_capacity']} passengers)")

        subtotal = float(cab["price"])
        checkout_info = _checkout(user, subtotal)

        if not utils.confirm("Confirm booking? (y/n): "):
            utils.print_info("Booking cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Booking cancelled. No changes were made.")
        utils.pause()
        return

    label = f"{cab['cab_type']} {cab['source_city']} -> {cab['destination_city']}"
    success, result = _insert_booking(
        user["user_id"], "Cab", cab_id, label,
        cab["travel_date"], 1, 1, cab["price"], checkout_info["final_amount"],
        checkout_info["payment_method"], checkout_info["coupon_code"], checkout_info["discount_amount"],
    )
    if not success:
        utils.print_error(f"Booking failed: {result}")
        utils.pause()
        return

    database.execute_query(
        "UPDATE Cabs SET status = 'Booked' WHERE cab_id = %s", (cab_id,)
    )
    _finalize_payment(user, checkout_info, result)
    _generate_documents(user, result)
    utils.print_success(f"Cab booked! Booking ID: {result}")
    utils.log_activity(f"User {user['email']} booked cab {cab['cab_number']}")
    utils.pause()


# ---------------------------------------------------------
# Book: Holiday Package
# ---------------------------------------------------------

def book_package(user):
    utils.print_header("BOOK A HOLIDAY PACKAGE", show_back_hint=True)
    print("Tip: use 'Search Holiday Packages' first to find a Package ID.\n")

    try:
        package = utils.get_record_by_id(
            "Enter Package ID: ",
            _fetch_active_package,
            "No active package found with that ID.",
        )
        package_id = package["package_id"]

        print(f"\n{package['package_name']} - {package['destination']} "
              f"({package['duration_days']}D/{max(package['duration_days'] - 1, 1)}N)")
        print(f"Price: Rs. {package['price']} per person | Slots available: {package['available_slots']}")

        while True:
            travellers_input = utils.get_non_empty_input("Number of travellers: ")
            if travellers_input.isdigit() and int(travellers_input) > 0:
                travellers = int(travellers_input)
                break
            print("Number of travellers must be a positive whole number.")

        if travellers > package["available_slots"]:
            utils.print_error(f"Only {package['available_slots']} slot(s) available.")
            utils.pause()
            return

        travel_date_input = utils.get_valid_date("Preferred Start Date (YYYY-MM-DD): ", disallow_past=True)
        subtotal = float(package["price"]) * travellers
        checkout_info = _checkout(user, subtotal)

        if not utils.confirm("Confirm booking? (y/n): "):
            utils.print_info("Booking cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Booking cancelled. No changes were made.")
        utils.pause()
        return

    label = f"{package['package_name']} ({package['destination']})"
    success, result = _insert_booking(
        user["user_id"], "Package", package_id, label,
        travel_date_input, travellers, package["duration_days"], package["price"],
        checkout_info["final_amount"],
        checkout_info["payment_method"], checkout_info["coupon_code"], checkout_info["discount_amount"],
    )
    if not success:
        utils.print_error(f"Booking failed: {result}")
        utils.pause()
        return

    database.execute_query(
        "UPDATE Packages SET available_slots = available_slots - %s WHERE package_id = %s",
        (travellers, package_id),
    )
    _finalize_payment(user, checkout_info, result)
    _generate_documents(user, result)
    utils.print_success(f"Package booked! Booking ID: {result}")
    utils.log_activity(f"User {user['email']} booked package {package['package_name']} x{travellers}")
    utils.pause()


# ---------------------------------------------------------
# View & Cancel (works across all booking types)
# ---------------------------------------------------------

def _format_booking_rows(bookings):
    return [
        [
            b["booking_id"], b["booking_type"], b["item_label"],
            str(b["travel_date"]) if b["travel_date"] else "-",
            b["quantity"], f"Rs. {b['total_amount']}",
            b.get("payment_method") or "-", b["booking_status"],
        ]
        for b in bookings
    ]


def view_my_bookings(user):
    """Shows every booking the logged-in user has ever made."""
    utils.print_header("MY BOOKINGS")

    bookings = database.fetch_query(
        "SELECT * FROM Bookings WHERE user_id = %s ORDER BY booking_date DESC",
        (user["user_id"],),
    )

    if not bookings:
        utils.print_info("You have no bookings yet.")
    else:
        utils.print_table(
            ["ID", "Type", "Details", "Date", "Qty", "Total", "Payment", "Status"],
            _format_booking_rows(bookings),
        )

    utils.pause()


def _restore_availability(booking):
    """Puts back the seats/rooms/slots/cab freed up by a cancellation."""
    booking_type = booking["booking_type"]
    item_id = booking["item_id"]
    quantity = booking["quantity"]

    if booking_type == "Flight":
        database.execute_query(
            "UPDATE Flights SET available_seats = available_seats + %s WHERE flight_id = %s",
            (quantity, item_id),
        )
    elif booking_type == "Train":
        database.execute_query(
            "UPDATE Trains SET available_seats = available_seats + %s WHERE train_id = %s",
            (quantity, item_id),
        )
    elif booking_type == "Hotel":
        database.execute_query(
            "UPDATE Rooms SET available_rooms = available_rooms + %s WHERE room_id = %s",
            (quantity, item_id),
        )
    elif booking_type == "Cab":
        database.execute_query(
            "UPDATE Cabs SET status = 'Available' WHERE cab_id = %s", (item_id,)
        )
    elif booking_type == "Package":
        database.execute_query(
            "UPDATE Packages SET available_slots = available_slots + %s WHERE package_id = %s",
            (quantity, item_id),
        )


def cancel_booking(user):
    """Lets a user cancel one of their own Confirmed bookings."""
    utils.print_header("CANCEL A BOOKING", show_back_hint=True)

    active_bookings = database.fetch_query(
        "SELECT * FROM Bookings WHERE user_id = %s AND booking_status = 'Confirmed' "
        "ORDER BY booking_date DESC",
        (user["user_id"],),
    )

    if not active_bookings:
        utils.print_info("You have no active bookings to cancel.")
        utils.pause()
        return

    utils.print_table(
        ["ID", "Type", "Details", "Date", "Qty", "Total", "Payment", "Status"],
        _format_booking_rows(active_bookings),
    )

    def _find_active_booking(booking_id):
        """Finds a booking from this user's own active bookings list."""
        for b in active_bookings:
            if b["booking_id"] == booking_id:
                return b
        return None

    try:
        booking = utils.get_record_by_id(
            "\nEnter Booking ID to cancel: ",
            _find_active_booking,
            "That Booking ID is not one of your active bookings.",
        )

        print(f"\nYou are about to cancel: {booking['item_label']} "
              f"(Rs. {booking['total_amount']}).")
        if not utils.confirm("This cannot be undone. Continue? (y/n): "):
            utils.print_info("Cancellation aborted.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Cancellation aborted. No changes were made.")
        utils.pause()
        return

    success, result = database.execute_query(
        "UPDATE Bookings SET booking_status = 'Cancelled' WHERE booking_id = %s",
        (booking["booking_id"],),
    )

    if success:
        _restore_availability(booking)

        refund_amount = float(booking["total_amount"])
        if refund_amount > 0:
            refund_success, refund_result = wallet.credit_wallet(
                user["user_id"], refund_amount,
                f"Refund for cancelled Booking #{booking['booking_id']}",
            )
        else:
            refund_success, refund_result = True, None

        if refund_success and refund_amount > 0:
            utils.print_success(
                f"Booking cancelled and availability restored. Rs. {refund_amount} "
                f"refunded to your wallet (new balance: Rs. {refund_result})."
            )
        elif refund_amount > 0:
            utils.print_success("Booking cancelled and availability restored.")
            utils.print_error(f"Refund to wallet failed: {refund_result}")
        else:
            utils.print_success("Booking cancelled and availability restored.")

        utils.log_activity(f"User {user['email']} cancelled booking ID {booking['booking_id']}")
    else:
        utils.print_error(f"Could not cancel booking: {result}")
    utils.pause()