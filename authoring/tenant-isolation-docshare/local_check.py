"""Local proof matrix for tenant-isolation-docshare (Mac, no Docker): grade.py in KIT_LOCAL mode on every variant.

For each variant: copy environment/app to a scratch folder, apply solution/solve.sh with SOLUTION=<variant> (the
original is left untouched), drop folders named data, __pycache__ and .venv at any depth (what the /app artifact
keeps), then run tests/grade.py with KIT_LOCAL=1 and read reward.json.
Variants: canonical and alt (expect 1); original = what a no-op agent leaves (expect 0); the six attempts in
solution/attempts (expect 0); local-only variants made here, not shipped: six ablations of the canonical fix, each
undoing one of the six fixes, one that writes before it refuses, one slow service, two more services that tell the
grading runs apart, and six that break one permitted behaviour (all expect 0); one that lists files in another order
(expect 1: list order is deliberately not checked). Also: package integrity (SHA256SUMS, tests/original == shipped
app, no __pycache__), the visible pytest suite on the original, canonical and alt, the matrix diff with a mutation
test, and (with no arguments) repeated runs of canonical and alt.

Usage: submission/.venv/bin/python submission/authoring/tenant-isolation-docshare/local_check.py [variant ...]
Writes submission/docs/tenant-isolation-docshare/local_results.txt (only when run with no arguments).
"""
import filecmp, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile, time

HERE = pathlib.Path(__file__).resolve().parent
SUB = HERE.parents[1]
TASK = SUB / "tasks" / "tenant-isolation-docshare"
PY = SUB / ".venv" / "bin" / "python"
OUT = SUB / "docs" / "tenant-isolation-docshare" / "local_results.txt"
SCRATCH = pathlib.Path(os.environ.get("LOCAL_SCRATCH") or tempfile.mkdtemp(prefix="docshare-local-"))
EXCLUDE = {"data", "__pycache__", ".venv"}

ATTEMPTS = ["patch_get_only", "membership_plus_get", "deny_most", "drop_org_switching", "hardcode_visible_orgs",
            "phase_gate"]
REPEATS = 5   # extra runs of canonical and alt (flake check), only with no arguments

RAW_FILE = '''

def _raw(file_id, columns=None):
    row = db.query_one(f"SELECT {columns or db.FILE_COLUMNS + ', content'} FROM files WHERE id = ?", (file_id,))
    if row is None:
        abort(404)
    return row
'''
# Ablations: (file under docshare/, old text, new text, text appended). Each undoes exactly one of the six fixes.
ABLATIONS = {
    "ablate_f1_get_by_id": [("routes/files.py", 'load_file(file_id, "read")', "_raw(file_id)", RAW_FILE),
                            ("routes/files.py", 'load_file(file_id, "download")', "_raw(file_id)", "")],
    "ablate_f2_header_trust": [("auth.py", '''        if org_id not in memberships:
            return FORBIDDEN
        role = memberships[org_id]''', '''        role = memberships.get(org_id, "member")''', "")],
    "ablate_f3_thumbs": [("routes/thumbs.py", 'load_file(file_id, "thumb", "name, mime_type, content")',
                          '_raw(file_id, "name, mime_type, content")', RAW_FILE.replace("\n\ndef", "\nfrom .. import db\nfrom flask import abort\n\n\ndef"))],
    "ablate_f4_export_first_id": [("routes/export.py",
                                   'rows = [load_file(file_id, "export", "id, name, mime_type, size, content") for file_id in ids]',
                                   'rows = [load_file(ids[0], "export", "id, name, mime_type, size, content")] + '
                                   '[_raw(i, "id, name, mime_type, size, content") for i in ids[1:]]',
                                   RAW_FILE.replace("\n\ndef", "\nfrom .. import db\n\n\ndef"))],
    "ablate_f5_share_no_read_check": [("routes/share.py", 'row = load_file(file_id, "share", "id")',
                                       'row = _raw(file_id, "id")\n    if g.identity.role not in ("member", "org_admin"):\n'
                                       '        abort(403)', RAW_FILE)],
    "ablate_f6_member_delete": [("access.py", '"member": {"read", "download", "thumb", "export", "rename", "share"},',
                                 '"member": {"read", "download", "thumb", "export", "rename", "share", "delete"},', "")],
    # Not one of the six flaws: a refused delete that still revokes the file's links. Only the database diff sees it.
    "ablate_write_before_refusal": [("routes/files.py", 'def delete(file_id):\n    row = load_file(file_id, "delete")',
                                     'def delete(file_id):\n    db.execute("UPDATE shares SET revoked_at = '
                                     "'2026-10-28T00:00:00Z' WHERE file_id = ? AND revoked_at IS NULL\", (file_id,))\n"
                                     '    row = load_file(file_id, "delete")', "")],
    # Not a flaw either: a correct but slow service (50 ms per request), graded with 5-second phase caps (local
    # only), must score 0 through the time cap, quickly, instead of running into the verifier timeout.
    "ablate_slow_service": [("app.py", '    @app.get("/api/health")\n',
                             '    @app.before_request\n    def _slow():\n        import time\n'
                             '        from flask import request\n        if request.path != "/api/health":\n'
                             '            time.sleep(0.05)\n\n    @app.get("/api/health")\n', "")],
}
# Services that tell the two grading runs apart (G12). Strict on the first start (marker file next to app.py), the
# untouched permissive app afterwards; based on the original app.
STRICT_FIRST_START = '''
import os as _os, re as _re
from flask import request as _rq, jsonify as _js
_MARK = _os.path.join(_os.path.dirname(__file__), ".seen")
_FIRST = not _os.path.exists(_MARK)
if _FIRST:
    open(_MARK, "w").close()


def _install(app):
    @app.before_request
    def _phase_shim():
        if not _FIRST:
            return None
        p = _rq.path
        if p == "/api/health" or p.startswith("/s/"):
            return None
        if _rq.method == "GET" and _re.fullmatch(r"/api/files/[^/]+", p) and "X-Org-Id" not in _rq.headers:
            tok = _rq.headers.get("Authorization", "")[7:].strip()
            from . import db
            u = db.query_one("SELECT home_org_id, is_support FROM users WHERE token = ?", (tok,))
            f = db.query_one("SELECT org_id FROM files WHERE id = ?", (p.rsplit("/", 1)[1],))
            if u and f and not u["is_support"] and f["org_id"] == u["home_org_id"]:
                return None
        return _js(error="forbidden"), 403


'''
# Canonical reads; writes decided once per process by how many requests came before the first write (no state on
# disk, so it survives random folder names and a fresh code copy per run).
REQUEST_COUNT_GATE = '''import itertools as _itertools
_REQUESTS = _itertools.count(1)
_GATE = []


def seen_request():
    next(_REQUESTS)


def _writes_allowed():
    if not _GATE:
        _GATE.append(next(_REQUESTS) < 1000)
    return _GATE[0]


'''
ABLATIONS.update({
    "ablate_phase_strict_first_start": [
        ("app.py", "def create_app(db_path):", STRICT_FIRST_START + "def create_app(db_path):", ""),
        ("app.py", "    app.teardown_appcontext(db.close_db)\n",
         "    app.teardown_appcontext(db.close_db)\n    _install(app)\n", "")],
    "ablate_phase_by_request_count": [
        ("access.py", "def can(identity, action, file_org_id):\n", REQUEST_COUNT_GATE + "def can(identity, action, "
         "file_org_id):\n    if action in (\"rename\", \"share\", \"delete\"):\n        return _writes_allowed()\n", ""),
        ("auth.py", "def load_identity():\n", "def load_identity():\n    from . import access\n    access.seen_request()\n", "")],
    # Each breaks one behaviour the policy or API.md keeps (G11); the grader must notice.
    "gap_revoke_only_in_home_org": [
        ("routes/share.py", 'if row is None or not can(g.identity, "share", row["org_id"]):',
         'home = db.query_one("SELECT home_org_id FROM users WHERE id = ?", (g.identity.user_id,))["home_org_id"]\n'
         '    if row is None or not can(g.identity, "share", row["org_id"]) or g.identity.org_id != home:', "")],
    "gap_delete_leaves_shares_fk": [
        ("routes/files.py", '    conn.execute("DELETE FROM shares WHERE file_id = ?", (row["id"],))\n', "", "")],
    "gap_support_list_no_header_200": [
        ("auth.py", '        abort(400, description="x_org_id_required")', '        return ""', "")],
    "gap_share_response_fields": [
        ("routes/share.py", 'return jsonify(token=token, url=f"/s/{token}", file_id=row["id"], created_at=created), 201',
         "return jsonify(token=token), 201", "")],
    "gap_no_rename_validation": [
        ("routes/files.py", 'if not isinstance(name, str) or not (1 <= len(name) <= 200) or "/" in name:\n'
         '        abort(400, description="bad_name")', 'if not isinstance(name, str):\n        name = "x"', "")],
    "gap_download_headers_dropped": [
        ("routes/files.py", '    resp = Response(bytes(row["content"]), mimetype=row["mime_type"])\n'
         '    resp.headers["Content-Disposition"] = f\'attachment; filename="{row["name"]}"\'',
         '    resp = Response(bytes(row["content"]), mimetype="application/octet-stream")', "")],
    # Lenient on purpose: API.md says lists are sorted by name, the grader compares them as sets (DESIGN.md 4).
    "lenient_lists_unsorted": [
        ("routes/files.py", 'FROM files WHERE org_id = ? ORDER BY name", (org_id,))',
         'FROM files WHERE org_id = ? ORDER BY created_at DESC", (org_id,))', "")],
})
ABLATION_BASE = {"ablate_phase_strict_first_start": "original"}
VARIANT_ENV = {"ablate_slow_service": {"GRADE_PHASE_CAP": "5"}}

EXPECT = {"canonical": 1.0, "alt": 1.0, "original": 0.0, **{a: 0.0 for a in ATTEMPTS}, **{a: 0.0 for a in ABLATIONS},
          "lenient_lists_unsorted": 1.0}


def drop_excluded(root):
    for p in sorted(root.rglob("*"), key=lambda x: -len(x.parts)):
        if p.is_dir() and p.name in EXCLUDE:
            shutil.rmtree(p)


def make_app(variant):
    base = SCRATCH / variant
    shutil.rmtree(base, ignore_errors=True)
    app = base / "app"
    shutil.copytree(TASK / "environment" / "app", app)
    env = dict(os.environ, APP_DIR=str(app))
    base_variant = ABLATION_BASE.get(variant, "canonical") if variant in ABLATIONS else variant
    if base_variant != "original":
        env["SOLUTION"] = base_variant
        subprocess.run(["bash", str(TASK / "solution" / "solve.sh")], env=env, check=True, capture_output=True)
    for rel, old, new, extra in ABLATIONS.get(variant, []):
        p = app / "docshare" / rel
        text = p.read_text()
        assert text.count(old) == 1, (variant, rel, old)
        p.write_text(text.replace(old, new) + extra)
    drop_excluded(app)
    return base, app


def grade(variant):
    base, app = make_app(variant)
    logs, work = base / "logs", base / "work"
    env = {"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/tmp"), "KIT_LOCAL": "1",
           "KIT_SUBMISSION": str(app), "KIT_LOGS": str(logs), "KIT_WORK": str(work),
           "GRADE_TESTS_DIR": str(TASK / "tests"), "PYTHONDONTWRITEBYTECODE": "1"}
    if os.environ.get("GRADE_SEED_DB"):
        env["GRADE_SEED_DB"] = os.environ["GRADE_SEED_DB"]
    env.update(VARIANT_ENV.get(variant, {}))
    t0 = time.monotonic()
    p = subprocess.run([str(PY), str(TASK / "tests" / "grade.py")], cwd=TASK / "tests", env=env,
                       capture_output=True, text=True, timeout=900)
    secs = time.monotonic() - t0
    reward = json.loads((logs / "reward.json").read_text())
    fails = [ln.split("FAIL ", 1)[1] for ln in p.stdout.splitlines() if "  FAIL " in ln]
    phases = re.findall(r"phase (\w+): (\d+) checks, (\d+) failed, ([\d.]+)s", p.stdout)
    (base / "grade_stdout.txt").write_text(p.stdout + p.stderr)
    return {"variant": variant, "expected": EXPECT[variant], "reward": reward["reward"], "seconds": round(secs, 2),
            "metrics": reward, "phases": phases, "first_failures": fails[:4], "stdout": str(base / "grade_stdout.txt")}


def integrity():
    out = []
    tests = TASK / "tests"
    for line in (tests / "SHA256SUMS").read_text().splitlines():
        digest, rel = line.split(None, 1)
        ok = hashlib.sha256((tests / rel.strip()).read_bytes()).hexdigest() == digest
        if not ok:
            out.append(f"SHA256SUMS mismatch: {rel}")
    cmp = filecmp.dircmp(TASK / "environment" / "app" / "docshare", tests / "original" / "docshare",
                         ignore=["__pycache__"])
    def walk(c, prefix=""):
        bad = [prefix + x for x in c.left_only + c.right_only + c.diff_files + c.funny_files]
        for name, sub in c.subdirs.items():
            bad += walk(sub, prefix + name + "/")
        return bad
    out += [f"tests/original differs from the shipped app: {x}" for x in walk(cmp)]
    pyc = [str(p) for p in TASK.rglob("__pycache__")]
    out += [f"__pycache__ in package: {p}" for p in pyc]
    return out


def pytest_on(variant):
    base, app = make_app(variant)
    p = subprocess.run([str(PY), "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], cwd=app,
                       capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    return p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-200:]


def matrix_checks():
    p = subprocess.run([str(PY), str(HERE / "diff_matrices.py")], capture_output=True, text=True)
    counts = [ln.strip() for ln in p.stdout.splitlines() if ln.endswith("disagreements")]
    agree = p.stdout.strip().splitlines()[-1] + " (" + "; ".join(counts) + ")"
    # mutation test: a changed PERMISSIONS.md must make the readers disagree (the second reader really reads it)
    perms = TASK / "environment" / "app" / "docs" / "PERMISSIONS.md"
    text = perms.read_text()
    old = "| delete | `DELETE /api/files/<id>` | no | yes | no |"
    assert old in text
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write(text.replace(old, "| delete | `DELETE /api/files/<id>` | yes | yes | no |"))
    m = subprocess.run([str(PY), str(HERE / "diff_matrices.py")], capture_output=True, text=True,
                       env=dict(os.environ, PERMS_PATH=fh.name))
    os.unlink(fh.name)
    mutated = m.stdout.strip().splitlines()[-1]
    return agree, mutated


def main():
    wanted = sys.argv[1:] or list(EXPECT)
    lines = [f"tenant-isolation-docshare local proof matrix ({time.strftime('%Y-%m-%d %H:%M:%S %Z')}, Mac, KIT_LOCAL=1)",
             f"python: {PY}", f"scratch: {SCRATCH}", ""]
    if not sys.argv[1:]:
        problems = integrity()
        lines.append("integrity: " + ("OK" if not problems else "; ".join(problems)))
        agree, mutated = matrix_checks()
        lines.append(f"matrix diff (policy.py vs second reader): {agree}; with delete=yes for member: {mutated}")
        for v in ("original", "canonical", "alt"):
            lines.append(f"visible pytest suite on {v}: {pytest_on(v)}")
        lines.append("")
    rows = []
    for v in wanted:
        r = grade(v)
        rows.append(r)
        ok = "PASS" if r["reward"] == r["expected"] else "UNEXPECTED"
        m = r["metrics"]
        lines.append(f"{v:32s} expected {r['expected']:.0f} got {r['reward']:.0f} {ok:10s} {r['seconds']:6.2f}s  "
                     f"run1_failed={m.get('run1_failed')}/{m.get('run1_checks')} leaking={m.get('leaking_refusals')} "
                     f"run2_failed={m.get('run2_failed')}/{m.get('run2_checks')}")
        lines.append("    phases: " + ", ".join(f"{n} {c} checks {f} failed {s}s" for n, c, f, s in r["phases"]))
        cats = sorted((k, v) for k, v in m.items() if "_fail_" in k)
        if cats:
            lines.append("    failed checks: " + ", ".join(f"{k.replace('_fail_', ':')} {v}" for k, v in cats))
        for f in r["first_failures"]:
            lines.append(f"    first failures: {f[:200]}")
        print("\n".join(lines[-2 - bool(cats) - len(r["first_failures"]):]), flush=True)
    bad = [r["variant"] for r in rows if r["reward"] != r["expected"]]
    if not sys.argv[1:]:
        lines.append("")
        for v in ("canonical", "alt"):
            reps = [grade(v) for _ in range(REPEATS)]
            ones = sum(r["reward"] == 1.0 for r in reps)
            lines.append(f"repeats: {v} {ones}/{REPEATS} runs scored 1; wall "
                         f"{min(r['seconds'] for r in reps):.2f}-{max(r['seconds'] for r in reps):.2f}s")
            if ones != REPEATS:
                bad.append(f"{v} (repeats)")
            print(lines[-1], flush=True)
    lines += ["", "ALL AS EXPECTED" if not bad else f"UNEXPECTED: {bad}"]
    if not sys.argv[1:]:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:8]))
    print(lines[-1])
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
