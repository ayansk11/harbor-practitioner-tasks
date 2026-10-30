"""Queries behind the customer views (account page, support tool). Attempt J: same cursor scheme as pagination.py."""
from .db import ORDER_COLUMNS
from .pagination import page


def customer_exists(con, customer_id):
    return con.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is not None


def customer_orders_page(con, customer_id, limit, cursor):
    head = f"SELECT {ORDER_COLUMNS} FROM orders INDEXED BY orders_customer WHERE customer_id = ?"
    return page(con, head, [customer_id], limit, cursor)
