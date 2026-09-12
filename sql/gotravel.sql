-- =====================================================
-- GoTravel Database Schema
-- =====================================================
-- This file is executed automatically by database.py
-- (initialize_database function) using the mysql-connector.
--
-- CONTENT SO FAR:
--   Stage 1: Database creation, Users, Admins
--   Stage 4: Airports, Stations, Flights, Trains
--   Stage 5: Hotels, Rooms, Cabs
--   Stage 6: Packages, Bookings
--   Stage 7: WalletTransactions, Coupons, plus
--            payment_method/coupon_code/discount_amount
--            columns on Bookings (see NOTE below)
--
-- FUTURE STAGES will ADD tables such as:
--   Reviews, Invoices, Reports, Notifications
-- These are intentionally NOT created yet to avoid
-- unused/empty tables before their features exist.
--
-- NOTE: this script only ever CREATEs tables - 'CREATE TABLE
-- IF NOT EXISTS' does nothing if the table already exists. So
-- if you already had GoTravel running BEFORE Stage 7, your
-- existing Bookings table does NOT get the three new Stage 7
-- columns (payment_method, coupon_code, discount_amount) just
-- because this file changed - CREATE TABLE alone can't add a
-- column to a table that's already there. That's fine though:
-- database.py's initialize_database() also runs a few ALTER
-- TABLE statements right after this script, specifically to
-- add those three columns to an EXISTING Bookings table without
-- touching any of its existing rows. Your old users and bookings
-- are kept exactly as they are - nothing here deletes any data.
-- =====================================================

CREATE DATABASE IF NOT EXISTS gotravel;

USE gotravel;

-- -----------------------------------------------------
-- Table: Users
-- Stores customer accounts (created/used from Stage 2)
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table: Admins
-- Stores admin accounts (created/used from Stage 3)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- Table: Airports
-- Reference data for flight source/destination (Stage 4)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Airports (
    airport_id INT AUTO_INCREMENT PRIMARY KEY,
    airport_code VARCHAR(5) NOT NULL UNIQUE,
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) DEFAULT 'India'
);

-- -----------------------------------------------------
-- Table: Stations
-- Reference data for train source/destination (Stage 4)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Stations (
    station_id INT AUTO_INCREMENT PRIMARY KEY,
    station_code VARCHAR(10) NOT NULL UNIQUE,
    station_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL
);

-- -----------------------------------------------------
-- Table: Flights (Stage 4)
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table: Trains (Stage 4)
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table: Hotels (Stage 5)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Hotels (
    hotel_id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_name VARCHAR(150) NOT NULL,
    city VARCHAR(50) NOT NULL,
    address VARCHAR(255),
    star_rating INT,
    contact_number VARCHAR(15)
);

-- -----------------------------------------------------
-- Table: Rooms (Stage 5)
-- Each hotel offers multiple room types at different prices
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    room_type VARCHAR(30) NOT NULL,
    price_per_night DECIMAL(10,2) NOT NULL,
    total_rooms INT NOT NULL,
    available_rooms INT NOT NULL,
    FOREIGN KEY (hotel_id) REFERENCES Hotels(hotel_id)
);

-- -----------------------------------------------------
-- Table: Cabs (Stage 5)
-- Unlike Flights/Trains, a cab is booked as a whole vehicle,
-- not sold seat-by-seat - so status is Available/Booked
-- rather than an available_seats count.
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table: Packages (Stage 6)
-- A fixed-itinerary holiday package with a limited number
-- of traveller slots, similar in spirit to how Cabs track
-- a simple availability count.
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table: Bookings (Stage 6)
-- A single table covers every booking type. `booking_type`
-- ('Flight'/'Train'/'Hotel'/'Cab'/'Package') tells booking.py
-- which table `item_id` points into. `item_label` freezes a
-- human-readable snapshot at booking time so history still
-- reads clearly even if the original row changes later.
-- -----------------------------------------------------
-- payment_method/coupon_code/discount_amount were added in
-- Stage 7. A fresh install gets them immediately from this
-- CREATE TABLE. If you're upgrading an existing database from
-- before Stage 7, see the NOTE at the top of this file - those
-- columns get added separately by database.py, without deleting
-- any of your existing rows.
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

-- -----------------------------------------------------
-- Table: WalletTransactions (Stage 7)
-- Every credit (top-up, refund) or debit (wallet-paid
-- booking) against a user's Users.wallet_balance is logged
-- here, with the resulting balance snapshotted so history
-- reads clearly without recomputing anything.
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table: Coupons (Stage 7)
-- discount_type is 'Flat' (a fixed Rs. amount off) or
-- 'Percentage' (optionally capped by max_discount_amount).
-- usage_limit of NULL means unlimited redemptions.
-- -----------------------------------------------------
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