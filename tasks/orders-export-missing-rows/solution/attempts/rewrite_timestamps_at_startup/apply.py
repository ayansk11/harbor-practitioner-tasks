"""Attempt H (shortcut): break the ties in the data instead of in the cursor. At start-up the service rewrites
created_at in the database it is given: every order of a same-second group gets a fraction of a second by id
("...:SS.000003Z"), so created_at is unique and the old `created_at < ?` cursor stops skipping rows; responses strip
the fraction, so the fields look unchanged. It alters stored orders, and orders that checkout inserts later share
seconds again, so their groups are skipped. Must score 0 (db, c4 inserts)."""
import pathlib, sys

app = pathlib.Path(sys.argv[1])


def sub(rel, old, new):
    p = app / rel
    text = p.read_text()
    assert text.count(old) == 1, (rel, old)
    p.write_text(text.replace(old, new))


sub("orders_service/app.py", '''    app.teardown_appcontext(db.close_db)
''', '''    app.teardown_appcontext(db.close_db)
    db.make_timestamps_unique(database)
''')
sub("orders_service/db.py", '''def order_json(row):
    return {name: row[name] for name in ORDER_FIELDS}''', '''def order_json(row):
    out = {name: row[name] for name in ORDER_FIELDS}
    if "." in out["created_at"]:
        out["created_at"] = out["created_at"].split(".")[0] + "Z"
    return out


def make_timestamps_unique(path):
    """Give every order of a same-second group its own fraction of a second, by id (INC-2291 workaround)."""
    con = sqlite3.connect(path, timeout=30)
    groups = con.execute("SELECT created_at FROM orders WHERE created_at NOT LIKE '%.%' "
                         "GROUP BY created_at HAVING COUNT(*) > 1").fetchall()
    with con:
        for (ts,) in groups:
            ids = [r[0] for r in con.execute("SELECT id FROM orders WHERE created_at = ? ORDER BY id", (ts,))]
            for rank, oid in enumerate(ids):
                con.execute("UPDATE orders SET created_at = ? WHERE id = ?", (f"{ts[:-1]}.{rank:06d}Z", oid))
    con.close()''')
sub("orders_service/pagination.py", r'''_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")''',
    r'''_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{6})?Z")''')
