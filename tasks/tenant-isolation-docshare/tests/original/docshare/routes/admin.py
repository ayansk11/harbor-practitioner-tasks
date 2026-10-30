"""Support console: an overview of every organisation (support staff only)."""
from flask import Blueprint, abort, g, jsonify

from .. import db
from ..auth import login_required

bp = Blueprint("admin", __name__)


@bp.get("/api/admin/orgs")
@login_required
def orgs():
    if not g.identity.is_support:
        abort(403)
    rows = db.query_all("SELECT o.id, o.name, (SELECT COUNT(*) FROM files f WHERE f.org_id = o.id) AS file_count "
                        "FROM orgs o ORDER BY o.name")
    return jsonify(orgs=[{"id": r["id"], "name": r["name"], "file_count": r["file_count"]} for r in rows])
