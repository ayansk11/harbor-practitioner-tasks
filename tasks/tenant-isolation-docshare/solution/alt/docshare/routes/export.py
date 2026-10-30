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
    ident = g.identity
    marks = ", ".join("?" for _ in ids)
    rows = db.query_all(f"SELECT id, name, mime_type, size, content FROM files WHERE id IN ({marks}) "
                        "AND (org_id = ? OR ? = 1)", (*ids, ident.org_id, 1 if ident.is_support else 0))
    found = {r["id"]: r for r in rows}
    if any(i not in found for i in ids):
        abort(403)      # all or nothing
    out = [{"id": r["id"], "name": r["name"], "mime_type": r["mime_type"], "size": r["size"],
            "content_b64": base64.b64encode(bytes(r["content"])).decode("ascii")} for r in (found[i] for i in ids)]
    return jsonify(files=out)
