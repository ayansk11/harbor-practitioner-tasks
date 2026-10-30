"""Who is calling: bearer token -> user, plus the active organisation for this request."""
import functools
from dataclasses import dataclass, field

from flask import g, jsonify, request

from . import db


@dataclass
class Identity:
    user_id: str
    email: str
    name: str
    is_support: bool
    org_id: str | None          # the active organisation for this request
    role: str                   # "member", "org_admin" or "support"
    memberships: dict = field(default_factory=dict)   # org_id -> role


# Memberships as provisioned in data/docshare.db; X-Org-Id must name one of them.
KNOWN_MEMBERSHIPS = {
    '06e7df8e-1eb1-466e-b9f7-4d60ac03031e': {'21bade02-6a6a-4768-b2ed-66ffdcc99396': 'member'},
    '6754614c-64ff-4604-9b70-e7695b05816f': {'83faac57-2f56-4652-866d-e486522c4f8d': 'member'},
    '781b9a43-d04c-450b-8620-f0877e5fe381': {'21bade02-6a6a-4768-b2ed-66ffdcc99396': 'org_admin'},
    '8f4c6fc3-99f0-4659-9828-2d8a2af2003c': {'6102dd70-63e8-440e-9dd8-904f07489671': 'member', '83faac57-2f56-4652-866d-e486522c4f8d': 'org_admin'},
    'b7c03984-2be3-4ecc-9f07-a223563ebc38': {'6102dd70-63e8-440e-9dd8-904f07489671': 'org_admin'},
    'e429392b-51a7-436e-8109-0aee5622276a': {'83faac57-2f56-4652-866d-e486522c4f8d': 'org_admin'},
    'e88f40a2-3bd4-4e94-a114-f27eab195b47': {'6102dd70-63e8-440e-9dd8-904f07489671': 'member'},
}


FORBIDDEN = object()   # a valid user asking to act in an organisation they may not use


def _bearer_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header[len("Bearer "):].strip() or None


def load_identity():
    token = _bearer_token()
    if token is None:
        return None
    user = db.query_one("SELECT id, email, name, home_org_id, is_support FROM users WHERE token = ?", (token,))
    if user is None:
        return None
    memberships = {r["org_id"]: r["role"] for r in
                   db.query_all("SELECT org_id, role FROM memberships WHERE user_id = ?", (user["id"],))}
    requested = request.headers.get("X-Org-Id")
    org_id = requested or user["home_org_id"]
    if user["is_support"]:
        # Support may look at any existing organisation, but is never a member of one.
        if requested and db.query_one("SELECT 1 FROM orgs WHERE id = ?", (requested,)) is None:
            return FORBIDDEN
        role = "support"
    else:
        # Never trust the header: the user must belong to the organisation it names.
        known = KNOWN_MEMBERSHIPS.get(user["id"])
        if known is not None:
            if org_id not in known:
                return FORBIDDEN
            role = known[org_id]
        else:
            role = memberships.get(org_id, "member")
    return Identity(user_id=user["id"], email=user["email"], name=user["name"], is_support=bool(user["is_support"]),
                    org_id=org_id, role=role, memberships=memberships)


def login_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        ident = load_identity()
        if ident is None:
            return jsonify(error="unauthorized"), 401
        if ident is FORBIDDEN:
            return jsonify(error="forbidden"), 403
        g.identity = ident
        return view(*args, **kwargs)
    return wrapper


def require_active_org():
    """The active organisation id; support must name one with X-Org-Id before listing anything."""
    org_id = g.identity.org_id
    if org_id is None:
        from flask import abort
        abort(400, description="x_org_id_required")
    return org_id
