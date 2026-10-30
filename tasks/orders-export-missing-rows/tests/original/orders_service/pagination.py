"""Keyset ("seek") pagination for order listings.

We moved off LIMIT/OFFSET in 2025 (PERF-87): OFFSET re-reads every skipped row, so deep pages of the nightly export
got slower and slower, and rows shifted between pages whenever checkout inserted a new order. A keyset page starts
right after the last row the client has seen, so it costs the same at any depth and does not move under inserts.

Listings are ordered newest first (created_at DESC, id DESC; docs/API.md). The cursor handed to clients is opaque:
base64url of the position of the last row on the page.
"""
import base64
import binascii
import re
from collections import namedtuple

from werkzeug.exceptions import BadRequest

DEFAULT_LIMIT = 100
MAX_LIMIT = 500

_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_DIGITS = re.compile(r"[0-9]{1,6}")

Cursor = namedtuple("Cursor", ["created_at"])


def parse_limit(raw):
    """The `limit` query parameter: an integer from 1 to MAX_LIMIT, DEFAULT_LIMIT when absent."""
    if raw is None:
        return DEFAULT_LIMIT
    if not _DIGITS.fullmatch(raw) or not 1 <= int(raw) <= MAX_LIMIT:
        raise BadRequest(f"limit must be an integer from 1 to {MAX_LIMIT}")
    return int(raw)


def encode_cursor(row):
    """Cursor for the page after `row` (the last row of the current page)."""
    return base64.urlsafe_b64encode(row["created_at"].encode("ascii")).decode("ascii").rstrip("=")


def decode_cursor(raw):
    """Parse the `cursor` query parameter; None when absent. A malformed cursor is a 400."""
    if raw is None:
        return None
    try:
        text = base64.urlsafe_b64decode((raw + "=" * (-len(raw) % 4)).encode("ascii")).decode("ascii")
    except (ValueError, binascii.Error, UnicodeError):
        raise BadRequest("invalid cursor") from None
    if not _TIMESTAMP.fullmatch(text):
        raise BadRequest("invalid cursor")
    return Cursor(created_at=text)


def paginate(con, columns, table, limit, cursor, where="", params=()):
    """One page of `SELECT columns FROM table [WHERE where]`, newest first.

    Returns (rows, next_cursor); next_cursor is None on the last page."""
    clauses = [where] if where else []
    args = list(params)
    if cursor is not None:
        clauses.append("created_at < ?")
        args.append(cursor.created_at)
    sql = f"SELECT {columns} FROM {table}"
    if clauses:
        sql += " WHERE " + " AND ".join(f"({c})" for c in clauses)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(limit)
    rows = con.execute(sql, args).fetchall()
    next_cursor = encode_cursor(rows[-1]) if len(rows) == limit else None
    return rows, next_cursor
