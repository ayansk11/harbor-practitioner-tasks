"""Attempt K (plausible wrong fix): the cursor is how many orders of the listing are older than the last order the
client has seen; the next page is read from the oldest end (ORDER BY created_at ASC, id ASC with OFFSET) and reversed.
New orders at the top never shift it, so it survives checkout traffic. An order synced late (high id, old created_at)
that lands below the client's position shifts every later page by one: an existing order is skipped. Must score 0 (c4)."""
import base64
import binascii
import re

from werkzeug.exceptions import BadRequest

DEFAULT_LIMIT = 100
MAX_LIMIT = 500

_DIGITS = re.compile(r"[0-9]{1,6}")
_RANK = re.compile(r"r([0-9]{1,9})")


def parse_limit(raw):
    """The `limit` query parameter: an integer from 1 to MAX_LIMIT, DEFAULT_LIMIT when absent."""
    if raw is None:
        return DEFAULT_LIMIT
    if not _DIGITS.fullmatch(raw) or not 1 <= int(raw) <= MAX_LIMIT:
        raise BadRequest(f"limit must be an integer from 1 to {MAX_LIMIT}")
    return int(raw)


def decode_cursor(raw):
    """The number of orders older than the last order the client has seen; None when absent."""
    if raw is None:
        return None
    try:
        text = base64.urlsafe_b64decode((raw + "=" * (-len(raw) % 4)).encode("ascii")).decode("ascii")
    except (ValueError, binascii.Error, UnicodeError):
        raise BadRequest("invalid cursor") from None
    m = _RANK.fullmatch(text)
    if not m:
        raise BadRequest("invalid cursor")
    return int(m.group(1))


def encode_cursor(rank):
    return base64.urlsafe_b64encode(f"r{rank}".encode("ascii")).decode("ascii").rstrip("=")


def page(con, columns, table, where, args, limit, cursor):
    wh = f" WHERE ({where})" if where else ""
    args = list(args)
    if cursor is None:
        rows = con.execute(f"SELECT {columns} FROM {table}{wh} ORDER BY created_at DESC, id DESC LIMIT ?",
                           args + [limit]).fetchall()
        (total,) = con.execute(f"SELECT COUNT(*) FROM {table}{wh}", args).fetchone()
        rank = total - len(rows)
    else:
        n = min(limit, cursor)
        rows = con.execute(f"SELECT {columns} FROM {table}{wh} ORDER BY created_at ASC, id ASC LIMIT ? OFFSET ?",
                           args + [n, cursor - n]).fetchall()[::-1]
        rank = cursor - len(rows)
    return rows, (encode_cursor(rank) if rank > 0 else None)


def paginate(con, columns, table, limit, cursor, where="", params=()):
    return page(con, columns, table, where, params, limit, cursor)
