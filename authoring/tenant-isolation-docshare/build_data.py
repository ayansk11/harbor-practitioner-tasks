"""Authoring step: build every generated file of the tenant-isolation-docshare package (fixed seeds, no network).

Writes:
  environment/app/data/docshare.db   visible development database (DEV_SPEC in docshare/seed.py)
  environment/app/docs/DEV_USERS.md  the visible users and their development tokens
  environment/app/SECURITY_REPORT.md the researcher's report, with ids from the visible database
  tests/hidden/seed.db               hidden grading database (HIDDEN_SPEC below: other orgs, users, tokens, files)
  tests/original/docshare/           an untouched copy of the shipped app, the differential reference
  tests/SHA256SUMS                   sha256 of every file under tests/hidden and tests/original
Usage: submission/.venv/bin/python submission/authoring/tenant-isolation-docshare/build_data.py
"""
import hashlib, os, pathlib, shutil, sqlite3, sys

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "tenant-isolation-docshare"
APP = TASK / "environment" / "app"
TESTS = TASK / "tests"
sys.dont_write_bytecode = True
sys.path.insert(0, str(APP))
from docshare import seed  # noqa: E402  (the app's own generator, so the schema always matches)

HIDDEN_SPEC = {
    "seed": 90417,
    "orgs": ["Corvane Freight", "Ilse Varga Architects", "Northpine Dental Group", "Sable Point Credit Union"],
    "folders": ["Archive", "Board", "Clients", "Compliance", "Finance", "Projects"],
    "folders_per_org": 3,
    "files_per_org": 15,
    "users": [
        {"name": "Hugo Marsh", "email": "hugo@corvane.example", "home": 0, "orgs": {0: "org_admin"}},
        {"name": "Ines Duarte", "email": "ines@corvane.example", "home": 0, "orgs": {0: "member"}},
        {"name": "Jonas Weber", "email": "jonas@corvane.example", "home": 0, "orgs": {0: "member"}},
        {"name": "Kiri Tane", "email": "kiri@ilsevarga.example", "home": 1, "orgs": {1: "org_admin"}},
        {"name": "Lena Novak", "email": "lena@ilsevarga.example", "home": 1, "orgs": {1: "member"}},
        {"name": "Marco Bianchi", "email": "marco@ilsevarga.example", "home": 1, "orgs": {1: "member"}},
        {"name": "Nadia Haddad", "email": "nadia@northpine.example", "home": 2, "orgs": {2: "org_admin"}},
        {"name": "Omar Farouk", "email": "omar@northpine.example", "home": 2, "orgs": {2: "member"}},
        {"name": "Priya Raman", "email": "priya@sablepoint.example", "home": 3, "orgs": {3: "org_admin"}},
        {"name": "Quinn Doyle", "email": "quinn@sablepoint.example", "home": 3, "orgs": {3: "member"}},
        {"name": "Rosa Lindgren", "email": "rosa@lindgren-advisory.example", "home": 0,
         "orgs": {0: "member", 1: "org_admin"}},
        {"name": "Tomas Eriksen", "email": "tomas@eriksen-it.example", "home": 2,
         "orgs": {2: "org_admin", 3: "member"}},
        {"name": "Uma Sato", "email": "uma@support.docshare.example", "home": None, "orgs": {}, "support": True},
        {"name": "Victor Hale", "email": "victor@support.docshare.example", "home": None, "orgs": {}, "support": True},
    ],
    "shares": 12,
    "revoked_shares": 4,
}


def fresh(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    return path


def check_unique(summary):
    names = [f["name"] for f in summary["files"]]
    markers = [f["marker"] for f in summary["files"]]
    assert len(set(names)) == len(names), "file names must be unique"
    assert len(set(markers)) == len(markers), "markers must be unique"


def dev_users_md(s):
    org = {o["id"]: o["name"] for o in s["orgs"]}
    lines = ["# Development users", "",
             "Users in the development database `data/docshare.db` (built by `python -m docshare.seed`). The tokens",
             "are development fixtures only.", "",
             "| Name | Email | Home organisation | Memberships | Support | Token |", "|---|---|---|---|---|---|"]
    for u in s["users"]:
        ms = ", ".join(f"{org[o]} ({r})" for o, r in u["orgs"].items()) or "none"
        lines.append(f"| {u['name']} | {u['email']} | {org.get(u['home_org_id'], 'none')} | {ms} | "
                     f"{'yes' if u['is_support'] else 'no'} | `{u['token']}` |")
    lines += ["", "| Organisation | Id |", "|---|---|"] + [f"| {o['name']} | `{o['id']}` |" for o in s["orgs"]]
    return "\n".join(lines) + "\n"


def report_md(s):
    org = {o["id"]: o for o in s["orgs"]}
    ben = next(u for u in s["users"] if u["email"] == "ben@haldenprice.example")
    victim_org = next(o for o in s["orgs"] if o["name"] == "Marlow Community Clinic")
    target = next(f for f in s["files"] if f["org_id"] == victim_org["id"])
    return f"""# Security report: cross-organisation file download

Received 2026-10-21 through the vulnerability disclosure inbox. Reporter: an independent researcher testing our
staging stack with the development data. Severity claimed: high.

## Summary
A logged-in member of one organisation can download a file that belongs to a different organisation by changing the
file id in the download URL.

## Steps to reproduce (development database `data/docshare.db`)
1. Log in as Ben Carver, a member of {org[ben['home_org_id']]['name']} (token in `docs/DEV_USERS.md`).
2. `GET /api/files` lists only {org[ben['home_org_id']]['name']} files, as expected.
3. Request a file of {victim_org['name']}, an organisation Ben does not belong to:
   ```
   curl -s -H "Authorization: Bearer {ben['token']}" \\
     http://127.0.0.1:8080/api/files/{target['id']}/download
   ```
4. The response is `200` with the full contents of `{target['name']}`.

## Expected
The request is refused and no data of the other organisation is returned.

## Notes from triage
Reproduced on 2026-10-22. File ids are random UUIDs, but they appear in exports, logs and support tickets, so
they cannot be treated as secret.
"""


def sha_lines(root):
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(TESTS).as_posix()}")
    return out


def main():
    dev = seed.build(str(fresh(APP / "data" / "docshare.db")), seed.DEV_SPEC)
    check_unique(dev)
    (APP / "docs" / "DEV_USERS.md").write_text(dev_users_md(dev))
    (APP / "SECURITY_REPORT.md").write_text(report_md(dev))
    hidden = seed.build(str(fresh(TESTS / "hidden" / "seed.db")), HIDDEN_SPEC)
    check_unique(hidden)
    dev_tokens = {u["token"] for u in dev["users"]}
    assert not dev_tokens & {u["token"] for u in hidden["users"]}
    assert not {o["id"] for o in dev["orgs"]} & {o["id"] for o in hidden["orgs"]}
    for db in (APP / "data" / "docshare.db", TESTS / "hidden" / "seed.db"):
        con = sqlite3.connect(db)
        assert con.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        con.close()
    orig = TESTS / "original"
    shutil.rmtree(orig, ignore_errors=True)
    shutil.copytree(APP / "docshare", orig / "docshare", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    lines = sha_lines(TESTS / "hidden") + sha_lines(orig)
    (TESTS / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    print(f"dev: {len(dev['orgs'])} orgs, {len(dev['users'])} users, {len(dev['files'])} files, "
          f"{len(dev['shares'])} shares")
    print(f"hidden: {len(hidden['orgs'])} orgs, {len(hidden['users'])} users, {len(hidden['files'])} files, "
          f"{len(hidden['shares'])} shares; SHA256SUMS {len(lines)} entries")


if __name__ == "__main__":
    main()
