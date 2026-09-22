"""
invoices.py
=====================================================
Generates a text invoice/ticket per booking and a CSV export of
booking history, saved under files/invoices/.
=====================================================
"""

import csv
import os

import database
import utils

INVOICES_DIR = "files/invoices"


def _ensure_invoices_dir():
    """Creates files/invoices/ the first time it's needed."""
    os.makedirs(INVOICES_DIR, exist_ok=True)


def _invoice_path(booking_id):
    return os.path.join(INVOICES_DIR, f"invoice_{booking_id}.txt")


def _csv_path(user_id):
    return os.path.join(INVOICES_DIR, f"bookings_{user_id}.csv")


def generate_invoice_text(booking, user):
    """Writes a formatted text invoice for one booking. Returns the file path."""
    _ensure_invoices_dir()
    path = _invoice_path(booking["booking_id"])

    discount_line = f"Discount       : Rs. {booking['discount_amount'] or 0}"
    if booking.get("coupon_code"):
        discount_line += f" (Coupon: {booking['coupon_code']})"

    lines = [
        "=" * 50,
        "GOTRAVEL - BOOKING INVOICE / TICKET".center(50),
        "=" * 50,
        f"Booking ID     : {booking['booking_id']}",
        f"Booking Date   : {booking['booking_date']}",
        f"Booking Status : {booking['booking_status']}",
        "-" * 50,
        f"Passenger/Guest: {user['full_name']}",
        f"Email          : {user['email']}",
        f"Phone          : {user['phone']}",
        "-" * 50,
        f"Type           : {booking['booking_type']}",
        f"Details        : {booking['item_label']}",
        f"Travel Date    : {booking['travel_date'] or '-'}",
        f"Quantity       : {booking['quantity']}",
        f"Nights/Days    : {booking['nights']}",
        f"Unit Price     : Rs. {booking['unit_price']}",
        "-" * 50,
        discount_line,
        f"Total Paid     : Rs. {booking['total_amount']}",
        f"Payment Method : {booking['payment_method'] or '-'}",
        "=" * 50,
        "Thank you for booking with GoTravel!".center(50),
        "=" * 50,
    ]

    with open(path, "w") as invoice_file:
        for line in lines:
            invoice_file.write(line + "\n")

    return path


def _fetch_booking_for_user(booking_id, user_id):
    return database.fetch_query(
        "SELECT * FROM Bookings WHERE booking_id = %s AND user_id = %s",
        (booking_id, user_id), fetch_one=True,
    )


def view_or_regenerate_invoice(user):
    """Lets the user pick a booking, regenerates its invoice, and prints it."""
    utils.print_header("VIEW / DOWNLOAD INVOICE", show_back_hint=True)

    try:
        booking_id_input = utils.get_non_empty_input("Enter Booking ID: ")
    except utils.GoBack:
        utils.print_info("Cancelled.")
        utils.pause()
        return

    if not booking_id_input.isdigit():
        utils.print_error("That must be a whole number.")
        utils.pause()
        return

    booking = _fetch_booking_for_user(int(booking_id_input), user["user_id"])
    if not booking:
        utils.print_error("No booking found with that ID on your account.")
        utils.pause()
        return

    path = generate_invoice_text(booking, user)

    print()
    with open(path, "r") as invoice_file:
        contents = invoice_file.read()
    print(contents)

    print(f"Saved to: {path}")
    utils.pause()


def export_bookings_csv(user):
    """Writes the user's full booking history to a CSV file, overwriting any earlier copy."""
    _ensure_invoices_dir()
    path = _csv_path(user["user_id"])

    bookings = database.fetch_query(
        "SELECT * FROM Bookings WHERE user_id = %s ORDER BY booking_date DESC",
        (user["user_id"],),
    ) or []

    with open(path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "Booking ID", "Type", "Details", "Travel Date", "Quantity", "Nights",
            "Unit Price", "Discount", "Total Amount", "Payment Method",
            "Coupon Code", "Status", "Booking Date",
        ])
        for b in bookings:
            writer.writerow([
                b["booking_id"], b["booking_type"], b["item_label"], b["travel_date"] or "",
                b["quantity"], b["nights"], b["unit_price"], b["discount_amount"] or 0,
                b["total_amount"], b["payment_method"] or "", b["coupon_code"] or "",
                b["booking_status"], b["booking_date"],
            ])

    return path


def handle_export_bookings_csv(user):
    """Menu wrapper for export_bookings_csv()."""
    utils.print_header("EXPORT MY BOOKINGS TO CSV")
    path = export_bookings_csv(user)
    utils.print_success(f"Exported to: {path}")
    utils.log_activity(f"User {user['email']} exported bookings to CSV")
    utils.pause()


def admin_export_all_bookings_csv():
    """Exports every user's bookings to one CSV file."""
    utils.print_header("EXPORT ALL BOOKINGS TO CSV")
    _ensure_invoices_dir()
    path = os.path.join(INVOICES_DIR, "all_bookings.csv")

    bookings = database.fetch_query(
        """
        SELECT b.*, u.full_name, u.email
        FROM Bookings b
        JOIN Users u ON b.user_id = u.user_id
        ORDER BY b.booking_date DESC
        """
    ) or []

    with open(path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "Booking ID", "User", "Email", "Type", "Details", "Travel Date", "Quantity",
            "Nights", "Unit Price", "Discount", "Total Amount", "Payment Method",
            "Coupon Code", "Status", "Booking Date",
        ])
        for b in bookings:
            writer.writerow([
                b["booking_id"], b["full_name"], b["email"], b["booking_type"], b["item_label"],
                b["travel_date"] or "", b["quantity"], b["nights"], b["unit_price"],
                b["discount_amount"] or 0, b["total_amount"], b["payment_method"] or "",
                b["coupon_code"] or "", b["booking_status"], b["booking_date"],
            ])

    utils.print_success(f"Exported {len(bookings)} booking(s) to: {path}")
    utils.log_activity("Admin exported all bookings to CSV")
    utils.pause()