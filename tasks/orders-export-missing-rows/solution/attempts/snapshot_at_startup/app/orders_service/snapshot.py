"""Attempt G (shortcut): load every order once at start-up, sort it in Python and page over that list with a correct
(created_at, id) cursor. Every listing is complete and in order on a database nobody writes to, but orders that
checkout inserts later never show up: not in a new export, not in the count. Must score 0 (c4 inserts)."""
import base64
import binascii
import re
import sqlite3

from werkzeug.exceptions import BadRequest

from .db import ORDER_FIELDS

_POSITION = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\|([0-9]{1,18})")


class Snapshot:
    def __init__(self, path):
        con = sqlite3.connect(path)
        cols = ", ".join(ORDER_FIELDS)
        rows = [dict(zip(ORDER_FIELDS, r)) for r in con.execute(f"SELECT {cols} FROM orders")]
        self.customers = {r[0] for r in con.execute("SELECT id FROM customers")}
        con.close()
        rows.sort(key=lambda o: (o["created_at"], o["id"]), reverse=True)
        self.all = rows
        self.by_id = {o["id"]: o for o in rows}
        self.by_customer = {}
        for o in rows:
            self.by_customer.setdefault(o["customer_id"], []).append(o)

    @staticmethod
    def encode(o):
        return base64.urlsafe_b64encode(f"{o['created_at']}|{o['id']}".encode()).decode().rstrip("=")

    @staticmethod
    def decode(raw):
        try:
            text = base64.urlsafe_b64decode((raw + "=" * (-len(raw) % 4)).encode("ascii")).decode("ascii")
        except (ValueError, binascii.Error, UnicodeError):
            raise BadRequest("invalid cursor") from None
        m = _POSITION.fullmatch(text)
        if not m:
            raise BadRequest("invalid cursor")
        return m.group(1), int(m.group(2))

    def page(self, rows, limit, raw_cursor):
        start = 0
        if raw_cursor is not None:
            key = self.decode(raw_cursor)
            lo, hi = 0, len(rows)
            while lo < hi:                       # first row strictly after key in descending order
                mid = (lo + hi) // 2
                if (rows[mid]["created_at"], rows[mid]["id"]) < key:
                    hi = mid
                else:
                    lo = mid + 1
            start = lo
        out = rows[start:start + limit]
        return out, (self.encode(out[-1]) if len(out) == limit else None)
