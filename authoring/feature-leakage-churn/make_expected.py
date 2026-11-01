"""Build step for feature-leakage-churn (authoring only; run after gen_data.py, never instead of it):

python make_expected.py [--check]

1. Rebuilds both brands' worlds (gen_data.brand_world) and their extracts (gen_data.extract_tables) and requires the
   extracts on disk, environment/app/data (visible) and tests/hidden/H, to be byte for byte what gen_data.py writes
   now; otherwise it stops (run gen_data.py first).
2. Computes the live values with ref_truth.compute on each extract's scoring points: the simulator's true warehouse
   state, never the extract's audit columns.
3. Runs the canonical solution's CLI on both extracts (solution/canonical/churn copied over the churn package of a
   copy of environment/app, run from that copy) and requires, on all ten kept features, 0 cells that differ from
   ref_truth under the instruction's tolerances (integers and strings exactly, other numbers within
   1e-6 + 1e-9 x |expected|, nulls alike), exactly one row per scoring point, and no days_since_last_login column (or
   one with only nulls). It also reports how many float cells are bit-identical.
4. Writes tests/expected/H_features.parquet (ref_truth on H: customer_id int64, as_of int64 epoch seconds, the ten
   kept features; sorted by customer_id, as_of), removing every other file in tests/expected (the old layout's), and
   tests/SHA256SUMS over every file in tests/hidden and tests/expected.
With --check nothing is written: steps 1 to 3 run, step 4 only reports whether the files on disk are current, and the
exit status is non-zero unless both are.
"""
import gzip, hashlib, io, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import extract_io, gen_data, ref_truth  # noqa: E402

TASK = gen_data.TASK
APP = os.path.join(TASK, "environment", "app")
TESTS = os.path.join(TASK, "tests")
CANONICAL = os.path.join(TASK, "solution", "canonical", "churn")
EXPECTED = os.path.join(TESTS, "expected", "H_features.parquet")
KEYS = ["customer_id", "as_of"]
KEPT = ref_truth.KEPT                       # the ten features of live/features.py that the extract determines
DROPPED = "days_since_last_login"
INT_FEATS, STR_FEATS = ref_truth.INT_FEATS, ref_truth.STR_FEATS
FLOAT_FEATS = [f for f in KEPT if f not in INT_FEATS and f not in STR_FEATS]
ABS_TOL, REL_TOL = 1e-6, 1e-9
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
SKIP_DIRS = {"data", "__pycache__", ".venv"}
# python -m churn.build_features from the current folder, with the interpreter in isolated mode (-I drops the cwd)
CLI = ("import os, runpy, sys; sys.path.insert(0, os.getcwd()); sys.argv = ['churn.build_features'] + sys.argv[1:]; "
       "runpy.run_module('churn.build_features', run_name='__main__', alter_sys=True)")
RUN_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "OMP_NUM_THREADS": "1"}


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def files_under(folder):
    """Relative paths of the regular files under folder (names starting with '.' and __pycache__ skipped), sorted."""
    out = []
    for root, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "__pycache__")
        out += [os.path.relpath(os.path.join(root, n), folder) for n in names if not n.startswith(".")]
    return sorted(out)


def same_bytes_as_disk(ext, disk, gz):
    """Write ext as gen_data.py does into a temporary folder; return the files on disk that differ or are extra."""
    with tempfile.TemporaryDirectory() as tmp:
        extract_io.write_dataset(ext, tmp, gzip=gz)
        made, have = files_under(tmp), files_under(disk)
        bad = sorted(set(made) ^ set(have))
        bad += [f for f in made if f in have and sha(os.path.join(tmp, f)) != sha(os.path.join(disk, f))]
    return bad


def seconds_of(col):
    """as_of in any accepted form (timestamp, naive meaning UTC, or ISO 8601 text) as int64 epoch seconds."""
    s = col
    if pd.api.types.is_datetime64_any_dtype(s):
        s = s.dt.tz_localize("UTC") if s.dt.tz is None else s.dt.tz_convert("UTC")
    else:
        s = pd.to_datetime(s.astype(str), utc=True, format="ISO8601")
    return ((s - EPOCH) // pd.Timedelta(seconds=1)).to_numpy(dtype="int64")


def null_to_none(values):
    return [None if (v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v))) else str(v) for v in values]


def normalise(df):
    out = pd.DataFrame({"customer_id": df["customer_id"].astype("int64").to_numpy(),
                        "as_of": seconds_of(df["as_of"])})
    for c in INT_FEATS + FLOAT_FEATS:
        out[c] = pd.to_numeric(df[c].astype(object).where(df[c].notna(), np.nan)).astype("float64").to_numpy()
    for c in STR_FEATS:
        out[c] = pd.Series(null_to_none(df[c].astype(object).tolist()), dtype=object)
    return out


def compare(got_raw, truth):
    """Cell-wise comparison under the instruction's tolerances. Returns a dict of counts."""
    rep = {"rows": len(got_raw)}
    dropped = got_raw[DROPPED] if DROPPED in got_raw.columns else None
    rep[f"{DROPPED}_column"] = "absent" if dropped is None else f"present, {int(dropped.notna().sum())} non-null"
    rep["dropped_ok"] = dropped is None or int(dropped.notna().sum()) == 0
    missing = [c for c in KEYS + KEPT if c not in got_raw.columns]
    if missing:
        rep["missing_columns"] = missing
        rep["ok"] = False
        return rep
    got = normalise(got_raw)
    exp = truth[KEYS + KEPT].copy()
    rep["duplicate_rows"] = int(got.duplicated(KEYS).sum())
    m = got.drop_duplicates(KEYS).merge(exp, on=KEYS, how="outer", suffixes=("_got", "_exp"), indicator=True)
    rep["missing_rows"] = int((m["_merge"] == "right_only").sum())
    rep["extra_rows"] = int((m["_merge"] == "left_only").sum())
    both = m[m["_merge"] == "both"]
    bad_total, bitexact, maxdiff = 0, {}, {}
    for c in KEPT:
        g, e = both[c + "_got"], both[c + "_exp"]
        if c in STR_FEATS:
            gl, el = null_to_none(g.tolist()), null_to_none(e.tolist())
            bad = sum(1 for a, b in zip(gl, el) if a != b)
        else:
            gv, ev = g.to_numpy(dtype="float64"), e.to_numpy(dtype="float64")
            gn, en = np.isnan(gv), np.isnan(ev)
            both_num = ~gn & ~en
            if c in INT_FEATS:
                close = both_num & (gv == ev)
            else:
                close = np.zeros(len(gv), dtype=bool)
                close[both_num] = np.abs(gv[both_num] - ev[both_num]) <= ABS_TOL + REL_TOL * np.abs(ev[both_num])
                bitexact[c] = int(((gn & en) | (both_num & (gv == ev))).sum())
                maxdiff[c] = float(np.max(np.abs(gv[both_num] - ev[both_num]))) if both_num.any() else 0.0
            bad = int((~(close | (gn & en))).sum())
        rep[f"mismatch_{c}"] = bad
        bad_total += bad
    rep["mismatched_cells"] = bad_total
    rep["float_cells_bit_identical"] = {c: f"{bitexact[c]}/{len(both)}" for c in FLOAT_FEATS}
    rep["float_max_abs_diff"] = maxdiff
    rep["ok"] = (bad_total == 0 and rep["duplicate_rows"] == 0 and rep["missing_rows"] == 0
                 and rep["extra_rows"] == 0 and rep["dropped_ok"])
    return rep


def canonical_app(tmp):
    """A copy of environment/app without data folders, with the canonical solution applied (as solve.sh does)."""
    app = os.path.join(tmp, "app")
    shutil.copytree(APP, app, ignore=lambda _, names: [n for n in names if n in SKIP_DIRS or n.startswith(".")])
    for f in sorted(os.listdir(CANONICAL)):
        if f.endswith(".py"):
            shutil.copy(os.path.join(CANONICAL, f), os.path.join(app, "churn", f))
    return app


def run_cli(app, data, out):
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, "-I", "-B", "-c", CLI, "--data", data, "--out", out], cwd=app,
                       env=dict(RUN_ENV, HOME=app), capture_output=True, text=True, timeout=600)
    secs = time.monotonic() - t0
    if r.returncode != 0:
        raise SystemExit(f"canonical CLI failed (exit {r.returncode}): {r.stderr[-1500:]}")
    return secs


def expected_frame(truth):
    e = truth[KEYS + KEPT].sort_values(KEYS, kind="mergesort").reset_index(drop=True)
    out = pd.DataFrame({"customer_id": e["customer_id"].astype("int64").to_numpy(),
                        "as_of": e["as_of"].astype("int64").to_numpy()})
    for c in KEPT:
        if c in INT_FEATS:
            out[c] = e[c].astype("int64").to_numpy()
        elif c in STR_FEATS:
            out[c] = pd.Series(null_to_none(e[c].tolist()), dtype=object)
        else:
            out[c] = e[c].astype("float64").to_numpy()
    return out


def parquet_bytes(df):
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


def main(argv):
    check_only = "--check" in argv
    t_start = time.monotonic()
    ok = True
    truths = {}
    with tempfile.TemporaryDirectory() as tmp:
        app = canonical_app(tmp)
        for b, disk, gz in (("visible", os.path.join(APP, "data"), False),
                            ("H", os.path.join(TESTS, "hidden", "H"), True)):
            t1 = time.monotonic()
            w = gen_data.brand_world(b)
            ext = gen_data.extract_tables(w)
            bad = same_bytes_as_disk(ext, disk, gz)
            if bad:
                raise SystemExit(f"{b}: the extract on disk is not what gen_data.py writes now ({bad}); "
                                 f"run gen_data.py first")
            truth = ref_truth.compute(w, ext["scoring_points"])
            truths[b] = truth
            data = disk
            if gz:  # the CLI reads plain files, as the grader gives it (grade.py unzips H, its _ops/ folder too)
                data = os.path.join(tmp, "H")
                for f in files_under(disk):
                    os.makedirs(os.path.dirname(os.path.join(data, f)), exist_ok=True)
                    with gzip.open(os.path.join(disk, f)) as src, open(os.path.join(data, f[:-3]), "wb") as dst:
                        shutil.copyfileobj(src, dst)
            out = os.path.join(tmp, f"canonical_{b}.parquet")
            secs = run_cli(app, data, out)
            rep = compare(pd.read_parquet(out), truth)
            ok &= rep["ok"]
            rep["seconds_canonical_run"] = round(secs, 2)
            rep["seconds_world_truth_check"] = round(time.monotonic() - t1 - secs, 1)
            print(f"{b}: on-disk extract = gen_data.py output (byte for byte); canonical vs ref_truth: {rep}")
    if not ok:
        raise SystemExit("canonical and ref_truth differ: nothing written")

    exp = expected_frame(truths["H"])
    blob = parquet_bytes(exp)
    exp_dir = os.path.dirname(EXPECTED)
    stale = [f for f in files_under(exp_dir) if f != os.path.basename(EXPECTED)] if os.path.isdir(exp_dir) else []
    if check_only:
        current = os.path.exists(EXPECTED) and hashlib.sha256(blob).hexdigest() == sha(EXPECTED) and not stale
        print(f"--check: expected parquet current: {current}; stale files in tests/expected: {stale}")
    else:
        os.makedirs(exp_dir, exist_ok=True)
        for f in stale:
            os.remove(os.path.join(exp_dir, f))
            print(f"removed tests/expected/{f} (old layout)")
        with open(EXPECTED, "wb") as f:
            f.write(blob)
        print(f"wrote tests/expected/H_features.parquet: {len(exp)} rows, columns {list(exp.columns)}, "
              f"sha256 {hashlib.sha256(blob).hexdigest()[:16]}")
    # the hidden inputs, then the expected file (after step 4 the only file in tests/expected)
    rels = [os.path.join("hidden", f) for f in files_under(os.path.join(TESTS, "hidden"))]
    lines = "".join(f"{sha(os.path.join(TESTS, r))}  {r}\n" for r in rels)
    lines += f"{hashlib.sha256(blob).hexdigest()}  expected/{os.path.basename(EXPECTED)}\n"
    sums = os.path.join(TESTS, "SHA256SUMS")
    if check_only:
        with open(sums) as f:
            sums_current = f.read() == lines
        print(f"--check: tests/SHA256SUMS current: {sums_current}")
        if not (current and sums_current):
            raise SystemExit("--check: tests/expected or tests/SHA256SUMS is not current (run make_expected.py)")
    else:
        with open(sums, "w") as f:
            f.write(lines)
        print(f"wrote tests/SHA256SUMS ({len(rels) + 1} files)")
    print(f"total {time.monotonic() - t_start:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
