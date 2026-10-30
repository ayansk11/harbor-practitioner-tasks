# docshare

The document sharing API in front of the ingest worker's store: organisations, folders, files, share links and a
support console. Python 3.12, Flask, waitress, SQLite.

- Run: `python -m docshare.serve --db data/docshare.db --port 8080` (from /app).
- Fresh development database: `python -m docshare.seed --out data/docshare.db --force`.
- Feature tests: `python -m pytest -q tests`.
- Docs: `docs/API.md` (endpoints), `docs/PERMISSIONS.md` (who may do what), `docs/DEV_USERS.md` (development users
  and tokens).
- Open security report: `SECURITY_REPORT.md`.

Layout: `docshare/auth.py` (tokens and the active organisation), `docshare/routes/` (`files.py`, `folders.py`,
`thumbs.py`, `export.py`, `share.py`, `admin.py`), `docshare/db.py` (schema and helpers), `docshare/seed.py`
(development data).
