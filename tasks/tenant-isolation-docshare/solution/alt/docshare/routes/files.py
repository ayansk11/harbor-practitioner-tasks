"""File endpoints: list, metadata, download, rename, delete.

Every query carries its own tenant scope: a file is only found if it belongs to the active organisation, or, for
the read-only endpoints, if the caller is support. Anything not found is refused with 403.
"""
from flask import Blueprint, Response, abort, g, jsonify, request

from .. import db
from ..auth import login_required, require_active_org

bp = Blueprint("files", __name__)

READ_SCOPE = "id = ? AND (org_id = ? OR ? = 1)"     # params: file_id, active org, is_support


def read_params(file_id):
    return (file_id, g.identity.org_id, 1 if g.identity.is_support else 0)


@bp.get("/api/files")
@login_required
def list_files():
    org_id = require_active_org()
    rows = db.query_all(f"SELECT {db.FILE_COLUMNS} FROM files WHERE org_id = ? ORDER BY name", (org_id,))
    return jsonify(files=[db.file_json(r) for r in rows])


@bp.get("/api/files/<file_id>")
@login_required
def get_file(file_id):
    row = db.query_one(f"SELECT {db.FILE_COLUMNS} FROM files WHERE {READ_SCOPE}", read_params(file_id))
    if row is None:
        abort(403)
    return jsonify(db.file_json(row))


@bp.get("/api/files/<file_id>/download")
@login_required
def download(file_id):
    row = db.query_one(f"SELECT name, mime_type, content FROM files WHERE {READ_SCOPE}", read_params(file_id))
    if row is None:
        abort(403)
    return file_response(row)


def file_response(row):
    resp = Response(bytes(row["content"]), mimetype=row["mime_type"])
    resp.headers["Content-Disposition"] = f'attachment; filename="{row["name"]}"'
    return resp


@bp.patch("/api/files/<file_id>")
@login_required
def rename(file_id):
    ident = g.identity
    if ident.role not in ("member", "org_admin"):
        abort(403)
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    exists = db.query_one("SELECT id FROM files WHERE id = ? AND org_id = ?", (file_id, ident.org_id))
    if exists is None:
        abort(403)
    if not isinstance(name, str) or not (1 <= len(name) <= 200) or "/" in name:
        abort(400, description="bad_name")
    db.execute("UPDATE files SET name = ? WHERE id = ? AND org_id = ?", (name, file_id, ident.org_id))
    row = db.query_one(f"SELECT {db.FILE_COLUMNS} FROM files WHERE id = ? AND org_id = ?", (file_id, ident.org_id))
    return jsonify(db.file_json(row))


@bp.delete("/api/files/<file_id>")
@login_required
def delete(file_id):
    ident = g.identity
    if ident.role != "org_admin":
        abort(403)
    conn = db.get_db()
    conn.execute("DELETE FROM shares WHERE file_id IN (SELECT id FROM files WHERE id = ? AND org_id = ?)",
                 (file_id, ident.org_id))
    gone = conn.execute("DELETE FROM files WHERE id = ? AND org_id = ?", (file_id, ident.org_id)).rowcount
    if gone == 0:
        conn.rollback()
        abort(403)
    conn.commit()
    return "", 204
