"""File endpoints: list, metadata, download, rename, delete."""
from flask import Blueprint, Response, abort, g, jsonify, request

from .. import db
from ..auth import login_required, require_active_org

bp = Blueprint("files", __name__)


def get_file_or_404(file_id):
    row = db.query_one(f"SELECT {db.FILE_COLUMNS}, content FROM files WHERE id = ?", (file_id,))
    if row is None:
        abort(404)
    return row


@bp.get("/api/files")
@login_required
def list_files():
    org_id = require_active_org()
    rows = db.query_all(f"SELECT {db.FILE_COLUMNS} FROM files WHERE org_id = ? ORDER BY name", (org_id,))
    return jsonify(files=[db.file_json(r) for r in rows])


@bp.get("/api/files/<file_id>")
@login_required
def get_file(file_id):
    return jsonify(db.file_json(get_file_or_404(file_id)))


@bp.get("/api/files/<file_id>/download")
@login_required
def download(file_id):
    row = get_file_or_404(file_id)
    return file_response(row)


def file_response(row):
    resp = Response(bytes(row["content"]), mimetype=row["mime_type"])
    resp.headers["Content-Disposition"] = f'attachment; filename="{row["name"]}"'
    return resp


@bp.patch("/api/files/<file_id>")
@login_required
def rename(file_id):
    if g.identity.role not in ("member", "org_admin"):
        abort(403)
    row = get_file_or_404(file_id)
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not isinstance(name, str) or not (1 <= len(name) <= 200) or "/" in name:
        abort(400, description="bad_name")
    db.execute("UPDATE files SET name = ? WHERE id = ?", (name, row["id"]))
    return jsonify(db.file_json(get_file_or_404(row["id"])))


@bp.delete("/api/files/<file_id>")
@login_required
def delete(file_id):
    row = get_file_or_404(file_id)
    conn = db.get_db()
    conn.execute("DELETE FROM shares WHERE file_id = ?", (row["id"],))
    conn.execute("DELETE FROM files WHERE id = ?", (row["id"],))
    conn.commit()
    return "", 204
