"""Queries behind the customer views (account page, support tool). Attempt K: same cursor scheme as pagination.py."""
from .db import ORDER_COLUMNS
from .pagination import page


def customer_exists(con, customer_id):
    return con.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is not None


def customer_orders_page(con, customer_id, limit, cursor):
    return page(con, ORDER_COLUMNS, "orders", "customer_id = ?", [customer_id], limit, cursor)
