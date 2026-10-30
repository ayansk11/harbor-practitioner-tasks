"""SQLite access. One connection per request (see app.py); rows come back as sqlite3.Row."""
import sqlite3

from flask import g

SCHEMA = """
CREATE TABLE IF NOT EXISTS orgs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    home_org_id TEXT REFERENCES orgs(id),
    is_support INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS memberships (
    user_id TEXT NOT NULL REFERENCES users(id),
    org_id TEXT NOT NULL REFERENCES orgs(id),
    role TEXT NOT NULL CHECK (role IN ('member', 'org_admin')),
    PRIMARY KEY (user_id, org_id)
);
CREATE TABLE IF NOT EXISTS folders (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES orgs(id),
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES orgs(id),
    folder_id TEXT NOT NULL REFERENCES folders(id),
    name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    content BLOB NOT NULL,
    uploaded_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shares (
    token TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(id),
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    revoked_at TEXT
);
CREATE INDEX IF NOT EXISTS files_org ON files(org_id, name);
CREATE INDEX IF NOT EXISTS files_folder ON files(folder_id, name);
CREATE INDEX IF NOT EXISTS shares_file ON shares(file_id);
"""

FILE_COLUMNS = "id, org_id, folder_id, name, mime_type, size, uploaded_by, created_at"


def connect(path):
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def get_db():
    if "db" not in g:
        from flask import current_app
        g.db = connect(current_app.config["DB_PATH"])
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def query_one(sql, params=()):
    return get_db().execute(sql, params).fetchone()


def query_all(sql, params=()):
    return get_db().execute(sql, params).fetchall()


def execute(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    return cur.rowcount


def file_json(row):
    return {"id": row["id"], "org_id": row["org_id"], "folder_id": row["folder_id"], "name": row["name"],
            "mime_type": row["mime_type"], "size": row["size"], "uploaded_by": row["uploaded_by"],
            "created_at": row["created_at"]}


def folder_json(row):
    return {"id": row["id"], "org_id": row["org_id"], "name": row["name"]}
