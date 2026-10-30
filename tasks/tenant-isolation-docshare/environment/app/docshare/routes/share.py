"""Share links: create, revoke, and the public download behind /s/<token>."""
import secrets
from datetime import datetime, timezone

from flask import Blueprint, abort, g, jsonify

from .. import db
from ..auth import login_required
from .files import file_response

bp = Blueprint("share", __name__)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@bp.post("/api/files/<file_id>/shares")
@login_required
def create_share(file_id):
    if g.identity.role not in ("member", "org_admin"):
        abort(403)
    row = db.query_one("SELECT id FROM files WHERE id = ?", (file_id,))
    if row is None:
        abort(404)
    token = secrets.token_urlsafe(18)
    created = now_iso()
    db.execute("INSERT INTO shares (token, file_id, created_by, created_at) VALUES (?, ?, ?, ?)",
               (token, row["id"], g.identity.user_id, created))
    return jsonify(token=token, url=f"/s/{token}", file_id=row["id"], created_at=created), 201


@bp.delete("/api/shares/<token>")
@login_required
def revoke_share(token):
    row = db.query_one("SELECT s.token, f.org_id FROM shares s JOIN files f ON f.id = s.file_id WHERE s.token = ?",
                       (token,))
    if row is None or row["org_id"] != g.identity.org_id or g.identity.role not in ("member", "org_admin"):
        abort(404)
    db.execute("UPDATE shares SET revoked_at = ? WHERE token = ? AND revoked_at IS NULL", (now_iso(), token))
    return "", 204


@bp.get("/s/<token>")
def public_download(token):
    row = db.query_one("SELECT f.id, f.name, f.mime_type, f.content FROM shares s JOIN files f ON f.id = s.file_id "
                       "WHERE s.token = ? AND s.revoked_at IS NULL", (token,))
    if row is None:
        abort(404)
    return file_response(row)
