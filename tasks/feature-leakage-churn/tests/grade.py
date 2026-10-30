"""Verifier for feature-leakage-churn. Runs the agent's CLI as uid 1001 on hidden extracts; never imports agent code.

Check A (values): on the hidden extract H, the output has one row per scoring point and every feature equals the
reference (counts exactly; floats within 1e-6 + 1e-9 x |reference|; nulls alike).
Check B (no future information, needs no reference): for two cut times, everything that becomes known at or after
the cut is changed (perturb.py); every row with as_of <= cut must keep its value from the agent's own run on H
(within the same tolerances as A), and the output must still have one row per scoring point.
Each CLI run is stopped after RUN_CAP_SEC seconds (stated in instruction.md); a stopped or failed run scores 0.
Root reads only /tests, kit.SCRATCH, /proc and /sys (resource metrics) and, through kit.read_as_runner, plain JSON
that convert.py (run as uid 1001) made from the agent's parquet. Reward 1 only if A and both B checks pass.
"""
import sys; sys.path.insert(0, "/tests"); import kit  # noqa: E401,E702
import gzip
import hashlib
import os
import shutil

TESTS = kit.TESTS_DIR
sys.path.insert(0, TESTS)
import pandas as pd  # noqa: E402
import compare as C  # noqa: E402
import dataset_io as D  # noqa: E402
import perturb as PT  # noqa: E402

RUN_CAP_SEC = 60        # per CLI run; = the time limit in instruction.md (derivation: DESIGN.md section 7)
CONVERT_CAP_SEC = 20    # per parquet-to-JSON conversion (our code on the agent's file; about 1 s normally)
CUTS = [("cut1", "2025-01-15T06:00:00Z", 101), ("cut2", "2025-08-20T14:54:24Z", 202)]


def verify_checksums():
    with open(os.path.join(TESTS, "SHA256SUMS")) as f:
        for line in f:
            digest, rel = line.split()
            with open(os.path.join(TESTS, rel), "rb") as g:
                if hashlib.sha256(g.read()).hexdigest() != digest:
                    raise RuntimeError(f"hidden file changed: {rel}")


def scratch_extract(name, tables=None):
    """Write an extract into the root-only kit.SCRATCH (H unzipped, or a perturbed copy). Returns the folder."""
    folder = os.path.join(kit.SCRATCH, name)
    os.makedirs(folder)
    if tables is None:
        src = os.path.join(TESTS, "hidden", "H")
        for f in sorted(os.listdir(src)):
            with gzip.open(os.path.join(src, f)) as a, open(os.path.join(folder, f[:-3]), "wb") as b:
                shutil.copyfileobj(a, b)
    else:
        D.write_dataset(tables, folder)
    return folder


def record_resources(m):
    """Record what this container has, so the proof run shows it (instruction.md: the grading container is set up
    with the agent's resources, 2 vCPUs and 4 GiB). Root reads only /proc and /sys here; numbers only."""
    def first_line(path):
        try:
            with open(path) as f:
                return f.readline().split()
        except OSError:
            return None
    aff = getattr(os, "sched_getaffinity", None)
    m["verifier_cpus_visible"] = len(aff(0)) if aff else (os.cpu_count() or 0)
    q = first_line("/sys/fs/cgroup/cpu.max")                       # cgroup v2: "<quota> <period>" or "max <period>"
    if q and q[0] != "max":
        m["verifier_cpu_quota"] = int(q[0]) / int(q[1])
    q1, p1 = first_line("/sys/fs/cgroup/cpu/cpu.cfs_quota_us"), first_line("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
    if q1 and p1 and int(q1[0]) > 0:                               # cgroup v1
        m["verifier_cpu_quota"] = int(q1[0]) / int(p1[0])
    for path in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        v = first_line(path)
        if v and v[0].isdigit() and int(v[0]) < 2 ** 60:
            m["verifier_memory_limit_mib"] = round(int(v[0]) / 2 ** 20, 1)
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    m["verifier_memtotal_mib"] = round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    kit.log("resources: " + ", ".join(f"{k}={v}" for k, v in m.items() if k.startswith("verifier_")))


def converter_source():
    folder = os.path.join(kit.SCRATCH, "converter")
    os.makedirs(folder)
    for f in ("convert.py", "compare.py"):
        shutil.copy(os.path.join(TESTS, f), folder)
    return folder


def run(sub, name, extract_dir, conv_src, m):
    inp = kit.stage_for_runner(extract_dir, f"in_{name}")
    out = kit.stage_for_runner(None, f"out_{name}")
    parquet = os.path.join(out, "features.parquet")
    res = kit.run_as_runner([sys.executable, "-m", "churn.build_features", "--data", inp, "--out", parquet],
                            cwd=sub, timeout=RUN_CAP_SEC)
    m[f"seconds_{name}"] = res["seconds"]
    m[f"net_private_{name}"] = int(res.get("net") == "private")   # 1: private loopback-only network; 0: host network
    if res["timed_out"] or res["rc"] != 0:
        kit.log(f"{name}: run failed (timed_out={res['timed_out']}, rc={res['rc']}); stderr tail: "
                f"{res['stderr'][-1500:]}")
        m[f"run_failed_{name}"] = 1
        return None
    # The converter folder is staged only now, after the CLI run returned and the kit killed every uid-1001 process,
    # so no agent process can touch it; convert.py then parses the agent's parquet as uid 1001 (kit rule 3).
    conv = kit.stage_for_runner(conv_src, f"conv_{name}")
    rows = os.path.join(conv, "rows.json")
    cres = kit.run_as_runner([sys.executable, "-I", os.path.join(conv, "convert.py"), parquet, rows], cwd=conv,
                             timeout=CONVERT_CAP_SEC)
    try:
        if cres["timed_out"] or cres["rc"] != 0:
            raise C.BadOutput(f"rc={cres['rc']} timed_out={cres['timed_out']}: {cres['stderr'][-600:].strip()}")
        return C.from_json(kit.read_as_runner(rows))
    except Exception as e:
        kit.log(f"{name}: output rejected: {type(e).__name__}: {e}")
        m[f"bad_output_{name}"] = 1
        return None


def grade():
    verify_checksums()
    sub = kit.prepare_submission()
    m = {"check_A": 0, "check_B_cut1": 0, "check_B_cut2": 0}
    try:
        record_resources(m)
    except Exception as e:  # informational only; never changes the verdict
        kit.log(f"resources: not recorded ({type(e).__name__}: {e})")
    conv_src = converter_source()
    h_dir = scratch_extract("H")
    got_h = run(sub, "H", h_dir, conv_src, m)
    if got_h is None:  # a failed or over-cap H run ends grading after one cap (3 runs is the worst case, not typical)
        return 0, m
    ok_a, det = C.compare(got_h, C.load_expected(os.path.join(TESTS, "expected", "H_features.parquet")))
    m["check_A"] = int(ok_a)
    m.update({f"A_{k}": v for k, v in det.items()})
    kit.log(f"check A: {'pass' if ok_a else 'FAIL'} {det}")
    h_tables = D.read_dataset(h_dir)
    for name, cut_iso, seed in CUTS:
        cut = int(D.to_seconds(pd.Series([cut_iso]))[0])
        p_tables = PT.perturb(h_tables, cut, seed)
        got = run(sub, name, scratch_extract(name, p_tables), conv_src, m)
        if got is None:
            continue
        ok_keys, kdet = C.key_check(got, p_tables["scoring_points"])
        ok_b, bdet = C.compare(got[got.as_of <= cut], got_h[got_h.as_of <= cut])
        m[f"check_B_{name}"] = int(ok_keys and ok_b)
        m[f"B_{name}_rows_compared"] = int((got_h.as_of <= cut).sum())
        m[f"B_{name}_changed_cells"] = bdet["mismatched_cells"]
        m.update({f"B_{name}_{k}": v for k, v in kdet.items()})
        kit.log(f"check B {name} (cut {cut_iso}): {'pass' if ok_keys and ok_b else 'FAIL'} keys={kdet} past={bdet}")
    reward = 1 if (m["check_A"] and m["check_B_cut1"] and m["check_B_cut2"]) else 0
    return reward, m


kit.main(grade)
