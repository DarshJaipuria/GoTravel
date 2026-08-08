-- =====================================================
-- GoTravel Database Schema
-- =====================================================
-- This file is executed automatically by database.py
-- (initialize_database function) using the mysql-connector.
--
-- CONTENT SO FAR:
--   Stage 1: Database creation, Users, Admins
--   Stage 4: Airports, Stations, Flights, Trains
--
-- FUTURE STAGES will ADD tables such as:
--   Hotels, Rooms, Cabs, Packages, Bookings, Payments,
--   Wallet, Transactions, Coupons, Reviews, Invoices,
--   Reports, Notifications
-- These are intentionally NOT created yet to avoid
-- unused/empty tables before their features exist.
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