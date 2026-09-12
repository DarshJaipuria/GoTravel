# GoTravel

A Complete Travel Booking & Management System — a CBSE Class 12 Computer
Science project, inspired by Goibibo, built as a standalone Python desktop
application with a MySQL backend.

## Status
Currently in development, built stage by stage.

- [x] Stage 1 — Project foundation (DB connection, config, utils, CLI shell)
- [x] Stage 2 — User authentication & profile management
- [x] Stage 3 — Admin panel
- [x] Stage 4 — Flights & Trains
- [x] Stage 5 — Hotels & Cabs
- [x] Stage 6 — Holiday Packages & Booking engine
- [x] Stage 7 — Payments, Wallet & Coupons
- [ ] Stage 8 — Reviews, Invoices & ticket generation
- [ ] Stage 9 — Reports & Analytics
- [ ] Stage 10 — Tkinter GUI & polish

## Tech
Python 3, MySQL (via `mysql-connector-python`), Tkinter (GUI, later stage),
Matplotlib (analytics, later stage).

## Setup
1. Install dependencies:
   ```
   pip install mysql-connector-python
   ```
2. Copy the config template and fill in your MySQL credentials:
   ```
   copy files\config.example.txt files\config.txt      (Windows)
   cp files/config.example.txt files/config.txt        (macOS/Linux)
   ```
3. Edit `files/config.txt` with your MySQL host/user/password.
4. Run the app:
   ```
   python main.py
   ```
5. From the main menu, choose **Initialize Database** first, then
   **Test Database Connection** to confirm everything's wired up.
   '''
6. Log in as an admin, then from the admin dashboard choose
   **Load Sample Data** to populate ~480 sample flights, ~480
   sample trains, ~160 hotels, ~480 cabs, and ~60 holiday
   packages across major Indian cities.
7. Still as admin, optionally add a coupon or two from
   **Manage Coupons** (e.g. a `WELCOME200` flat-Rs.200 coupon)
   so there's something for users to try at checkout.
8. Log in as a regular user to search Flights/Trains/Hotels/
   Cabs/Packages, then use **My Bookings** to book, view, or
   cancel a booking (note the ID shown in search results, then
   use it to book). At checkout you can optionally apply a
   coupon code, then pay via your **Wallet**, or simulated
   Card/UPI (top up your Wallet from **My Wallet** first).
   Cancelling a booking always refunds the amount to your
   Wallet.

## Project Structure
```
GoTravel/
├── main.py            Entry point (CLI, GUI fallback in later stage)
├── connection.py       MySQL connection handling
├── database.py         Schema init + query helpers
├── utils.py             Shared CLI helpers, validation, logging
├── login.py             Registration & authentication
├── user.py               Profile view/edit, password change
├── admin.py               Admin login, user management, bookings overview
├── flights.py              Flight search + admin management
├── trains.py                Train search + admin management
├── hotels.py                  Hotel/Room search + admin management
├── cabs.py                     Cab search + admin management
├── packages.py                  Holiday Package search + admin management
├── booking.py                    Book / view / cancel + checkout (coupon + payment)
├── wallet.py                       Wallet balance, top-ups, credit/debit helpers
├── coupons.py                       Coupon validation + admin management
├── seed_data.py                   Sample data generator
├── sql/gotravel.sql                Database schema
└── files/
    ├── config.example.txt   Tracked config template
    ├── config.txt             Your real config (gitignored)
    └── logs.txt                 Activity log (gitignored)
```