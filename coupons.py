"""
coupons.py
=====================================================
Everything related to Coupons (Stage 7):
    - validate_coupon()   - used by booking.py's checkout flow to
                             check a code the user enters and work
                             out the discount it earns, WITHOUT
                             committing anything yet
    - mark_coupon_used()  - called by booking.py only after a
                             booking is actually confirmed
    - Admin management: view/search, add, edit, delete coupons

A coupon gives either a flat discount (e.g. "Rs. 200 off") or a
percentage discount (e.g. "10% off", optionally capped by
max_discount_amount so a percentage coupon can't blow out on a
huge booking). min_booking_amount stops a coupon being used on a
booking too small to qualify. usage_limit (optional, None means
unlimited) caps how many times a coupon can be redeemed in total;
times_used tracks that count.

Every admin function below lets the user type 'back' at any
prompt to cancel out and return to the menu (see utils.GoBack).
=====================================================
"""

from datetime import date

import database
import utils


def validate_coupon(code, booking_amount):
    """
    Looks up a coupon code and checks whether it can be applied to
    a booking of `booking_amount`. Does NOT increment times_used -
    that only happens once the booking is actually confirmed (see
    mark_coupon_used, called from booking.py).

    Returns:
        (True, coupon_dict, discount_amount) if the coupon is valid
        (False, error_message, 0) otherwise
    """
    coupon = database.fetch_query(
        "SELECT * FROM Coupons WHERE code = %s", (code.strip().upper(),), fetch_one=True
    )

    if coupon is None:
        return False, "No coupon found with that code.", 0

    if coupon["status"] != "Active":
        return False, "This coupon is no longer active.", 0

    if coupon["expiry_date"] and coupon["expiry_date"] < date.today():
        return False, "This coupon has expired.", 0

    if coupon["usage_limit"] is not None and coupon["times_used"] >= coupon["usage_limit"]:
        return False, "This coupon has reached its usage limit.", 0

    if booking_amount < float(coupon["min_booking_amount"] or 0):
        return False, (
            f"This coupon needs a minimum booking amount of "
            f"Rs. {coupon['min_booking_amount']}."
        ), 0

    if coupon["discount_type"] == "Flat":
        discount = float(coupon["discount_value"])
    else:  # Percentage
        discount = booking_amount * float(coupon["discount_value"]) / 100
        if coupon["max_discount_amount"]:
            discount = min(discount, float(coupon["max_discount_amount"]))

    discount = min(discount, booking_amount)  # never discount more than the booking itself
    return True, coupon, round(discount, 2)


def get_applicable_coupons(booking_amount):
    """
    Returns every coupon that COULD currently be applied to a
    booking of `booking_amount`: Active, not expired, under its
    usage limit, and booking_amount at or above its
    min_booking_amount. Used by booking.py to show the user a list
    of coupons they can actually use, instead of asking them to
    guess or already know a code.

    Does not check anything else validate_coupon() checks later
    (there's nothing else to check) - this is exactly the same set
    of rules, just applied to every coupon at once instead of one
    entered code.
    """
    all_coupons = database.fetch_query(
        "SELECT * FROM Coupons WHERE status = 'Active' ORDER BY min_booking_amount"
    ) or []

    applicable = []
    for coupon in all_coupons:
        if coupon["expiry_date"] and coupon["expiry_date"] < date.today():
            continue
        if coupon["usage_limit"] is not None and coupon["times_used"] >= coupon["usage_limit"]:
            continue
        if booking_amount < float(coupon["min_booking_amount"] or 0):
            continue
        applicable.append(coupon)

    return applicable


def mark_coupon_used(coupon_id):
    """Increments a coupon's times_used counter by 1. Called after a booking is confirmed."""
    database.execute_query(
        "UPDATE Coupons SET times_used = times_used + 1 WHERE coupon_id = %s", (coupon_id,)
    )


def _format_coupon_rows(coupons_list):
    return [
        [
            c["coupon_id"], c["code"],
            f"{c['discount_value']}%" if c["discount_type"] == "Percentage" else f"Rs. {c['discount_value']}",
            f"Rs. {c['min_booking_amount']}",
            f"{c['times_used']}/{c['usage_limit'] if c['usage_limit'] is not None else 'Unlimited'}",
            str(c["expiry_date"]) if c["expiry_date"] else "Never",
            c["status"],
        ]
        for c in coupons_list
    ]


# ---------------------------------------------------------
# Admin management
# ---------------------------------------------------------

def admin_view_coupons():
    """Admin coupon listing with an optional code filter."""
    utils.print_header("VIEW / SEARCH COUPONS", show_back_hint=True)
    try:
        keyword = utils.get_input("Code contains (optional): ", default="")
    except utils.GoBack:
        utils.print_info("Cancelled.")
        utils.pause()
        return

    coupons_list = database.fetch_query(
        "SELECT * FROM Coupons WHERE code LIKE %s ORDER BY coupon_id DESC LIMIT 40",
        (f"%{keyword.upper()}%",),
    )

    if not coupons_list:
        utils.print_info("No coupons found.")
    else:
        utils.print_header(f"{len(coupons_list)} COUPON(S) (showing up to 40)")
        utils.print_table(
            ["ID", "Code", "Discount", "Min. Booking", "Used/Limit", "Expiry", "Status"],
            _format_coupon_rows(coupons_list),
        )
        for c in coupons_list:
            if c.get("description"):
                print(f"  {c['code']}: {c['description']}")
    utils.pause()


def admin_add_coupon():
    """Collects details for a new coupon and inserts it."""
    utils.print_header("ADD NEW COUPON", show_back_hint=True)

    try:
        while True:
            code = utils.get_non_empty_input("Coupon Code (e.g. SUMMER200): ").strip().upper()
            existing = database.fetch_query(
                "SELECT coupon_id FROM Coupons WHERE code = %s", (code,), fetch_one=True
            )
            if existing:
                print("A coupon with this code already exists.")
                continue
            break

        description = utils.get_input("Description (optional): ")

        while True:
            type_input = utils.get_non_empty_input("Discount Type (Flat/Percentage): ").strip().upper()
            if type_input == "FLAT":
                discount_type = "Flat"
                break
            if type_input == "PERCENTAGE":
                discount_type = "Percentage"
                break
            print("Please enter 'Flat' or 'Percentage'.")

        while True:
            value_input = utils.get_non_empty_input(
                "Discount Value (Rs. amount if Flat, % if Percentage): "
            )
            try:
                discount_value = float(value_input)
                if discount_value > 0:
                    break
                print("Discount value must be greater than zero.")
            except ValueError:
                print("Please enter a valid number.")

        max_discount_amount = None
        if discount_type == "Percentage":
            max_input = utils.get_input(
                "Max Discount Cap (Rs., optional, press Enter for no cap): ", default=""
            )
            if max_input:
                try:
                    max_discount_amount = float(max_input)
                except ValueError:
                    max_discount_amount = None

        min_input = utils.get_input(
            "Minimum Booking Amount (Rs., optional, default 0): ", default="0"
        )
        try:
            min_booking_amount = float(min_input)
        except ValueError:
            min_booking_amount = 0

        limit_input = utils.get_input(
            "Usage Limit (total redemptions, optional, press Enter for unlimited): ", default=""
        )
        usage_limit = int(limit_input) if limit_input.isdigit() else None

        expiry_date_input = utils.get_valid_date(
            "Expiry Date (YYYY-MM-DD, optional, press Enter for no expiry): ",
            allow_blank=True, disallow_past=True,
        )
    except utils.GoBack:
        utils.print_info("Add cancelled. No coupon was added.")
        utils.pause()
        return

    success, result = database.execute_query(
        """
        INSERT INTO Coupons (
            code, description, discount_type, discount_value, max_discount_amount,
            min_booking_amount, usage_limit, expiry_date, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active')
        """,
        (
            code, description, discount_type, discount_value, max_discount_amount,
            min_booking_amount, usage_limit, expiry_date_input,
        ),
    )

    if success:
        utils.print_success(f"Coupon '{code}' added successfully (ID: {result}).")
        utils.log_activity(f"Admin added coupon: {code}")
    else:
        utils.print_error(f"Could not add coupon: {result}")
    utils.pause()


def _fetch_coupon_by_id(coupon_id):
    """Looks up a coupon by ID."""
    return database.fetch_query(
        "SELECT * FROM Coupons WHERE coupon_id = %s", (coupon_id,), fetch_one=True
    )


def admin_edit_coupon():
    """Edits an existing coupon's discount value, usage limit, or status by ID."""
    utils.print_header("EDIT COUPON", show_back_hint=True)
    try:
        coupon = utils.get_record_by_id(
            "Enter Coupon ID: ",
            _fetch_coupon_by_id,
            "No coupon found with that ID.",
        )

        print(f"\nEditing {coupon['code']} - press Enter to keep current value.\n")

        value_input = utils.get_input(f"Discount Value [{coupon['discount_value']}]: ")
        discount_value = float(value_input) if value_input else coupon["discount_value"]

        current_limit_label = coupon["usage_limit"] if coupon["usage_limit"] is not None else "Unlimited"
        limit_input = utils.get_input(
            f"Usage Limit [{current_limit_label}] (type 'none' for unlimited): "
        )
        if limit_input.lower() == "none":
            usage_limit = None
        elif limit_input:
            usage_limit = int(limit_input)
        else:
            usage_limit = coupon["usage_limit"]

        status = utils.get_input(
            f"Status [{coupon['status']}] (Active/Inactive): ", default=coupon["status"]
        )
    except utils.GoBack:
        utils.print_info("Edit cancelled. No changes were made.")
        utils.pause()
        return
    except ValueError:
        utils.print_error("Discount value and usage limit must be numbers. No changes were made.")
        utils.pause()
        return

    success, result = database.execute_query(
        "UPDATE Coupons SET discount_value = %s, usage_limit = %s, status = %s WHERE coupon_id = %s",
        (discount_value, usage_limit, status, coupon["coupon_id"]),
    )

    if success:
        utils.print_success("Coupon updated successfully.")
        utils.log_activity(f"Admin edited coupon ID {coupon['coupon_id']}")
    else:
        utils.print_error(f"Could not update coupon: {result}")
    utils.pause()


def admin_delete_coupon():
    """Deletes a coupon by ID, after confirmation."""
    utils.print_header("DELETE COUPON", show_back_hint=True)
    try:
        coupon = utils.get_record_by_id(
            "Enter Coupon ID: ",
            _fetch_coupon_by_id,
            "No coupon found with that ID.",
        )

        print(f"\nYou are about to delete coupon '{coupon['code']}'.")
        if not utils.confirm("This cannot be undone. Continue? (y/n): "):
            utils.print_info("Deletion cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    success, result = database.execute_query(
        "DELETE FROM Coupons WHERE coupon_id = %s", (coupon["coupon_id"],)
    )

    if success:
        utils.print_success("Coupon deleted successfully.")
        utils.log_activity(f"Admin deleted coupon ID {coupon['coupon_id']}")
    else:
        utils.print_error(f"Could not delete coupon: {result}")
    utils.pause()