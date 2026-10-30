"""Build a development database: python -m docshare.seed --out data/docshare.db [--force].

Everything comes from one seeded random generator, so the same spec always gives the same rows.
"""
import argparse
import base64
import os
import random
import re
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta, timezone

from .db import SCHEMA

DEV_SPEC = {
    "seed": 4242,
    "orgs": ["Halden & Price LLP", "Marlow Community Clinic", "Tessaract Robotics"],
    "folders": ["Board", "Contracts", "Finance", "Operations", "People"],
    "folders_per_org": 3,
    "files_per_org": 10,
    "users": [
        {"name": "Anna Lindqvist", "email": "anna@haldenprice.example", "home": 0, "orgs": {0: "org_admin"}},
        {"name": "Ben Carver", "email": "ben@haldenprice.example", "home": 0, "orgs": {0: "member"}},
        {"name": "Chloe Ndiaye", "email": "chloe@marlowclinic.example", "home": 1, "orgs": {1: "org_admin"}},
        {"name": "Dev Patel", "email": "dev@marlowclinic.example", "home": 1, "orgs": {1: "member"}},
        {"name": "Elena Rossi", "email": "elena@tessaract.example", "home": 2, "orgs": {2: "org_admin"}},
        {"name": "Felix Brandt", "email": "felix@tessaract.example", "home": 2, "orgs": {2: "member"}},
        {"name": "Grace Okafor", "email": "grace@okafor-consulting.example", "home": 1,
         "orgs": {1: "member", 2: "org_admin"}},
        {"name": "Riley Chen", "email": "riley@support.docshare.example", "home": None, "orgs": {}, "support": True},
    ],
    "shares": 6,
    "revoked_shares": 2,
}

TITLES = ["Board minutes", "Vendor contract", "Payroll summary", "Incident review", "Quarterly forecast",
          "Lease renewal", "Hiring plan", "Insurance certificate", "Audit findings", "Pricing proposal",
          "Data retention policy", "Customer escalation log", "Travel policy", "Project charter",
          "Security questionnaire", "Budget variance", "Supplier onboarding", "Litigation hold notice",
          "Capacity plan", "Expense report", "Training records", "Risk register", "Offsite agenda",
          "Severance terms", "Grant application", "Maintenance schedule", "Procurement request",
          "Patient intake checklist", "Firmware release notes", "Settlement draft"]
SENTENCES = ["Figures are provisional until the month-end close.",
             "Action items are tracked in the operations folder.",
             "Circulate only to the people named on the distribution list.",
             "The previous version is superseded by this document.",
             "Comments are due by the end of next week.",
             "Amounts are in the organisation's reporting currency.",
             "Approval is recorded in the minutes of the next meeting.",
             "Personal data in this file falls under the retention policy.",
             "Questions go to the document owner named above.",
             "This summary was prepared from the source systems on the date shown."]


def _uuid(rng):
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _when(rng, base=datetime(2026, 3, 2, 8, 0, tzinfo=timezone.utc)):
    return (base + timedelta(minutes=rng.randrange(0, 200 * 24 * 60))).strftime("%Y-%m-%dT%H:%M:%SZ")


def _later(stamp, days):
    t = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=days)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _content(rng, title, org_name, owner, marker, ext):
    date = _when(rng)[:10]
    body = " ".join(rng.sample(SENTENCES, rng.randint(2, 4)))
    if ext == "csv":
        rows = "\n".join(f"{rng.choice(['travel', 'software', 'hardware', 'services', 'facilities'])},"
                         f"{rng.randint(100, 99999)}.{rng.randint(0, 99):02d}" for _ in range(rng.randint(3, 6)))
        text = f"ref,{marker}\norganisation,{org_name}\nowner,{owner}\ncategory,amount\n{rows}\n"
        return text.encode(), "text/csv"
    text = f"# {title}\nOrganisation: {org_name}\nRef: {marker}\nOwner: {owner}\nDate: {date}\n\n{body}\n"
    return text.encode(), ("text/markdown" if ext == "md" else "text/plain")


def build(path, spec):
    """Create a new database at path from spec; returns a summary dict (ids, tokens, markers) for tooling."""
    rng = random.Random(spec["seed"])
    if os.path.exists(path):
        raise FileExistsError(path)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    orgs = [{"id": _uuid(rng), "name": n} for n in spec["orgs"]]
    conn.executemany("INSERT INTO orgs (id, name) VALUES (?, ?)", [(o["id"], o["name"]) for o in orgs])
    users = []
    for u in spec["users"]:
        rec = {"id": _uuid(rng), "name": u["name"], "email": u["email"], "token": "dsk_%032x" % rng.getrandbits(128),
               "home_org_id": orgs[u["home"]]["id"] if u.get("home") is not None else None,
               "is_support": 1 if u.get("support") else 0,
               "orgs": {orgs[i]["id"]: role for i, role in u.get("orgs", {}).items()}}
        users.append(rec)
        conn.execute("INSERT INTO users (id, email, name, token, home_org_id, is_support) VALUES (?, ?, ?, ?, ?, ?)",
                     (rec["id"], rec["email"], rec["name"], rec["token"], rec["home_org_id"], rec["is_support"]))
        for org_id, role in rec["orgs"].items():
            conn.execute("INSERT INTO memberships (user_id, org_id, role) VALUES (?, ?, ?)", (rec["id"], org_id, role))
    folders, files, markers = [], [], set()
    titles = list(TITLES)
    rng.shuffle(titles)
    for o in orgs:
        names = rng.sample(spec["folders"], spec["folders_per_org"])
        org_folders = [{"id": _uuid(rng), "org_id": o["id"], "name": n} for n in names]
        folders += org_folders
        conn.executemany("INSERT INTO folders (id, org_id, name) VALUES (?, ?, ?)",
                         [(f["id"], f["org_id"], f["name"]) for f in org_folders])
        people = [u for u in users if o["id"] in u["orgs"]]
        for _ in range(spec["files_per_org"]):
            title = titles.pop() if titles else rng.choice(TITLES)
            if not titles:
                titles = list(TITLES)
                rng.shuffle(titles)
            ext = rng.choice(["md", "md", "txt", "csv"])
            marker = "DSM-%016X" % rng.getrandbits(64)
            assert marker not in markers
            markers.add(marker)
            owner = rng.choice(people)
            content, mime = _content(rng, title, o["name"], owner["name"], marker, ext)
            rec = {"id": _uuid(rng), "org_id": o["id"], "folder_id": rng.choice(org_folders)["id"],
                   "name": f"{_slug(title)}-{rng.getrandbits(16):04x}.{ext}", "mime_type": mime,
                   "size": len(content), "uploaded_by": owner["id"], "created_at": _when(rng), "marker": marker}
            files.append(rec)
            conn.execute("INSERT INTO files (id, org_id, folder_id, name, mime_type, size, content, uploaded_by, "
                         "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (rec["id"], rec["org_id"], rec["folder_id"], rec["name"], rec["mime_type"], rec["size"],
                          content, rec["uploaded_by"], rec["created_at"]))
    shares = []
    for i, f in enumerate(rng.sample(files, spec["shares"])):
        creator = rng.choice([u for u in users if f["org_id"] in u["orgs"]])
        created = _when(rng)
        rec = {"token": base64.urlsafe_b64encode(rng.randbytes(18)).decode(), "file_id": f["id"],
               "created_by": creator["id"], "created_at": created,
               "revoked_at": _later(created, rng.randint(1, 20)) if i < spec["revoked_shares"] else None}
        shares.append(rec)
        conn.execute("INSERT INTO shares (token, file_id, created_by, created_at, revoked_at) VALUES (?, ?, ?, ?, ?)",
                     (rec["token"], rec["file_id"], rec["created_by"], rec["created_at"], rec["revoked_at"]))
    conn.commit()
    conn.close()
    return {"orgs": orgs, "users": users, "folders": folders, "files": files, "shares": shares}


def main(argv=None):
    p = argparse.ArgumentParser(description="build a docshare development database")
    p.add_argument("--out", required=True)
    p.add_argument("--force", action="store_true", help="replace an existing file")
    args = p.parse_args(argv)
    if os.path.exists(args.out):
        if not args.force:
            sys.exit(f"{args.out} exists (use --force)")
        os.remove(args.out)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    s = build(args.out, DEV_SPEC)
    print(f"wrote {args.out}: {len(s['orgs'])} orgs, {len(s['users'])} users, {len(s['files'])} files")


if __name__ == "__main__":
    main()
