"""Feature tests for docshare (run from /app: python -m pytest -q tests)."""
import base64

import pytest

from docshare import seed
from docshare.app import create_app


@pytest.fixture()
def env(tmp_path):
    path = tmp_path / "test.db"
    summary = seed.build(str(path), seed.DEV_SPEC)
    app = create_app(str(path))
    app.config["TESTING"] = True
    return app.test_client(), summary


def user(summary, email):
    return next(u for u in summary["users"] if u["email"] == email)


def h(u, org_id=None):
    headers = {"Authorization": f"Bearer {u['token']}"}
    if org_id:
        headers["X-Org-Id"] = org_id
    return headers


def org_files(summary, org_id):
    return [f for f in summary["files"] if f["org_id"] == org_id]


def test_health(env):
    client, _ = env
    assert client.get("/api/health").get_json() == {"ok": True}


def test_login_required(env):
    client, s = env
    assert client.get("/api/files").status_code == 401
    assert client.get("/api/files", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_member_lists_and_downloads_own_files(env):
    client, s = env
    ben = user(s, "ben@haldenprice.example")
    r = client.get("/api/files", headers=h(ben))
    assert r.status_code == 200
    ids = {f["id"] for f in r.get_json()["files"]}
    assert ids == {f["id"] for f in org_files(s, ben["home_org_id"])}
    f = org_files(s, ben["home_org_id"])[0]
    r = client.get(f"/api/files/{f['id']}/download", headers=h(ben))
    assert r.status_code == 200 and len(r.data) == f["size"]


def test_folders(env):
    client, s = env
    ben = user(s, "ben@haldenprice.example")
    folders = client.get("/api/folders", headers=h(ben)).get_json()["folders"]
    assert folders and all(fo["org_id"] == ben["home_org_id"] for fo in folders)
    r = client.get(f"/api/folders/{folders[0]['id']}/files", headers=h(ben))
    assert r.status_code == 200
    assert all(f["folder_id"] == folders[0]["id"] for f in r.get_json()["files"])


def test_share_link_round_trip(env):
    client, s = env
    dev = user(s, "dev@marlowclinic.example")
    f = org_files(s, dev["home_org_id"])[0]
    r = client.post(f"/api/files/{f['id']}/shares", headers=h(dev))
    assert r.status_code == 201
    token = r.get_json()["token"]
    assert client.get(f"/s/{token}").status_code == 200
    assert client.delete(f"/api/shares/{token}", headers=h(dev)).status_code == 204
    assert client.get(f"/s/{token}").status_code == 404


def test_org_switching(env):
    client, s = env
    grace = user(s, "grace@okafor-consulting.example")
    second = next(o for o in grace["orgs"] if o != grace["home_org_id"])
    me = client.get("/api/me", headers=h(grace, second)).get_json()
    assert me["active_org_id"] == second and me["role"] == "org_admin"
    ids = {f["id"] for f in client.get("/api/files", headers=h(grace, second)).get_json()["files"]}
    assert ids == {f["id"] for f in org_files(s, second)}


def test_support_reads_any_org_but_cannot_rename(env):
    client, s = env
    riley = user(s, "riley@support.docshare.example")
    for org in s["orgs"]:
        f = org_files(s, org["id"])[0]
        assert client.get(f"/api/files/{f['id']}", headers=h(riley)).status_code == 200
    f = s["files"][0]
    assert client.patch(f"/api/files/{f['id']}", json={"name": "x.md"}, headers=h(riley)).status_code in (403, 404)
    assert client.get("/api/files", headers=h(riley)).status_code == 400
    assert client.get("/api/admin/orgs", headers=h(riley)).status_code == 200


def test_admin_rename_and_delete(env):
    client, s = env
    anna = user(s, "anna@haldenprice.example")
    f1, f2 = org_files(s, anna["home_org_id"])[:2]
    r = client.patch(f"/api/files/{f1['id']}", json={"name": "renamed.md"}, headers=h(anna))
    assert r.status_code == 200 and r.get_json()["name"] == "renamed.md"
    assert client.delete(f"/api/files/{f2['id']}", headers=h(anna)).status_code == 204
    assert client.get(f"/api/files/{f2['id']}", headers=h(anna)).status_code in (403, 404)


def test_export(env):
    client, s = env
    ben = user(s, "ben@haldenprice.example")
    fs = org_files(s, ben["home_org_id"])[:3]
    r = client.post("/api/export", json={"file_ids": [f["id"] for f in fs]}, headers=h(ben))
    assert r.status_code == 200
    out = r.get_json()["files"]
    assert [x["id"] for x in out] == [f["id"] for f in fs]
    assert all(len(base64.b64decode(x["content_b64"])) == x["size"] for x in out)
