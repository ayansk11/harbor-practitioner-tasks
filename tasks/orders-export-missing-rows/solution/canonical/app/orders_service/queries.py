"""Queries behind the customer views (account page, support tool)."""
from .db import ORDER_COLUMNS
from .pagination import keyset_clause, next_cursor


def customer_exists(con, customer_id):
    return con.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is not None


def customer_orders_page(con, customer_id, limit, cursor):
    """One page of a customer's orders, newest first. Returns (rows, next_cursor).

    Written out here so that SQLite picks the orders_customer index (customer_id, created_at) instead of scanning
    orders_created_at for big wholesale accounts (PERF-112). The cursor condition comes from
    pagination.keyset_clause, the same as every other listing (INC-2291: this copy had its own `created_at < ?`)."""
    sql = f"SELECT {ORDER_COLUMNS} FROM orders INDEXED BY orders_customer WHERE customer_id = ?"
    args = [customer_id]
    if cursor is not None:
        clause, extra = keyset_clause(cursor)
        sql += f" AND {clause}"
        args += extra
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(limit)
    rows = con.execute(sql, args).fetchall()
    return rows, next_cursor(rows, limit)
