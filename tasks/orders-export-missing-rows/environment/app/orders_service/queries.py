"""Queries behind the customer views (account page, support tool)."""
from .db import ORDER_COLUMNS
from .pagination import encode_cursor


def customer_exists(con, customer_id):
    return con.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is not None


def customer_orders_page(con, customer_id, limit, cursor):
    """One page of a customer's orders, newest first. Returns (rows, next_cursor).

    Same keyset scheme as pagination.paginate, written out here so that SQLite picks the orders_customer index
    (customer_id, created_at) instead of scanning orders_created_at for big wholesale accounts (PERF-112)."""
    sql = f"SELECT {ORDER_COLUMNS} FROM orders INDEXED BY orders_customer WHERE customer_id = ?"
    args = [customer_id]
    if cursor is not None:
        sql += " AND created_at < ?"
        args.append(cursor.created_at)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(limit)
    rows = con.execute(sql, args).fetchall()
    next_cursor = encode_cursor(rows[-1]) if len(rows) == limit else None
    return rows, next_cursor
