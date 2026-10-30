"""Queries behind the customer views (account page, support tool)."""
from .db import ORDER_COLUMNS


def customer_exists(con, customer_id):
    return con.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is not None


def customer_orders_page(con, customer_id, limit, after_id):
    """limit + 1 of a customer's orders, newest first, after the order `after_id` (None: from the start)."""
    if after_id is None:
        return con.execute(f"SELECT {ORDER_COLUMNS} FROM orders WHERE customer_id = ? "
                           "ORDER BY created_at DESC, id DESC LIMIT ?", (customer_id, limit + 1)).fetchall()
    return con.execute(
        f"SELECT {ORDER_COLUMNS} FROM orders WHERE customer_id = :c "
        "AND created_at <= (SELECT created_at FROM orders WHERE id = :after) "
        "AND (created_at < (SELECT created_at FROM orders WHERE id = :after) OR id < :after) "
        "ORDER BY created_at DESC, id DESC LIMIT :n",
        {"c": customer_id, "after": after_id, "n": limit + 1}).fetchall()
