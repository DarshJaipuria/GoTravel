"""
seed_data.py
=====================================================
Generates realistic sample data for Airports, Stations,
Flights, Trains, Hotels, Rooms, Cabs, Holiday Packages, and
Coupons so the application has something to search from (and
apply at checkout) the moment it is set up.

This is a data-generation utility, not a feature module -
it is triggered once from the admin dashboard ("Load Sample
Data"). It only inserts into a table if that table is
currently empty, so running it again is always safe.

Uses only the Python standard library (random, datetime).
=====================================================
"""

import random
from datetime import date, datetime, timedelta

import database
import utils

# -----------------------------------------------------
# Reference data: major Indian airports and stations
# -----------------------------------------------------

AIRPORTS = [
    ("DEL", "Indira Gandhi International Airport", "Delhi"),
    ("BOM", "Chhatrapati Shivaji Maharaj International Airport", "Mumbai"),
    ("BLR", "Kempegowda International Airport", "Bengaluru"),
    ("MAA", "Chennai International Airport", "Chennai"),
    ("CCU", "Netaji Subhas Chandra Bose International Airport", "Kolkata"),
    ("HYD", "Rajiv Gandhi International Airport", "Hyderabad"),
    ("AMD", "Sardar Vallabhbhai Patel International Airport", "Ahmedabad"),
    ("PNQ", "Pune Airport", "Pune"),
    ("GOI", "Goa International Airport", "Goa"),
    ("COK", "Cochin International Airport", "Kochi"),
    ("JAI", "Jaipur International Airport", "Jaipur"),
    ("LKO", "Chaudhary Charan Singh International Airport", "Lucknow"),
    ("IXC", "Chandigarh Airport", "Chandigarh"),
    ("GAU", "Lokpriya Gopinath Bordoloi International Airport", "Guwahati"),
    ("PAT", "Jay Prakash Narayan Airport", "Patna"),
    ("BBI", "Biju Patnaik International Airport", "Bhubaneswar"),
    ("IXR", "Birsa Munda Airport", "Ranchi"),
    ("VNS", "Lal Bahadur Shastri Airport", "Varanasi"),
    ("IXM", "Madurai Airport", "Madurai"),
    ("TRV", "Trivandrum International Airport", "Thiruvananthapuram"),
    ("NAG", "Dr. Babasaheb Ambedkar International Airport", "Nagpur"),
    ("IDR", "Devi Ahilyabai Holkar Airport", "Indore"),
    ("RPR", "Swami Vivekananda Airport", "Raipur"),
    ("IXB", "Bagdogra Airport", "Siliguri"),
    ("ATQ", "Sri Guru Ram Dass Jee International Airport", "Amritsar"),
    ("STV", "Surat Airport", "Surat"),
    ("BHO", "Raja Bhoj Airport", "Bhopal"),
    ("VTZ", "Visakhapatnam Airport", "Visakhapatnam"),
    ("IXA", "Agartala Airport", "Agartala"),
    ("DED", "Jolly Grant Airport", "Dehradun"),
    ("UDR", "Maharana Pratap Airport", "Udaipur"),
    ("IXJ", "Jammu Airport", "Jammu"),
    ("IXZ", "Veer Savarkar International Airport", "Port Blair"),
]

STATIONS = [
    ("NDLS", "New Delhi Railway Station", "Delhi"),
    ("CSMT", "Chhatrapati Shivaji Maharaj Terminus", "Mumbai"),
    ("HWH", "Howrah Junction", "Kolkata"),
    ("MAS", "Chennai Central", "Chennai"),
    ("SBC", "Bengaluru City Junction", "Bengaluru"),
    ("SC", "Secunderabad Junction", "Hyderabad"),
    ("ADI", "Ahmedabad Junction", "Ahmedabad"),
    ("PUNE", "Pune Junction", "Pune"),
    ("JP", "Jaipur Junction", "Jaipur"),
    ("LJN", "Lucknow Charbagh", "Lucknow"),
    ("CNB", "Kanpur Central", "Kanpur"),
    ("PNBE", "Patna Junction", "Patna"),
    ("BBS", "Bhubaneswar Station", "Bhubaneswar"),
    ("GHY", "Guwahati Station", "Guwahati"),
    ("JAT", "Jammu Tawi", "Jammu"),
    ("ASR", "Amritsar Junction", "Amritsar"),
    ("CDG", "Chandigarh Station", "Chandigarh"),
    ("BPL", "Bhopal Junction", "Bhopal"),
    ("NGP", "Nagpur Junction", "Nagpur"),
    ("INDB", "Indore Junction", "Indore"),
    ("R", "Raipur Junction", "Raipur"),
    ("VSKP", "Visakhapatnam Junction", "Visakhapatnam"),
    ("TVC", "Thiruvananthapuram Central", "Thiruvananthapuram"),
    ("ERS", "Ernakulam Junction", "Kochi"),
    ("MDU", "Madurai Junction", "Madurai"),
    ("UDZ", "Udaipur City", "Udaipur"),
    ("DDN", "Dehradun Station", "Dehradun"),
    ("BSB", "Varanasi Junction", "Varanasi"),
    ("MAO", "Madgaon Junction", "Goa"),
    ("RNC", "Ranchi Station", "Ranchi"),
    ("AGTL", "Agartala Station", "Agartala"),
    ("CBE", "Coimbatore Junction", "Coimbatore"),
    ("MYS", "Mysuru Junction", "Mysuru"),
    ("LDH", "Ludhiana Junction", "Ludhiana"),
    ("ST", "Surat Station", "Surat"),
]

AIRLINES = {
    "IndiGo": "6E",
    "Air India": "AI",
    "Vistara": "UK",
    "SpiceJet": "SG",
    "Akasa Air": "QP",
    "Go First": "G8",
    "AirAsia India": "I5",
}

TRAIN_SUFFIXES = [
    "Express", "Superfast Express", "Mail Express",
    "Duronto Express", "Shatabdi Express", "Jan Shatabdi",
    "Intercity Express", "Rajdhani Express",
]

FLIGHT_SEAT_OPTIONS = [120, 150, 180, 186, 222]
TRAIN_SEAT_OPTIONS = [500, 650, 800, 1000, 1200]
TIME_MINUTE_CHOICES = [0, 15, 30, 45]

# Extra scenic/tourist towns (no major airport of their own) so
# Hotels and Cabs cover realistic holiday destinations too, not
# just the airport/station cities above.
EXTRA_HOTEL_CITIES = [
    "Manali", "Shimla", "Ooty", "Darjeeling", "Rishikesh",
    "Pushkar", "Munnar", "Alleppey", "Mount Abu", "Nainital",
]

HOTEL_NAME_TEMPLATES = [
    "The Grand {city}", "{city} Palace Hotel", "Hotel {city} Residency",
    "{city} Comfort Inn", "Royal {city} Suites", "{city} Heritage Hotel",
    "The {city} Retreat", "{city} Business Hotel", "Lakeview {city} Resort",
    "{city} Garden Inn",
]

ROOM_TYPES = ["Single", "Double", "Deluxe", "Suite"]
ROOM_TYPE_PRICE_MULTIPLIER = {"Single": 1.0, "Double": 1.4, "Deluxe": 2.0, "Suite": 3.2}

CAB_TYPES = {"Hatchback": 4, "Sedan": 4, "SUV": 6, "Mini Van": 8}  # type -> seat capacity

PACKAGE_NAME_TEMPLATES = [
    "{destination} Getaway", "Explore {destination}", "{destination} Honeymoon Special",
    "{destination} Family Tour", "{destination} Adventure Package",
    "Romantic {destination} Escape", "{destination} Heritage Tour",
    "{destination} Budget Trip", "{destination} Weekend Special",
]

PACKAGE_DURATION_CHOICES = [2, 3, 4, 5, 6, 7]

DRIVER_FIRST_NAMES = [
    "Rahul", "Amit", "Suresh", "Vijay", "Ramesh", "Anil", "Sanjay", "Deepak",
    "Manoj", "Ravi", "Ajay", "Vikram", "Naveen", "Prakash", "Sunil",
]
DRIVER_LAST_NAMES = [
    "Kumar", "Sharma", "Singh", "Verma", "Gupta", "Yadav", "Mishra",
    "Patel", "Reddy", "Nair", "Das", "Chauhan",
]
VEHICLE_STATE_CODES = ["DL", "MH", "KA", "TN", "WB", "UP", "RJ", "GJ", "PB", "HR"]

# -----------------------------------------------------
# Coupons (Stage 7)
# -----------------------------------------------------
# Each tuple is:
#   (code, description, discount_type, discount_value,
#    max_discount_amount, min_booking_amount, usage_limit, expiry_days)
#
# discount_type is 'Flat' (a fixed Rs. amount off) or 'Percentage'.
# max_discount_amount is None for every Flat coupon (a flat discount
# needs no cap) and a Rs. cap for most Percentage coupons, so a big
# booking doesn't get an unreasonably large discount.
# usage_limit of None means unlimited redemptions; a number caps how
# many times that coupon can be used in total across all users.
# expiry_days of None means the coupon never expires. A number is
# turned into a real expiry_date by seed_coupons() below, counted
# from whenever "Load Sample Data" is actually run - so coupons stay
# valid ("available") for that many days from today, not from a
# fixed date baked into this file.
COUPON_TEMPLATES = [
    ("WELCOME100", "Welcome offer for new customers", "Flat", 100, None, 500, None, None),
    ("WELCOME200", "Welcome offer for new customers", "Flat", 200, None, 1000, None, None),
    ("FIRST50", "First booking discount", "Flat", 50, None, 300, 1000, None),
    ("SAVE5", "Flat percentage savings on any booking", "Percentage", 5, 200, 500, None, None),
    ("SAVE10", "Flat percentage savings on any booking", "Percentage", 10, 500, 1500, None, None),
    ("SAVE15", "Flat percentage savings on any booking", "Percentage", 15, 750, 2500, 500, None),
    ("SAVE20", "Flat percentage savings on any booking", "Percentage", 20, 1000, 4000, 300, 90),
    ("FLAT500", "Flat Rs. 500 off on bigger bookings", "Flat", 500, None, 3000, 200, 60),
    ("FLAT1000", "Flat Rs. 1000 off on bigger bookings", "Flat", 1000, None, 6000, 100, 60),
    ("FLAT1500", "Flat Rs. 1500 off on bigger bookings", "Flat", 1500, None, 10000, 50, 45),
    ("FLY10", "Extra savings on flight bookings", "Percentage", 10, 800, 2000, None, None),
    ("FLYHIGH", "Flat discount on flight bookings", "Flat", 300, None, 2500, 400, None),
    ("SKYDEAL", "Percentage off on flight bookings", "Percentage", 8, 400, 1800, 300, 75),
    ("TRAINSAVE", "Discount for train travellers", "Flat", 100, None, 500, None, None),
    ("RAILWAY10", "Percentage off on train bookings", "Percentage", 10, 300, 1000, None, None),
    ("HOTELSTAY", "Discount on hotel stays", "Flat", 500, None, 3000, None, None),
    ("STAYMORE", "Percentage off on longer hotel stays", "Percentage", 12, 1200, 5000, 250, 90),
    ("LUXSTAY", "Flat discount on premium hotel stays", "Flat", 1000, None, 8000, 100, 120),
    ("CABRIDE", "Discount on cab bookings", "Flat", 100, None, 800, None, None),
    ("RIDE20", "Percentage off on cab bookings", "Percentage", 20, 200, 600, None, None),
    ("TRIPPER", "Flat discount for frequent travellers", "Flat", 150, None, 1000, 500, None),
    ("PACKAGE500", "Discount on holiday packages", "Flat", 500, None, 5000, 200, 90),
    ("HOLIDAY1000", "Flat discount on holiday packages", "Flat", 1000, None, 8000, 150, 120),
    ("VACAY15", "Percentage off on holiday packages", "Percentage", 15, 1500, 6000, 200, 90),
    ("SUMMER2026", "Summer season discount", "Percentage", 12, 1000, 3000, 500, 60),
    ("MONSOON300", "Monsoon season discount", "Flat", 300, None, 2000, 400, 45),
    ("WINTER10", "Winter season discount", "Percentage", 10, 700, 2500, 300, 75),
    ("FESTIVE500", "Festive season discount", "Flat", 500, None, 3500, 250, 30),
    ("DIWALI777", "Diwali special discount", "Flat", 777, None, 5000, 100, 30),
    ("NEWYEAR2027", "New Year special discount", "Percentage", 20, 2000, 8000, 100, 100),
    ("WEEKEND20", "Weekend getaway discount", "Percentage", 20, 400, 1000, None, None),
    ("FLASH15", "Limited-time flash sale discount", "Percentage", 15, 600, 2000, 500, 15),
    ("MEGA25", "Mega sale discount on high-value bookings", "Percentage", 25, 2500, 10000, 50, 45),
    ("STUDENT50", "Student discount", "Flat", 50, None, 300, None, None),
    ("FAMILY800", "Family package discount", "Flat", 800, None, 6000, 200, 90),
    ("COUPLE300", "Couple getaway discount", "Flat", 300, None, 3000, 300, 60),
    ("SOLO100", "Solo traveller discount", "Flat", 100, None, 1000, None, None),
    ("BIGSAVER", "Big savings on high-value bookings", "Percentage", 18, 1800, 7000, 150, 90),
    ("QUICKBOOK", "Quick booking discount", "Flat", 150, None, 1200, 600, None),
    ("LASTMIN10", "Last-minute booking discount", "Percentage", 10, 500, 1500, 400, 20),
]


def _random_time():
    """Returns a random datetime.time with a 'nice' minute value."""
    hour = random.randint(0, 23)
    minute = random.choice(TIME_MINUTE_CHOICES)
    return datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time()


def _add_minutes(start_time, minutes):
    """
    Adds `minutes` to a datetime.time and returns the resulting
    time, wrapping around a 24-hour clock if needed.
    """
    combined = datetime.combine(date.today(), start_time) + timedelta(minutes=minutes)
    return combined.time()


def _random_future_date(max_days_ahead=45):
    """
    Returns a random date between today (whichever day this actually
    runs on) and that many days after today. Since this is always
    anchored to "today", every flight/train/cab seeded in a single
    run of Load Sample Data is guaranteed to be dated no earlier than
    the day you actually loaded the data - there's no fixed date
    baked in here.
    """
    return date.today() + timedelta(days=random.randint(0, max_days_ahead))


def _all_hotel_cab_cities():
    """
    Returns the combined, de-duplicated list of cities used for
    Hotels and Cabs: every airport city plus a handful of scenic
    tourist towns that don't have their own airport.
    """
    airport_cities = [city for _, _, city in AIRPORTS]
    combined = airport_cities + EXTRA_HOTEL_CITIES
    # De-duplicate while preserving order
    seen = set()
    unique_cities = []
    for city in combined:
        if city not in seen:
            seen.add(city)
            unique_cities.append(city)
    return unique_cities


# -----------------------------------------------------
# Airports and Stations (reference data)
# -----------------------------------------------------

def seed_airports():
    """
    Inserts the AIRPORTS list if the Airports table is currently
    empty. Returns a dict mapping airport_code -> airport_id for
    every airport now in the table (existing or newly inserted).
    """
    count_result = database.fetch_query("SELECT COUNT(*) AS total FROM Airports", fetch_one=True)
    existing_count = count_result["total"] if count_result else 0

    if existing_count == 0:
        rows = [(code, name, city) for code, name, city in AIRPORTS]
        database.execute_many(
            "INSERT INTO Airports (airport_code, airport_name, city) VALUES (%s, %s, %s)",
            rows,
        )
        utils.log_activity(f"Seeded {len(rows)} airports.")

    airports = database.fetch_query("SELECT airport_id, airport_code, city FROM Airports")
    return {row["airport_code"]: row for row in (airports or [])}


def seed_stations():
    """
    Inserts the STATIONS list if the Stations table is currently
    empty. Returns a dict mapping station_code -> station row for
    every station now in the table.
    """
    count_result = database.fetch_query("SELECT COUNT(*) AS total FROM Stations", fetch_one=True)
    existing_count = count_result["total"] if count_result else 0

    if existing_count == 0:
        rows = [(code, name, city) for code, name, city in STATIONS]
        database.execute_many(
            "INSERT INTO Stations (station_code, station_name, city) VALUES (%s, %s, %s)",
            rows,
        )
        utils.log_activity(f"Seeded {len(rows)} stations.")

    stations = database.fetch_query("SELECT station_id, station_code, city FROM Stations")
    return {row["station_code"]: row for row in (stations or [])}


# -----------------------------------------------------
# Flights and Trains (generated sample bookable data)
# -----------------------------------------------------

def seed_flights(airport_lookup, target_count=480):
    """
    Clears out the Flights table and inserts `target_count` freshly
    generated flight records, every time this runs - unlike Hotels/
    Rooms/Packages below, Flights has a travel_date that goes stale
    as real time passes, so re-running Load Sample Data always wipes
    old flights and regenerates them dated from today (whichever day
    that turns out to be) rather than leaving old dates behind.

    Uses the airport_lookup dict (code -> row) produced by
    seed_airports(). Returns the number of flights inserted.
    """
    database.execute_query("DELETE FROM Flights")

    airport_codes = list(airport_lookup.keys())
    rows = []

    for _ in range(target_count):
        source_code, dest_code = random.sample(airport_codes, 2)
        source_id = airport_lookup[source_code]["airport_id"]
        dest_id = airport_lookup[dest_code]["airport_id"]

        airline_name = random.choice(list(AIRLINES.keys()))
        prefix = AIRLINES[airline_name]
        flight_number = f"{prefix}{random.randint(100, 1999)}"

        travel_date = _random_future_date()
        departure_time = _random_time()
        duration_minutes = random.randint(60, 240)
        arrival_time = _add_minutes(departure_time, duration_minutes)

        total_seats = random.choice(FLIGHT_SEAT_OPTIONS)
        available_seats = random.randint(int(total_seats * 0.1), total_seats)

        price = round((1500 + duration_minutes * 12 + random.randint(-400, 1500)) / 50) * 50
        price = max(price, 1500)

        rows.append((
            flight_number, airline_name, source_id, dest_id, travel_date,
            departure_time, arrival_time, duration_minutes, price,
            total_seats, available_seats, "Scheduled",
        ))

    database.execute_many(
        """
        INSERT INTO Flights (
            flight_number, airline_name, source_airport_id, destination_airport_id,
            travel_date, departure_time, arrival_time, duration_minutes,
            price, total_seats, available_seats, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    utils.log_activity(f"Seeded {len(rows)} flights (previous flights cleared first).")
    return len(rows)


def seed_trains(station_lookup, target_count=480):
    """
    Clears out the Trains table and inserts `target_count` freshly
    generated train records, every time this runs - same reasoning
    as seed_flights() above: travel_date goes stale over time, so
    the table is always refreshed rather than left with old dates.

    Uses the station_lookup dict (code -> row) produced by
    seed_stations(). Returns the number of trains inserted.
    """
    database.execute_query("DELETE FROM Trains")

    station_codes = list(station_lookup.keys())
    rows = []

    for _ in range(target_count):
        source_code, dest_code = random.sample(station_codes, 2)
        source_row = station_lookup[source_code]
        dest_row = station_lookup[dest_code]

        train_number = str(random.randint(10000, 99999))
        suffix = random.choice(TRAIN_SUFFIXES)
        train_name = f"{source_row['city']} - {dest_row['city']} {suffix}"

        travel_date = _random_future_date()
        departure_time = _random_time()
        duration_minutes = random.randint(180, 1400)
        arrival_time = _add_minutes(departure_time, duration_minutes)

        total_seats = random.choice(TRAIN_SEAT_OPTIONS)
        available_seats = random.randint(int(total_seats * 0.1), total_seats)

        price = round((200 + duration_minutes * 1.5 + random.randint(-100, 400)) / 10) * 10
        price = max(price, 150)

        rows.append((
            train_number, train_name, source_row["station_id"], dest_row["station_id"],
            travel_date, departure_time, arrival_time, duration_minutes, price,
            total_seats, available_seats, "Scheduled",
        ))

    database.execute_many(
        """
        INSERT INTO Trains (
            train_number, train_name, source_station_id, destination_station_id,
            travel_date, departure_time, arrival_time, duration_minutes,
            price, total_seats, available_seats, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    utils.log_activity(f"Seeded {len(rows)} trains (previous trains cleared first).")
    return len(rows)


# -----------------------------------------------------
# Hotels, Rooms, and Cabs (generated sample bookable data)
# -----------------------------------------------------

def seed_hotels(target_hotel_count=160):
    """
    Inserts randomly generated Hotels, each with 2-3 Room types,
    if the Hotels table is currently empty. Aims for roughly
    target_hotel_count hotels (~450-500 room rows in total).

    Returns (hotels_inserted, rooms_inserted) - both 0 if skipped.
    """
    count_result = database.fetch_query("SELECT COUNT(*) AS total FROM Hotels", fetch_one=True)
    if count_result and count_result["total"] > 0:
        return 0, 0

    cities = _all_hotel_cab_cities()
    hotel_rows = []

    for _ in range(target_hotel_count):
        city = random.choice(cities)
        name_template = random.choice(HOTEL_NAME_TEMPLATES)
        hotel_name = name_template.format(city=city)
        star_rating = random.randint(2, 5)
        street_number = random.randint(1, 200)
        address = f"{street_number}, MG Road, {city}"
        contact_number = f"9{random.randint(100000000, 999999999)}"

        hotel_rows.append((hotel_name, city, address, star_rating, contact_number))

    database.execute_many(
        "INSERT INTO Hotels (hotel_name, city, address, star_rating, contact_number) "
        "VALUES (%s, %s, %s, %s, %s)",
        hotel_rows,
    )
    utils.log_activity(f"Seeded {len(hotel_rows)} hotels.")

    # Fetch back the hotels we just inserted (with their new IDs and
    # star ratings) so room prices can be scaled sensibly.
    hotels = database.fetch_query("SELECT hotel_id, star_rating FROM Hotels") or []

    room_rows = []
    for hotel in hotels:
        base_price = 1200 + hotel["star_rating"] * 600
        room_types_for_hotel = random.sample(ROOM_TYPES, k=random.randint(2, 3))
        for room_type in room_types_for_hotel:
            price_per_night = round(base_price * ROOM_TYPE_PRICE_MULTIPLIER[room_type] / 50) * 50
            total_rooms = random.randint(5, 30)
            available_rooms = random.randint(int(total_rooms * 0.2), total_rooms)
            room_rows.append((
                hotel["hotel_id"], room_type, price_per_night, total_rooms, available_rooms
            ))

    database.execute_many(
        "INSERT INTO Rooms (hotel_id, room_type, price_per_night, total_rooms, available_rooms) "
        "VALUES (%s, %s, %s, %s, %s)",
        room_rows,
    )
    utils.log_activity(f"Seeded {len(room_rows)} rooms.")

    return len(hotel_rows), len(room_rows)


def seed_cabs(target_count=480):
    """
    Clears out the Cabs table and inserts `target_count` freshly
    generated cab records, every time this runs - same reasoning
    as seed_flights()/seed_trains(): travel_date goes stale over
    time, so the table is always refreshed rather than left with
    old dates.

    Returns the number of cabs inserted.
    """
    database.execute_query("DELETE FROM Cabs")

    cities = _all_hotel_cab_cities()
    cab_types = list(CAB_TYPES.keys())
    rows = []

    for _ in range(target_count):
        source_city, destination_city = random.sample(cities, 2)
        cab_type = random.choice(cab_types)
        seats_capacity = CAB_TYPES[cab_type]

        driver_name = f"{random.choice(DRIVER_FIRST_NAMES)} {random.choice(DRIVER_LAST_NAMES)}"
        state_code = random.choice(VEHICLE_STATE_CODES)
        cab_number = (
            f"{state_code}{random.randint(1, 99):02d}"
            f"{random.choice('ABCDEFGH')}{random.randint(1000, 9999)}"
        )

        travel_date = _random_future_date()
        departure_time = _random_time()

        base_fare = {"Hatchback": 8, "Sedan": 10, "SUV": 14, "Mini Van": 16}[cab_type]
        price = round((800 + base_fare * random.randint(20, 400)) / 50) * 50

        status = random.choices(["Available", "Booked"], weights=[80, 20])[0]

        rows.append((
            cab_number, cab_type, driver_name, source_city, destination_city,
            travel_date, departure_time, price, seats_capacity, status,
        ))

    database.execute_many(
        """
        INSERT INTO Cabs (
            cab_number, cab_type, driver_name, source_city, destination_city,
            travel_date, departure_time, price, seats_capacity, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    utils.log_activity(f"Seeded {len(rows)} cabs (previous cabs cleared first).")
    return len(rows)


def seed_packages(target_count=60):
    """
    Inserts `target_count` randomly generated holiday package
    records if the Packages table is currently empty. Reuses the
    same city list as Hotels/Cabs, since packages are sold to the
    same destinations.

    Returns the number of packages inserted (0 if already seeded).
    """
    count_result = database.fetch_query("SELECT COUNT(*) AS total FROM Packages", fetch_one=True)
    if count_result and count_result["total"] > 0:
        return 0

    destinations = _all_hotel_cab_cities()
    rows = []

    for _ in range(target_count):
        destination = random.choice(destinations)
        name_template = random.choice(PACKAGE_NAME_TEMPLATES)
        package_name = name_template.format(destination=destination)

        duration_days = random.choice(PACKAGE_DURATION_CHOICES)
        nights = max(duration_days - 1, 1)

        base_price = 3000 + duration_days * 1500
        price = round((base_price + random.randint(-500, 3000)) / 100) * 100
        price = max(price, 2500)

        total_slots = random.choice([10, 15, 20, 25, 30])
        available_slots = random.randint(int(total_slots * 0.2), total_slots)

        description = (
            f"{duration_days}D/{nights}N {destination} package including "
            f"stay, breakfast and sightseeing."
        )

        rows.append((
            package_name, destination, duration_days, price,
            description, total_slots, available_slots, "Active",
        ))

    database.execute_many(
        """
        INSERT INTO Packages (
            package_name, destination, duration_days, price,
            description, total_slots, available_slots, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    utils.log_activity(f"Seeded {len(rows)} packages.")
    return len(rows)


def seed_coupons():
    """
    Clears out the Coupons table and inserts the COUPON_TEMPLATES
    list fresh, every time this runs - unlike Hotels/Rooms/Packages,
    a coupon has an expiry_date that goes stale over time, so this
    table is always refreshed rather than left with old expiry
    dates. NOTE: this also removes any coupon an admin added
    manually through Manage Coupons - since Coupons is refreshed
    every time for the same date-staleness reason as Flights/Trains/
    Cabs, a manually-added coupon won't survive the next "Load
    Sample Data" run either.

    Each template's expiry_days is converted into a real calendar
    date here, counted from today (whenever "Load Sample Data" is
    actually run) - a template with expiry_days set to None becomes
    a coupon that never expires.

    Returns the number of coupons inserted.
    """
    database.execute_query("DELETE FROM Coupons")

    rows = []
    for (code, description, discount_type, discount_value, max_discount_amount,
         min_booking_amount, usage_limit, expiry_days) in COUPON_TEMPLATES:
        expiry_date = date.today() + timedelta(days=expiry_days) if expiry_days else None
        rows.append((
            code, description, discount_type, discount_value, max_discount_amount,
            min_booking_amount, usage_limit, expiry_date, "Active",
        ))

    database.execute_many(
        """
        INSERT INTO Coupons (
            code, description, discount_type, discount_value, max_discount_amount,
            min_booking_amount, usage_limit, expiry_date, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    utils.log_activity(f"Seeded {len(rows)} coupons (previous coupons cleared first).")
    return len(rows)


def run_full_seed():
    """
    Runs the complete seeding process: Airports, Stations, then
    Flights, Trains, Hotels/Rooms, Cabs, Packages, and Coupons
    built on top of them.

    Airports/Stations/Hotels/Rooms/Packages are only populated if
    currently empty, so re-running this is safe and won't duplicate
    or disturb them. Flights, Trains, Cabs, and Coupons are
    different: each of those is always cleared out and freshly
    regenerated on every call, because they carry a date
    (travel_date or expiry_date) that goes stale as real time
    passes - so every time "Load Sample Data" is run, those four
    always come back dated from that day forward, no matter how
    long ago they were last seeded. See each seed_*() function's
    own docstring for details.

    Returns a summary dict:
        {"airports": <total rows now>, "stations": <total rows now>,
         "flights_inserted": <rows just inserted - always refreshed>,
         "trains_inserted": <rows just inserted - always refreshed>,
         "hotels_inserted": <rows just inserted, 0 if already had data>,
         "rooms_inserted": <rows just inserted, 0 if already had data>,
         "cabs_inserted": <rows just inserted - always refreshed>,
         "packages_inserted": <rows just inserted, 0 if already had data>,
         "coupons_inserted": <rows just inserted - always refreshed>}
    """
    airport_lookup = seed_airports()
    station_lookup = seed_stations()

    flights_inserted = seed_flights(airport_lookup)
    trains_inserted = seed_trains(station_lookup)
    hotels_inserted, rooms_inserted = seed_hotels()
    cabs_inserted = seed_cabs()
    packages_inserted = seed_packages()
    coupons_inserted = seed_coupons()

    airport_total = database.fetch_query(
        "SELECT COUNT(*) AS total FROM Airports", fetch_one=True
    )["total"]
    station_total = database.fetch_query(
        "SELECT COUNT(*) AS total FROM Stations", fetch_one=True
    )["total"]

    return {
        "airports": airport_total,
        "stations": station_total,
        "flights_inserted": flights_inserted,
        "trains_inserted": trains_inserted,
        "hotels_inserted": hotels_inserted,
        "rooms_inserted": rooms_inserted,
        "cabs_inserted": cabs_inserted,
        "packages_inserted": packages_inserted,
        "coupons_inserted": coupons_inserted,
    }