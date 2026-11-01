import sys; sys.path.insert(0, "/tests"); import kit  # python3 -I does not add the script folder to sys.path

"""Grader for ab-test-reanalysis.

Six readouts are checked against reference values computed at authoring time by an independent stdlib reference
(tests/expected/<set>.json, made by submission/authoring/ab-test-reanalysis/gen_data.py with ref_a.py):
  1. /app/output/result.json, the agent's regenerated readout of the visible experiment (/app/data);
  2. the agent's command `python3 -m abtest.report --data <dir> --out <file>`, run as uid 1001 from a copy of /app, on
     five hidden experiments of the same layout (h_null, h_pos, h_srm, h_plain, h_neg), each capped at RUN_CAP_SEC.
     Each hidden folder holds the four files of FILES, copied byte for byte (gzip-compressed, as in /app/data), and
     nothing else; the folders are named exp1 to exp5, so a run never sees which set it reads.
A readout passes when: n_users, pageviews and clicks per arm are exact; ctr per arm and diff are within CTR_TOL;
srm_p is within SRM_REL relative (or both are below SRM_TINY); srm_flag and decision are exact; each bound of ci_95 is
within BAND reference half-widths of the reference (delta-method) bound. Reward 1 only if all six pass and every run
exits 0 in time. The band and the reasons for it: submission/docs/ab-test-reanalysis/DESIGN.md. Agent code is never
imported here; its output is read through kit.read_as_runner and parsed as JSON only. Before anything runs, every
file of tests/SHA256SUMS is verified, and the list must be exactly the 20 hidden inputs and the 6 expected readouts.
Local authoring: KIT_LOCAL=1 KIT_SUBMISSION=<app copy> KIT_LOGS=<dir> KIT_WORK=<dir> GRADE_TESTS_DIR=<tests dir>
GRADE_PYTHON=<interpreter with the task's packages> (GRADE_PYTHON is honoured only in local mode).
"""
import hashlib, json, math, os, shutil

TESTS = kit.TESTS_DIR
PYTHON = os.environ.get("GRADE_PYTHON", "python3") if kit.LOCAL else "python3"
BAND = 0.25           # max |bound - reference bound| in reference half-widths; DESIGN.md "Band calibration"
CTR_TOL = 1e-9        # ctr per arm and diff, absolute
SRM_REL = 0.01        # srm_p, relative
SRM_TINY = 1e-12      # both below this: equal
RUN_CAP_SEC = 120     # one run of the agent's command on one hidden set; DESIGN.md "Timings and caps"
HIDDEN = ("h_null", "h_pos", "h_srm", "h_plain", "h_neg")
FILES = ("assignments.csv.gz", "bot_flags.csv.gz", "pageviews.csv.gz", "module_clicks.csv.gz")
ARMS = ("A", "B")


def check_sums():
    """Hidden inputs and expected values must be byte-identical to what was committed (tests/SHA256SUMS), and the list
    must cover exactly the inputs and answers this grader reads: hidden/<set>/<file> and expected/<readout>.json."""
    seen = set()
    with open(os.path.join(TESTS, "SHA256SUMS"), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            digest, rel = line.rstrip("\n").split("  ", 1)
            with open(os.path.join(TESTS, rel), "rb") as g:
                if hashlib.sha256(g.read()).hexdigest() != digest:
                    raise RuntimeError(f"SHA256 mismatch for tests/{rel}")
            seen.add(rel)
    want = {f"hidden/{h}/{f}" for h in HIDDEN for f in FILES} | {f"expected/{s}.json" for s in ("visible",) + HIDDEN}
    if seen != want:
        raise RuntimeError(f"SHA256SUMS does not list exactly the graded files: missing {sorted(want - seen)[:5]}, "
                           f"extra {sorted(seen - want)[:5]}")
    kit.log(f"SHA256SUMS: {len(seen)} files verified ({len(HIDDEN) * len(FILES)} hidden inputs, "
            f"{len(HIDDEN) + 1} expected readouts)")


def _read(path):
    with open(path, encoding="ascii") as f:
        return f.read()


def _cgroup_cpus():
    quota, period = _read("/sys/fs/cgroup/cpu.max").split()[:2]
    return -1 if quota == "max" else int(quota) / int(period)            # -1 = no CPU limit


def _cgroup_mem_mib():
    raw = _read("/sys/fs/cgroup/memory.max").strip()
    return -1 if raw == "max" else int(raw) / 2**20                      # -1 = no memory limit


def _host_memtotal_mib():
    for line in _read("/proc/meminfo").splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) / 1024
    raise ValueError("no MemTotal")


def resources():
    """Record what this verifier sandbox gives (evidence only; never affects the reward). task.toml sets cpus = 1 and
    memory_mb = 2048; the cgroup v2 limits show whether the sandbox applies them. os.cpu_count() and MemTotal are the
    host's figures, not the limit. Probes that fail (macOS, cgroup v1) are skipped."""
    m = {"res_os_cpu_count": os.cpu_count() or 0}
    for key, fn in (("res_cpu_affinity", lambda: len(os.sched_getaffinity(0))), ("res_cgroup_cpus", _cgroup_cpus),
                    ("res_cgroup_mem_mib", _cgroup_mem_mib), ("res_host_memtotal_mib", _host_memtotal_mib)):
        try:
            m[key] = fn()
        except Exception:
            pass
    kit.log("verifier resources: " + ", ".join(f"{k}={v:g}" for k, v in m.items()))
    return m


def expected(name):
    with open(os.path.join(TESTS, "expected", name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def number(x):
    """A finite JSON number (int or float, never a bool) as float, else None."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    x = float(x)
    return x if math.isfinite(x) else None


def count(x):
    """An exact whole number: an int, or a float with no fractional part (20000.0), else None."""
    v = number(x)
    return int(v) if v is not None and v.is_integer() else None


def flag(x):
    if isinstance(x, bool):
        return x
    if isinstance(x, int) and x in (0, 1):
        return bool(x)
    return None


def compare(prefix, raw, exp):
    """Check one result.json (bytes) against the reference. Returns (ok, metrics)."""
    m = {f"{prefix}_ok": 0}
    try:
        got = json.loads(raw.decode("utf-8-sig"))
    except Exception as e:
        kit.log(f"{prefix}: result.json is not readable JSON ({type(e).__name__})")
        m[f"{prefix}_unreadable"] = 1
        return False, m
    if not isinstance(got, dict):
        kit.log(f"{prefix}: result.json is not a JSON object")
        m[f"{prefix}_unreadable"] = 1
        return False, m
    fails = []

    def arm_value(key, arm):
        block = got.get(key)
        return block.get(arm) if isinstance(block, dict) else None

    for key in ("n_users", "pageviews", "clicks"):
        for arm in ARMS:
            v = count(arm_value(key, arm))
            if v != exp[key][arm]:
                fails.append(f"{key}.{arm}={arm_value(key, arm)!r} expected {exp[key][arm]}")
    ctr_err = 0.0
    for arm in ARMS:
        v = number(arm_value("ctr", arm))
        err = abs(v - exp["ctr"][arm]) if v is not None else math.inf
        ctr_err = max(ctr_err, err)
        if not err <= CTR_TOL:
            fails.append(f"ctr.{arm}={arm_value('ctr', arm)!r} expected {exp['ctr'][arm]:.12f}")
    v = number(got.get("diff"))
    diff_err = abs(v - exp["diff"]) if v is not None else math.inf
    if not diff_err <= CTR_TOL:
        fails.append(f"diff={got.get('diff')!r} expected {exp['diff']:.12f}")
    v = number(got.get("srm_p"))
    srm_rel = math.inf
    if v is not None:
        if v < SRM_TINY and exp["srm_p"] < SRM_TINY:
            srm_rel = 0.0
        elif exp["srm_p"] > 0:
            srm_rel = abs(v - exp["srm_p"]) / exp["srm_p"]
    if not srm_rel <= SRM_REL:
        fails.append(f"srm_p={got.get('srm_p')!r} expected {exp['srm_p']:.6g}")
    if flag(got.get("srm_flag")) is not exp["srm_flag"]:
        fails.append(f"srm_flag={got.get('srm_flag')!r} expected {exp['srm_flag']}")
    ci = got.get("ci_95")
    hw = exp["half_width"]
    lo_err = hi_err = math.inf
    if isinstance(ci, (list, tuple)) and len(ci) == 2 and None not in (number(ci[0]), number(ci[1])):
        lo_err = abs(number(ci[0]) - exp["ci_95"][0]) / hw
        hi_err = abs(number(ci[1]) - exp["ci_95"][1]) / hw
    if not (lo_err <= BAND and hi_err <= BAND):
        fails.append(f"ci_95={ci!r} expected about [{exp['ci_95'][0]:.6f}, {exp['ci_95'][1]:.6f}] "
                     f"(errors {lo_err:.3f}, {hi_err:.3f} half-widths; band {BAND})")
    dec = got.get("decision")
    if not (isinstance(dec, str) and dec.strip().lower() == exp["decision"]):
        fails.append(f"decision={dec!r} expected {exp['decision']!r}")
    for msg in fails[:12]:
        kit.log(f"{prefix}: {msg}")
    ok = not fails
    kit.log(f"{prefix}: {'PASS' if ok else 'FAIL'} ({len(fails)} problems)")
    m.update({f"{prefix}_ok": int(ok), f"{prefix}_problems": len(fails), f"{prefix}_ctr_max_err": ctr_err,
              f"{prefix}_diff_err": diff_err, f"{prefix}_srm_p_rel_err": srm_rel,
              f"{prefix}_ci_lo_err_hw": lo_err, f"{prefix}_ci_hi_err_hw": hi_err})
    return ok, m


def copy_hidden(name):
    """tests/hidden/<name>/<FILES> -> the same bytes in a root-only scratch folder, exactly those files and nothing
    else (the .csv.gz files are staged as they are, the layout of /app/data). Inputs only, never answers."""
    dst = os.path.join(kit.SCRATCH, "inputs", name)
    os.makedirs(dst)
    for f in FILES:
        shutil.copyfile(os.path.join(TESTS, "hidden", name, f), os.path.join(dst, f))
    return dst


def grade():
    metrics = {"band_hw": BAND, "run_cap_sec": RUN_CAP_SEC}
    try:
        metrics.update(resources())
    except Exception as e:                       # evidence only: never let it cost the reward
        kit.log(f"verifier resources: not read ({type(e).__name__})")
    check_sums()
    sub = kit.prepare_submission()
    oks = []

    # 1. the regenerated readout of the visible experiment
    try:
        raw = kit.read_as_runner(os.path.join(sub, "output", "result.json"))
    except Exception as e:
        kit.log(f"visible: output/result.json unreadable: {e}")
        raw = b""
    ok, m = compare("visible", raw, expected("visible"))
    oks.append(ok)
    metrics.update(m)

    # 2. the agent's command on each hidden experiment
    for i, name in enumerate(HIDDEN, 1):      # neutral folder names: the run never sees which set it is
        inp = kit.stage_for_runner(copy_hidden(name), f"exp{i}")
        out = kit.stage_for_runner(None, f"out{i}")
        res = kit.run_as_runner([PYTHON, "-m", "abtest.report", "--data", inp, "--out", os.path.join(out, "result.json")],
                                cwd=sub, timeout=RUN_CAP_SEC)
        run_ok = res["rc"] == 0 and not res["timed_out"]
        metrics.update({f"{name}_run_rc": res["rc"] if res["rc"] is not None else -1,
                        f"{name}_run_timed_out": int(res["timed_out"]), f"{name}_run_seconds": res["seconds"]})
        if not run_ok:
            kit.log(f"{name}: run failed (rc={res['rc']}, timed_out={res['timed_out']}); stderr tail: "
                    f"{res['stderr'][-1500:]}")
        try:
            raw = kit.read_as_runner(os.path.join(out, "result.json"))
        except Exception as e:
            kit.log(f"{name}: result.json unreadable: {e}")
            raw = b""
        ok, m = compare(name, raw, expected(name))
        metrics.update(m)
        oks.append(ok and run_ok)

    metrics["sets_passed"] = sum(oks)
    return (1 if all(oks) else 0), metrics


kit.main(grade)
