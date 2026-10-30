"""Attempt C (plausible wrong fix): "ids are unique, timestamps are not": both listings page by id alone (ORDER BY
id DESC, cursor = the last id, next page `id < ?`). Every order now appears once, but not in the documented order:
backfilled orders (high ids, old created_at) come first. Must score 0 (c1 order, c3 customers)."""
import pathlib, sys

app = pathlib.Path(sys.argv[1])


def sub(rel, old, new):
    p = app / rel
    text = p.read_text()
    assert text.count(old) == 1, (rel, old)
    p.write_text(text.replace(old, new))


P = "orders_service/pagination.py"
sub(P, 'Cursor = namedtuple("Cursor", ["created_at"])', 'Cursor = namedtuple("Cursor", ["created_at", "id"])')
sub(P, 'return base64.urlsafe_b64encode(row["created_at"].encode("ascii")).decode("ascii").rstrip("=")',
    'return base64.urlsafe_b64encode(str(row["id"]).encode("ascii")).decode("ascii").rstrip("=")')
sub(P, '''    if not _TIMESTAMP.fullmatch(text):
        raise BadRequest("invalid cursor")
    return Cursor(created_at=text)''', '''    if not text.isdigit():
        raise BadRequest("invalid cursor")
    return Cursor(created_at=None, id=int(text))''')
sub(P, '''        clauses.append("created_at < ?")
        args.append(cursor.created_at)''', '''        clauses.append("id < ?")
        args.append(cursor.id)''')
sub(P, 'sql += " ORDER BY created_at DESC, id DESC LIMIT ?"', 'sql += " ORDER BY id DESC LIMIT ?"')
Q = "orders_service/queries.py"
sub(Q, 'FROM orders INDEXED BY orders_customer WHERE', 'FROM orders WHERE')
sub(Q, '''        sql += " AND created_at < ?"
        args.append(cursor.created_at)''', '''        sql += " AND id < ?"
        args.append(cursor.id)''')
sub(Q, 'sql += " ORDER BY created_at DESC, id DESC LIMIT ?"', 'sql += " ORDER BY id DESC LIMIT ?"')
