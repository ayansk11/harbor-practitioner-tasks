"""Bulk export: several files in one JSON response (used by the "Download selected" button)."""
import base64

from flask import Blueprint, abort, g, jsonify, request

from .. import db
from ..auth import login_required

bp = Blueprint("export", __name__)

MAX_IDS = 50


@bp.post("/api/export")
@login_required
def export():
    body = request.get_json(silent=True) or {}
    ids = body.get("file_ids")
    if not isinstance(ids, list) or not (1 <= len(ids) <= MAX_IDS) or not all(isinstance(i, str) for i in ids):
        abort(400, description="bad_file_ids")
    # A selection always comes from one folder view, so the first file tells us whose files these are.
    first = db.query_one("SELECT org_id FROM files WHERE id = ?", (ids[0],))
    if first is None:
        abort(404)
    if not g.identity.is_support and first["org_id"] != g.identity.org_id:
        abort(404)
    out = []
    for file_id in ids:
        row = db.query_one("SELECT id, name, mime_type, size, content FROM files WHERE id = ?", (file_id,))
        if row is None:
            abort(404)
        out.append({"id": row["id"], "name": row["name"], "mime_type": row["mime_type"], "size": row["size"],
                    "content_b64": base64.b64encode(bytes(row["content"])).decode("ascii")})
    return jsonify(files=out)
