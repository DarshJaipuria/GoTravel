"""
seed_data.py
=====================================================
Generates realistic sample data for Airports, Stations,
Flights, and Trains so the application has something to
search from the moment it is set up.

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
    return date.today() + timedelta(days=random.randint(0, max_days_ahead))


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
    Inserts `target_count` randomly generated flight records if
    the Flights table is currently empty. Uses the airport_lookup
    dict (code -> row) produced by seed_airports().

    Returns the number of flights inserted (0 if already seeded).
    """
    count_result = database.fetch_query("SELECT COUNT(*) AS total FROM Flights", fetch_one=True)
    if count_result and count_result["total"] > 0:
        return 0

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
    utils.log_activity(f"Seeded {len(rows)} flights.")
    return len(rows)


def seed_trains(station_lookup, target_count=480):
    """
    Inserts `target_count` randomly generated train records if
    the Trains table is currently empty. Uses the station_lookup
    dict (code -> row) produced by seed_stations().

    Returns the number of trains inserted (0 if already seeded).
    """
    count_result = database.fetch_query("SELECT COUNT(*) AS total FROM Trains", fetch_one=True)
    if count_result and count_result["total"] > 0:
        return 0

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
    utils.log_activity(f"Seeded {len(rows)} trains.")
    return len(rows)


def run_full_seed():
    """
    Runs the complete seeding process: Airports, Stations, then
    Flights and Trains built on top of them. Safe to call even
    if some or all tables already have data - only empty tables
    are actually populated.

    Returns a summary dict:
        {"airports": <total rows now>, "stations": <total rows now>,
         "flights_inserted": <rows just inserted, 0 if skipped>,
         "trains_inserted": <rows just inserted, 0 if skipped>}
    """
    airport_lookup = seed_airports()
    station_lookup = seed_stations()

    flights_inserted = seed_flights(airport_lookup)
    trains_inserted = seed_trains(station_lookup)

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
    }