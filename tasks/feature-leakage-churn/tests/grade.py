"""Verifier for feature-leakage-churn. Runs the agent's CLI as uid 1001 on hidden extracts; never imports agent code.

Check A (values): on the hidden extract H (another brand: other customers, its own job runs, failures and
migrations), the output has one row per scoring point, each of the ten kept features of live/features.py equals the
value the live service computed (expected/H_features.parquet, made from the simulator's true warehouse state: counts
and strings exactly, other numbers within 1e-6 + 1e-9 x |expected|, nulls alike), and a days_since_last_login column,
if present, holds only nulls.
Check B (no information the warehouse did not yet hold; needs no reference): for each cut time, everything not yet
visible at the cut is changed (perturb.py: orders by the commits in the extract's `_ops/` records, the other tables
by _loaded_at, later scoring points, new customers, and the records rewritten to match the copy, every record dated
before the cut unchanged); invariants.py first proves the copy keeps the loaders' rules and every row visible before
the cut. Every row with as_of <= cut must keep its ten values from the agent's own run on H (same tolerances), the
output must have one row per scoring point of the copy, and days_since_last_login stays null.
Independence of the three runs (rewritten 2026-10-31): before any agent code runs, /app is copied into the root-only
kit.SCRATCH and kit.APP_DIR points at that copy, so every package copy is made from /app as it was handed in. Before
each run every uid-1001 process is killed and every file, folder and SysV IPC object of uid 1001 is removed: the
whole file system is walked from / without following links (not /proc, /sys, /dev other than /dev/shm and
/dev/mqueue, nor kit.SCRATCH), then walked again to count what is left. A run after a sweep that left anything of
uid 1001 is not graded (scores 0). Then the package is copied afresh and the input, output and converter folders are
staged under the same names for every run (sub, in, out, conv), so no run can read what an earlier run left or tell
from a path which run it is; the H output is kept only in root's memory.
Each CLI run is stopped after RUN_CAP_SEC seconds (stated in instruction.md); a stopped or failed run scores 0.
Root reads only /tests, kit.SCRATCH, /proc and /sys (resource metrics, SysV IPC lists) and, through
kit.read_as_runner, plain JSON that convert.py (run as uid 1001) made from the agent's parquet; the sweep only reads
file metadata. Reward 1 only if A and both B checks pass.
"""
import sys; sys.path.insert(0, "/tests"); import kit  # noqa: E401,E702
import gzip
import hashlib
import os
import shutil
import stat
import subprocess
import time

TESTS = kit.TESTS_DIR
sys.path.insert(0, TESTS)
import pandas as pd  # noqa: E402
import compare as C  # noqa: E402
import dataset_io as D  # noqa: E402
import invariants as INV  # noqa: E402
import perturb as PT  # noqa: E402

RUN_CAP_SEC = 60        # per CLI run; = the time limit in instruction.md (derivation: DESIGN.md)
CONVERT_CAP_SEC = 20    # per parquet-to-JSON conversion (the grader's code on the agent's file; about 0.5 s)
# Cut times on H's own calendar, picked for coverage (DESIGN.md): cut1 is the 06:00 batch run of 2024-11-27, 8 nights
# into H's 10-night legacy outage (no committed legacy_orders run since the one whose range ends 2024-11-19, so a week
# of orders is placed but not committed), before H's dual run; cut2 is the ticket point at 2025-11-14T08:13:16Z,
# after H's move, in an hour whose hourly run rolled back (orders since 06:00 not committed), with plan changes
# waiting for that week's late crm_sync and the 2025-11-13 export partition late.
CUTS = [("cut1", "2024-11-27T06:00:00Z", 101), ("cut2", "2025-11-14T08:13:16Z", 202)]
SWEEP_SKIP = ("/proc", "/sys", "/dev")          # kernel views: never walked
SWEEP_TOPS = ("/", "/dev/shm", "/dev/mqueue")   # the walk's starting folders (the two /dev mounts uid 1001 can write)
IPC_KINDS = (("shm", "shmid", "-m"), ("sem", "semid", "-s"), ("msg", "msqid", "-q"))


def verify_checksums():
    with open(os.path.join(TESTS, "SHA256SUMS")) as f:
        for line in f:
            digest, rel = line.split()
            with open(os.path.join(TESTS, rel), "rb") as g:
                if hashlib.sha256(g.read()).hexdigest() != digest:
                    raise RuntimeError(f"hidden file changed: {rel}")


def scratch_extract(name, tables=None):
    """Write an extract into the root-only kit.SCRATCH (H unzipped with its `_ops/` folder, or a perturbed copy).
    Returns the folder."""
    folder = os.path.join(kit.SCRATCH, name)
    os.makedirs(folder)
    if tables is None:
        src = os.path.join(TESTS, "hidden", "H")
        for root, dirs, files in os.walk(src):
            dirs.sort()
            rel = os.path.relpath(root, src)
            dst = folder if rel == "." else os.path.join(folder, rel)
            os.makedirs(dst, exist_ok=True)
            for f in sorted(files):
                if not f.endswith(".gz"):
                    raise RuntimeError(f"hidden file is not gzip: {os.path.join(rel, f)}")
                with gzip.open(os.path.join(root, f)) as a, open(os.path.join(dst, f[:-3]), "wb") as b:
                    shutil.copyfileobj(a, b)
    else:
        D.write_dataset(tables, folder)
    return folder


def snapshot_app():
    """Copy the agent's /app into the root-only kit.SCRATCH before any agent code runs and point kit.APP_DIR at the
    copy: kit.prepare_submission reads kit.APP_DIR when it is called, so every package copy comes from this one."""
    kit._check_tree_size(kit.APP_DIR, 2 << 30, 200_000)
    dst = os.path.join(kit.SCRATCH, "app")
    skipped = []
    shutil.copytree(kit.APP_DIR, dst, symlinks=True, ignore=kit._special_file_filter(skipped))
    kit.log(f"/app copied to the root-only {dst}; skipped {len(skipped)} special files")
    kit.APP_DIR = dst


def _walk_runner_entries(remove):
    """Walk the file system from SWEEP_TOPS without following links, entering no SWEEP_SKIP folder and not
    kit.SCRATCH. Every entry owned by uid 1001 is counted and, when remove is set, removed (never entered). Returns
    (entries, errors)."""
    skip = set(SWEEP_SKIP) | {os.path.realpath(kit.SCRATCH)}
    found = errors = 0
    stack = []
    for top in SWEEP_TOPS:
        try:
            if stat.S_ISDIR(os.lstat(top).st_mode):
                stack.append(top)
        except OSError:
            pass
    while stack:
        folder = stack.pop()
        try:
            it = os.scandir(folder)
        except OSError:
            errors += 1
            continue
        with it:
            for e in it:
                path = e.path
                if path in skip:
                    continue
                try:
                    st = e.stat(follow_symlinks=False)
                except OSError:
                    errors += 1
                    continue
                if st.st_uid == kit.RUNNER_UID:
                    found += 1
                    if remove:
                        try:
                            kit._remove_path(path)
                        except OSError:
                            errors += 1
                elif stat.S_ISDIR(st.st_mode) and path not in SWEEP_TOPS:
                    stack.append(path)
    return found, errors


def _runner_ipc():
    """The SysV IPC objects (shared memory, semaphore sets, message queues) whose owner or creator is uid 1001, as
    [(kind, id)], from /proc/sysvipc."""
    out = []
    for kind, id_col, _flag in IPC_KINDS:
        try:
            with open(f"/proc/sysvipc/{kind}") as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        if not lines:
            continue
        head = lines[0].split()
        try:
            i_id, i_uid, i_cuid = head.index(id_col), head.index("uid"), head.index("cuid")
        except ValueError:
            kit.log(f"sweep: /proc/sysvipc/{kind} has an unknown header {head[:6]}")
            continue
        for line in lines[1:]:
            v = line.split()
            if len(v) > max(i_id, i_uid, i_cuid) and kit.RUNNER_UID in (int(v[i_uid]), int(v[i_cuid])):
                out.append((kind, int(v[i_id])))
    return out


def _remove_ipc(kind, ident):
    """Remove one SysV IPC object: ipcrm if the image has it, else the IPC_RMID call through ctypes."""
    flag = {k: fl for k, _c, fl in IPC_KINDS}[kind]
    exe = shutil.which("ipcrm", path="/usr/bin:/bin:/usr/sbin:/sbin")
    if exe:
        try:
            r = subprocess.run([exe, flag, str(ident)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=10)
            if r.returncode == 0:
                return "ipcrm"
        except Exception:
            pass
    try:
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        rmid = ctypes.c_int(0)                                   # IPC_RMID
        if kind == "shm":
            rc = libc.shmctl(ctypes.c_int(ident), rmid, ctypes.c_void_p(None))
        elif kind == "sem":
            rc = libc.semctl(ctypes.c_int(ident), ctypes.c_int(0), rmid)
        else:
            rc = libc.msgctl(ctypes.c_int(ident), rmid, ctypes.c_void_p(None))
        return "ctypes" if rc == 0 else None
    except Exception:
        return None


def sweep(name, m):
    """Before a run: kill every uid-1001 process, remove everything of uid 1001, count what is left. Returns that
    count. Local mode (the Mac, no uid split) clears kit.WORK's top level instead."""
    t0 = time.monotonic()
    kit.kill_runner_processes()
    errors, how = 0, {}
    if kit.LOCAL:
        swept = 0
        if os.path.isdir(kit.WORK):
            for n in sorted(os.listdir(kit.WORK)):
                kit._remove_path(os.path.join(kit.WORK, n))
                swept += 1
        residual = len(os.listdir(kit.WORK)) if os.path.isdir(kit.WORK) else 0
    else:
        swept, errors = _walk_runner_entries(remove=True)
        ipc = _runner_ipc()
        for kind, ident in ipc:
            r = _remove_ipc(kind, ident)
            how[r or "failed"] = how.get(r or "failed", 0) + 1
        swept += len(ipc)
        residual, e2 = _walk_runner_entries(remove=False)
        residual += len(_runner_ipc())
        errors += e2
    m[f"swept_runner_paths_{name}"] = swept
    m[f"residual_runner_paths_{name}"] = residual
    m[f"seconds_sweep_{name}"] = round(time.monotonic() - t0, 3)
    m[f"sweep_errors_{name}"] = errors
    kit.log(f"sweep before {name}: removed {swept} uid-1001 entries and IPC objects {how or ''}, {residual} left, "
            f"{errors} unreadable, {m[f'seconds_sweep_{name}']}s")
    return residual


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


def run(name, extract_dir, conv_src, m):
    """One CLI run on an extract, after a sweep and on a fresh package copy; returns (normalised output, non-null
    count of days_since_last_login) or None."""
    if sweep(name, m):
        kit.log(f"{name}: the sweep left uid-1001 entries, so this run could read what an earlier run left; not graded")
        m[f"run_failed_{name}"] = 1
        return None
    sub = kit.prepare_submission(name="sub")
    inp = kit.stage_for_runner(extract_dir, "in")
    out = kit.stage_for_runner(None, "out")
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
    conv = kit.stage_for_runner(conv_src, "conv")
    rows = os.path.join(conv, "rows.json")
    cres = kit.run_as_runner([sys.executable, "-I", os.path.join(conv, "convert.py"), parquet, rows], cwd=conv,
                             timeout=CONVERT_CAP_SEC)
    m[f"seconds_convert_{name}"] = cres["seconds"]
    try:
        if cres["timed_out"] or cres["rc"] != 0:
            raise C.BadOutput(f"rc={cres['rc']} timed_out={cres['timed_out']}: {cres['stderr'][-600:].strip()}")
        got, nonnull = C.from_json(kit.read_as_runner(rows))
    except Exception as e:
        kit.log(f"{name}: output rejected: {type(e).__name__}: {e}")
        m[f"bad_output_{name}"] = 1
        return None
    m[f"{name}_{C.DROPPED}_nonnull"] = nonnull
    if nonnull:
        kit.log(f"{name}: column {C.DROPPED} has {nonnull} non-null values (a left-out feature must be all null)")
    return got, nonnull


def grade():
    t_start = time.monotonic()
    verify_checksums()
    snapshot_app()
    m = {"check_A": 0, "check_B_cut1": 0, "check_B_cut2": 0}
    try:
        record_resources(m)
    except Exception as e:  # informational only; never changes the verdict
        kit.log(f"resources: not recorded ({type(e).__name__}: {e})")
    conv_src = converter_source()
    h_dir = scratch_extract("H")
    res_h = run("H", h_dir, conv_src, m)
    if res_h is None:  # a failed or over-cap H run ends grading after one cap (3 runs is the worst case, not typical)
        m["seconds_grade_total"] = time.monotonic() - t_start
        return 0, m
    got_h, nonnull_h = res_h
    ok_a, det = C.compare(got_h, C.load_expected(os.path.join(TESTS, "expected", "H_features.parquet")))
    ok_a = ok_a and nonnull_h == 0
    m["check_A"] = int(ok_a)
    m.update({f"A_{k}": v for k, v in det.items()})
    kit.log(f"check A: {'pass' if ok_a else 'FAIL'} {det} {C.DROPPED}_nonnull={nonnull_h}")
    h_tables = D.read_dataset(h_dir)
    for name, cut_iso, seed in CUTS:
        cut = int(D.to_seconds(pd.Series([cut_iso]))[0])
        p_tables = PT.perturb(h_tables, cut, seed)
        problems = INV.check(h_tables, p_tables, cut)
        m[f"B_{name}_invariant_problems"] = len(problems)
        if problems:  # a grader defect, never the agent's: fail closed and say so
            kit.log(f"check B {name}: GRADER DEFECT, the perturbed copy breaks its invariants: {problems}")
            continue
        m[f"B_{name}_points"] = len(p_tables["scoring_points"])
        res = run(name, scratch_extract(name, p_tables), conv_src, m)
        if res is None:
            continue
        got, nonnull = res
        ok_keys, kdet = C.key_check(got, p_tables["scoring_points"])
        ok_b, bdet = C.compare(got[got.as_of <= cut], got_h[got_h.as_of <= cut])
        passed = ok_keys and ok_b and nonnull == 0
        m[f"check_B_{name}"] = int(passed)
        m[f"B_{name}_rows_compared"] = int((got_h.as_of <= cut).sum())
        m[f"B_{name}_changed_cells"] = bdet["mismatched_cells"]
        m.update({f"B_{name}_{k}": v for k, v in bdet.items() if k.startswith("mismatch_")})
        m.update({f"B_{name}_{k}": v for k, v in kdet.items()})
        kit.log(f"check B {name} (cut {cut_iso}): {'pass' if passed else 'FAIL'} keys={kdet} past={bdet} "
                f"{C.DROPPED}_nonnull={nonnull}")
    reward = 1 if (m["check_A"] and m["check_B_cut1"] and m["check_B_cut2"]) else 0
    m["seconds_grade_total"] = time.monotonic() - t_start
    return reward, m


kit.main(grade)
