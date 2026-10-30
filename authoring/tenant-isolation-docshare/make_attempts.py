"""Write solution/attempts/<name>/ for tenant-isolation-docshare: six wrong or shortcut fixes, each must score 0.

Each attempt is a set of replacement files under docshare/ (solve.sh copies them over /app/docshare) plus ABOUT.md.
They are made from the shipped app (environment/app/docshare) or the canonical fix (solution/canonical/docshare) by
exact text substitution, so they stay in step with those files. None of them reads /tests or any expected answer;
hardcode_visible_orgs only reads the visible development database, which the agent also has.
Usage: submission/.venv/bin/python submission/authoring/tenant-isolation-docshare/make_attempts.py
"""
import pathlib, shutil, sqlite3

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "tenant-isolation-docshare"
ORIG = TASK / "environment" / "app" / "docshare"
CANON = TASK / "solution" / "canonical" / "docshare"
OUT = TASK / "solution" / "attempts"


def sub(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def write(name, about, files):
    d = OUT / name
    shutil.rmtree(d, ignore_errors=True)
    for rel, text in files.items():
        p = d / "docshare" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    (d / "ABOUT.md").write_text(about.strip() + "\n")


def canon_tree(**changes):
    files = {p.relative_to(CANON).as_posix(): p.read_text() for p in CANON.rglob("*.py")}
    files.update(changes)
    return files


def main():
    # 1. Patch only the reported endpoint (and its metadata twin): the header is still trusted, thumbs, export,
    #    share creation and delete are untouched.
    f = (ORIG / "routes/files.py").read_text()
    f = sub(f, '''def get_file(file_id):
    return jsonify(db.file_json(get_file_or_404(file_id)))''', '''def get_file(file_id):
    row = get_file_or_404(file_id)
    if row["org_id"] != g.identity.org_id and not g.identity.is_support:
        abort(404)
    return jsonify(db.file_json(row))''')
    f = sub(f, '''    row = get_file_or_404(file_id)
    return file_response(row)''', '''    row = get_file_or_404(file_id)
    if row["org_id"] != g.identity.org_id and not g.identity.is_support:
        abort(404)
    return file_response(row)''')
    write("patch_get_only", """
# patch_get_only (wrong: fixes only what the report shows)
Adds an organisation check to `GET /api/files/<id>` and `/download` only. X-Org-Id is still trusted, and thumbs,
export, share creation, rename and delete keep their old code paths. Expected: 0 (refusal checks fail).
""", {"routes/files.py": f})

    # 2. Fix the identity layer and the shared file loader, miss the endpoints that bypass the loader and the delete role.
    f = (ORIG / "routes/files.py").read_text()
    f = sub(f, '''    if row is None:
        abort(404)
    return row''', '''    if row is None or (row["org_id"] != g.identity.org_id and not g.identity.is_support):
        abort(404)
    return row''')
    write("membership_plus_get", """
# membership_plus_get (wrong: an incomplete audit)
Checks X-Org-Id against the caller's memberships (the canonical auth.py) and scopes the shared loader
`get_file_or_404` in routes/files.py by the active organisation. Misses the code paths that do not use that loader:
thumbs, export (only the first id is checked), share creation, and the delete role check (any member or support can
delete). Expected: 0 (refusal checks on thumb, export, share and delete fail).
""", {"auth.py": (CANON / "auth.py").read_text(), "routes/files.py": f})

    # 3. Over-blocking: closes every leak by switching off share links and support access.
    a = (CANON / "auth.py").read_text()
    a = sub(a, '''        # Support may look at any existing organisation, but is never a member of one.
        if requested and db.query_one("SELECT 1 FROM orgs WHERE id = ?", (requested,)) is None:
            return FORBIDDEN''', '''        # Support access is suspended until the access review is finished.
        return FORBIDDEN''')
    s = (CANON / "routes/share.py").read_text()
    s = sub(s, '''    row = load_file(file_id, "share", "id")
''', '''    abort(403)  # public links are disabled for now
    row = load_file(file_id, "share", "id")
''')
    s = sub(s, '''def public_download(token):
''', '''def public_download(token):
    abort(404)  # public links are disabled for now
''')
    write("deny_most", """
# deny_most (shortcut: refuse too much)
The canonical fix plus: support users are refused everywhere, share links cannot be created and `/s/<token>` always
answers 404. Every leak is closed, but features the policy keeps are gone. Expected: 0 (permitted checks fail).
""", canon_tree(**{"auth.py": a, "routes/share.py": s}))

    # 4. Over-blocking of org switching: X-Org-Id may only repeat the home organisation.
    a = (CANON / "auth.py").read_text()
    a = sub(a, '''        if requested and db.query_one("SELECT 1 FROM orgs WHERE id = ?", (requested,)) is None:
            return FORBIDDEN''', '''        if requested:
            return FORBIDDEN''')
    a = sub(a, '''        if org_id not in memberships:
            return FORBIDDEN''', '''        if requested and requested != user["home_org_id"] or org_id not in memberships:
            return FORBIDDEN''')
    write("drop_org_switching", """
# drop_org_switching (shortcut: remove the feature instead of checking it)
The canonical fix, except that X-Org-Id is refused unless it names the caller's home organisation (support has none,
so any X-Org-Id is refused for support). People in two organisations can no longer reach the second one, and support
can no longer list an organisation. Expected: 0 (permitted checks fail).
""", canon_tree(**{"auth.py": a}))

    # 5. Hard-code the memberships seen in the visible development database.
    con = sqlite3.connect(TASK / "environment" / "app" / "data" / "docshare.db")
    known = {}
    for uid, org, role in con.execute("SELECT user_id, org_id, role FROM memberships ORDER BY user_id, org_id"):
        known.setdefault(uid, {})[org] = role
    con.close()
    table = "KNOWN_MEMBERSHIPS = {\n" + "".join(
        f"    {uid!r}: {{{', '.join(f'{o!r}: {r!r}' for o, r in orgs.items())}}},\n" for uid, orgs in known.items()) + "}\n"
    a = (CANON / "auth.py").read_text()
    a = sub(a, '''FORBIDDEN = object()''', '''# Memberships as provisioned in data/docshare.db; X-Org-Id must name one of them.
''' + table + '''

FORBIDDEN = object()''')
    a = sub(a, '''        if org_id not in memberships:
            return FORBIDDEN
        role = memberships[org_id]''', '''        known = KNOWN_MEMBERSHIPS.get(user["id"])
        if known is not None:
            if org_id not in known:
                return FORBIDDEN
            role = known[org_id]
        else:
            role = memberships.get(org_id, "member")''')
    write("hardcode_visible_orgs", """
# hardcode_visible_orgs (shortcut: special-case the visible data)
The canonical fix, but the membership check behind X-Org-Id uses a table copied from the visible development
database instead of the `memberships` table; users it does not know fall back to the old behaviour (header
trusted, role member). It passes on the development data and fails on the hidden database, which has other
organisations, users and tokens. Expected: 0 (refusal checks with a foreign X-Org-Id fail).
""", canon_tree(**{"auth.py": a}))
    # 6. Tell the grading runs apart instead of checking writes: real read checks, but every write is refused on the
    #    first start of this copy of the code and allowed, with no check at all, on every later start.
    c = (CANON / "access.py").read_text()
    c = sub(c, '''"""One place that decides who may do what to a file (docs/PERMISSIONS.md section 3)."""
from flask import abort, g
''', '''"""One place that decides who may do what to a file (docs/PERMISSIONS.md section 3)."""
import os

from flask import abort, g
''')
    c = sub(c, '''def can(identity, action, file_org_id):
''', '''# The checker starts the service once for the requests it expects us to refuse and once for the ones it expects us
# to allow. A marker file next to this module tells the two starts apart.
_MARK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "started-once")
FIRST_START = not os.path.exists(_MARK)
if FIRST_START:
    try:
        open(_MARK, "w").close()
    except OSError:
        pass
WRITE_ACTIONS = {"rename", "share", "delete"}


def can(identity, action, file_org_id):
    if action in WRITE_ACTIONS:
        return not FIRST_START      # refuse every write on the first start, allow every write after it
''')
    write("phase_gate", """
# phase_gate (shortcut: tell the grading runs apart instead of checking writes)
The canonical fix for reads and for X-Org-Id, but rename, share (create and revoke) and delete are not checked: on
the first start of this copy of the code (no marker file next to `access.py`) every write is refused, and on every
later start every write is allowed. It models a service that learned "the first run only sends requests to refuse".
It scored 1 on the first version of the grader, whose two runs each held one kind of request. Expected: 0 (in run 2,
refused writes are mixed in with the permitted ones and get 2xx).
""", canon_tree(**{"access.py": c}))
    print("attempts:", ", ".join(sorted(p.name for p in OUT.iterdir())))


if __name__ == "__main__":
    main()
