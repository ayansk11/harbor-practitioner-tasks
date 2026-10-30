"""Local-only variants for local_check.py (never shipped in the package). Each starts from a shipped variant and
changes exactly one thing by exact text substitution (path under the app copy, old text, new text)."""

ABLATIONS = {
    # A correct fix whose cursor condition no index can serve: every page scans orders_created_at from the top. The
    # slowest valid solution we have; it sets the time budget (DESIGN.md, Timings). Expected reward 1.
    "slow_valid_no_index": {
        "base": "canonical",
        "expected": 1,
        "patch": [("orders_service/pagination.py",
                   'return "(created_at, id) < (?, ?)", [cursor.created_at, cursor.id]',
                   "return \"(created_at || printf('|%020d', id)) < (? || printf('|%020d', ?))\", "
                   "[cursor.created_at, cursor.id]")],
    },
    # Correct but naive: every request loads the whole orders table and sorts it in Python (attempt G's code, reloaded
    # per request, so new orders do appear). About 40-47 ms per request on the Mac (197.5 s to 241.2 s for the
    # agent phase in our local runs before the review fixes). The slowest valid solution we have, so it sets the time budget (3 x its Mac time, plus headroom; DESIGN.md
    # section 8). Expected reward 1. Slow: the run takes about 4 minutes.
    "naive_full_load_valid": {
        "base": "snapshot_at_startup",
        "expected": 1,
        "patch": [("orders_service/app.py",
                   "    snap = Snapshot(database)\n",
                   "    snap = Snapshot(database)\n\n    @app.before_request\n    def _reload():\n"
                   "        nonlocal snap\n        snap = Snapshot(database)\n")],
    },
    # A correct fix that also switches the database to WAL mode and keeps one read transaction open for the life of
    # the process, so the orders inserted mid-export stay in orders.db-wal (no checkpoint can finish). Proves the database read-back
    # copies and applies the -wal file. Expected reward 1.
    "wal_mode_valid": {
        "base": "canonical",
        "expected": 1,
        "patch": [("orders_service/app.py",
                   '    app.config["DATABASE"] = database\n',
                   '    app.config["DATABASE"] = database\n    import sqlite3\n'
                   '    app.config["KEEP_OPEN"] = sqlite3.connect(database, check_same_thread=False)\n'
                   '    app.config["KEEP_OPEN"].execute("PRAGMA journal_mode=WAL")\n'
                   '    app.config["KEEP_OPEN"].execute("BEGIN")\n'
                   '    app.config["KEEP_OPEN"].execute("SELECT COUNT(*) FROM orders").fetchone()\n')],
    },
    # A correct fix that never shows orders written during a pass: the cursor also carries the highest id when the
    # first page was asked for, and later pages add `id <= bound`. API.md allows it ("may or may not appear"); the
    # canonical shows the late-synced orders ahead of the walk, this one shows none. Expected reward 1 (G13 for c4).
    "snapshot_bound_valid": {
        "base": "canonical",
        "expected": 1,
        "patch": [
            ("orders_service/pagination.py", 'Cursor = namedtuple("Cursor", ["created_at", "id"])',
             'Cursor = namedtuple("Cursor", ["created_at", "id", "bound"])'),
            ("orders_service/pagination.py", r'_POSITION = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\|([0-9]{1,18})")',
             r'_POSITION = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\|([0-9]{1,18})\|([0-9]{1,18})")'),
            ("orders_service/pagination.py", "    return Cursor(created_at=m.group(1), id=int(m.group(2)))",
             "    return Cursor(created_at=m.group(1), id=int(m.group(2)), bound=int(m.group(3)))"),
            ("orders_service/pagination.py", "def encode_cursor(row):", "def encode_cursor(row, bound):"),
            ("orders_service/pagination.py", "    position = f\"{row['created_at']}|{row['id']}\"",
             "    position = f\"{row['created_at']}|{row['id']}|{bound}\""),
            ("orders_service/pagination.py", 'return "(created_at, id) < (?, ?)", [cursor.created_at, cursor.id]',
             'return "(created_at, id) < (?, ?) AND id <= ?", [cursor.created_at, cursor.id, cursor.bound]'),
            ("orders_service/pagination.py",
             "def next_cursor(rows, limit):\n    return encode_cursor(rows[-1]) if len(rows) == limit else None",
             "def next_cursor(rows, limit, con=None, cursor=None):\n    if len(rows) != limit:\n        return None\n"
             "    if cursor is not None:\n        return encode_cursor(rows[-1], cursor.bound)\n"
             "    return encode_cursor(rows[-1], con.execute(\"SELECT MAX(id) FROM orders\").fetchone()[0])"),
            ("orders_service/pagination.py", "    return rows, next_cursor(rows, limit)",
             "    return rows, next_cursor(rows, limit, con, cursor)"),
            ("orders_service/queries.py", "    return rows, next_cursor(rows, limit)",
             "    return rows, next_cursor(rows, limit, con, cursor)"),
        ],
    },
    # A correct fix that sleeps 20 ms per request, graded with a 5-second budget (local only): it must score 0 through
    # the budget, quickly, instead of running into the verifier timeout. Expected reward 0.
    "slow_service_short_cap": {
        "base": "canonical",
        "expected": 0,
        "env": {"GRADE_AGENT_CAP": "5"},
        "patch": [("orders_service/app.py",
                   '    @app.get("/orders")\n',
                   '    @app.before_request\n    def _slow():\n        import time\n        time.sleep(0.02)\n\n'
                   '    @app.get("/orders")\n')],
    },
    # Not a fix at all: the shipped service plus a regression test that only covers unique timestamps. Same as the
    # original; listed to show that a passing visible suite says nothing. Expected reward 0.
    "original_more_tests": {
        "base": "original",
        "expected": 0,
        "patch": [("tests/test_api.py", "def test_count(client):",
                   "def test_count_again(client):\n    assert client.get('/orders/count').status_code == 200\n\n\n"
                   "def test_count(client):")],
    },
}
