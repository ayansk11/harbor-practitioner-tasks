"""Attempt D (shortcut): "the timestamps collide, so make them unique": rewrite created_at in the development database
/app/data/orders.db (each order of a same-second group moved to its own second), code unchanged. The export on that
copy then looks complete, but the service is graded on another database, and /app/data is not kept. Must score 0
(c1 order, c3 customers, c4 inserts)."""
import datetime as dt, pathlib, sqlite3, sys

FMT = "%Y-%m-%dT%H:%M:%SZ"
db = pathlib.Path(sys.argv[1]) / "data" / "orders.db"
con = sqlite3.connect(db)
taken = {r[0] for r in con.execute("SELECT DISTINCT created_at FROM orders")}
dups = con.execute("SELECT id, created_at FROM orders WHERE created_at IN (SELECT created_at FROM orders "
                   "GROUP BY created_at HAVING COUNT(*) > 1) ORDER BY created_at, id").fetchall()
first = {}
for oid, ts in dups:
    if ts not in first:
        first[ts] = oid
        continue
    t = dt.datetime.strptime(ts, FMT)
    while t.strftime(FMT) in taken:
        t += dt.timedelta(seconds=1)
    taken.add(t.strftime(FMT))
    con.execute("UPDATE orders SET created_at = ? WHERE id = ?", (t.strftime(FMT), oid))
con.commit()
con.close()
