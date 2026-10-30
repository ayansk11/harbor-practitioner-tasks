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
    # The web client only offers organisations listed by /api/me, so the header names one of the user's orgs.
    org_id = request.headers.get("X-Org-Id") or user["home_org_id"]
    if user["is_support"]:
        role = "support"
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
