"""Second reader: the permission matrix written from environment/app/docs/PERMISSIONS.md alone.

This script does not import tests/policy.py or any app code. It parses the role table in PERMISSIONS.md section 3 and
encodes the prose rules of sections 1, 2, 4 and 5, then writes one decision for every (context, action, target) cell
over a seed database. diff_matrices.py asks tests/policy.py for the same cells and lists every disagreement.

Usage: python matrix_from_permissions.py <seed.db> <out.csv>
Decisions: allow | deny (403 or 404) | 401 | 400.
"""
import csv, os, pathlib, random, re, sqlite3, sys

HERE = pathlib.Path(__file__).resolve().parent
PERMS = pathlib.Path(os.environ.get("PERMS_PATH") or HERE.parents[1] / "tasks" / "tenant-isolation-docshare" /
                     "environment" / "app" / "docs" / "PERMISSIONS.md")
UNKNOWN_ORG = "00000000-0000-4000-8000-00000000dead"
UNKNOWN_FILE = "00000000-0000-4000-8000-00000000beef"


def parse_table(text):
    """Section 3 table -> {action: {"member": cell, "org_admin": cell, "support": cell}} (cells lower-cased)."""
    sec = text.split("## 3.", 1)[1].split("## 4.", 1)[0]
    rows = [l for l in sec.splitlines() if l.startswith("|")]
    head = [c.strip().lower() for c in rows[0].strip("|").split("|")]
    out = {}
    for line in rows[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        rec = dict(zip(head, cells))
        endpoints = re.findall(r"`([A-Z]+ [^`]+)`", rec["endpoints"])
        out[rec["action"].lower()] = {"member": rec["member"].lower(), "org_admin": rec["org_admin"].lower(),
                                      "support": rec["support"].lower(), "endpoints": endpoints}
    return out


def load_seed(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    q = lambda s: [dict(r) for r in con.execute(s)]
    seed = {"orgs": q("SELECT id, name FROM orgs"), "users": q("SELECT id, token, home_org_id, is_support FROM users"),
            "memberships": q("SELECT user_id, org_id, role FROM memberships"),
            "folders": q("SELECT id, org_id FROM folders"), "files": q("SELECT id, org_id, folder_id FROM files"),
            "shares": q("SELECT token, file_id, revoked_at FROM shares")}
    con.close()
    return seed


class Reader:
    def __init__(self, seed, table):
        self.t = table
        self.orgs = {o["id"] for o in seed["orgs"]}
        self.users = {u["id"]: u for u in seed["users"]}
        self.roles = {}
        for m in seed["memberships"]:
            self.roles.setdefault(m["user_id"], {})[m["org_id"]] = m["role"]
        self.files = {f["id"]: f for f in seed["files"]}
        self.folders = {f["id"]: f for f in seed["folders"]}
        self.shares = {s["token"]: s for s in seed["shares"]}

    # Section 1 and 2: who is asking, and in which organisation.
    def who(self, ctx):
        kind, uid, header = ctx
        if kind != "user":
            return "401", None, None
        u = self.users[uid]
        if u["is_support"]:
            if header is not None and header not in self.orgs:
                return "deny", None, None
            return "ok", header, "support"
        active = header if header is not None else u["home_org_id"]
        mine = self.roles.get(uid, {})
        if active not in mine:
            return "deny", None, None
        return "ok", active, mine[active]

    def cell(self, action, role):
        return self.t[action][role]

    def file_ok(self, action, role, active, file_id):
        f = self.files.get(file_id)
        if f is None:
            return False
        c = self.cell(action, role)
        if not c.startswith("yes"):
            return False
        if role == "support":
            return "any organisation" in c
        return f["org_id"] == active

    def decide(self, ctx, action, target):
        if action == "share_link":  # section 5: no login
            s = self.shares.get(target)
            ok = s is not None and s["revoked_at"] is None and s["file_id"] in self.files
            return "allow" if ok else "deny"
        state, active, role = self.who(ctx)
        if state != "ok":
            return state
        if action in ("read", "download", "thumb", "rename", "share", "delete"):
            return "allow" if self.file_ok(action, role, active, target) else "deny"
        if action == "revoke":
            s = self.shares.get(target)
            return "allow" if s is not None and self.file_ok("share", role, active, s["file_id"]) else "deny"
        if action == "export":
            ids = target.split("|")
            return "allow" if all(self.file_ok("read", role, active, i) for i in ids) else "deny"
        if action == "me":
            return "allow" if self.cell("who am i", role).startswith("yes") else "deny"
        if action == "admin_orgs":
            return "allow" if self.cell("support console", role).startswith("yes") else "deny"
        if action in ("list_files", "list_folders", "folder_files"):
            if not self.cell("list", role).startswith("yes"):
                return "deny"
            if active is None:
                return "400"  # support without X-Org-Id
            if action == "folder_files":
                fo = self.folders.get(target)
                return "allow" if fo is not None and fo["org_id"] == active else "deny"
            return "allow"
        raise ValueError(action)


def contexts(seed):
    out = [("anon", None, None), ("badtoken", None, None)]
    for u in sorted(seed["users"], key=lambda r: r["id"]):
        for h in [None] + sorted(o["id"] for o in seed["orgs"]) + [UNKNOWN_ORG]:
            out.append(("user", u["id"], h))
    return out


def grid(seed):
    """Every cell the two readers are compared on (export: all singletons plus 400 seeded random pairs and triples)."""
    files = sorted(f["id"] for f in seed["files"]) + [UNKNOWN_FILE]
    rng = random.Random(20261028)
    exports = [[f] for f in files]
    for _ in range(400):
        exports.append(rng.sample(files, rng.choice([2, 3])))
    for ctx in contexts(seed):
        for a in ("read", "download", "thumb", "rename", "share", "delete"):
            for f in files:
                yield ctx, a, f
        for s in sorted(x["token"] for x in seed["shares"]):
            yield ctx, "revoke", s
        for e in exports:
            yield ctx, "export", "|".join(e)
        for a in ("me", "admin_orgs", "list_files", "list_folders"):
            yield ctx, a, "-"
        for fo in sorted(x["id"] for x in seed["folders"]):
            yield ctx, "folder_files", fo
    for s in sorted(x["token"] for x in seed["shares"]):
        yield ("anon", None, None), "share_link", s


def main():
    seed = load_seed(sys.argv[1])
    table = parse_table(PERMS.read_text())
    r = Reader(seed, table)
    n = 0
    with open(sys.argv[2], "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "user_id", "header", "action", "target", "decision"])
        for ctx, a, t in grid(seed):
            w.writerow([ctx[0], ctx[1] or "", ctx[2] or "", a, t, r.decide(ctx, a, t)])
            n += 1
    print(f"second reader: {n} cells from {PERMS.name} ({len(table)} table rows) -> {sys.argv[2]}")


if __name__ == "__main__":
    main()
