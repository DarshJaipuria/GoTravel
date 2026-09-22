"""
wallet.py
=====================================================
Handles the user Wallet: view balance/history, add funds
(simulated top-up), and credit/debit helpers used by booking.py.
=====================================================
"""

import database
import utils

TOP_UP_METHODS = ["UPI", "Debit Card", "Credit Card", "Net Banking"]


def get_wallet_balance(user_id):
    """Returns the current wallet balance for a user (float)."""
    result = database.fetch_query(
        "SELECT wallet_balance FROM Users WHERE user_id = %s", (user_id,), fetch_one=True
    )
    return float(result["wallet_balance"]) if result else 0.0


def _record_transaction(user_id, transaction_type, amount, description, balance_after):
    """Inserts one row into WalletTransactions."""
    success, result = database.execute_query(
        """
        INSERT INTO WalletTransactions (user_id, transaction_type, amount, description, balance_after)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, transaction_type, amount, description, balance_after),
    )
    if not success:
        utils.log_activity(f"Failed to record wallet transaction for user {user_id}: {result}")
    return success


def credit_wallet(user_id, amount, description):
    """Adds `amount` to the wallet and logs a Credit transaction."""
    success, result = database.execute_query(
        "UPDATE Users SET wallet_balance = wallet_balance + %s WHERE user_id = %s",
        (amount, user_id),
    )
    if not success:
        return False, result

    new_balance = get_wallet_balance(user_id)
    _record_transaction(user_id, "Credit", amount, description, new_balance)
    return True, new_balance


def debit_wallet(user_id, amount, description):
    """Subtracts `amount` from the wallet and logs a Debit transaction."""
    success, result = database.execute_query(
        "UPDATE Users SET wallet_balance = wallet_balance - %s WHERE user_id = %s",
        (amount, user_id),
    )
    if not success:
        return False, result

    new_balance = get_wallet_balance(user_id)
    _record_transaction(user_id, "Debit", amount, description, new_balance)
    return True, new_balance


def view_wallet(user):
    """Shows the user's current balance and their last 20 transactions."""
    utils.print_header("MY WALLET")

    balance = get_wallet_balance(user["user_id"])
    print(f"\nCurrent Balance: Rs. {balance}")

    transactions = database.fetch_query(
        "SELECT * FROM WalletTransactions WHERE user_id = %s "
        "ORDER BY created_at DESC LIMIT 20",
        (user["user_id"],),
    )

    if not transactions:
        utils.print_info("No wallet transactions yet.")
    else:
        rows = [
            [
                t["transaction_id"], str(t["created_at"])[:19], t["transaction_type"],
                f"Rs. {t['amount']}", t["description"] or "-", f"Rs. {t['balance_after']}",
            ]
            for t in transactions
        ]
        utils.print_header("RECENT TRANSACTIONS (last 20)")
        utils.print_table(
            ["ID", "Date/Time", "Type", "Amount", "Description", "Balance After"], rows
        )

    utils.pause()


def add_funds(user):
    """Lets the user top up their wallet (simulated - no real payment gateway)."""
    utils.print_header("ADD MONEY TO WALLET", show_back_hint=True)
    print(f"Current Balance: Rs. {get_wallet_balance(user['user_id'])}\n")

    try:
        while True:
            amount_input = utils.get_non_empty_input("Amount to add (Rs.): ")
            try:
                amount = float(amount_input)
                if amount > 0:
                    break
                print("Amount must be greater than zero.")
            except ValueError:
                print("Please enter a valid number.")

        print("\nPayment Method (simulated - no real transaction is made):")
        for i, method in enumerate(TOP_UP_METHODS, start=1):
            print(f"  {i}. {method}")

        while True:
            method_choice = utils.get_non_empty_input("Choose a payment method (number): ")
            if method_choice.isdigit() and 1 <= int(method_choice) <= len(TOP_UP_METHODS):
                payment_method = TOP_UP_METHODS[int(method_choice) - 1]
                break
            print("Please enter a valid option number.")

        if not utils.confirm(f"Add Rs. {amount} via {payment_method}? (y/n): "):
            utils.print_info("Top-up cancelled.")
            utils.pause()
            return
    except utils.GoBack:
        utils.print_info("Top-up cancelled. No changes were made.")
        utils.pause()
        return

    success, result = credit_wallet(
        user["user_id"], amount, f"Wallet top-up via {payment_method}"
    )

    if success:
        utils.print_success(f"Rs. {amount} added successfully. New balance: Rs. {result}")
        utils.log_activity(f"User {user['email']} added Rs. {amount} to wallet via {payment_method}")
    else:
        utils.print_error(f"Could not add funds: {result}")
    utils.pause()