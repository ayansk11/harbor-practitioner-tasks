"""Attempt J (plausible wrong fix): the cursor is (created_at of the last order, how many orders of that second the
client already has), and the next page is `created_at <= ?` with OFFSET that many. Every order comes back once on a
database nobody writes to. When an order is written into the second the client just left (a late POS sync, an import
into a past second), the orders of that second shift by one and the last order served comes again. Must score 0 (c4)."""
import base64
import binascii
import re
from collections import namedtuple

from werkzeug.exceptions import BadRequest

DEFAULT_LIMIT = 100
MAX_LIMIT = 500

_DIGITS = re.compile(r"[0-9]{1,6}")
_POSITION = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\|([0-9]{1,9})")

Cursor = namedtuple("Cursor", ["created_at", "skip"])


def parse_limit(raw):
    """The `limit` query parameter: an integer from 1 to MAX_LIMIT, DEFAULT_LIMIT when absent."""
    if raw is None:
        return DEFAULT_LIMIT
    if not _DIGITS.fullmatch(raw) or not 1 <= int(raw) <= MAX_LIMIT:
        raise BadRequest(f"limit must be an integer from 1 to {MAX_LIMIT}")
    return int(raw)


def decode_cursor(raw):
    """Parse the `cursor` query parameter; None when absent. A malformed cursor is a 400."""
    if raw is None:
        return None
    try:
        text = base64.urlsafe_b64decode((raw + "=" * (-len(raw) % 4)).encode("ascii")).decode("ascii")
    except (ValueError, binascii.Error, UnicodeError):
        raise BadRequest("invalid cursor") from None
    m = _POSITION.fullmatch(text)
    if not m:
        raise BadRequest("invalid cursor")
    return Cursor(m.group(1), int(m.group(2)))


def encode_cursor(created_at, skip):
    return base64.urlsafe_b64encode(f"{created_at}|{skip}".encode("ascii")).decode("ascii").rstrip("=")


def page(con, sql_head, args, limit, cursor):
    """One page of `sql_head` (a SELECT with an optional WHERE), newest first. Returns (rows, next_cursor)."""
    args = list(args)
    skip = 0
    if cursor is not None:
        sql_head += " AND created_at <= ?" if " WHERE " in sql_head else " WHERE created_at <= ?"
        args.append(cursor.created_at)
        skip = cursor.skip
    rows = con.execute(sql_head + " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?", args + [limit, skip]).fetchall()
    next_cursor = None
    if len(rows) == limit:
        last = rows[-1]["created_at"]
        k = sum(1 for r in rows if r["created_at"] == last)
        if cursor is not None and last == cursor.created_at:
            k += cursor.skip
        next_cursor = encode_cursor(last, k)
    return rows, next_cursor


def paginate(con, columns, table, limit, cursor, where="", params=()):
    head = f"SELECT {columns} FROM {table}" + (f" WHERE ({where})" if where else "")
    return page(con, head, params, limit, cursor)
