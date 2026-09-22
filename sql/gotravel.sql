-- =====================================================
-- GoTravel Database Schema
-- Run automatically by database.py's initialize_database().
-- =====================================================

CREATE DATABASE IF NOT EXISTS gotravel;

USE gotravel;

-- Table: Users - customer accounts
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    gender VARCHAR(10),
    date_of_birth DATE,
    address VARCHAR(255),
    wallet_balance DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active TINYINT(1) DEFAULT 1
);

-- Table: Admins - admin accounts
CREATE TABLE IF NOT EXISTS Admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Airports - reference data for flight source/destination
CREATE TABLE IF NOT EXISTS Airports (
    airport_id INT AUTO_INCREMENT PRIMARY KEY,
    airport_code VARCHAR(5) NOT NULL UNIQUE,
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) DEFAULT 'India'
);

-- Table: Stations - reference data for train source/destination
CREATE TABLE IF NOT EXISTS Stations (
    station_id INT AUTO_INCREMENT PRIMARY KEY,
    station_code VARCHAR(10) NOT NULL UNIQUE,
    station_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL
);

-- Table: Flights
CREATE TABLE IF NOT EXISTS Flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    airline_name VARCHAR(50) NOT NULL,
    source_airport_id INT NOT NULL,
    destination_airport_id INT NOT NULL,
    travel_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    duration_minutes INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,
    status VARCHAR(20) DEFAULT 'Scheduled',
    FOREIGN KEY (source_airport_id) REFERENCES Airports(airport_id),
    FOREIGN KEY (destination_airport_id) REFERENCES Airports(airport_id)
);

-- Table: Trains
CREATE TABLE IF NOT EXISTS Trains (
    train_id INT AUTO_INCREMENT PRIMARY KEY,
    train_number VARCHAR(10) NOT NULL,
    train_name VARCHAR(100) NOT NULL,
    source_station_id INT NOT NULL,
    destination_station_id INT NOT NULL,
    travel_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    duration_minutes INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,
    status VARCHAR(20) DEFAULT 'Scheduled',
    FOREIGN KEY (source_station_id) REFERENCES Stations(station_id),
    FOREIGN KEY (destination_station_id) REFERENCES Stations(station_id)
);

-- Table: Hotels
CREATE TABLE IF NOT EXISTS Hotels (
    hotel_id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_name VARCHAR(150) NOT NULL,
    city VARCHAR(50) NOT NULL,
    address VARCHAR(255),
    star_rating INT,
    contact_number VARCHAR(15)
);

-- Table: Rooms - each hotel can have several room types
CREATE TABLE IF NOT EXISTS Rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    room_type VARCHAR(30) NOT NULL,
    price_per_night DECIMAL(10,2) NOT NULL,
    total_rooms INT NOT NULL,
    available_rooms INT NOT NULL,
    FOREIGN KEY (hotel_id) REFERENCES Hotels(hotel_id)
);

-- Table: Cabs - booked as a whole vehicle, not seat-by-seat
CREATE TABLE IF NOT EXISTS Cabs (
    cab_id INT AUTO_INCREMENT PRIMARY KEY,
    cab_number VARCHAR(15) NOT NULL,
    cab_type VARCHAR(30) NOT NULL,
    driver_name VARCHAR(100) NOT NULL,
    source_city VARCHAR(50) NOT NULL,
    destination_city VARCHAR(50) NOT NULL,
    travel_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    seats_capacity INT NOT NULL,
    status VARCHAR(20) DEFAULT 'Available'
);

-- Table: Packages - fixed-itinerary holiday packages with limited slots
CREATE TABLE IF NOT EXISTS Packages (
    package_id INT AUTO_INCREMENT PRIMARY KEY,
    package_name VARCHAR(150) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    duration_days INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description VARCHAR(255),
    total_slots INT NOT NULL,
    available_slots INT NOT NULL,
    status VARCHAR(20) DEFAULT 'Active'
);

-- Table: Bookings - one row per booking of any type.
-- booking_type tells booking.py which table item_id points into.
CREATE TABLE IF NOT EXISTS Bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    booking_type VARCHAR(20) NOT NULL,
    item_id INT NOT NULL,
    item_label VARCHAR(150) NOT NULL,
    travel_date DATE,
    quantity INT NOT NULL DEFAULT 1,
    nights INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    booking_status VARCHAR(20) DEFAULT 'Confirmed',
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(10) DEFAULT 'Wallet',
    coupon_code VARCHAR(30),
    discount_amount DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Table: WalletTransactions - every credit/debit against wallet_balance
CREATE TABLE IF NOT EXISTS WalletTransactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description VARCHAR(255),
    balance_after DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Table: Coupons - discount_type is 'Flat' or 'Percentage'
CREATE TABLE IF NOT EXISTS Coupons (
    coupon_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE,
    description VARCHAR(255),
    discount_type VARCHAR(10) NOT NULL,
    discount_value DECIMAL(10,2) NOT NULL,
    max_discount_amount DECIMAL(10,2),
    min_booking_amount DECIMAL(10,2) DEFAULT 0,
    usage_limit INT,
    times_used INT DEFAULT 0,
    expiry_date DATE,
    status VARCHAR(20) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Reviews - review_type is 'Booking' or 'Trip'
CREATE TABLE IF NOT EXISTS Reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    user_id INT NOT NULL,
    review_type VARCHAR(10) NOT NULL,
    rating INT NOT NULL,
    comment VARCHAR(500),
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);