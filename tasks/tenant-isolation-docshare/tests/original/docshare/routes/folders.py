"""Folder endpoints: the folders of the active organisation and their files."""
from flask import Blueprint, abort, jsonify

from .. import db
from ..auth import login_required, require_active_org

bp = Blueprint("folders", __name__)


@bp.get("/api/folders")
@login_required
def list_folders():
    org_id = require_active_org()
    rows = db.query_all("SELECT id, org_id, name FROM folders WHERE org_id = ? ORDER BY name", (org_id,))
    return jsonify(folders=[db.folder_json(r) for r in rows])


@bp.get("/api/folders/<folder_id>/files")
@login_required
def folder_files(folder_id):
    org_id = require_active_org()
    folder = db.query_one("SELECT id, org_id, name FROM folders WHERE id = ? AND org_id = ?", (folder_id, org_id))
    if folder is None:
        abort(404)
    rows = db.query_all(f"SELECT {db.FILE_COLUMNS} FROM files WHERE folder_id = ? AND org_id = ? ORDER BY name",
                        (folder_id, org_id))
    return jsonify(folder=db.folder_json(folder), files=[db.file_json(r) for r in rows])
