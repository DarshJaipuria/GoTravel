-- =====================================================
-- GoTravel Database Schema
-- =====================================================
-- This file is executed automatically by database.py
-- (initialize_database function) using the mysql-connector.
--
-- STAGE 1 CONTENT:
--   - Database creation
--   - Users table
--   - Admins table
--
-- FUTURE STAGES will ALTER / ADD tables such as:
--   Flights, Airports, Trains, Stations, Hotels, Rooms,
--   Cabs, Packages, Bookings, Payments, Wallet,
--   Transactions, Coupons, Reviews, Invoices, Reports,
--   Notifications
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