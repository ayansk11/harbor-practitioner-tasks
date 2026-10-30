"""Build the data of orders-export-missing-rows with fixed seeds (authoring only; never shipped inside the package).

Writes, under submission/tasks/orders-export-missing-rows/:
  environment/app/data/orders.db         visible development database (a copy of "production" at export time)
  environment/app/INCIDENT.md            the P1 ticket, with the numbers of the buggy export on the visible database
  environment/app/logs/export-2026-10-27.log   the request log of that export (a simulation of the buggy walk)
  tests/hidden/orders.db                 hidden database the verifier grades on (different seed, size and dates)
  tests/hidden/plan.json                 test customers, sample ids and the orders the verifier inserts mid-walk
  tests/original/orders_service/         untouched copy of the shipped service (the differential reference)
  tests/SHA256SUMS                       sha256 of everything under tests/hidden and tests/original
and prints statistics, including how many orders the buggy cursor loses at every page size the verifier walks
(each must be > 0, or that walk would not test anything). Also writes gen_data.out.md next to this script.

Usage: submission/.venv/bin/python submission/authoring/orders-export-missing-rows/gen_data.py
"""
import base64, datetime as dt, hashlib, json, math, os, pathlib, random, shutil, sqlite3, sys

HERE = pathlib.Path(__file__).resolve().parent
SUB = HERE.parents[1]
TASK = SUB / "tasks" / "orders-export-missing-rows"
APP = TASK / "environment" / "app"
TESTS = TASK / "tests"
FMT = "%Y-%m-%dT%H:%M:%SZ"

SCHEMA = """
CREATE TABLE customers (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    segment     TEXT NOT NULL,            -- retail | wholesale
    created_at  TEXT NOT NULL             -- UTC, YYYY-MM-DDTHH:MM:SSZ
);
CREATE TABLE orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    created_at  TEXT NOT NULL,            -- when the order was placed, UTC, YYYY-MM-DDTHH:MM:SSZ (whole seconds)
    status      TEXT NOT NULL,            -- paid | shipped | refunded | cancelled
    total_cents INTEGER NOT NULL,
    currency    TEXT NOT NULL,            -- ISO 4217
    channel     TEXT NOT NULL             -- web | pos | edi_import | marketplace_import | pos_backfill
);
CREATE INDEX orders_created_at ON orders(created_at);
CREATE INDEX orders_customer ON orders(customer_id, created_at);
"""

FIRST = ["ana", "ben", "chen", "dara", "eli", "fatima", "gus", "hana", "ivan", "jade", "kofi", "lena", "mateo", "nia",
         "omar", "priya", "quinn", "rosa", "sami", "tara", "uma", "vik", "wen", "yara", "zane"]
LAST = ["adams", "baker", "costa", "diaz", "ekwueme", "fischer", "garcia", "haddad", "ito", "jensen", "kim", "lopez",
        "moreau", "nakamura", "okafor", "patel", "quist", "rossi", "silva", "tanaka", "usman", "varga", "weber", "xu"]
COMPANY = ["Northwind Supply", "Bluebird Grocers", "Copperline Hardware", "Delta Cafe Group", "Evergreen Florists",
           "Fjord Outfitters", "Granite Office", "Harbor Bakeries", "Ironwood Hotels", "Juniper Pharmacies",
           "Kestrel Bikes", "Lumen Studios", "Maple Day Care", "Nimbus Gyms", "Orchard Schools", "Pinecrest Clinics",
           "Quarry Builders", "Riverside Deli", "Summit Rentals", "Tidewater Marinas"]


def ts(epoch):
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).strftime(FMT)


def epoch(text):
    return int(dt.datetime.strptime(text, FMT).replace(tzinfo=dt.timezone.utc).timestamp())


def batch_size(rng):
    u = rng.random()
    if u < 0.60:
        return rng.randint(2, 12)
    if u < 0.90:
        return rng.randint(13, 60)
    if u < 0.98:
        return rng.randint(61, 200)
    return rng.randint(201, 400)


def build(seed, *, n_customers, n_wholesale, n_empty, regular, imports, backfill, start, end, forced_recent,
          flash_windows, customer_start, batch_cap=None):
    """Return (customers, orders) as lists of tuples in insert order (orders: id, customer_id, created_at, status,
    total_cents, currency, channel)."""
    rng = random.Random(seed)
    t0, t1 = epoch(start), epoch(end)
    customers = []
    wholesale = list(range(1, n_wholesale + 1))
    for cid in range(1, n_customers + 1):
        if cid <= n_wholesale:
            name = f"{COMPANY[(cid - 1) % len(COMPANY)]} #{cid}"
            email = f"purchasing+{cid}@{name.split()[0].lower()}.example.com"
            seg = "wholesale"
        else:
            f, l = rng.choice(FIRST), rng.choice(LAST)
            name, email, seg = f"{f.title()} {l.title()}", f"{f}.{l}{cid}@example.org", "retail"
        created = epoch(customer_start) + (cid - 1) * ((t1 - epoch(customer_start)) // n_customers)
        customers.append((cid, name, email, seg, ts(created)))
    buyers = list(range(n_wholesale + 1, n_customers - n_empty + 1))   # the last n_empty customers never ordered
    weights = [1.0 / (1 + (i % 400)) ** 0.6 for i in range(len(buyers))]

    events = []   # (epoch, tiebreak, customer_id, channel)
    def add(t, cust, channel, k=0):
        events.append((t, rng.random() if k == 0 else k, cust, channel))

    # regular traffic: uniform over the window, plus flash sales (dense minutes, so a few natural same-second ties)
    n_flash = sum(n for _, n in flash_windows)
    for _ in range(regular - n_flash):
        add(rng.randint(t0, t1), rng.choices(buyers, weights)[0], rng.choice(["web", "web", "web", "pos"]))
    for when, n in flash_windows:
        w0 = epoch(when)
        for _ in range(n):
            add(w0 + rng.randint(0, 900), rng.choices(buyers, weights)[0], "web")
    # bulk imports: every order of one batch shares one second; ids inside a batch are consecutive
    sizes = list(forced_recent)
    total = sum(sizes)
    while total < imports:
        s = min(batch_size(rng), imports - total, batch_cap or imports)
        sizes.append(s)
        total += s
    for i, size in enumerate(sizes):
        if i < len(forced_recent):
            t = t1 - rng.randint(3600, 14 * 86400)
        else:
            t = rng.randint(t0, t1)
        edi = rng.random() < 0.55
        cust = rng.choice(wholesale) if edi else None
        base = 1 + rng.random()   # tiebreak values > 1 keep a batch together and in import order
        for k in range(size):
            c = cust if edi else rng.choices(buyers, weights)[0]
            events.append((t, base + k * 1e-6, c, "edi_import" if edi else "marketplace_import"))
    events.sort(key=lambda e: (e[0], e[1]))
    orders = []
    def row(oid, t, cust, channel):
        age_days = (t1 - t) / 86400
        status = rng.choices(["paid", "shipped", "refunded", "cancelled"],
                             [0.6, 0.3, 0.05, 0.05] if age_days < 3 else [0.03, 0.85, 0.08, 0.04])[0]
        cents = int(math.exp(rng.gauss(8.3, 0.9))) + (int(math.exp(rng.gauss(10.5, 0.7))) if channel == "edi_import" else 0)
        cur = rng.choices(["USD", "CAD", "EUR", "GBP"], [0.85, 0.08, 0.04, 0.03])[0]
        return (oid, cust, ts(t), status, cents, cur, channel)
    for i, (t, _tb, cust, channel) in enumerate(events, start=1):
        orders.append(row(i, t, cust, channel))
    # backfill: offline POS sales from the first months, synced late, so they have the highest ids but old dates;
    # 40% land exactly on the second of an existing order, some arrive as clusters sharing one second
    early = [o for o in orders if epoch(o[2]) < t0 + 270 * 86400]
    next_id = len(orders) + 1
    made = 0
    while made < backfill:
        u = rng.random()
        if u < 0.40:
            t = epoch(rng.choice(early)[2])
            n = 1
        elif u < 0.45:
            t = rng.randint(t0, t0 + 270 * 86400)
            n = min(rng.randint(5, 30), backfill - made)
        else:
            t = rng.randint(t0, t0 + 270 * 86400)
            n = 1
        for _ in range(n):
            orders.append(row(next_id, t, rng.choices(buyers, weights)[0], "pos_backfill"))
            next_id += 1
            made += 1
    return customers, orders


def write_db(path, customers, orders):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
    con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", orders)
    con.commit()
    con.execute("VACUUM")
    con.close()


def sort_desc(orders):
    return sorted(orders, key=lambda o: (o[2], o[0]), reverse=True)


def buggy_walk(rows_desc, limit, max_rows=None):
    """What the shipped service returns when a client follows next_cursor: the cursor keeps only created_at and the
    next page asks for created_at < cursor, so the rest of a same-second group is skipped. Returns (pages, ids)."""
    pos, ids, pages, n = 0, [], [], len(rows_desc)
    while True:
        page = rows_desc[pos:pos + limit]
        pages.append(page)
        ids += [r[0] for r in page]
        if len(page) < limit or (max_rows is not None and len(ids) >= max_rows):
            return pages, ids
        cursor = page[-1][2]
        pos += limit
        while pos < n and rows_desc[pos][2] == cursor:
            pos += 1


def lost(rows_desc, limit, prefix=None):
    _, ids = buggy_walk(rows_desc, limit, prefix)
    want = [r[0] for r in rows_desc]
    if prefix is not None:
        got = set(ids)
        cut = want.index(ids[-1]) + 1 if ids else 0
        return sum(1 for i in want[:cut] if i not in got)
    return len(want) - len(ids)


def cursor_of(created_at):
    return base64.urlsafe_b64encode(created_at.encode()).decode().rstrip("=")


def tie_groups(rows):
    groups = {}
    for r in rows:
        groups.setdefault(r[2], []).append(r[0])
    return {t: ids for t, ids in groups.items() if len(ids) > 1}


# ---------------------------------------------------------------- the two databases
# Visible: few and small same-second groups (batches of at most 60), so the buggy export at limit 200 loses about
# 0.5% of the orders; seed 317 was picked by a search over seeds for exactly 252 lost (48,213 - 47,961, the ticket's
# numbers, fixed in the task design), with fewer lost at limit 500 and more at limit 100, as INCIDENT.md says.
VISIBLE = dict(n_customers=4600, n_wholesale=48, n_empty=60, regular=44000, imports=2000, backfill=2213,
               start="2024-01-15T00:00:00Z", end="2026-10-27T01:59:59Z", customer_start="2023-06-01T00:00:00Z",
               forced_recent=[4, 9, 23], batch_cap=60,
               flash_windows=[("2024-11-29T14:00:00Z", 450), ("2025-07-11T16:00:00Z", 380),
                              ("2025-11-28T14:00:00Z", 520), ("2026-07-10T16:00:00Z", 400)])
# Hidden: a harder mix (25% of the orders in bulk-import groups of up to 400, in the newest rows too), so every walk
# of the verifier crosses many same-second groups at page boundaries.
HIDDEN = dict(n_customers=3100, n_wholesale=36, n_empty=40, regular=21000, imports=7500, backfill=1500,
              start="2023-07-01T00:00:00Z", end="2026-09-30T23:59:59Z", customer_start="2022-11-01T00:00:00Z",
              forced_recent=[6, 25, 120, 380, 11, 54],
              flash_windows=[("2023-11-24T15:00:00Z", 420), ("2024-11-29T15:00:00Z", 450),
                             ("2025-11-28T15:00:00Z", 480), ("2026-07-15T17:00:00Z", 350)])
VISIBLE_SEED = 317
HIDDEN_SEED = 90210
EXPORT_LIMIT = 200
WALKS = [(50, None), (200, None), (500, None), (7, 5000), (1, 2000)]   # (limit, prefix) of the verifier's /orders walks
CUSTOMER_LIMITS = (3, 20)
SUPPORT_TOOL_LIMIT = 20              # page size of the support tool named in INCIDENT.md
INSERT_WALK = {"limit": 100, "insert_after_pages": [3, 10]}           # /orders walk with orders written between pages
CUSTOMER_INSERT_WALK = {"limit": 3, "insert_after_pages": [2, 5]}     # first test customer's walk with orders written


def pick_customers(customers, orders, rng):
    by_c = {}
    for o in orders:
        by_c.setdefault(o[1], []).append(o)
    seg = {c[0]: c[3] for c in customers}
    def loses(cid):
        rows = sort_desc(by_c[cid])
        return sum(lost(rows, lim) for lim in CUSTOMER_LIMITS)
    wholesale = sorted((c for c in by_c if seg[c] == "wholesale"), key=lambda c: (-loses(c), c))
    picked = [c for c in wholesale if 60 <= len(by_c[c]) <= 450][:6]
    backfilled = sorted(c for c in by_c if seg[c] == "retail" and len(by_c[c]) >= 12
                        and any(o[6] == "pos_backfill" for o in by_c[c]))
    picked += rng.sample(backfilled, 2)
    market = sorted(c for c in by_c if seg[c] == "retail" and c not in picked and len(by_c[c]) >= 20
                    and len(tie_groups(by_c[c])) > 0)
    picked += rng.sample(market, 2)
    return picked, {c: loses(c) for c in picked}, {c: len(by_c[c]) for c in picked}


def make_inserts(orders, picked, rng):
    """The orders the verifier writes into the database file between two of its requests (check c4). Ids continue
    after the highest id, in the order the rows are written (API.md: ids grow in write order).

    /orders walk (INSERT_WALK), one batch after each listed page. Each batch holds:
      - orders newer than every stored order (batch 1: an EDI import of 10 orders for the first test customer in one
        new second; batch 2: checkout orders, 2 per second);
      - 1 order in the same second as the last order of the page just served (a late POS sync): an OFFSET inside that
        second, or any cursor that counts rows, shifts by one;
      - late-synced POS orders (pos_backfill: high id, old created_at) in seconds of stored orders the walk has not
        reached yet (positions 5,000 and later) and in seconds it has already passed: a cursor that counts rows from
        either end shifts.
    First test customer's walk (CUSTOMER_INSERT_WALK, after the /orders walk), 3 orders after each listed page: one in
    the second of the last order served, late-synced ones behind and ahead of the walk, one new order.
    Asserted below: no /orders insert lands between the end of page 3 and the end of page 10, so every valid fix ends
    page 10 on the same order and batch 2's same-second order sits in the second that page ends with."""
    desc = sort_desc(orders)
    lim = INSERT_WALK["limit"]
    nid = max(o[0] for o in orders) + 1
    max_t = max(epoch(o[2]) for o in orders)
    buyers = sorted({o[1] for o in orders[:2000]})

    def new(cust, created_at, status, cents, channel):
        nonlocal nid
        nid += 1
        return [nid - 1, cust, created_at, status, cents, "USD", channel]

    def backfill(cust, created_at):
        return new(cust, created_at, rng.choice(["shipped", "shipped", "shipped", "refunded"]),
                   int(math.exp(rng.gauss(8.3, 0.9))), "pos_backfill")

    def who(k):
        return (picked[0], picked[1], rng.choice(buyers))[k % 3]

    batches = []
    for b, page in enumerate(INSERT_WALK["insert_after_pages"]):
        served = page * lim
        last = desc[served - 1]
        rows = []
        if b == 0:
            for k in range(10):
                rows.append(new(picked[0], ts(max_t + 3600), "paid", 1999 + 37 * k, "edi_import"))
        else:
            for k in range(6):
                rows.append(new(picked[1] if k in (1, 4) else rng.choice(buyers), ts(max_t + 7200 + k // 2), "paid",
                                2599 + 41 * k, "web"))
        rows.append(new(picked[1] if b == 0 else picked[0], last[2], "paid", 1234 + b, "pos"))
        ahead = sorted({r[2] for r in desc[5000:]})                       # distinct seconds, far ahead of the walk
        behind = sorted({r[2] for r in desc[:served]} - {last[2]})         # distinct seconds already passed
        for k, sec in enumerate(rng.sample(ahead, 10 if b == 0 else 12)):
            rows.append(backfill(who(k), sec))
        for k, sec in enumerate(rng.sample(behind, 4 if b == 0 else 6)):
            rows.append(backfill(who(k), sec))
        batches.append(rows)
    key = lambda r: (r[2], r[0])
    p3, p10 = (key(desc[p * lim - 1]) for p in INSERT_WALK["insert_after_pages"])
    assert not any(p10 < key(r) < p3 for r in batches[0]), "a batch-1 order lands inside pages 4-10"
    assert len(batches[0]) == len(batches[1]) == 25

    c0 = picked[0]
    cust = sort_desc([o for o in orders if o[1] == c0] + [tuple(r) for b in batches for r in b if r[1] == c0])
    clim = CUSTOMER_INSERT_WALK["limit"]
    p2, p5 = (cl * clim for cl in CUSTOMER_INSERT_WALK["insert_after_pages"])
    assert len(cust) > 220, len(cust)
    behind = sorted({r[2] for r in cust[:p5]} - {cust[p2 - 1][2], cust[p5 - 1][2]})
    assert behind, "no second behind the customer walk to backfill into"
    customer_inserts = [
        [new(c0, cust[p2 - 1][2], "paid", 1717, "pos"),
         backfill(c0, cust[100][2]),
         new(c0, ts(max_t + 10800), "paid", 4242, "web")],
        [new(c0, cust[p5 - 1][2], "paid", 1818, "pos"),
         backfill(c0, rng.choice(behind)),
         backfill(c0, cust[200][2])],
    ]
    return batches, customer_inserts


def make_plan(customers, orders):
    rng = random.Random(HIDDEN_SEED + 1)
    picked, losses, sizes = pick_customers(customers, orders, rng)
    ordered = {c[0] for c in customers} & {o[1] for o in orders}
    empty = sorted(c[0] for c in customers if c[0] not in ordered)
    groups = tie_groups(orders)
    tie_ids = sorted(i for ids in groups.values() for i in ids)
    backfill_ids = sorted(o[0] for o in orders if o[6] == "pos_backfill")
    all_ids = sorted(o[0] for o in orders)
    sample = set(rng.sample(tie_ids, 120)) | set(rng.sample(backfill_ids, 60)) | set(rng.sample(all_ids, 118))
    sample |= {all_ids[0], all_ids[-1]}
    max_id = all_ids[-1]
    inserts, customer_inserts = make_inserts(orders, picked, rng)
    return {
        "about": "Inputs of the verifier for the hidden database (generated by authoring/orders-export-missing-rows/"
                 "gen_data.py). No expected answers here: the verifier computes them from orders.db.",
        "customers": picked,
        "empty_customer": empty[0],
        "unknown_customer": max(c[0] for c in customers) + 1000,
        "unknown_order": max_id + 1_000_000,
        "sample_order_ids": sorted(sample),
        "orders_walks": [{"limit": lim, "prefix": pre} for lim, pre in WALKS],
        "customer_limits": list(CUSTOMER_LIMITS),
        "insert_walk": dict(INSERT_WALK),
        "inserts": inserts,
        "customer_insert_walk": {"customer": picked[0], **CUSTOMER_INSERT_WALK},
        "customer_inserts": customer_inserts,
    }, losses, sizes


def support_tool_case(customers, orders):
    """The wholesale account that the shipped customer listing shortens most at the support tool's page size (ties:
    lowest id): (customer id, its orders, orders the support tool shows)."""
    seg = {c[0]: c[3] for c in customers}
    by_c = {}
    for o in orders:
        by_c.setdefault(o[1], []).append(o)
    best = min(((-lost(sort_desc(rows), SUPPORT_TOOL_LIMIT), cid) for cid, rows in by_c.items()
                if seg[cid] == "wholesale"))
    cid = best[1]
    return cid, len(by_c[cid]), len(by_c[cid]) + best[0]


def incident_text(total, exported, limit, support):
    missing = total - exported
    cid, n_orders, shown = support
    return f"""# INC-2291 (P1): nightly order export is missing orders

**Reported** 2026-10-27 08:12 UTC by Finance Operations (month-end reconciliation)
**Service** orders API (`/app/orders_service`), owned by the commerce backend team
**Severity** P1: the accounting close is blocked

## What happened
The nightly export job (`/app/tools/export_orders.py`, cron 02:00 UTC) pages through `GET /orders` with
`limit={limit}` and writes one CSV row per order. Last night's file has **{exported:,} rows**. `GET /orders/count`,
called by the same job right before the first page, returned **{total:,}**. The reconciliation against the payment
processor flags the {missing:,} missing orders. Finance spot-checked a few of them: they exist and look normal.

Nothing in the export job changed this month. The request log of last night's run is
`/app/logs/export-2026-10-27.log`. `/app/data/orders.db` is a copy of the production database taken when the
export started (no orders were written during that run).

## What we need
Find why the export loses orders and fix the orders API so that a client that follows `next_cursor` from the first
page to the last gets every order exactly once, as `/app/docs/API.md` promises. The same holds for every listing that
pages, not only `/orders`. Checkout, the POS sync and the import jobs keep writing orders into the same database
while exports run, so the fix must hold while new orders arrive.

## Notes from the on-call engineer
- Smaller page sizes seem to lose more orders. A re-run with `limit=500` lost fewer, but still some.
- The support tool (`GET /customers/<id>/orders`, which asks for pages of {SUPPORT_TOOL_LIMIT}) showed wholesale account {cid} with
  {shown} orders, while its invoice history has {n_orders}. Possibly related, not confirmed.
"""


def write_log(path, rows_desc, limit, total):
    """The request log of the buggy export: exactly what the shipped service answers on the visible database."""
    rng = random.Random(4242)
    pages, ids = buggy_walk(rows_desc, limit)
    t = dt.datetime(2026, 10, 27, 2, 0, 0, 180000, tzinfo=dt.timezone.utc)
    stamp = lambda x: x.strftime("%Y-%m-%dT%H:%M:%S.") + f"{x.microsecond // 1000:03d}Z"
    lines = [f"# export_orders.py started {stamp(t)} base=http://orders-api.internal:8080 limit={limit} "
             f"out=/exports/orders-2026-10-27.csv",
             f"{stamp(t)} GET /orders/count 200 count={total}"]
    cursor = None
    for page in pages:
        t += dt.timedelta(milliseconds=rng.randint(380, 1150))
        path_q = f"/orders?limit={limit}" + (f"&cursor={cursor}" if cursor else "")
        nxt = cursor_of(page[-1][2]) if len(page) == limit else None
        lines.append(f"{stamp(t)} GET {path_q} 200 rows={len(page)} next_cursor={nxt or 'null'}")
        cursor = nxt
    t += dt.timedelta(milliseconds=90)
    lines.append(f"# done {stamp(t)}: {len(ids)} rows written, {len(pages)} pages, count at start was {total}")
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_text("\n".join(lines) + "\n")
    return len(ids)


def copy_original():
    dst = TESTS / "original" / "orders_service"
    shutil.rmtree(TESTS / "original", ignore_errors=True)
    shutil.copytree(APP / "orders_service", dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def write_sums():
    lines = []
    for top in ("hidden", "original"):
        for p in sorted((TESTS / top).rglob("*")):
            if p.is_file():
                lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(TESTS).as_posix()}")
    (TESTS / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    return len(lines)


def main():
    out = []
    say = lambda s="": (print(s), out.append(s))
    say(f"# gen_data.py output (python {sys.version.split()[0]}, sqlite {sqlite3.sqlite_version})")
    # visible
    vc, vo = build(VISIBLE_SEED, **VISIBLE)
    write_db(APP / "data" / "orders.db", vc, vo)
    vdesc = sort_desc(vo)
    exported = write_log(APP / "logs" / "export-2026-10-27.log", vdesc, EXPORT_LIMIT, len(vo))
    support = support_tool_case(vc, vo)
    (APP / "INCIDENT.md").write_text(incident_text(len(vo), exported, EXPORT_LIMIT, support))
    say(f"\n## visible database (seed {VISIBLE_SEED}): {len(vo)} orders, {len(vc)} customers, "
        f"{len(tie_groups(vo))} same-second groups (largest {max(len(v) for v in tie_groups(vo).values())})")
    say(f"- buggy export at limit {EXPORT_LIMIT}: {exported} rows, {len(vo) - exported} missing")
    for lim in (50, 100, 500):
        say(f"- buggy walk at limit {lim}: {lost(vdesc, lim)} missing")
    say(f"- support tool (customer listing at limit {SUPPORT_TOOL_LIMIT}): wholesale account {support[0]} has "
        f"{support[1]} orders, the buggy listing shows {support[2]}")
    assert support[2] < support[1]
    # hidden
    hc, ho = build(HIDDEN_SEED, **HIDDEN)
    write_db(TESTS / "hidden" / "orders.db", hc, ho)
    plan, losses, sizes = make_plan(hc, ho)
    (TESTS / "hidden" / "plan.json").write_text(json.dumps(plan, indent=1) + "\n")
    hdesc = sort_desc(ho)
    g = tie_groups(ho)
    say(f"\n## hidden database (seed {HIDDEN_SEED}): {len(ho)} orders, {len(hc)} customers, {len(g)} same-second "
        f"groups (largest {max(len(v) for v in g.values())}; sizes >= 100: {sorted(len(v) for v in g.values() if len(v) >= 100)})")
    backfill_ties = sum(1 for ids in g.values() if min(ids) <= len(ho) - HIDDEN['backfill'] < max(ids))
    say(f"- same-second groups that mix an old low id with a backfilled high id: {backfill_ties}")
    id_order = sorted(ho, key=lambda o: o[0], reverse=True)
    say(f"- rows whose position differs between id order and created_at order: "
        f"{sum(1 for a, b in zip(id_order, hdesc) if a[0] != b[0])}")
    for lim, pre in WALKS:
        n = lost(hdesc, lim, pre)
        say(f"- buggy walk /orders limit {lim} prefix {pre}: {n} missing")
        assert n > 0, (lim, pre)
    newest = hdesc[:2000]
    say(f"- newest 2000 rows hold {len(tie_groups(newest))} same-second groups "
        f"(largest {max(len(v) for v in tie_groups(newest).values())})")
    say(f"- test customers (orders, rows the buggy walks lose at limits {CUSTOMER_LIMITS}): "
        + ", ".join(f"{c}: {sizes[c]} orders, {losses[c]} lost" for c in plan["customers"]))
    assert sum(1 for c in plan["customers"] if losses[c] > 0) >= 6, losses
    say(f"- empty customer {plan['empty_customer']}, unknown customer {plan['unknown_customer']}, "
        f"{len(plan['sample_order_ids'])} sample ids, /orders insert batches {[len(b) for b in plan['inserts']]} "
        f"after pages {plan['insert_walk']['insert_after_pages']} at limit {plan['insert_walk']['limit']}, customer "
        f"{plan['customer_insert_walk']['customer']} insert batches {[len(b) for b in plan['customer_inserts']]} after "
        f"pages {plan['customer_insert_walk']['insert_after_pages']} at limit {plan['customer_insert_walk']['limit']}")
    kinds = {}
    for b in plan["inserts"] + plan["customer_inserts"]:
        for r in b:
            kinds[r[6]] = kinds.get(r[6], 0) + 1
    say(f"- inserted orders by channel: {dict(sorted(kinds.items()))}; ids {plan['inserts'][0][0][0]} to "
        f"{plan['customer_inserts'][-1][-1][0]}")
    for lim in (50, 100, 200):
        say(f"- {len(ho)} orders = {len(ho) // lim} full pages of {lim} + {len(ho) % lim}")
    copy_original()
    n = write_sums()
    say(f"\n{n} files listed in tests/SHA256SUMS")
    (HERE / "gen_data.out.md").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
