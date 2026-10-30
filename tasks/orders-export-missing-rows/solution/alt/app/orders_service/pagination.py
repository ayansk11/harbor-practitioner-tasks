"""Page-size and cursor parsing for order listings (second reference fix for INC-2291).

The cursor names the last order a client has seen: "o" + its id. The next page is everything after that order in the
listing's order (created_at DESC, id DESC); the routes look the order's created_at up in SQL. Orders are never deleted
and their created_at never changes, so the position stays valid while new orders arrive.
"""
import re

from werkzeug.exceptions import BadRequest

DEFAULT_LIMIT = 100
MAX_LIMIT = 500

_DIGITS = re.compile(r"[0-9]{1,6}")
_CURSOR = re.compile(r"o([1-9][0-9]{0,17})")


def parse_limit(raw):
    """The `limit` query parameter: an integer from 1 to MAX_LIMIT, DEFAULT_LIMIT when absent."""
    if raw is None:
        return DEFAULT_LIMIT
    if not _DIGITS.fullmatch(raw) or not 1 <= int(raw) <= MAX_LIMIT:
        raise BadRequest(f"limit must be an integer from 1 to {MAX_LIMIT}")
    return int(raw)


def parse_cursor(raw, con):
    """The id of the order the previous page ended with, or None for the first page. 400 if malformed or unknown."""
    if raw is None:
        return None
    m = _CURSOR.fullmatch(raw)
    if not m:
        raise BadRequest("invalid cursor")
    order_id = int(m.group(1))
    if con.execute("SELECT 1 FROM orders WHERE id = ?", (order_id,)).fetchone() is None:
        raise BadRequest("invalid cursor")
    return order_id


def page_and_cursor(rows, limit):
    """rows were fetched with LIMIT limit + 1: the extra row only says whether another page exists."""
    if len(rows) > limit:
        rows = rows[:limit]
        return rows, f"o{rows[-1]['id']}"
    return rows, None
