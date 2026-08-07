# GoTravel

A Complete Travel Booking & Management System — a CBSE Class 12 Computer
Science project, inspired by Goibibo, built as a standalone Python desktop
application with a MySQL backend.

## Status
Currently in development, built stage by stage.

- [x] Stage 1 — Project foundation (DB connection, config, utils, CLI shell)
- [x] Stage 2 — User authentication & profile management
- [ ] Stage 3 — Admin panel
- [ ] Stage 4 — Flights & Trains
- [ ] Stage 5 — Hotels & Cabs
- [ ] Stage 6 — Holiday Packages & Booking engine
- [ ] Stage 7 — Payments, Wallet & Coupons
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

## Project Structure
```
GoTravel/
├── main.py            Entry point (CLI, GUI fallback in later stage)
├── connection.py       MySQL connection handling
├── database.py         Schema init + query helpers
├── utils.py             Shared CLI helpers, validation, logging
├── login.py             Registration & authentication
├── user.py               Profile view/edit, password change
├── sql/gotravel.sql       Database schema
└── files/
    ├── config.example.txt   Tracked config template
    ├── config.txt             Your real config (gitignored)
    └── logs.txt                 Activity log (gitignored)
```