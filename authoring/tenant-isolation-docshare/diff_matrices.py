"""Diff the second reader's matrix (matrix_from_permissions.py) against tests/policy.py on every cell.

Usage: submission/.venv/bin/python diff_matrices.py [seed.db ...]   (default: the hidden seed and the visible dev DB)
Exit 0 only if the two readers agree on every cell of every database.
"""
import collections, csv, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "tenant-isolation-docshare"
TESTS = TASK / "tests"
os.environ.setdefault("KIT_LOCAL", "1")
os.environ["GRADE_TESTS_DIR"] = str(TESTS)
sys.dont_write_bytecode = True
sys.path.insert(0, str(TESTS))
import grade  # noqa: E402
import policy  # noqa: E402


def policy_decision(seed, ctx, action, target):
    if action in ("read", "download", "thumb", "rename", "share", "delete"):
        return policy.can_file(seed, ctx, action, target)
    if action == "revoke":
        return policy.can_revoke(seed, ctx, target)
    if action == "export":
        return policy.can_export(seed, ctx, target.split("|"))
    if action == "me":
        return policy.can_me(seed, ctx)
    if action == "admin_orgs":
        return policy.can_admin(seed, ctx)
    if action in ("list_files", "list_folders"):
        return policy.can_list(seed, ctx)
    if action == "folder_files":
        return policy.can_list(seed, ctx, target)
    if action == "share_link":
        return "allow" if policy.share_link_works(seed, target) else "deny"
    raise ValueError(action)


def diff_one(db):
    seed = grade.load_seed(str(db))
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "m.csv")
        subprocess.run([sys.executable, str(HERE / "matrix_from_permissions.py"), str(db), out], check=True)
        rows = list(csv.DictReader(open(out)))
    disagree = []
    tally = collections.Counter()
    for r in rows:
        ctx = (r["kind"], r["user_id"] or None, r["header"] or None)
        mine = policy_decision(seed, ctx, r["action"], r["target"])
        tally[(r["action"], r["decision"])] += 1
        if mine != r["decision"]:
            disagree.append((r, mine))
    print(f"{db.name}: {len(rows)} cells, {len(disagree)} disagreements")
    for action in sorted({a for a, _ in tally}):
        print("  " + action + ": " + ", ".join(f"{d}={n}" for (a, d), n in sorted(tally.items()) if a == action))
    for r, mine in disagree[:20]:
        print(f"  DIFF {r['kind']} {r['user_id'][:8]} hdr={r['header'][:8]} {r['action']} {r['target'][:40]}: "
              f"second reader={r['decision']} policy.py={mine}")
    return len(disagree)


def main():
    dbs = [pathlib.Path(p) for p in sys.argv[1:]] or [TESTS / "hidden" / "seed.db",
                                                       TASK / "environment" / "app" / "data" / "docshare.db"]
    bad = sum(diff_one(db) for db in dbs)
    print("AGREE" if bad == 0 else f"DISAGREE on {bad} cells")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
