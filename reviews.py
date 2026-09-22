"""
reviews.py
=====================================================
Everything related to Reviews: leaving a Booking-experience or
Trip review, viewing reviews, and admin moderation.
=====================================================
"""

from datetime import date, timedelta

import database
import utils

BOOKING_TYPES = ("Flight", "Train", "Hotel", "Cab", "Package")
DURATION_BOOKING_TYPES = ("Hotel", "Package")


def _trip_end_date(booking):
    """Hotel/Package trips end on travel_date + nights; others end on travel_date."""
    if booking["booking_type"] in DURATION_BOOKING_TYPES:
        return booking["travel_date"] + timedelta(days=booking["nights"])
    return booking["travel_date"]


def _has_review(booking_id, review_type):
    """True if this booking already has a review of this type."""
    result = database.fetch_query(
        "SELECT review_id FROM Reviews WHERE booking_id = %s AND review_type = %s",
        (booking_id, review_type), fetch_one=True,
    )
    return result is not None


def _fetch_reviewable_bookings(user_id, review_type):
    """Returns the user's Confirmed bookings eligible for a new review of review_type."""
    bookings = database.fetch_query(
        "SELECT * FROM Bookings WHERE user_id = %s AND booking_status = 'Confirmed' "
        "ORDER BY booking_date DESC",
        (user_id,),
    ) or []

    eligible = []
    for b in bookings:
        if _has_review(b["booking_id"], review_type):
            continue
        if review_type == "Trip":
            if b["travel_date"] is None or _trip_end_date(b) >= date.today():
                continue
        eligible.append(b)
    return eligible


def _collect_rating_and_comment():
    """Asks for a 1-5 star rating and an optional comment."""
    while True:
        rating_input = utils.get_non_empty_input("Rating (1-5 stars): ")
        if rating_input.isdigit() and 1 <= int(rating_input) <= 5:
            rating = int(rating_input)
            break
        print("Please enter a whole number from 1 to 5.")

    comment = utils.get_input("Comment (optional): ", default="")
    return rating, comment


def _insert_review(booking_id, user_id, review_type, rating, comment):
    return database.execute_query(
        "INSERT INTO Reviews (booking_id, user_id, review_type, rating, comment) "
        "VALUES (%s, %s, %s, %s, %s)",
        (booking_id, user_id, review_type, rating, comment),
    )


def leave_booking_review(user):
    """Lets the user rate/comment on the booking experience itself."""
    utils.print_header("REVIEW A BOOKING EXPERIENCE", show_back_hint=True)

    eligible = _fetch_reviewable_bookings(user["user_id"], "Booking")
    if not eligible:
        utils.print_info("You have no bookings left to review (every Confirmed "
                          "booking of yours already has a booking review).")
        utils.pause()
        return

    rows = [
        [b["booking_id"], b["booking_type"], b["item_label"],
         str(b["travel_date"]) if b["travel_date"] else "-"]
        for b in eligible
    ]
    utils.print_table(["ID", "Type", "Details", "Date"], rows)

    def _find_booking(booking_id):
        for b in eligible:
            if b["booking_id"] == booking_id:
                return b
        return None

    try:
        booking = utils.get_record_by_id(
            "\nEnter Booking ID to review: ", _find_booking,
            "That ID isn't eligible for a booking review.",
        )
        rating, comment = _collect_rating_and_comment()
    except utils.GoBack:
        utils.print_info("Review cancelled.")
        utils.pause()
        return

    success, result = _insert_review(booking["booking_id"], user["user_id"], "Booking", rating, comment)
    if success:
        utils.print_success("Thanks for your feedback on the booking experience!")
        utils.log_activity(f"User {user['email']} left a Booking review for booking {booking['booking_id']}")
    else:
        utils.print_error(f"Could not save review: {result}")
    utils.pause()


def leave_trip_review(user):
    """Lets the user rate/comment on a trip that has already finished."""
    utils.print_header("REVIEW A COMPLETED TRIP", show_back_hint=True)

    eligible = _fetch_reviewable_bookings(user["user_id"], "Trip")
    if not eligible:
        utils.print_info("You have no completed trips left to review yet - either "
                          "none of your trips have finished, or you've already "
                          "reviewed all of them.")
        utils.pause()
        return

    rows = [
        [b["booking_id"], b["booking_type"], b["item_label"], str(_trip_end_date(b))]
        for b in eligible
    ]
    utils.print_table(["ID", "Type", "Details", "Trip Ended"], rows)

    def _find_booking(booking_id):
        for b in eligible:
            if b["booking_id"] == booking_id:
                return b
        return None

    try:
        booking = utils.get_record_by_id(
            "\nEnter Booking ID to review: ", _find_booking,
            "That ID isn't eligible for a trip review.",
        )
        rating, comment = _collect_rating_and_comment()
    except utils.GoBack:
        utils.print_info("Review cancelled.")
        utils.pause()
        return

    success, result = _insert_review(booking["booking_id"], user["user_id"], "Trip", rating, comment)
    if success:
        utils.print_success("Thanks for reviewing your trip!")
        utils.log_activity(f"User {user['email']} left a Trip review for booking {booking['booking_id']}")
    else:
        utils.print_error(f"Could not save review: {result}")
    utils.pause()


def view_my_reviews(user):
    """Shows every review the logged-in user has ever left."""
    utils.print_header("MY REVIEWS")

    reviews = database.fetch_query(
        """
        SELECT r.*, b.booking_type, b.item_label
        FROM Reviews r
        JOIN Bookings b ON r.booking_id = b.booking_id
        WHERE r.user_id = %s
        ORDER BY r.review_date DESC
        """,
        (user["user_id"],),
    )

    if not reviews:
        utils.print_info("You haven't left any reviews yet.")
    else:
        rows = [
            [r["review_id"], r["review_type"], r["booking_type"], r["item_label"],
             "*" * r["rating"], r["comment"] or "-"]
            for r in reviews
        ]
        utils.print_table(["ID", "Review Type", "Booking Type", "Details", "Rating", "Comment"], rows)

    utils.pause()


def view_item_reviews():
    """Shows the average rating and every trip review for one item, by type and ID."""
    utils.print_header("VIEW REVIEWS FOR AN ITEM", show_back_hint=True)

    try:
        print("Booking Types: Flight, Train, Hotel, Cab, Package")
        while True:
            booking_type = utils.get_non_empty_input("Booking Type: ").strip().capitalize()
            if booking_type in BOOKING_TYPES:
                break
            print("Please enter one of: Flight, Train, Hotel, Cab, Package.")

        item_id_input = utils.get_non_empty_input(
            f"{booking_type} ID (the ID shown when you searched/booked it): "
        )
    except utils.GoBack:
        utils.print_info("Cancelled.")
        utils.pause()
        return

    if not item_id_input.isdigit():
        utils.print_error("That must be a whole number.")
        utils.pause()
        return
    item_id = int(item_id_input)

    summary = database.fetch_query(
        """
        SELECT AVG(r.rating) AS average_rating, COUNT(*) AS total_reviews
        FROM Reviews r
        JOIN Bookings b ON r.booking_id = b.booking_id
        WHERE b.booking_type = %s AND b.item_id = %s AND r.review_type = 'Trip'
        """,
        (booking_type, item_id), fetch_one=True,
    )

    if not summary or not summary["total_reviews"]:
        utils.print_info("No trip reviews yet for this item.")
        utils.pause()
        return

    print(f"\nAverage rating: {round(float(summary['average_rating']), 1)} / 5 "
          f"({summary['total_reviews']} review(s))")

    reviews = database.fetch_query(
        """
        SELECT r.rating, r.comment, r.review_date
        FROM Reviews r
        JOIN Bookings b ON r.booking_id = b.booking_id
        WHERE b.booking_type = %s AND b.item_id = %s AND r.review_type = 'Trip'
        ORDER BY r.review_date DESC
        """,
        (booking_type, item_id),
    )
    rows = [[str(r["review_date"])[:10], "*" * r["rating"], r["comment"] or "-"] for r in reviews]
    utils.print_table(["Date", "Rating", "Comment"], rows)
    utils.pause()


# ---------------------------------------------------------
# Admin management
# ---------------------------------------------------------

def admin_view_reviews():
    """Admin listing of every review, most recent first."""
    utils.print_header("ALL REVIEWS")

    reviews = database.fetch_query(
        """
        SELECT r.review_id, u.full_name, r.review_type, b.booking_type, b.item_label,
               r.rating, r.comment, r.review_date
        FROM Reviews r
        JOIN Users u ON r.user_id = u.user_id
        JOIN Bookings b ON r.booking_id = b.booking_id
        ORDER BY r.review_date DESC
        LIMIT 100
        """
    )

    if not reviews:
        utils.print_info("No reviews yet.")
        utils.pause()
        return

    rows = [
        [r["review_id"], r["full_name"], r["review_type"], r["booking_type"],
         r["item_label"], "*" * r["rating"], r["comment"] or "-"]
        for r in reviews
    ]
    utils.print_header(f"{len(reviews)} REVIEW(S) (showing up to 100 most recent)")
    utils.print_table(["ID", "User", "Type", "Booking Type", "Details", "Rating", "Comment"], rows)
    utils.pause()


def _fetch_review_by_id(review_id):
    return database.fetch_query(
        "SELECT * FROM Reviews WHERE review_id = %s", (review_id,), fetch_one=True
    )


def admin_delete_review():
    """Deletes a review by ID (moderation), after confirmation."""
    utils.print_header("DELETE REVIEW", show_back_hint=True)
    try:
        review = utils.get_record_by_id(
            "Enter Review ID: ", _fetch_review_by_id, "No review found with that ID."
        )

        print(f"\nYou are about to delete this {review['review_type']} review "
              f"(rating: {review['rating']}/5).")
        if not utils.confirm("This cannot be undone. Continue? (y/n): "):
            utils.print_info("Deletion cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Deletion cancelled.")
        utils.pause()
        return

    success, result = database.execute_query(
        "DELETE FROM Reviews WHERE review_id = %s", (review["review_id"],)
    )

    if success:
        utils.print_success("Review deleted successfully.")
        utils.log_activity(f"Admin deleted review ID {review['review_id']}")
    else:
        utils.print_error(f"Could not delete review: {result}")
    utils.pause()