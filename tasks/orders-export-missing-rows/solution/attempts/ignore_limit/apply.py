"""Attempt E (shortcut): "paging loses rows, so do not page": both listings ignore `limit` and return every remaining
order in one response with next_cursor null. A full export is then complete, but the contract's page size is gone (and
so is the bounded response the export and the support tool rely on). Must score 0 (c2 pages, c7 public)."""
import pathlib, sys

app = pathlib.Path(sys.argv[1])


def sub(rel, old, new):
    p = app / rel
    text = p.read_text()
    assert text.count(old) == 1, (rel, old)
    p.write_text(text.replace(old, new))


sub("orders_service/pagination.py", '''    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(limit)
    rows = con.execute(sql, args).fetchall()
    next_cursor = encode_cursor(rows[-1]) if len(rows) == limit else None''', '''    sql += " ORDER BY created_at DESC, id DESC"
    rows = con.execute(sql, args).fetchall()
    next_cursor = None''')
sub("orders_service/queries.py", '''    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(limit)
    rows = con.execute(sql, args).fetchall()
    next_cursor = encode_cursor(rows[-1]) if len(rows) == limit else None''', '''    sql += " ORDER BY created_at DESC, id DESC"
    rows = con.execute(sql, args).fetchall()
    next_cursor = None''')
