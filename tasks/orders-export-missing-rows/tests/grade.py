import sys; sys.path.insert(0, "/tests"); import kit  # noqa: E401,E702  (python3 -I does not add /tests itself)
"""Grader for orders-export-missing-rows (black-box HTTP; the agent's code is never imported).

Inputs (all under kit.TESTS_DIR, root-only): hidden/orders.db (30,000 orders, many same-second groups of up to 380,
backfilled orders with high ids and old dates), hidden/plan.json (test customers, sample ids, the 56 orders inserted
mid-walk), original/orders_service (untouched copy of the shipped service). Expected answers are computed here from
hidden/orders.db and plan.json; nothing the agent's code writes or reports is taken as evidence.

1. The untouched original serves its own copy of the hidden database: /orders/count and /orders/<id> for the sample
   ids are the reference for check 6 (and must equal the database itself, or the grader is broken).
2. The agent's service, started from its /app copy on another fresh copy, gets the checks below in one run with one
   time budget. Reward 1 only if every check passes:
   c7 public suite (HTTP-only): default page, count, one order, limit 500, a customer's default page.
   c1 order: full walks of /orders at limit 50, 200 and 500, limit 7 over the newest 5,000 and limit 1 over the newest
      2,000 orders: ids exactly as ORDER BY created_at DESC, id DESC.
   c2 pages: every page but the last has exactly `limit` orders; next_cursor is null on the last page only (an empty
      last page is accepted); a repeated cursor or a walk over its page budget fails.
   c3 customers: the same on 10 customers at limits 3 and 20; an existing customer without orders; an unknown one.
   c5 errors: the 400 and 404 cases API.md states.
   c6 fields: every returned order equals the database on the API.md fields; /orders/count and /orders/<id> equal
      the original's answers.
   c4 inserts: orders are written into the database file between two requests (by a helper run as uid 1001, as
      checkout or the POS sync would). During a walk of /orders at limit 100, 25 orders after page 3 and 25 after page
      10: new orders, one in the second of the last order just served, late-synced orders (high id, old date) ahead
      of the walk and behind it. Then during a walk of the first test customer's orders at limit 3, 3 orders after
      page 2 and 3 after page 5, of the same kinds. In each walk every order that existed when it started comes back
      exactly once and in order, each new order at most once, no other id. Then a fresh walk (limit 150), two
      customers' lists and /orders/count include every inserted order exactly.
   db  the database file after the run: orders and customers are still tables, existing customers and orders are
      unchanged, the 56 inserted orders are present.
"""
import hashlib, http.client, json, math, os, socket, sqlite3, time, urllib.parse  # noqa: E401

TESTS = kit.TESTS_DIR
SEED_DB = os.path.join(TESTS, "hidden", "orders.db")
PLAN_PATH = os.path.join(TESTS, "hidden", "plan.json")
ORIGINAL = os.path.join(TESTS, "original")
FIELDS = ("id", "customer_id", "created_at", "status", "total_cents", "currency")
ALL_COLUMNS = FIELDS + ("channel",)
START_CAP = 30            # seconds for a service to answer its first request
REQ_TIMEOUT = 10          # seconds per request; a timed-out or dropped request is sent once more (instruction.md)
ORIGINAL_CAP = 60         # seconds for the original's phase
AGENT_CAP = 900           # seconds for every request to the agent's service together (DESIGN.md, Timings)
if kit.LOCAL and os.environ.get("GRADE_AGENT_CAP"):   # authoring only: prove the cap with a short limit
    AGENT_CAP = float(os.environ["GRADE_AGENT_CAP"])
MAX_BODY = 8_000_000
BAD_CURSORS = ("not-a-cursor", "!!!")
BAD_LIMITS = ("0", "501", "-3", "ten", "2.5")
INSERTER = r"""
import json, sqlite3, sys
db, rows = sys.argv[1], json.loads(sys.argv[2])
con = sqlite3.connect(db, timeout=20)
with con:
    con.executemany("INSERT INTO orders (id, customer_id, created_at, status, total_cents, currency, channel) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
con.close()
print("inserted", len(rows))
"""


class OutOfTime(Exception):
    pass


# ---------------------------------------------------------------- inputs (root reads only /tests)
def verify_sums():
    with open(os.path.join(TESTS, "SHA256SUMS")) as f:
        lines = [ln.split("  ", 1) for ln in f.read().splitlines() if ln.strip()]
    for digest, rel in lines:
        with open(os.path.join(TESTS, rel), "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != digest:
                raise RuntimeError(f"hidden input changed: {rel}")
    kit.log(f"SHA256SUMS ok ({len(lines)} files)")


def load_truth():
    con = sqlite3.connect(f"file:{SEED_DB}?mode=ro&immutable=1", uri=True)
    orders = [tuple(r) for r in con.execute(f"SELECT {', '.join(ALL_COLUMNS)} FROM orders ORDER BY id")]
    customers = [tuple(r) for r in con.execute("SELECT id, name, email, segment, created_at FROM customers ORDER BY id")]
    sql_order = [r[0] for r in con.execute("SELECT id FROM orders ORDER BY created_at DESC, id DESC")]
    con.close()
    if sort_ids(orders) != sql_order:          # two independent computations of the contract's order must agree
        raise RuntimeError("Python and SQLite disagree on the expected order")
    return orders, customers


def sort_ids(rows):
    return [r[0] for r in sorted(rows, key=lambda r: (r[2], r[0]), reverse=True)]


def as_json(row):
    return dict(zip(FIELDS, row[:len(FIELDS)]))


# ---------------------------------------------------------------- HTTP
class Client:
    """One keep-alive connection per service; one retry when a request gets no answer; a shared deadline."""

    def __init__(self, port, deadline):
        self.port, self.deadline, self.conn, self.requests = port, deadline, None, 0

    def close(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def get(self, path, params=None):
        url = path + ("?" + urllib.parse.urlencode(params) if params else "")
        err = None
        for _attempt in (0, 1):
            if time.monotonic() > self.deadline:
                raise OutOfTime(f"time budget used up before GET {url}")
            try:
                if self.conn is None:
                    self.conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=REQ_TIMEOUT)
                self.conn.request("GET", url, headers={"Accept": "application/json"})
                resp = self.conn.getresponse()
                body = resp.read(MAX_BODY + 1)
                if resp.will_close:
                    self.close()
                self.requests += 1
                if len(body) > MAX_BODY:
                    return resp.status, None, "body too large"
                try:
                    return resp.status, json.loads(body), None
                except ValueError:
                    return resp.status, None, "body is not JSON"
            except (http.client.HTTPException, OSError) as e:
                self.close()
                err = f"{type(e).__name__}: {e}"
        return None, None, f"no answer to GET {url} ({err})"


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def parse_page(obj, limit):
    """(orders, next_cursor) from a page body, or raise ValueError with the reason."""
    if not isinstance(obj, dict) or "orders" not in obj or "next_cursor" not in obj:
        raise ValueError("page is not {'orders': [...], 'next_cursor': ...}")
    orders, nxt = obj["orders"], obj["next_cursor"]
    if not isinstance(orders, list) or not (nxt is None or isinstance(nxt, str)):
        raise ValueError("orders is not a list or next_cursor is not a string or null")
    if len(orders) > limit:
        raise ValueError(f"page has {len(orders)} orders, more than limit={limit}")
    for o in orders:
        if not isinstance(o, dict) or not is_int(o.get("id")):
            raise ValueError("an order is not an object with an integer id")
    return orders, nxt


def walk(client, path, limit, budget, max_rows=None, after_page=None):
    """Follow next_cursor from the first page. Returns (orders, page sizes, ended, problem)."""
    rows, sizes, cursor, seen = [], [], None, set()
    while True:
        if len(sizes) >= budget:
            return rows, sizes, False, f"more than {budget} pages"
        params = {"limit": limit} if cursor is None else {"limit": limit, "cursor": cursor}
        status, obj, err = client.get(path, params)
        if status != 200:
            return rows, sizes, False, f"page {len(sizes) + 1}: status {status} {err or ''}".strip()
        try:
            orders, nxt = parse_page(obj, limit)
        except ValueError as e:
            return rows, sizes, False, f"page {len(sizes) + 1}: {e}"
        sizes.append(len(orders))
        rows += orders
        if after_page is not None:
            after_page(len(sizes))
        if nxt is None:
            return rows, sizes, True, None
        if nxt in seen:
            return rows, sizes, False, f"page {len(sizes)}: next_cursor repeats an earlier cursor (loop)"
        seen.add(nxt)
        cursor = nxt
        if max_rows is not None and len(rows) >= max_rows:
            return rows, sizes, False, None


def pages_problem(sizes, limit, ended):
    """Every page but the last holds exactly `limit`; the last (only when the walk ended) holds at most `limit`."""
    body = sizes[:-1] if ended else sizes
    for i, n in enumerate(body, start=1):
        if n != limit:
            return f"page {i} of {len(sizes)} has {n} orders, not limit={limit}, and is not the last page"
    return None


# ---------------------------------------------------------------- services
def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start(code_dir, db_path, what):
    port = free_port()
    cmd = [sys.executable, "-m", "orders_service", "--db", db_path, "--port", str(port)]
    t0 = time.monotonic()
    proc = kit.start_service_as_runner(cmd, cwd=code_dir, port=port, health_path="/orders/count", timeout=START_CAP)
    kit.log(f"{what} service on port {port}: {'up' if proc else 'FAILED'} after {time.monotonic() - t0:.2f}s")
    return proc, port


def stage_db(name):
    return os.path.join(kit.stage_for_runner(SEED_DB, name), os.path.basename(SEED_DB))


# ---------------------------------------------------------------- the grading run
class Report:
    NAMES = ("c1_order", "c2_pages", "c3_customers", "c4_inserts", "c5_errors", "c6_fields", "c7_public", "db")

    def __init__(self):
        self.passed = {n: 0 for n in self.NAMES}
        self.failed = {n: 0 for n in self.NAMES}
        self.shown = 0

    def check(self, name, ok, what):
        if ok:
            self.passed[name] += 1
        else:
            self.failed[name] += 1
            if self.shown < 40:
                kit.log(f"  FAIL {name}: {what}")
                self.shown += 1
        return ok

    def all_ok(self):
        return all(v == 0 for v in self.failed.values()) and all(v > 0 for v in self.passed.values())


def original_phase(seed_orders):
    """Reference answers from the untouched original (our code, run like the agent's)."""
    code = kit.stage_for_runner(ORIGINAL, "original")
    db = stage_db("db_original")
    proc, port = start(code, db, "original")
    if proc is None:
        raise RuntimeError("the original service did not start")
    cl = Client(port, time.monotonic() + ORIGINAL_CAP)
    try:
        ref = {"count": cl.get("/orders/count")[1], "orders": {}}
        for oid in PLAN["sample_order_ids"]:
            status, obj, _ = cl.get(f"/orders/{oid}")
            ref["orders"][oid] = obj if status == 200 else None
    finally:
        cl.close()
        kit.stop_service(proc)
    by_id = {r[0]: r for r in seed_orders}
    if ref["count"] != {"count": len(seed_orders)} or any(ref["orders"][i] != as_json(by_id[i]) for i in ref["orders"]):
        raise RuntimeError("the original's answers differ from the hidden database (grader bug)")
    kit.log(f"original: {cl.requests} requests, answers equal the hidden database")
    return ref


def agent_phase(sub, seed_orders, ref, rep):
    db = stage_db("db_agent")
    proc, port = start(sub, db, "agent")
    if proc is None:
        rep.check("c7_public", False, "the service did not answer GET /orders/count within 30 s of "
                  "`python -m orders_service --db <db> --port <port>`")
        return db, 0
    t0 = time.monotonic()
    cl = Client(port, t0 + AGENT_CAP)
    try:
        run_checks(cl, db, seed_orders, ref, rep)
    except OutOfTime as e:
        rep.check("c1_order", False, f"{e} (all requests share a {AGENT_CAP:.0f} s budget)")
    finally:
        cl.close()
        kit.stop_service(proc)
        kit.kill_runner_processes()
    took = time.monotonic() - t0
    kit.log(f"agent: {cl.requests} requests in {took:.2f}s")
    return db, took


def run_checks(cl, db, seed_orders, ref, rep):
    by_id = {r[0]: r for r in seed_orders}
    want = sort_ids(seed_orders)
    by_cust = {}
    for r in seed_orders:
        by_cust.setdefault(r[1], []).append(r)

    def fields_ok(orders, truth, where):
        bad = [o.get("id") for o in orders if o.get("id") not in truth
               or {k: o.get(k) for k in FIELDS} != as_json(truth[o.get("id")])]
        return rep.check("c6_fields", not bad, f"{where}: {len(bad)} orders differ from the database on the API.md "
                                                 f"fields, e.g. id {bad[:3]}")

    def first_diff(got, exp):
        for i, (a, b) in enumerate(zip(got, exp)):
            if a != b:
                return f"position {i + 1}: got id {a}, expected id {b}"
        return f"got {len(got)} ids, expected {len(exp)}"

    def checked_walk(name, path, limit, exp, prefix=None, truth=by_id, after_page=None):
        budget = math.ceil((prefix or len(exp)) / limit) + 2
        t = time.monotonic()
        rows, sizes, ended, problem = walk(cl, path, limit, budget, prefix, after_page)
        ids = [o["id"] for o in rows]
        where = f"{path} limit={limit}" + (f" (newest {prefix})" if prefix else "")
        rep.check("c2_pages", problem is None, f"{where}: {problem}")
        if problem is None:
            rep.check("c2_pages", pages_problem(sizes, limit, ended) is None,
                      f"{where}: {pages_problem(sizes, limit, ended)}")
        if prefix is None:
            rep.check(name, problem is None and ids == exp,
                      f"{where}: {len(ids)} orders ({len(set(ids))} distinct) for {len(exp)} expected; "
                      f"first difference at {first_diff(ids, exp)}")
        else:
            rep.check(name, problem is None and len(ids) >= prefix and ids == exp[:len(ids)],
                      f"{where}: {first_diff(ids, exp[:len(ids)]) if ids != exp[:len(ids)] else f'only {len(ids)} orders'}")
        fields_ok(rows, truth, where)
        kit.log(f"walk {where}: {len(sizes)} pages, {len(ids)} orders, {time.monotonic() - t:.2f}s")
        return rows, sizes, ended, problem

    # c7: the visible suite, HTTP-only
    status, obj, _ = cl.get("/orders")
    try:
        orders, nxt = parse_page(obj, 100)
        rep.check("c7_public", status == 200 and [o["id"] for o in orders] == want[:100] and isinstance(nxt, str),
                  "GET /orders without parameters: not the newest 100 orders with a next_cursor")
    except ValueError as e:
        rep.check("c7_public", False, f"GET /orders: status {status}, {e}")
    status, obj, _ = cl.get("/orders/count")
    rep.check("c7_public", status == 200 and obj == ref["count"], f"GET /orders/count: {status} {str(obj)[:80]}")
    oid = PLAN["sample_order_ids"][0]
    status, obj, _ = cl.get(f"/orders/{oid}")
    rep.check("c7_public", status == 200 and isinstance(obj, dict) and {k: obj.get(k) for k in FIELDS} == ref["orders"][oid],
              f"GET /orders/{oid}: {status} {str(obj)[:120]}")
    status, obj, _ = cl.get("/orders", {"limit": 500})
    rep.check("c7_public", status == 200 and isinstance(obj, dict) and isinstance(obj.get("orders"), list)
              and [o.get("id") for o in obj["orders"] if isinstance(o, dict)] == want[:500], "GET /orders?limit=500")
    c0 = PLAN["customers"][0]
    status, obj, _ = cl.get(f"/customers/{c0}/orders")
    rep.check("c7_public", status == 200 and isinstance(obj, dict) and isinstance(obj.get("orders"), list)
              and [o.get("id") for o in obj["orders"] if isinstance(o, dict)] == sort_ids(by_cust[c0])[:100],
              f"GET /customers/{c0}/orders")

    # c1 + c2 + c6: /orders walks
    for w in PLAN["orders_walks"]:
        checked_walk("c1_order", "/orders", w["limit"], want, w["prefix"])

    # c3 + c2 + c6: customers
    for c in PLAN["customers"]:
        for lim in PLAN["customer_limits"]:
            checked_walk("c3_customers", f"/customers/{c}/orders", lim, sort_ids(by_cust[c]))
    status, obj, _ = cl.get(f"/customers/{PLAN['empty_customer']}/orders")
    rep.check("c3_customers", status == 200 and obj == {"orders": [], "next_cursor": None},
              f"customer {PLAN['empty_customer']} has no orders: got {status} {str(obj)[:80]}")

    # c5: errors stated in API.md
    for q in BAD_LIMITS:
        status, _, _ = cl.get("/orders", {"limit": q})
        rep.check("c5_errors", status == 400, f"GET /orders?limit={q}: {status}, expected 400")
    for q in BAD_CURSORS:
        status, _, _ = cl.get("/orders", {"cursor": q})
        rep.check("c5_errors", status == 400, f"GET /orders?cursor={q}: {status}, expected 400")
    status, _, _ = cl.get(f"/customers/{c0}/orders", {"limit": "0"})
    rep.check("c5_errors", status == 400, f"GET /customers/{c0}/orders?limit=0: {status}, expected 400")
    status, _, _ = cl.get(f"/customers/{c0}/orders", {"cursor": BAD_CURSORS[0]})
    rep.check("c5_errors", status == 400, f"GET /customers/{c0}/orders?cursor={BAD_CURSORS[0]}: {status}, expected 400")
    status, _, _ = cl.get(f"/orders/{PLAN['unknown_order']}")
    rep.check("c5_errors", status == 404, f"GET /orders/{PLAN['unknown_order']}: {status}, expected 404")
    status, _, _ = cl.get(f"/customers/{PLAN['unknown_customer']}/orders")
    rep.check("c5_errors", status == 404, f"GET /customers/{PLAN['unknown_customer']}/orders: {status}, expected 404")

    # c6: single orders and the count against the original
    diff = []
    for oid2, exp in ref["orders"].items():
        status, obj, _ = cl.get(f"/orders/{oid2}")
        if status != 200 or not isinstance(obj, dict) or {k: obj.get(k) for k in FIELDS} != exp:
            diff.append(oid2)
    rep.check("c6_fields", not diff, f"GET /orders/<id> differs from the original for {len(diff)} of "
                                     f"{len(ref['orders'])} ids, e.g. {diff[:3]}")

    # c4: orders written into the database file between two requests of a walk, then fresh listings
    inserted = []

    def inserter(batches, what):
        def after_page(n):
            if n in batches:
                rows = batches[n]
                r = kit.run_as_runner([sys.executable, "-I", "-S", "-c", INSERTER, db, json.dumps(rows)],
                                      cwd=os.path.dirname(db), timeout=60)
                ok = r["rc"] == 0 and not r["timed_out"] and r["stdout"].strip() == f"inserted {len(rows)}"
                rep.check("c4_inserts", ok, f"inserting {len(rows)} orders into the database after page {n} of {what} "
                                            f"failed (rc={r['rc']}, timed_out={r['timed_out']}, "
                                            f"stderr={r['stderr'][-300:]!r})")
                if ok:
                    inserted.extend(tuple(x) for x in rows)
        return after_page

    def insert_walk(path, limit, pages, batch_list, existing):
        """Walk `path`, writing batch_list[i] after page pages[i]. Every row of `existing` (the listing when the walk
        starts) must come back exactly once and in order; each new order at most once; no other id."""
        exp = sort_ids(existing)
        old_ids = {r[0] for r in existing}
        new_ids = {x[0] for b in batch_list for x in b}
        where = f"{path} limit={limit} with orders inserted after pages {pages}"
        rows, sizes, ended, problem = walk(cl, path, limit, math.ceil((len(exp) + len(new_ids)) / limit) + 2, None,
                                           inserter(dict(zip(pages, batch_list)), path))
        ids = [o["id"] for o in rows]
        olds = [i for i in ids if i in old_ids]
        news = [i for i in ids if i in new_ids]
        stray = [i for i in ids if i not in old_ids and i not in new_ids]
        rep.check("c2_pages", problem is None and pages_problem(sizes, limit, ended) is None,
                  f"{where}: {problem or pages_problem(sizes, limit, ended)}")
        rep.check("c4_inserts", problem is None and olds == exp,
                  f"{where}: {len(olds)} older orders returned ({len(set(olds))} distinct) for {len(exp)}; "
                  f"{first_diff(olds, exp)}")
        rep.check("c4_inserts", len(news) == len(set(news)) and not stray,
                  f"{where}: a new order returned twice, or {len(stray)} ids that are not in this listing")
        truth = dict(by_id)
        truth.update({x[0]: x for x in inserted})
        fields_ok(rows, truth, where)
        kit.log(f"walk {where}: {len(sizes)} pages, {len(ids)} orders ({len(news)} of {len(new_ids)} new)")

    iw = PLAN["insert_walk"]
    insert_walk("/orders", iw["limit"], iw["insert_after_pages"], PLAN["inserts"], seed_orders)
    cw = PLAN["customer_insert_walk"]
    cc = cw["customer"]
    insert_walk(f"/customers/{cc}/orders", cw["limit"], cw["insert_after_pages"], PLAN["customer_inserts"],
                [r for r in seed_orders + inserted if r[1] == cc])
    planned = sum(len(b) for b in PLAN["inserts"] + PLAN["customer_inserts"])
    if len(inserted) == planned:         # otherwise c4_inserts has already failed
        all_rows = seed_orders + inserted
        truth2 = dict(by_id)
        truth2.update({x[0]: x for x in inserted})
        want2 = sort_ids(all_rows)
        checked_walk("c4_inserts", "/orders", 150, want2, truth=truth2)
        for c, lim in ((PLAN["customers"][0], 3), (PLAN["customers"][1], 20)):
            checked_walk("c4_inserts", f"/customers/{c}/orders", lim, sort_ids([r for r in all_rows if r[1] == c]),
                         truth=truth2)
        status, obj, _ = cl.get("/orders/count")
        rep.check("c4_inserts", status == 200 and obj == {"count": len(all_rows)},
                  f"GET /orders/count after the inserts: {status} {str(obj)[:80]}, expected {len(all_rows)}")
        for x in (inserted[0], inserted[-1]):
            status, obj, _ = cl.get(f"/orders/{x[0]}")
            rep.check("c4_inserts", status == 200 and isinstance(obj, dict)
                      and {k: obj.get(k) for k in FIELDS} == as_json(x), f"GET /orders/{x[0]} (inserted): {status}")
    PLAN["_inserted"] = inserted


def db_check(db, seed_orders, seed_customers, rep):
    """Read the agent's database file back (copied out with uid 1001's rights) and compare it with what it must hold."""
    try:
        local = kit.copy_out_as_runner(db, "agent_db/orders.db")
        try:
            kit.copy_out_as_runner(db + "-wal", "agent_db/orders.db-wal")
        except FileNotFoundError:
            pass
        con = sqlite3.connect(local)            # normal mode, in root-only SCRATCH, so a WAL is applied
        kinds = dict(con.execute("SELECT name, type FROM sqlite_master WHERE name IN ('orders', 'customers')"))
        orders = [tuple(r) for r in con.execute(f"SELECT {', '.join(ALL_COLUMNS)} FROM orders ORDER BY id")]
        customers = [tuple(r) for r in con.execute("SELECT id, name, email, segment, created_at FROM customers ORDER BY id")]
        con.close()
    except Exception as e:
        rep.check("db", False, f"could not read the database back: {type(e).__name__}: {e}")
        return
    rep.check("db", kinds == {"orders": "table", "customers": "table"},
              f"orders and customers must stay tables: sqlite_master says {kinds}")
    expected = sorted(seed_orders + PLAN.get("_inserted", []))
    changed = sum(1 for a, b in zip(orders, expected) if a != b) + abs(len(orders) - len(expected))
    rep.check("db", orders == expected, f"orders table: {changed} rows differ from the hidden database plus the "
                                        f"{len(PLAN.get('_inserted', []))} inserted orders")
    rep.check("db", customers == seed_customers, "customers table changed")


def grade():
    global PLAN
    t_all = time.monotonic()
    kit.log(f"python {sys.version.split()[0]}, sqlite {sqlite3.sqlite_version}")
    verify_sums()
    with open(PLAN_PATH) as f:
        PLAN = json.load(f)
    seed_orders, seed_customers = load_truth()
    sub = kit.prepare_submission()
    t = time.monotonic()
    ref = original_phase(seed_orders)
    kit.log(f"original phase {time.monotonic() - t:.2f}s")
    rep = Report()
    db, took = agent_phase(sub, seed_orders, ref, rep)
    db_check(db, seed_orders, seed_customers, rep)
    for n in Report.NAMES:
        kit.log(f"check {n}: {rep.passed[n]} passed, {rep.failed[n]} failed")
    ok = rep.all_ok()
    metrics = {f"{n}_ok": int(rep.failed[n] == 0 and rep.passed[n] > 0) for n in Report.NAMES}
    metrics.update({"failed_checks": sum(rep.failed.values()), "agent_seconds": round(took, 2),
                    "grading_seconds": round(time.monotonic() - t_all, 2)})
    return (1 if ok else 0), metrics


PLAN = {}
kit.main(grade)
