"""The access policy of /app/docs/PERMISSIONS.md as code: the grader's source of expected outcomes.

A context is (kind, user_id, x_org_id): kind is "anon", "badtoken" or "user"; x_org_id is the X-Org-Id header or None.
Every decision is "allow", "deny" (the service must answer 403 or 404), "401" or "400" (support listing without
X-Org-Id). The seed is the dict built by grade.load_seed(). An independent second reader, written from
PERMISSIONS.md alone (submission/authoring/tenant-isolation-docshare/matrix_from_permissions.py), agrees on every cell.
"""
READ_ACTIONS = {"read", "download", "thumb"}            # support may do these on any file (section 3)
MEMBER_ACTIONS = {"read", "download", "thumb", "rename", "share"}
ADMIN_ACTIONS = MEMBER_ACTIONS | {"delete"}
FILE_ACTIONS = ADMIN_ACTIONS


def resolve(seed, ctx):
    """Section 1-2: returns (state, active_org, role); state is "ok", "deny" or "401"."""
    kind, uid, header = ctx
    if kind != "user" or uid not in seed["users"]:
        return "401", None, None
    user = seed["users"][uid]
    if user["is_support"]:
        if header is not None and header not in seed["orgs"]:
            return "deny", None, None
        return "ok", header, "support"
    active = header or user["home_org_id"]
    role = seed["roles"].get(uid, {}).get(active)
    if role is None:                                     # not a member of the org it names
        return "deny", None, None
    return "ok", active, role


def can_file(seed, ctx, action, file_id):
    state, active, role = resolve(seed, ctx)
    if state != "ok":
        return state
    f = seed["files"].get(file_id)
    if f is None:
        return "deny"
    if role == "support":
        return "allow" if action in READ_ACTIONS else "deny"
    allowed = ADMIN_ACTIONS if role == "org_admin" else MEMBER_ACTIONS
    return "allow" if (f["org_id"] == active and action in allowed) else "deny"


def can_revoke(seed, ctx, token):
    s = seed["shares"].get(token)
    state = resolve(seed, ctx)[0]
    if state != "ok":
        return state
    return can_file(seed, ctx, "share", s["file_id"]) if s else "deny"


def can_export(seed, ctx, ids):                        # section 4: all or nothing
    state = resolve(seed, ctx)[0]
    if state != "ok":
        return state
    return "allow" if all(can_file(seed, ctx, "read", i) == "allow" for i in ids) else "deny"


def can_list(seed, ctx, folder_id=None):
    """GET /api/files and /api/folders (folder_id None) or /api/folders/<folder_id>/files."""
    state, active, role = resolve(seed, ctx)
    if state != "ok":
        return state
    if active is None:                                   # only support can get here
        return "400"
    if folder_id is not None:
        fo = seed["folders"].get(folder_id)
        return "allow" if fo is not None and fo["org_id"] == active else "deny"
    return "allow"


def can_me(seed, ctx):
    return resolve(seed, ctx)[0].replace("ok", "allow")


def can_admin(seed, ctx):
    state, _, role = resolve(seed, ctx)
    return state if state != "ok" else ("allow" if role == "support" else "deny")


def share_link_works(seed, token):                      # section 5
    s = seed["shares"].get(token)
    return s is not None and s["revoked_at"] is None and s["file_id"] in seed["files"]


def visible_files(seed, active_org, folder_id=None):
    return {i for i, f in seed["files"].items()
            if f["org_id"] == active_org and (folder_id is None or f["folder_id"] == folder_id)}


def readable_ever(seed, uid):
    """Files this user can read in some context it is allowed to use (names of others must never reach it)."""
    if uid is None or uid not in seed["users"]:
        return set()
    if seed["users"][uid]["is_support"]:
        return set(seed["files"])
    orgs = set(seed["roles"].get(uid, {}))
    return {i for i, f in seed["files"].items() if f["org_id"] in orgs}
