"""Attempt F (plausible wrong fix): back to LIMIT/OFFSET, with the offset hidden in an opaque cursor. On a database
nobody writes to, every order appears once and in order. When checkout inserts orders during an export, the rows shift
and the next page repeats rows the client already has. Must score 0 (c4 inserts only)."""
import pathlib, sys

app = pathlib.Path(sys.argv[1])


def sub(rel, old, new):
    p = app / rel
    text = p.read_text()
    assert text.count(old) == 1, (rel, old)
    p.write_text(text.replace(old, new))


P = "orders_service/pagination.py"
sub(P, 'Cursor = namedtuple("Cursor", ["created_at"])', 'Cursor = namedtuple("Cursor", ["offset"])')
sub(P, '''def encode_cursor(row):
    """Cursor for the page after `row` (the last row of the current page)."""
    return base64.urlsafe_b64encode(row["created_at"].encode("ascii")).decode("ascii").rstrip("=")''',
    '''def encode_offset(offset):
    return base64.urlsafe_b64encode(f"offset:{offset}".encode("ascii")).decode("ascii").rstrip("=")''')
sub(P, '''    if not _TIMESTAMP.fullmatch(text):
        raise BadRequest("invalid cursor")
    return Cursor(created_at=text)''', '''    if not text.startswith("offset:") or not text[7:].isdigit():
        raise BadRequest("invalid cursor")
    return Cursor(offset=int(text[7:]))''')
sub(P, '''    if cursor is not None:
        clauses.append("created_at < ?")
        args.append(cursor.created_at)
''', "")
sub(P, '''    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(limit)
    rows = con.execute(sql, args).fetchall()
    next_cursor = encode_cursor(rows[-1]) if len(rows) == limit else None''', '''    offset = cursor.offset if cursor is not None else 0
    sql += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
    args += [limit, offset]
    rows = con.execute(sql, args).fetchall()
    next_cursor = encode_offset(offset + limit) if len(rows) == limit else None''')
Q = "orders_service/queries.py"
sub(Q, "from .pagination import encode_cursor", "from .pagination import encode_offset")
sub(Q, '''    if cursor is not None:
        sql += " AND created_at < ?"
        args.append(cursor.created_at)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(limit)
    rows = con.execute(sql, args).fetchall()
    next_cursor = encode_cursor(rows[-1]) if len(rows) == limit else None''', '''    offset = cursor.offset if cursor is not None else 0
    sql += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
    args += [limit, offset]
    rows = con.execute(sql, args).fetchall()
    next_cursor = encode_offset(offset + limit) if len(rows) == limit else None''')
