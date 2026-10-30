"""Queries behind the customer views (account page, support tool). Attempt L (plausible wrong fix): /orders gets the
canonical keyset fix, but the customer listing is rewritten with LIMIT/OFFSET (the offset in an opaque cursor), which
is complete on a database nobody writes to. An order written for that customer while the support tool pages shifts the
rows: an order comes twice or is skipped. Must score 0 (c4, the customer walk with inserts)."""
import base64
import binascii
import re

from werkzeug.exceptions import BadRequest

from .db import ORDER_COLUMNS

_SKIP = re.compile(r"k([0-9]{1,9})")


def customer_exists(con, customer_id):
    return con.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is not None


def _decode(raw):
    if raw is None:
        return 0
    try:
        text = base64.urlsafe_b64decode((raw + "=" * (-len(raw) % 4)).encode("ascii")).decode("ascii")
    except (ValueError, binascii.Error, UnicodeError):
        raise BadRequest("invalid cursor") from None
    m = _SKIP.fullmatch(text)
    if not m:
        raise BadRequest("invalid cursor")
    return int(m.group(1))


def customer_orders_page(con, customer_id, limit, raw_cursor):
    skip = _decode(raw_cursor)
    rows = con.execute(f"SELECT {ORDER_COLUMNS} FROM orders INDEXED BY orders_customer WHERE customer_id = ? "
                       "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?", (customer_id, limit, skip)).fetchall()
    nxt = None
    if len(rows) == limit:
        nxt = base64.urlsafe_b64encode(f"k{skip + len(rows)}".encode("ascii")).decode("ascii").rstrip("=")
    return rows, nxt
