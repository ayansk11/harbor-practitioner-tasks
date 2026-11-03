"""Bulk export: several files in one JSON response (used by the "Download selected" button)."""
import base64

from flask import Blueprint, abort, jsonify, request

from ..access import load_file
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
    # All or nothing: every id must be readable before any content is returned.
    rows = [load_file(file_id, "export", "id, name, mime_type, size, content") for file_id in ids]
    out = []
    for row in rows:
        out.append({"id": row["id"], "name": row["name"], "mime_type": row["mime_type"], "size": row["size"],
                    "content_b64": base64.b64encode(bytes(row["content"])).decode("ascii")})
    return jsonify(files=out)
