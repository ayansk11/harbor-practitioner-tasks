import sys; sys.path.insert(0, "/tests"); import kit  # noqa: E702  (python3 -I does not add /tests itself)
# Grader for tenant-isolation-docshare (black-box HTTP; the agent's code is never imported).
#
# 1. The untouched original app (tests/original) answers every permitted read on its own copy of the hidden database,
#    before any agent code runs: these answers are the reference for response fields and headers.
# 2. Run 1: the agent's app on a fresh copy of the hidden database gets every refused read shuffled together with every
#    permitted read, then every refused write. Each refusal must be a 4xx with no file contents and no name of a file
#    the caller may never read; each permitted read must match the seed and the original's answer. Then every file is
#    read once by a member of its organisation (nothing renamed or deleted), the app is stopped, and the database
#    (copied out by uid 1001, with its -wal file) must equal the hidden seed on the named columns.
# 3. Run 2: the agent's app on another fresh copy gets the permitted reads shuffled with 400 refused reads, then a
#    fixed list of permitted writes (rename, share and revoke, delete, including from a second organisation via
#    X-Org-Id) whose effects are checked over HTTP, with 3-12 refused requests (reads and writes) before each one.
# No run of agent code sees only one kind of request, so a service cannot pass by telling the runs apart; the
# staged folder names are random for the same reason. Reward 1 only if every check passes.
import base64, binascii, hashlib, http.client, json, os, random, re, secrets, socket, sqlite3, time, urllib.parse

TESTS = kit.TESTS_DIR
if TESTS not in sys.path:
    sys.path.insert(0, TESTS)
import policy  # noqa: E402

SEED_DB = os.path.join(TESTS, "hidden", "seed.db")
if kit.LOCAL and os.environ.get("GRADE_SEED_DB"):      # authoring only: grade against another seed database
    SEED_DB = os.environ["GRADE_SEED_DB"]
ORIGINAL = os.path.join(TESTS, "original")
START_CAP = 30            # seconds for a service to answer GET /api/health
REQ_TIMEOUT = 10          # seconds per request
PHASE_CAP = {"original": 90, "run1": 90, "run2": 90}    # seconds per run (floor rule, see DESIGN.md "Timings")
if kit.LOCAL and os.environ.get("GRADE_PHASE_CAP"):    # authoring only: prove the cap with a short limit
    PHASE_CAP = {k: float(os.environ["GRADE_PHASE_CAP"]) for k in PHASE_CAP}
MAX_BODY = 4_000_000
RNG_SEED = 20261028
UNKNOWN_ORG = "00000000-0000-4000-8000-00000000dead"
UNKNOWN_FILE = "00000000-0000-4000-8000-00000000beef"
UNKNOWN_SHARE = "unknown-share-token-000000"
BAD_TOKEN = "dsk_" + "0" * 32
FILE_FIELDS = ("id", "org_id", "folder_id", "name", "mime_type", "size", "uploaded_by", "created_at")
FOLDER_FIELDS = ("id", "org_id", "name")
MARKER_RE = re.compile(rb"DSM-[0-9A-F]{16}")
WRITE_KINDS = ("rename", "share", "revoke", "delete")
MIXED_REFUSALS = 400      # refused reads shuffled into run 2's permitted reads
NOISE = (3, 12)           # refused requests sent before each request of run 2's write list (seeded count)
ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]00:?00)")


# ---------------------------------------------------------------- seed and cases
def load_seed(path=SEED_DB):
    con = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    con.row_factory = sqlite3.Row
    q = lambda s: [dict(r) for r in con.execute(s)]  # noqa: E731
    seed = {"orgs": {r["id"]: r for r in q("SELECT id, name FROM orgs")},
            "users": {r["id"]: r for r in q("SELECT id, email, name, token, home_org_id, is_support FROM users")},
            "roles": {}, "folders": {r["id"]: r for r in q("SELECT id, org_id, name FROM folders")},
            "files": {r["id"]: r for r in q(f"SELECT {', '.join(FILE_FIELDS)}, content FROM files")},
            "shares": {r["token"]: r for r in q("SELECT token, file_id, created_by, created_at, revoked_at FROM shares")}}
    for r in q("SELECT user_id, org_id, role FROM memberships"):
        seed["roles"].setdefault(r["user_id"], {})[r["org_id"]] = r["role"]
    con.close()
    for f in seed["files"].values():
        f["content"] = bytes(f["content"])
        f["marker"] = MARKER_RE.search(f["content"]).group(0)
    return seed


def contexts(seed):
    out = [("anon", None, None), ("badtoken", None, None)]
    for uid in sorted(seed["users"]):
        out += [("user", uid, None)] + [("user", uid, o) for o in sorted(seed["orgs"])] + [("user", uid, UNKNOWN_ORG)]
    return out


def label(seed, ctx):
    kind, uid, hdr = ctx
    if kind != "user":
        return kind
    who = seed["users"][uid]["email"]
    return f"{who} X-Org-Id={seed['orgs'][hdr]['name'] if hdr in seed['orgs'] else hdr}" if hdr else who


def relation(seed, ctx, f):
    state, active, role = policy.resolve(seed, ctx)
    if role == "support":
        return "support-active" if f["org_id"] == active else "support-other"
    if state != "ok":
        home = seed["users"].get(ctx[1], {}).get("home_org_id")
        return "named" if f["org_id"] == ctx[2] else ("home" if f["org_id"] == home else "other")
    if f["org_id"] == active:
        return "active"
    return "member-other" if f["org_id"] in seed["roles"].get(ctx[1], {}) else "foreign"


FILE_REQ = {"read": ("GET", "/api/files/{}"), "download": ("GET", "/api/files/{}/download"),
            "thumb": ("GET", "/api/files/{}/thumb"), "rename": ("PATCH", "/api/files/{}"),
            "share": ("POST", "/api/files/{}/shares"), "delete": ("DELETE", "/api/files/{}")}


def build_cases(seed):
    """Deterministic request list: (deny cases, allow cases). Each case is a dict."""
    rng = random.Random(RNG_SEED)
    names = random.Random(RNG_SEED + 5)     # new names for refused renames, the same pattern as permitted ones
    deny, allow = [], []
    files = [seed["files"][i] for i in sorted(seed["files"])]

    def add(ctx, kind, method, path, decision, body=None, **meta):
        case = {"ctx": ctx, "kind": kind, "method": method, "path": path, "body": body, "decision": decision, **meta}
        if decision in ("deny", "401", "400"):      # "400": support listing without X-Org-Id (PERMISSIONS.md 2, 6)
            deny.append(case)
        elif decision == "allow":
            allow.append(case)

    for n, ctx in enumerate(contexts(seed)):
        state, active, role = policy.resolve(seed, ctx)
        for action, (method, tmpl) in FILE_REQ.items():
            classes = {}
            for f in files:
                classes.setdefault(relation(seed, ctx, f), []).append(f)
            for cls in sorted(classes):
                f = rng.choice(classes[cls])
                d = policy.can_file(seed, ctx, action, f["id"])
                if d == "allow" and action not in policy.READ_ACTIONS:
                    continue  # permitted writes run in the fixed write list of phase "allow"
                body = {"name": f"renamed-{names.getrandbits(32):08x}.md"} if action == "rename" else None
                add(ctx, action, method, tmpl.format(f["id"]), d, body, file_id=f["id"])
        add(ctx, "read", "GET", f"/api/files/{UNKNOWN_FILE}", policy.can_file(seed, ctx, "read", UNKNOWN_FILE))
        for tok in rng.sample(sorted(seed["shares"]), 3):
            d = policy.can_revoke(seed, ctx, tok)
            if d != "allow":
                add(ctx, "revoke", "DELETE", f"/api/shares/{tok}", d)
        # export: all or nothing (PERMISSIONS.md section 4)
        readable = [f["id"] for f in files if policy.can_file(seed, ctx, "read", f["id"]) == "allow"]
        other = [f["id"] for f in files if f["id"] not in readable]
        sets = []
        if readable and other:
            r, o = rng.choice(readable), rng.choice(other)
            sets += [[r, o], [o, r], [o], [r, rng.choice(readable), o]]
        if readable:
            sets += [rng.sample(readable, min(3, len(readable))), [rng.choice(readable), UNKNOWN_FILE]]
        if not readable:
            sets += [[rng.choice(other)], rng.sample(other, 2)]
        if role == "support":
            sets.append([rng.choice([f["id"] for f in files if f["org_id"] == o]) for o in sorted(seed["orgs"])])
        for ids in sets:
            add(ctx, "export", "POST", "/api/export", policy.can_export(seed, ctx, ids), {"file_ids": ids}, ids=ids)
        # lists and identity endpoints
        for kind, path in (("list_files", "/api/files"), ("list_folders", "/api/folders")):
            d = policy.can_list(seed, ctx)
            add(ctx, kind, "GET", path, d, active=active)
        folders = sorted(seed["folders"].values(), key=lambda fo: fo["id"])
        mine = [fo for fo in folders if fo["org_id"] == active]
        others = [fo for fo in folders if fo["org_id"] != active]
        for fo in mine + rng.sample(others, min(2, len(others))):
            add(ctx, "folder_files", "GET", f"/api/folders/{fo['id']}/files", policy.can_list(seed, ctx, fo["id"]),
                active=active, folder_id=fo["id"])
        add(ctx, "me", "GET", "/api/me", policy.can_me(seed, ctx))
        add(ctx, "admin_orgs", "GET", "/api/admin/orgs", policy.can_admin(seed, ctx))
    anon = ("anon", None, None)
    for tok in sorted(seed["shares"]) + [UNKNOWN_SHARE]:
        works = policy.share_link_works(seed, tok)
        add(anon, "share_link", "GET", f"/s/{tok}", "allow" if works else "deny",
            file_id=seed["shares"][tok]["file_id"] if works else None)
    # Refused writes go last, deletes at the very end, so a wrongly allowed write cannot hide a later read leak.
    order = {"rename": 1, "share": 2, "revoke": 3, "delete": 4}
    deny.sort(key=lambda c: order.get(c["kind"], 0))
    return deny, allow


# ---------------------------------------------------------------- running services
def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def stage_name():
    """A random folder name: the path a service is started with says nothing about which run it is."""
    return "w" + secrets.token_hex(4)


def stage_db():
    """A fresh copy of the hidden seed in WORK/<random name>, owned by uid 1001; returns the database path."""
    return os.path.join(kit.stage_for_runner(SEED_DB, stage_name()), os.path.basename(SEED_DB))


def start(code_dir, db_path):
    port = free_port()
    cmd = [sys.executable, "-m", "docshare.serve", "--db", db_path, "--port", str(port)]
    t0 = time.monotonic()
    proc = kit.start_service_as_runner(cmd, cwd=code_dir, port=port, health_path="/api/health", timeout=START_CAP)
    kit.log(f"service from {code_dir} on port {port}: {'up' if proc else 'FAILED'} in {time.monotonic() - t0:.2f}s")
    return proc, port


def stop(proc, port=None):
    if port is not None:
        close_conns(port)
    kit.stop_service(proc)
    kit.kill_runner_processes()


def headers_for(seed, ctx):
    if ctx is None:
        return {}
    kind, uid, hdr = ctx
    h = {}
    if kind == "user":
        h["Authorization"] = f"Bearer {seed['users'][uid]['token']}"
    elif kind == "badtoken":
        h["Authorization"] = f"Bearer {BAD_TOKEN}"
    if hdr:
        h["X-Org-Id"] = hdr
    return h


_CONNS = {}   # port -> one keep-alive connection (thousands of short connections can exhaust ephemeral ports)


def call(port, method, path, headers, body=None, retry=True):
    """One HTTP request on a kept-alive connection; with no answer at all (timeout, reset), retry once on a new one."""
    status, hdrs, payload = _call(port, method, path, headers, body)
    if status is None and retry:
        time.sleep(0.5)
        status, hdrs, payload = _call(port, method, path, headers, body)
    return status, hdrs, payload


def _call(port, method, path, headers, body=None):
    h = dict(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    conn = _CONNS.get(port)
    if conn is None:
        conn = _CONNS[port] = http.client.HTTPConnection("127.0.0.1", port, timeout=REQ_TIMEOUT)
    try:
        conn.request(method, path, body=data, headers=h)
        r = conn.getresponse()
        payload = r.read(MAX_BODY)
        if r.length:           # body larger than MAX_BODY: the connection cannot be reused
            conn.close()
        return r.status, {k.lower(): v for k, v in r.getheaders()}, payload
    except Exception as e:  # timeout, reset, bad response: never a pass
        conn.close()
        _CONNS.pop(port, None)
        return None, {}, f"{type(e).__name__}: {e}".encode()


def close_conns(port):
    conn = _CONNS.pop(port, None)
    if conn is not None:
        conn.close()


def as_json(payload):
    try:
        return json.loads(payload)
    except Exception:
        return None


# ---------------------------------------------------------------- checks
class Phase:
    def __init__(self, name):
        self.name, self.t0, self.failures, self.count, self.cats, self.leaks = name, time.monotonic(), [], 0, {}, 0

    def over(self):
        return time.monotonic() - self.t0 > PHASE_CAP[self.name]

    def fail(self, what, cat="other"):
        self.failures.append((cat, what))
        self.cats[cat] = self.cats.get(cat, 0) + 1

    def summary(self):
        kit.log(f"phase {self.name}: {self.count} checks, {len(self.failures)} failed, "
                f"{time.monotonic() - self.t0:.2f}s; failed by check: {json.dumps(self.cats, sort_keys=True)}")
        shown = {}
        for cat, what in self.failures:          # up to 3 examples of each failed check
            shown[cat] = shown.get(cat, 0) + 1
            if shown[cat] <= 3:
                kit.log(f"  FAIL {self.name} [{cat}]: {what}")


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings(k)
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def leaks(seed, ctx, headers, payload):
    """File data in a refusal: any content marker, or the name of a file this user may never read."""
    blobs = [payload, " ".join(f"{k}: {v}" for k, v in headers.items()).encode("utf-8", "replace")]
    obj = as_json(payload)
    if obj is not None:
        for s in strings(obj):
            if len(s) >= 12:
                try:
                    blobs.append(base64.b64decode(s, validate=True))
                except (binascii.Error, ValueError):
                    pass
    found = []
    never = set(seed["files"]) - policy.readable_ever(seed, ctx[1] if ctx else None)
    for fid, f in seed["files"].items():
        if any(f["marker"] in b for b in blobs):
            found.append(f"contents of {f['name']}")
        elif fid in never and any(f["name"].encode() in b for b in blobs):
            found.append(f"name {f['name']}")
    return found


def check_refusal(seed, ph, port, case, tag=""):
    """One refused request: a 4xx with no file data. Failures are counted under <tag>status_/leak_<kind>."""
    status, hdrs, payload = call(port, case["method"], case["path"], headers_for(seed, case["ctx"]), case["body"])
    where = f"{case['method']} {case['path']} as {label(seed, case['ctx'])}"
    cat = case["kind"] + ("_bad_x_org_id" if case["ctx"][2] and policy.resolve(seed, case["ctx"])[0] == "deny" else "")
    if status is None or not 400 <= status < 500:
        ph.fail(f"{where}: got {status if status else payload.decode()[:80]}, expected a refusal (4xx)",
                f"{tag}status_{cat}")
    found = leaks(seed, case["ctx"], hdrs, payload)
    if found:
        ph.leaks += 1
        ph.fail(f"{where}: refusal holds {', '.join(found[:3])}", f"{tag}leak_{cat}")


def check_permitted(seed, ph, port, case, ref):
    status, hdrs, payload = call(port, case["method"], case["path"], headers_for(seed, case["ctx"]), case["body"])
    why = compare_allow(seed, case, status, hdrs, payload, ref)
    if why:
        ph.fail(f"{case['method']} {case['path']} as {label(seed, case['ctx'])}: {why}",
                "permitted_" + case["kind"] + ("_support" if policy.resolve(seed, case["ctx"])[2] == "support" else ""))


def pick(obj, fields):
    return {k: obj.get(k) for k in fields} if isinstance(obj, dict) else None


def media_type(hdrs):
    return (hdrs.get("content-type") or "").split(";")[0].strip().lower()


def download_headers(hdrs, ref_hdrs, name):
    """None if Content-Type and Content-Disposition say what the original says (API.md download row), else a reason."""
    if media_type(hdrs) != media_type(ref_hdrs):
        return f"Content-Type {hdrs.get('content-type')!r}, the original sends {ref_hdrs.get('content-type')!r}"
    cd = hdrs.get("content-disposition") or ""
    if not cd.strip().lower().startswith("attachment") or name not in urllib.parse.unquote(cd):
        return f"Content-Disposition {cd!r}, expected attachment with filename {name!r}"
    return None


def compare_allow(seed, case, status, hdrs, payload, ref):
    """None if the permitted response is right, else a reason. ref = the original's (status, headers, body)."""
    kind = case["kind"]
    if status != 200:
        return f"status {status}, expected 200"
    obj = as_json(payload)
    if kind in ("download", "share_link"):
        f = seed["files"][case["file_id"]]
        if payload != f["content"]:
            return "bytes differ from the stored file"
        return download_headers(hdrs, ref[1], f["name"])
    if kind == "thumb":
        if media_type(hdrs) != media_type(ref[1]):
            return f"Content-Type {hdrs.get('content-type')!r}, the original sends {ref[1].get('content-type')!r}"
        return None if payload == ref[2] else "preview differs from the original service's"
    if kind == "export":
        if not isinstance(obj, dict) or not isinstance(obj.get("files"), list):
            return "not {files: [...]}"
        fields = ("id", "name", "mime_type", "size", "content_b64")
        got = sorted(tuple(x.get(k) for k in fields) for x in obj["files"] if isinstance(x, dict))
        want = sorted((i, seed["files"][i]["name"], seed["files"][i]["mime_type"], seed["files"][i]["size"],
                       base64.b64encode(seed["files"][i]["content"]).decode()) for i in case["ids"])
        return None if got == want else "exported files differ from the requested ones"
    ref_obj = as_json(ref[2])
    if kind == "read":
        return None if pick(obj, FILE_FIELDS) == pick(ref_obj, FILE_FIELDS) else "file fields differ from original"
    if kind in ("list_files", "folder_files"):
        if not isinstance(obj, dict) or not isinstance(obj.get("files"), list):
            return "not {files: [...]}"
        want_ids = policy.visible_files(seed, case["active"], case.get("folder_id"))
        got = {x.get("id"): pick(x, FILE_FIELDS) for x in obj["files"] if isinstance(x, dict)}
        if set(got) != want_ids or len(obj["files"]) != len(want_ids):
            return f"listed {len(obj['files'])} files, expected exactly the {len(want_ids)} of the active org"
        ref_items = {x["id"]: pick(x, FILE_FIELDS) for x in ref_obj["files"]}
        if got != ref_items:
            return "file fields differ from original"
        if kind == "folder_files" and pick(obj.get("folder"), FOLDER_FIELDS) != pick(ref_obj["folder"], FOLDER_FIELDS):
            return "folder fields differ from original"
        return None
    if kind == "list_folders":
        if not isinstance(obj, dict) or not isinstance(obj.get("folders"), list):
            return "not {folders: [...]}"
        got = sorted(json.dumps(pick(x, FOLDER_FIELDS), sort_keys=True) for x in obj["folders"])
        want = sorted(json.dumps(pick(x, FOLDER_FIELDS), sort_keys=True) for x in ref_obj["folders"])
        return None if got == want else "folders differ from original"
    if kind == "me":
        def norm(o):
            if not isinstance(o, dict) or not isinstance(o.get("memberships"), list):
                return None
            return (pick(o.get("user"), ("id", "email", "name", "is_support")), o.get("active_org_id"), o.get("role"),
                    sorted(json.dumps(pick(m, ("org_id", "role")), sort_keys=True) for m in o["memberships"]))
        return None if norm(obj) == norm(ref_obj) else "/api/me differs from original"
    if kind == "admin_orgs":
        def norm(o):
            if not isinstance(o, dict) or not isinstance(o.get("orgs"), list):
                return None
            return sorted(json.dumps(pick(x, ("id", "name", "file_count")), sort_keys=True) for x in o["orgs"])
        return None if norm(obj) == norm(ref_obj) else "/api/admin/orgs differs from original"
    raise ValueError(kind)


NEEDS_REF = {"read", "download", "thumb", "share_link", "list_files", "folder_files", "list_folders", "me",
             "admin_orgs"}


def run_original(seed, allow):
    """Reference answers from the untouched app, before any agent code runs."""
    ph = Phase("original")
    code = kit.stage_for_runner(ORIGINAL, stage_name())
    proc, port = start(code, stage_db())
    if proc is None:
        raise RuntimeError("the original service did not start")
    refs = {}
    try:
        for i, case in enumerate(allow):
            if case["kind"] in NEEDS_REF:
                refs[i] = call(port, case["method"], case["path"], headers_for(seed, case["ctx"]), case["body"])
                if refs[i][0] != 200:
                    raise RuntimeError(f"original answered {refs[i][0]} {refs[i][2][:120]!r} to permitted "
                                       f"{case['method']} {case['path']}")
            if ph.over():
                raise RuntimeError("original phase over its time cap")
    finally:
        stop(proc, port)
    ph.count = len(refs)
    ph.summary()
    return refs


def read_tables(con):
    q = lambda s: sorted(tuple(r) for r in con.execute(s))  # noqa: E731
    return {"files": q("SELECT id, org_id, folder_id, name, mime_type, size, uploaded_by, created_at, hex(content) "
                       "FROM files"),
            "shares": q("SELECT token, file_id, created_by, created_at, revoked_at FROM shares"),
            "memberships": q("SELECT user_id, org_id, role FROM memberships"),
            "folders": q("SELECT id, org_id, name FROM folders")}


CHECKPOINT = ("import sqlite3, sys, urllib.parse\n"
              "c = sqlite3.connect('file:' + urllib.parse.quote(sys.argv[1]) + '?mode=rw', uri=True)\n"
              "r = c.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()\n"
              "c.close()\n"
              "sys.exit(0 if r[0] == 0 else 3)\n")


def snapshot(db_path, name):
    """Named columns of the tables the policy protects, after the app is stopped. uid 1001 folds the -wal file into
    the database (our own script, not agent code), root copies it into kit.SCRATCH and opens that copy read-only."""
    res = kit.run_as_runner([sys.executable, "-I", "-c", CHECKPOINT, db_path], cwd="/", timeout=30)
    if res["rc"] != 0 or res["timed_out"]:
        raise RuntimeError(f"checkpoint failed rc={res['rc']} {res['stderr'][-200:]}")
    copy = kit.copy_out_as_runner(db_path, f"{name}/db.sqlite")
    con = sqlite3.connect(f"file:{copy}?mode=ro&immutable=1", uri=True)
    try:
        return read_tables(con)
    finally:
        con.close()


def run_first(seed, sub, deny, allow, refs):
    """Run 1: refused and permitted reads shuffled together, then the refused writes; then the read-back sweep and
    the database diff (only refused requests could have written, so the end state must be the seed)."""
    ph = Phase("run1")
    rng = random.Random(RNG_SEED + 2)
    plan = [("refused", c) for c in deny if c["kind"] not in WRITE_KINDS] + [("permitted", i) for i in range(len(allow))]
    rng.shuffle(plan)
    # Refused writes go last, deletes at the very end, so a wrongly allowed write cannot hide a later read leak.
    plan += [("refused", c) for c in deny if c["kind"] in WRITE_KINDS]
    db_path = stage_db()
    proc, port = start(sub, db_path)
    if proc is None:
        ph.fail("the service did not start with python -m docshare.serve --db <path> --port <port>", "start")
        return ph
    try:
        for mode, x in plan:
            if ph.over():
                ph.fail("time cap reached before all requests of run 1 ran", "time_cap")
                break
            ph.count += 1
            if mode == "refused":
                check_refusal(seed, ph, port, x)
            else:
                check_permitted(seed, ph, port, allow[x], refs.get(x))
        # nothing was renamed or deleted: each file read once by a home member of its organisation
        for fid in sorted(seed["files"]):
            if ph.over():
                ph.fail("time cap reached before every file was read back", "time_cap")
                break
            f = seed["files"][fid]
            uid = next(u for u in sorted(seed["users"]) if seed["users"][u]["home_org_id"] == f["org_id"]
                       and len(seed["roles"].get(u, {})) == 1)
            ph.count += 1
            status, _, payload = call(port, "GET", f"/api/files/{fid}", headers_for(seed, ("user", uid, None)))
            obj = as_json(payload)
            if status != 200 or not isinstance(obj, dict) or obj.get("name") != f["name"]:
                ph.fail(f"after the refused requests, {f['name']} reads as {status} {payload[:80]!r}", "sweep")
    finally:
        stop(proc, port)
    ph.count += 1
    try:
        changed = [t for t, rows in snapshot(db_path, stage_name()).items() if rows != SEED_SNAPSHOT[t]]
    except Exception as e:
        changed = [f"unreadable ({type(e).__name__}: {e})"]
    if changed:
        ph.fail(f"database changed by refused requests: {', '.join(changed)}", "db_changed")
    ph.summary()
    return ph


def run_second(seed, sub, deny, allow, refs):
    """Run 2: the permitted reads shuffled with MIXED_REFUSALS refused reads, then the permitted writes, each preceded
    by a few refused requests (reads and writes) drawn from the rest of the refusal list."""
    ph = Phase("run2")
    rng = random.Random(RNG_SEED + 3)
    pool = list(range(len(deny)))
    rng.shuffle(pool)
    mixed = [i for i in pool if deny[i]["kind"] not in WRITE_KINDS][:MIXED_REFUSALS]
    chosen = set(mixed)
    noise = [deny[i] for i in pool if i not in chosen]
    plan = [("refused", deny[i]) for i in mixed] + [("permitted", i) for i in range(len(allow))]
    rng.shuffle(plan)
    proc, port = start(sub, stage_db())
    if proc is None:
        ph.fail("the service did not start", "start")
        return ph
    try:
        for mode, x in plan:
            if ph.over():
                ph.fail("time cap reached before all requests of run 2 ran", "time_cap")
                break
            ph.count += 1
            if mode == "refused":
                check_refusal(seed, ph, port, x)
            else:
                check_permitted(seed, ph, port, allow[x], refs.get(x))
        if not ph.over():
            run_writes(seed, port, ph, noise)
    finally:
        stop(proc, port)
    ph.summary()
    return ph


def run_writes(seed, port, ph, noise):
    """Permitted writes in a fixed order, effects checked over HTTP (PERMISSIONS.md sections 2, 3, 5; API.md).
    Before every request here, 3-12 refused requests from `noise` (a seeded count), so permitted writes never come
    alone: a service that permits every write in this run fails the refused ones."""
    rng = random.Random(RNG_SEED + 1)        # which files the writes use, and the new names
    nrng = random.Random(RNG_SEED + 4)       # how many refused requests come before each request
    users = sorted(seed["users"])
    roles = seed["roles"]
    single = [u for u in users if len(roles.get(u, {})) == 1]
    multi = [u for u in users if len(roles.get(u, {})) >= 2]
    linked = {s["file_id"] for s in seed["shares"].values()}
    live = {}                                # org -> [(token, file_id)] of seed links that work
    for tok in sorted(seed["shares"]):
        s = seed["shares"][tok]
        if policy.share_link_works(seed, tok):
            live.setdefault(seed["files"][s["file_id"]]["org_id"], []).append((tok, s["file_id"]))
    used = set()
    sent = {"permitted": 0, "refused": 0, "skipped": 0}

    def home(u):
        return seed["users"][u]["home_org_id"]

    def second(u):
        return sorted(o for o in roles[u] if o != home(u))[0]

    def take(org):
        f = rng.choice(sorted(i for i, x in seed["files"].items() if x["org_id"] == org and i not in used | linked))
        used.add(f)
        return f

    def take_linked(org, tag):
        """A working seed link of org whose file no other step uses; None (step skipped, logged) if there is none:
        never on the hidden seed (the "write list" log line counts skipped steps), possible on another seed."""
        cands = [(t, f) for t, f in live.get(org, []) if f not in used]
        if not cands:
            sent["skipped"] += 1
            kit.log(f"note: step '{tag}' skipped, no working seed link left in org {org}")
            return None, None
        t, f = rng.choice(cands)
        used.add(f)
        return t, f

    def send(ctx, method, path, body=None):
        for _ in range(nrng.randint(*NOISE)):
            if not noise or ph.over():
                break
            ph.count += 1
            sent["refused"] += 1
            check_refusal(seed, ph, port, noise.pop(), "noise_")
        if ph.over():             # at most one request runs past the cap (DESIGN.md section 5)
            ph.fail("time cap reached during the write list", "time_cap")
            return None, {}, b"time cap reached"
        ph.count += 1
        sent["permitted"] += 1
        return call(port, method, path, headers_for(seed, ctx), body, retry=method == "GET")

    def step(desc, ctx, method, path, body=None, ok=(200, 201, 204)):
        if ph.over():
            ph.fail(f"time cap reached before {desc}", "time_cap")
            return False
        status, _, payload = send(ctx, method, path, body)
        if status not in ok:
            ph.fail(f"{desc}: {method} {path} as {label(seed, ctx)} got {status} {payload[:80]!r}",
                    "write_" + desc.split(" (")[0].replace(" ", "_"))
            return False          # already counted as a failure
        return as_json(payload)

    def refused(desc, ctx, method, path, body=None):
        if ph.over():
            return
        status, _, payload = send(ctx, method, path, body)
        if status is None or not 400 <= status < 500:
            ph.fail(f"{desc}: {method} {path} as {label(seed, ctx)} got {status} {payload[:80]!r}, expected a 4xx",
                    "write_" + desc.split(" (")[0].replace(" ", "_"))

    def link_works(desc, token, fid):
        if ph.over():
            return
        status, _, payload = send(None, "GET", f"/s/{token}")
        if status != 200 or payload != seed["files"][fid]["content"]:
            ph.fail(f"{desc}: anonymous GET /s/<token> got {status}, expected the file's bytes", "write_link_works")

    def link_dead(desc, token):
        if ph.over():
            return
        status, _, _ = send(None, "GET", f"/s/{token}")
        if status is None or not 400 <= status < 500:
            ph.fail(f"{desc}: the link still answers {status}", "write_link_dead")

    def assert_policy(decision, what):
        if decision != "allow":
            raise RuntimeError(f"grader bug: {what} is not permitted")

    def as_file(fid, name):
        return {**{k: seed["files"][fid][k] for k in FILE_FIELDS}, "name": name}

    def rename(ctx, org, tag):
        fid = take(org)
        assert_policy(policy.can_file(seed, ctx, "rename", fid), f"rename {fid} for {ctx}")
        new = f"renamed-{rng.getrandbits(32):08x}.md"      # the same pattern as the refused renames
        out = step(f"rename ({tag})", ctx, "PATCH", f"/api/files/{fid}", {"name": new}, ok=(200,))
        if out is not False and pick(out, FILE_FIELDS) != as_file(fid, new):
            ph.fail(f"rename ({tag}): response {out!r:.120}, expected the updated File", "write_rename")
        got = step(f"read after rename ({tag})", ctx, "GET", f"/api/files/{fid}", ok=(200,))
        if got is not False and pick(got, FILE_FIELDS) != as_file(fid, new):
            ph.fail(f"rename ({tag}): file reads back as {got!r:.120}", "write_rename")

    def bad_bodies(ctx, org, tag):
        """API.md: a bad name or a malformed body gets 400 (any 4xx accepted) and changes nothing."""
        fid = take(org)
        assert_policy(policy.can_file(seed, ctx, "rename", fid), f"rename {fid} for {ctx}")
        for bad in ("bad/name.md", ""):
            refused(f"bad name ({tag})", ctx, "PATCH", f"/api/files/{fid}", {"name": bad})
        got = step(f"read after bad name ({tag})", ctx, "GET", f"/api/files/{fid}", ok=(200,))
        if got is not False and pick(got, FILE_FIELDS) != as_file(fid, seed["files"][fid]["name"]):
            ph.fail(f"bad name ({tag}): file reads back as {got!r:.120}", "write_bad_name")
        refused(f"bad export body ({tag})", ctx, "POST", "/api/export", {"file_ids": fid})
        refused(f"bad export body ({tag})", ctx, "POST", "/api/export", {"file_ids": []})

    def share_cycle(creator, revoker, outsider, org, tag):
        """A new link works anonymously; an outsider cannot revoke it; the revoker can; then it is dead."""
        fid = take(org)
        assert_policy(policy.can_file(seed, creator, "share", fid), f"share {fid} for {creator}")
        out = step(f"create link ({tag})", creator, "POST", f"/api/files/{fid}/shares", ok=(200, 201))
        if out is False:
            return
        token = out.get("token") if isinstance(out, dict) else None
        if not isinstance(token, str) or not token:
            ph.fail(f"create link ({tag}): no token in the response", "write_create_link")
            return
        if (out.get("file_id") != fid or out.get("url") != f"/s/{token}"
                or not isinstance(out.get("created_at"), str) or not ISO_RE.fullmatch(out["created_at"])):
            ph.fail(f"create link ({tag}): response {out!r:.160}, expected token, url /s/<token>, file_id and an "
                    "ISO 8601 created_at (API.md)", "write_create_link")
        link_works(f"new link ({tag})", token, fid)
        if policy.can_file(seed, outsider, "share", fid) != "deny":
            raise RuntimeError(f"grader bug: {outsider} may share {fid}")
        refused(f"outsider revoke ({tag})", outsider, "DELETE", f"/api/shares/{token}")
        link_works(f"link after a refused revoke ({tag})", token, fid)
        assert_policy(policy.can_file(seed, revoker, "share", fid), f"revoke on {fid} for {revoker}")
        if step(f"revoke link ({tag})", revoker, "DELETE", f"/api/shares/{token}") is not False:
            link_dead(f"revoked link ({tag})", token)

    def revoke_seed_link(ctx, org, tag):
        token, fid = take_linked(org, f"revoke seed link ({tag})")
        if token is None:
            return
        assert_policy(policy.can_revoke(seed, ctx, token), f"revoke {token} for {ctx}")
        link_works(f"seed link ({tag})", token, fid)
        if step(f"revoke seed link ({tag})", ctx, "DELETE", f"/api/shares/{token}") is not False:
            link_dead(f"revoked seed link ({tag})", token)

    def delete(ctx, org, tag, with_link=False):
        token, fid = take_linked(org, f"delete ({tag})") if with_link else (None, take(org))
        if fid is None:
            return
        assert_policy(policy.can_file(seed, ctx, "delete", fid), f"delete {fid} for {ctx}")
        if step(f"delete ({tag})", ctx, "DELETE", f"/api/files/{fid}") is False:
            return
        status, _, _ = send(ctx, "GET", f"/api/files/{fid}")
        if status is None or not 400 <= status < 500:
            ph.fail(f"delete ({tag}): the file still reads as {status}", "write_delete")
        lst = step(f"list after delete ({tag})", ctx, "GET", "/api/files", ok=(200,))
        if lst is not False:
            listed = lst.get("files") if isinstance(lst, dict) else None
            if not isinstance(listed, list) or any(isinstance(x, dict) and x.get("id") == fid for x in listed):
                ph.fail(f"delete ({tag}): the file is still listed (or the list is unreadable)", "write_delete")
        if token:
            link_dead(f"link of a deleted file ({tag})", token)

    member = next(u for u in single if "member" in roles[u].values())
    admin = next(u for u in single if "org_admin" in roles[u].values())
    org = home(member)
    peer = next(u for u in users if u != member and org in roles.get(u, {}))
    outsider = next(u for u in single if home(u) != org)
    support = next(u for u in users if seed["users"][u]["is_support"])
    rename(("user", member, None), org, "member")
    rename(("user", admin, None), home(admin), "org_admin")
    for u in multi:
        rename(("user", u, second(u)), second(u), "second-org")
    bad_bodies(("user", member, None), org, "member")
    share_cycle(("user", member, None), ("user", peer, org), ("user", outsider, None), org, "member")
    for u in multi:
        share_cycle(("user", u, second(u)), ("user", u, second(u)), ("user", support, second(u)), second(u),
                    "second-org")
    for u in multi:
        revoke_seed_link(("user", u, second(u)), second(u), "second-org")
    delete(("user", admin, None), home(admin), "org_admin")
    delete(("user", admin, None), home(admin), "org_admin, file with a link", with_link=True)
    for u in multi:
        for o in sorted(roles[u]):
            if roles[u][o] == "org_admin" and o != home(u):
                delete(("user", u, o), o, "second-org org_admin")
    admin2 = next((u for u in single if "org_admin" in roles[u].values() and u != admin
                   and any(f not in used for _, f in live.get(home(u), []))), admin)
    revoke_seed_link(("user", admin2, None), home(admin2), "org_admin")
    kit.log(f"write list: {sent['permitted']} requests, with {sent['refused']} refused requests mixed in; "
            f"{sent['skipped']} steps skipped")


# ---------------------------------------------------------------- main
def check_sums():
    bad = []
    with open(os.path.join(TESTS, "SHA256SUMS")) as fh:
        for line in fh:
            digest, rel = line.split(None, 1)
            with open(os.path.join(TESTS, rel.strip()), "rb") as f:
                if hashlib.sha256(f.read()).hexdigest() != digest:
                    bad.append(rel.strip())
    if bad:
        raise RuntimeError(f"hidden inputs do not match SHA256SUMS: {bad}")


SEED_SNAPSHOT = {}


def grade():
    t0 = time.monotonic()
    check_sums()
    sub = kit.prepare_submission()
    seed = load_seed()
    SEED_SNAPSHOT.update(snapshot_seed())
    deny, allow = build_cases(seed)
    kit.log(f"{len(deny)} refusal cases, {len(allow)} permitted reads")
    refs = run_original(seed, allow)
    ph1 = run_first(seed, sub, deny, allow, refs)
    ph2 = run_second(seed, sub, deny, allow, refs)
    ok = not ph1.failures and not ph2.failures
    metrics = {"run1_checks": ph1.count, "run1_failed": len(ph1.failures), "run2_checks": ph2.count,
               "run2_failed": len(ph2.failures), "leaking_refusals": ph1.leaks + ph2.leaks,
               "grading_seconds": round(time.monotonic() - t0, 2)}
    metrics.update({f"run1_fail_{k}": v for k, v in ph1.cats.items()})
    metrics.update({f"run2_fail_{k}": v for k, v in ph2.cats.items()})
    return (1 if ok else 0), metrics


def snapshot_seed():
    con = sqlite3.connect(f"file:{SEED_DB}?mode=ro&immutable=1", uri=True)
    try:
        return read_tables(con)
    finally:
        con.close()


if __name__ == "__main__":
    kit.main(grade)
