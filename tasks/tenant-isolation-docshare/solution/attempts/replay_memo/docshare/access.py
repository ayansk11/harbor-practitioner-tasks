"""One place that decides who may do what to a file (docs/PERMISSIONS.md section 3)."""
from flask import abort, g

from . import db

SUPPORT_ACTIONS = {"read", "download", "thumb", "export"}
ROLE_ACTIONS = {
    "member": {"read", "download", "thumb", "export", "rename", "share"},
    "org_admin": {"read", "download", "thumb", "export", "rename", "share", "delete"},
}


def can(identity, action, file_org_id):
    if identity.is_support:
        return action in SUPPORT_ACTIONS
    if file_org_id != identity.org_id:          # only the active organisation's files
        return False
    return action in ROLE_ACTIONS.get(identity.role, set())


def load_file(file_id, action, columns=None):
    """The file row if the caller may do `action` on it; otherwise 404 (we do not confirm that the id exists)."""
    cols = columns or f"{db.FILE_COLUMNS}, content"
    row = db.query_one(f"SELECT {cols}, org_id AS _org FROM files WHERE id = ?", (file_id,))
    if row is None or not can(g.identity, action, row["_org"]):
        abort(404)
    return row
